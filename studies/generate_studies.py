"""
V-Forge R0: Dataset & Study Generation Module
Generates 5 controlled studies with deterministic pipelines.
"""
from __future__ import annotations
import json
import numpy as np
from pathlib import Path
from typing import Any
import core
from core import (
    Claim, UncertaintyRequirement, OracleDefinition,
    STUDIES_DIR, DATA_DIR, MODELS_DIR, SEED, compute_sha256
)

np.random.seed(SEED)


def generate_synthetic_dataset(n_samples: int, n_features: int, n_classes: int, seed: int = SEED) -> dict:
    """Generate a synthetic tabular dataset as numpy arrays."""
    rng = np.random.default_rng(seed)
    X = rng.standard_normal((n_samples, n_features))
    # Simple linear decision boundary with noise
    weights = rng.standard_normal(n_features)
    logits = X @ weights
    y = (logits > 0).astype(int) % n_classes
    # Add some class imbalance for realism
    if n_classes == 2:
        p = [0.6, 0.4]
    elif n_classes == 3:
        p = [0.5, 0.3, 0.2]
    else:
        p = [1.0 / n_classes] * n_classes
    y = rng.choice(n_classes, size=n_samples, p=p)
    return {"X": X, "y": y, "seed": seed}


def save_dataset(data: dict, path: Path) -> str:
    """Save dataset to JSON-compatible format and return SHA256."""
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "X": data["X"].tolist(),
        "y": data["y"].tolist(),
        "seed": data["seed"],
        "n_samples": len(data["y"]),
        "n_features": data["X"].shape[1],
        "n_classes": len(np.unique(data["y"])),
    }
    raw = json.dumps(payload, sort_keys=True).encode()
    path.write_bytes(raw)
    return compute_sha256(raw)


# ──────────────────────────────────────────────────────────────
# Study 1: MNIST Logistic Regression Comparison (comparative_superiority)
# ──────────────────────────────────────────────────────────────
def build_study_01() -> dict:
    """Simple binary classification on synthetic data — model A vs model B."""
    data = generate_synthetic_dataset(n_samples=500, n_features=20, n_classes=2, seed=SEED)
    data_path = DATA_DIR / "study_01_dataset.json"
    data_hash = save_dataset(data, data_path)

    # Train simple logistic regression (numpy implementation)
    from sklearn.linear_model import LogisticRegression
    from sklearn.model_selection import train_test_split
    X_train, X_test, y_train, y_test = train_test_split(
        data["X"], data["y"], test_size=0.2, random_state=SEED, stratify=data["y"]
    )

    # Model A: default logistic regression
    model_a = LogisticRegression(random_state=SEED, max_iter=1000)
    model_a.fit(X_train, y_train)
    pred_a = model_a.predict(X_test)
    acc_a = np.mean(pred_a == y_test)

    # Model B: weaker baseline (higher regularization)
    model_b = LogisticRegression(random_state=SEED, max_iter=1000, C=0.01)
    model_b.fit(X_train, y_train)
    pred_b = model_b.predict(X_test)
    acc_b = np.mean(pred_b == y_test)

    models_dir = MODELS_DIR / "study_01"
    models_dir.mkdir(parents=True, exist_ok=True)
    import joblib
    joblib.dump(model_a, models_dir / "model_a.pkl")
    joblib.dump(model_b, models_dir / "model_b.pkl")

    return {
        "study_id": "study_01",
        "data_path": str(data_path),
        "data_hash": data_hash,
        "train_size": len(X_train),
        "test_size": len(X_test),
        "model_a_acc": float(acc_a),
        "model_b_acc": float(acc_b),
        "claim": Claim(
            claim_id="study_01_claim_01",
            study_id="study_01",
            natural_language_claim=(
                "LogisticRegression with default C=1.0 achieves significantly higher accuracy "
                "than LogisticRegression with C=0.01 on the synthetic binary classification dataset."
            ),
            claim_type="comparative_superiority",
            population="synthetic_binary_classification",
            method="LogisticRegression",
            comparator="LogisticRegression with C=0.01",
            outcome_metric="accuracy",
            direction="improves",
            reported_value=round(acc_a, 4),
            uncertainty_requirement=UncertaintyRequirement(type="confidence_interval", value=None, level=0.95),
            protocol_constraints=[
                "fixed_random_seed_for_data_generation",
                "stratified_train_test_split",
                "identical_feature_space",
                "same_training_set_for_both_models",
            ],
            required_artifacts=[str(data_path), str(models_dir / "model_a.pkl"), str(models_dir / "model_b.pkl")],
            evidence_targets=["model_a_accuracy", "model_b_accuracy", "statistical_significance"],
            validity_conditions=[
                "data_split_is_identical_for_both_models",
                "no_data_leakage_between_train_and_test",
                "model_trained_on_train_only",
                "evaluated_on_test_only",
            ],
            abstention_conditions=[
                "if_models_cannot_be_loaded",
                "if_test_set_is_empty",
            ],
            oracle_definition=OracleDefinition(
                description="Re-run both models on the same data split and verify model_a_acc > model_b_acc with statistical significance.",
                input_artifacts=[str(data_path), str(models_dir / "model_a.pkl"), str(models_dir / "model_b.pkl")],
                output_format="boolean",
            ),
        ),
        "raw_data": data,
        "X_train": X_train, "X_test": X_test,
        "y_train": y_train, "y_test": y_test,
    }


# ──────────────────────────────────────────────────────────────
# Study 2: CIFAR-10 OOD Generalization (ood_generalization)
# ──────────────────────────────────────────────────────────────
def build_study_02() -> dict:
    """Simulate OOD generalization study with synthetic 'images'."""
    rng = np.random.default_rng(SEED)
    # In-distribution: structured data
    X_in = rng.normal(0, 1, (300, 64))
    y_in = rng.choice(4, size=300)
    # Out-of-distribution: shifted distribution
    X_ood = rng.normal(2, 1.5, (100, 64))
    y_ood = rng.choice(4, size=100)

    data_path = DATA_DIR / "study_02_dataset.json"
    data_hash = save_dataset({"X": X_in, "y": y_in, "seed": SEED}, data_path)
    ood_path = DATA_DIR / "study_02_ood.json"
    save_dataset({"X": X_ood, "y": y_ood, "seed": SEED + 1}, ood_path)

    from sklearn.linear_model import LogisticRegression
    from sklearn.model_selection import train_test_split
    X_train, X_test, y_train, y_test = train_test_split(
        X_in, y_in, test_size=0.2, random_state=SEED, stratify=y_in
    )
    model = LogisticRegression(random_state=SEED, max_iter=1000)
    model.fit(X_train, y_train)
    acc_id = np.mean(model.predict(X_test) == y_test)
    acc_ood = np.mean(model.predict(X_ood) == y_ood)

    models_dir = MODELS_DIR / "study_02"
    models_dir.mkdir(parents=True, exist_ok=True)
    import joblib
    joblib.dump(model, models_dir / "model.pkl")

    return {
        "study_id": "study_02",
        "data_path": str(data_path),
        "ood_path": str(ood_path),
        "data_hash": data_hash,
        "acc_id": float(acc_id),
        "acc_ood": float(acc_ood),
        "claim": Claim(
            claim_id="study_02_claim_01",
            study_id="study_02",
            natural_language_claim=(
                "A logistic regression model trained on in-distribution data maintains "
                "accuracy above 0.50 on out-of-distribution shifted data."
            ),
            claim_type="ood_generalization",
            population="synthetic_high_dimensional",
            method="LogisticRegression on shifted Gaussian",
            comparator="in-distribution accuracy",
            outcome_metric="ood_accuracy",
            direction="degrades",
            reported_value=round(acc_ood, 4),
            uncertainty_requirement=UncertaintyRequirement(type="none", value=None, level=0.95),
            protocol_constraints=[
                "same_model_for_id_and_ood",
                "ood_data_has_different_mean_and_variance",
                "no_ood_data_in_training",
            ],
            required_artifacts=[str(data_path), str(ood_path), str(models_dir / "model.pkl")],
            evidence_targets=["in_distribution_accuracy", "out_of_distribution_accuracy"],
            validity_conditions=[
                "ood_set_is_completely_separate_from_training",
                "model_not_fine_tuned_on_ood",
                "accuracy_computed_correctly",
            ],
            abstention_conditions=[
                "if_ood_dataset_cannot_be_loaded",
                "if_model_prediction_fails",
            ],
            oracle_definition=OracleDefinition(
                description="Reload model and recompute accuracy on OOD data; verify acc_ood < acc_id (degradation expected).",
                input_artifacts=[str(data_path), str(ood_path), str(models_dir / "model.pkl")],
                output_format="boolean",
            ),
        ),
        "raw_data": {"X_in": X_in, "y_in": y_in, "X_ood": X_ood, "y_ood": y_ood},
    }


# ──────────────────────────────────────────────────────────────
# Study 3: Probability Calibration Assessment (calibration)
# ──────────────────────────────────────────────────────────────
def build_study_03() -> dict:
    """Assess calibration of a probabilistic classifier."""
    rng = np.random.default_rng(SEED)
    X = rng.standard_normal((400, 10))
    y = (rng.standard_normal(400) > 0).astype(int)

    data_path = DATA_DIR / "study_03_dataset.json"
    data_hash = save_dataset({"X": X, "y": y, "seed": SEED}, data_path)

    from sklearn.linear_model import LogisticRegression
    from sklearn.model_selection import train_test_split
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=SEED, stratify=y
    )
    model = LogisticRegression(random_state=SEED, max_iter=1000)
    model.fit(X_train, y_train)
    probs = model.predict_proba(X_test)[:, 1]

    # Expected calibration error (ECE)
    n_bins = 5
    bin_edges = np.linspace(0, 1, n_bins + 1)
    ece = 0.0
    for i in range(n_bins):
        mask = (probs >= bin_edges[i]) & (probs < bin_edges[i + 1])
        if mask.sum() > 0:
            bin_acc = y_test[mask].mean()
            bin_conf = probs[mask].mean()
            ece += mask.sum() / len(y_test) * abs(bin_acc - bin_conf)

    models_dir = MODELS_DIR / "study_03"
    models_dir.mkdir(parents=True, exist_ok=True)
    import joblib
    joblib.dump(model, models_dir / "model.pkl")

    return {
        "study_id": "study_03",
        "data_path": str(data_path),
        "data_hash": data_hash,
        "ece": float(ece),
        "mean_confidence": float(probs.mean()),
        "claim": Claim(
            claim_id="study_03_claim_01",
            study_id="study_03",
            natural_language_claim=(
                "The logistic regression classifier is well-calibrated with ECE below 0.10 "
                "on the held-out test set."
            ),
            claim_type="calibration",
            population="synthetic_binary_classification",
            method="LogisticRegression with probability calibration",
            comparator="ideal calibration (ECE=0)",
            outcome_metric="expected_calibration_error",
            direction="no_change",
            reported_value=round(ece, 4),
            uncertainty_requirement=UncertaintyRequirement(type="none", value=None, level=0.95),
            protocol_constraints=[
                "probabilities_from_predict_proba",
                "test_set_not_used_for_calibration",
                "ece_computed_with_5_equal_width_bins",
            ],
            required_artifacts=[str(data_path), str(models_dir / "model.pkl")],
            evidence_targets=["ece_value", "confidence_distribution"],
            validity_conditions=[
                "ECE_computed_on_holdout_only",
                "no_post_hoc_calibration_applied",
            ],
            abstention_conditions=[
                "if_model_probabilities_cannot_be_loaded",
            ],
            oracle_definition=OracleDefinition(
                description="Reload model, recompute predict_proba on test set, recalculate ECE; verify ECE < 0.10.",
                input_artifacts=[str(data_path), str(models_dir / "model.pkl")],
                output_format="boolean",
            ),
        ),
        "raw_data": {"X": X, "y": y, "probs": probs},
    }


# ──────────────────────────────────────────────────────────────
# Study 4: Subgroup Robustness Analysis (subgroup_robustness)
# ──────────────────────────────────────────────────────────────
def build_study_04() -> dict:
    """Test model robustness across demographic subgroups."""
    rng = np.random.default_rng(SEED)
    n = 600
    X = rng.standard_normal((n, 10))
    # Assign subgroup labels
    subgroup = rng.choice(["A", "B", "C"], size=n, p=[0.4, 0.4, 0.2])
    y = ((X[:, 0] + X[:, 1] > 0).astype(int) ^ (subgroup == "C")).astype(int)

    data_path = DATA_DIR / "study_04_dataset.json"
    payload = {"X": X.tolist(), "y": y.tolist(), "subgroup": subgroup.tolist(), "seed": SEED}
    raw = json.dumps(payload, sort_keys=True).encode()
    data_path.write_bytes(raw)
    data_hash = compute_sha256(raw)

    from sklearn.linear_model import LogisticRegression
    from sklearn.model_selection import train_test_split
    X_train, X_test, y_train, y_test, sub_train, sub_test = train_test_split(
        X, y, subgroup, test_size=0.2, random_state=SEED
    )
    model = LogisticRegression(random_state=SEED, max_iter=1000)
    model.fit(X_train, y_train)
    pred = model.predict(X_test)

    group_accs = {}
    for g in ["A", "B", "C"]:
        mask = sub_test == g
        if mask.sum() > 0:
            group_accs[g] = float(np.mean(pred[mask] == y_test[mask]))

    min_acc = min(group_accs.values())
    max_acc = max(group_accs.values())
    disparity = max_acc - min_acc

    models_dir = MODELS_DIR / "study_04"
    models_dir.mkdir(parents=True, exist_ok=True)
    import joblib
    joblib.dump(model, models_dir / "model.pkl")

    return {
        "study_id": "study_04",
        "data_path": str(data_path),
        "data_hash": data_hash,
        "group_accuracies": group_accs,
        "disparity": float(disparity),
        "claim": Claim(
            claim_id="study_04_claim_01",
            study_id="study_04",
            natural_language_claim=(
                "The classifier achieves parity across subgroups with accuracy disparity "
                "below 0.05 between any two subgroups."
            ),
            claim_type="subgroup_robustness",
            population="synthetic_with_subgroups",
            method="LogisticRegression evaluated per subgroup",
            comparator="equal performance across subgroups",
            outcome_metric="accuracy_disparity",
            direction="no_change",
            reported_value=round(disparity, 4),
            uncertainty_requirement=UncertaintyRequirement(type="none", value=None, level=0.95),
            protocol_constraints=[
                "same_model_for_all_subgroups",
                "subgroups_defined_at_data_generation",
                "evaluation_on_test_set_only",
            ],
            required_artifacts=[str(data_path), str(models_dir / "model.pkl")],
            evidence_targets=["accuracy_per_group", "max_disparity"],
            validity_conditions=[
                "all_subgroups_present_in_test_set",
                "no_data_leakage_across_subgroups",
            ],
            abstention_conditions=[
                "if_any_subgroup_has_zero_test_samples",
            ],
            oracle_definition=OracleDefinition(
                description="Reload model, recompute per-group accuracy on test set, verify max_disparity < 0.05.",
                input_artifacts=[str(data_path), str(models_dir / "model.pkl")],
                output_format="boolean",
            ),
        ),
        "raw_data": {"X": X, "y": y, "subgroup": subgroup},
    }


# ──────────────────────────────────────────────────────────────
# Study 5: Statistical Significance Testing (statistical_evidence) — TEST (frozen)
# ──────────────────────────────────────────────────────────────
def build_study_05() -> dict:
    """Compare two methods with proper statistical testing."""
    rng = np.random.default_rng(SEED)
    n = 400
    X = rng.standard_normal((n, 8))
    y = (X[:, 0] + X[:, 1] > 0).astype(int)

    data_path = DATA_DIR / "study_05_dataset.json"
    data_hash = save_dataset({"X": X, "y": y, "seed": SEED}, data_path)

    from sklearn.linear_model import LogisticRegression
    from sklearn.model_selection import cross_val_score
    import scipy.stats as stats

    # Method A: full feature set
    model_a = LogisticRegression(random_state=SEED, max_iter=1000)
    scores_a = cross_val_score(model_a, X, y, cv=5, scoring="accuracy")

    # Method B: subset of features (removes informative feature 0)
    X_reduced = X[:, 1:]
    model_b = LogisticRegression(random_state=SEED, max_iter=1000)
    scores_b = cross_val_score(model_b, X_reduced, y, cv=5, scoring="accuracy")

    mean_a, mean_b = float(scores_a.mean()), float(scores_b.mean())
    _, p_val = stats.ttest_rel(scores_a, scores_b)

    models_dir = MODELS_DIR / "study_05"
    models_dir.mkdir(parents=True, exist_ok=True)
    import joblib
    joblib.dump(model_a, models_dir / "model_a.pkl")
    joblib.dump(model_b, models_dir / "model_b.pkl")

    return {
        "study_id": "study_05",
        "data_path": str(data_path),
        "data_hash": data_hash,
        "scores_a": scores_a.tolist(),
        "scores_b": scores_b.tolist(),
        "mean_a": mean_a,
        "mean_b": mean_b,
        "p_value": float(p_val),
        "claim": Claim(
            claim_id="study_05_claim_01",
            study_id="study_05",
            natural_language_claim=(
                "Method A (full features) achieves statistically significantly higher accuracy "
                "than Method B (feature-subset) with p < 0.05 under paired 5-fold CV."
            ),
            claim_type="statistical_evidence",
            population="synthetic_binary_classification",
            method="Paired 5-fold cross-validation t-test",
            comparator="LogisticRegression with full vs reduced features",
            outcome_metric="cross_validation_accuracy",
            direction="improves",
            reported_value=round(mean_a, 4),
            uncertainty_requirement=UncertaintyRequirement(type="p_value", value=float(p_val), level=0.05),
            protocol_constraints=[
                "same_data_splits_for_both_methods",
                "paired_test_statistic_used",
                "alpha=0.05_significance_threshold",
                "5_fold_cross_validation",
            ],
            required_artifacts=[str(data_path), str(models_dir / "model_a.pkl"), str(models_dir / "model_b.pkl")],
            evidence_targets=["mean_accuracy_method_a", "mean_accuracy_method_b", "p_value"],
            validity_conditions=[
                "cross_validation_folds_are_identical_between_methods",
                "no_data_leakage_across_folds",
                "paired_test_appropriate_for_correlated_estimates",
            ],
            abstention_conditions=[
                "if_p_value_cannot_be_computed",
                "if_any_fold_has_zero_samples",
            ],
            oracle_definition=OracleDefinition(
                description="Re-run 5-fold CV for both methods on same data, recompute paired t-test, verify p < 0.05.",
                input_artifacts=[str(data_path), str(models_dir / "model_a.pkl"), str(models_dir / "model_b.pkl")],
                output_format="boolean",
            ),
        ),
        "raw_data": {"X": X, "y": y, "scores_a": scores_a, "scores_b": scores_b},
    }


# ──────────────────────────────────────────────────────────────
# Main: Build all studies and save
# ──────────────────────────────────────────────────────────────
def build_all_studies() -> dict[str, dict]:
    builders = {
        "study_01": build_study_01,
        "study_02": build_study_02,
        "study_03": build_study_03,
        "study_04": build_study_04,
        "study_05": build_study_05,
    }
    results = {}
    for sid, builder in builders.items():
        print(f"Building {sid}...")
        study = builder()
        # Save claim
        claim_path = STUDIES_DIR / sid / "claim.json"
        study["claim"].save(claim_path)
        # Save study metadata
        meta = {k: v for k, v in study.items() if k != "raw_data"}
        meta_path = STUDIES_DIR / sid / "metadata.json"
        with open(meta_path, "w") as f:
            json.dump(meta, f, indent=2, default=str)
        # Save raw data separately
        raw_path = STUDIES_DIR / sid / "raw_data.json"
        with open(raw_path, "w") as f:
            json.dump(study["raw_data"], f, indent=2, default=str)
        results[sid] = study
        print(f"  → saved to {STUDIES_DIR / sid}")
    return results


if __name__ == "__main__":
    studies = build_all_studies()
    print("\nAll studies built successfully.")
    for sid, s in studies.items():
        c = s["claim"]
        print(f"  {sid}: {c.claim_type} | {c.natural_language_claim[:60]}...")
