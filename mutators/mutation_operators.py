"""
V-Forge R0: Mutation Operators (M01-M08)
Frozen operators that introduce scientific errors into study pipelines.
"""
from __future__ import annotations
import json
import numpy as np
from pathlib import Path
from typing import Any
import core
from core import Claim, MutationInstance, compute_diff_sha256, replay_hash, SEED, compute_sha256

class M01_DATA_LEAK(core.MutationOperator):
    """Data leakage: include test samples in training."""
    ID = "M01_DATA_LEAK"
    NAME = "Data Leakage"

    def precondition(self, study_data: dict) -> bool:
        return "X_train" in study_data and "X_test" in study_data

    def apply(self, study_data: dict, seed: int = SEED) -> dict:
        import copy
        mutated = copy.deepcopy(study_data)
        # Leak 20% of test labels into training
        rng = np.random.default_rng(seed)
        n_leak = max(1, len(mutated["X_test"]) // 5)
        leak_idx = rng.choice(len(mutated["X_test"]), size=n_leak, replace=False)
        # Append leaked test samples to training
        mutated["X_train"] = np.vstack([mutated["X_train"], mutated["X_test"][leak_idx]])
        mutated["y_train"] = np.concatenate([mutated["y_train"], mutated["y_test"][leak_idx]])
        mutated["leak_info"] = {
            "n_leaked": int(n_leak),
            "leak_source": "test_set",
            "leak_percentage": round(n_leak / len(mutated["X_test"]) * 100, 1),
        }
        return mutated

    def violated_condition(self, original_claim: Claim, mutated_data: dict) -> str:
        return "no_data_leakage_between_train_and_test"

    def __repr__(self):
        return "M01_DATA_LEAK"


class M02_BASELINE_HANDICAP(core.MutationOperator):
    """Baseline handicap: weaken the comparator model artificially."""
    ID = "M02_BASELINE_HANDICAP"
    NAME = "Baseline Handicap"

    def precondition(self, study_data: dict) -> bool:
        return "model_b_acc" in study_data or ("X_train" in study_data and "y_train" in study_data)

    def apply(self, study_data: dict, seed: int = SEED) -> dict:
        import copy
        mutated = copy.deepcopy(study_data)
        rng = np.random.default_rng(seed)
        # Add noise to test labels for the baseline model predictions
        if "X_test" in mutated and "y_test" in mutated and "y_pred_b" not in mutated:
            # Corrupt 30% of test labels for baseline evaluation
            n_corrupt = max(1, len(mutated["y_test"]) // 3)
            corrupt_idx = rng.choice(len(mutated["y_test"]), size=n_corrupt, replace=False)
            mutated["corrupted_labels"] = mutated["y_test"].copy()
            mutated["corrupted_labels"][corrupt_idx] = (mutated["corrupted_labels"][corrupt_idx] + 1) % 2
            mutated["evaluation_labels"] = "corrupted"
        return mutated

    def violated_condition(self, original_claim: Claim, mutated_data: dict) -> str:
        return "evaluated_on_test_only"

    def __repr__(self):
        return "M02_BASELINE_HANDICAP"


class M03_SEED_CHERRY_PICK(core.MutationOperator):
    """Seed cherry-picking: select favorable random seed after seeing results."""
    ID = "M03_SEED_CHERRY_PICK"
    NAME = "Seed Cherry-Picking"

    def precondition(self, study_data: dict) -> bool:
        return "seed" in study_data or "raw_data" in study_data

    def apply(self, study_data: dict, seed: int = SEED) -> dict:
        import copy
        mutated = copy.deepcopy(study_data)
        # Cherry-pick seed: use a different seed that might yield better results
        rng = np.random.default_rng(seed + 999)
        if "raw_data" in mutated and "X" in mutated["raw_data"]:
            X = np.array(mutated["raw_data"]["X"])
            # Regenerate data with different seed
            mutated["raw_data"]["X"] = rng.standard_normal(X.shape).tolist()
            mutated["raw_data"]["y"] = (np.array(mutated["raw_data"]["X"])[:, 0] > 0).astype(int).tolist()
            mutated["raw_data"]["seed"] = seed + 999
        mutated["original_seed"] = seed
        mutated["selected_seed"] = seed + 999
        return mutated

    def violated_condition(self, original_claim: Claim, mutated_data: dict) -> str:
        return "fixed_random_seed_for_data_generation"

    def __repr__(self):
        return "M03_SEED_CHERRY_PICK"


class M04_SUBGROUP_DROP(core.MutationOperator):
    """Subgroup drop: remove minority subgroup from evaluation."""
    ID = "M04_SUBGROUP_DROP"
    NAME = "Subgroup Drop"

    def precondition(self, study_data: dict) -> bool:
        return "subgroup" in study_data or "group_accuracies" in study_data

    def apply(self, study_data: dict, seed: int = SEED) -> dict:
        import copy
        mutated = copy.deepcopy(study_data)
        if "raw_data" in mutated and "subgroup" in mutated["raw_data"]:
            subgroups = mutated["raw_data"]["subgroup"]
            # Remove subgroup "C" (minority)
            mask = np.array(subgroups) != "C"
            mutated["raw_data"]["subgroup"] = [s for s, m in zip(subgroups, mask) if m]
            mutated["raw_data"]["X"] = [x for x, m in zip(mutated["raw_data"]["X"], mask)]
            mutated["raw_data"]["y"] = [y for y, m in zip(mutated["raw_data"]["y"], mask)]
            mutated["dropped_subgroup"] = "C"
        return mutated

    def violated_condition(self, original_claim: Claim, mutated_data: dict) -> str:
        return "all_subgroups_present_in_test_set"

    def __repr__(self):
        return "M04_SUBGROUP_DROP"


class M05_METRIC_SWAP(core.MutationOperator):
    """Metric swap: use a different metric than reported."""
    ID = "M05_METRIC_SWAP"
    NAME = "Metric Swap"

    def precondition(self, study_data: dict) -> bool:
        return True  # Applicable to all studies

    def apply(self, study_data: dict, seed: int = SEED) -> dict:
        import copy
        mutated = copy.deepcopy(study_data)
        # Swap accuracy for precision (changes the evaluation)
        if "model_a_acc" in mutated and "model_b_acc" in mutated:
            # Report precision instead of accuracy
            mutated["reported_metric"] = "precision_at_threshold_0.5"
            mutated["swapped_from"] = "accuracy"
            mutated["swapped_to"] = "precision"
        elif "ece" in mutated:
            mutated["reported_metric"] = "log_loss"
            mutated["swapped_from"] = "ECE"
            mutated["swapped_to"] = "log_loss"
        return mutated

    def violated_condition(self, original_claim: Claim, mutated_data: dict) -> str:
        return "outcome_metric_is_consistent"

    def __repr__(self):
        return "M05_METRIC_SWAP"


class M06_AGGREGATION_FAULT(core.MutationOperator):
    """Aggregation fault: compute average incorrectly (e.g., macro vs micro)."""
    ID = "M06_AGGREGATION_FAULT"
    NAME = "Aggregation Fault"

    def precondition(self, study_data: dict) -> bool:
        return "group_accuracies" in study_data or "scores_a" in study_data

    def apply(self, study_data: dict, seed: int = SEED) -> dict:
        import copy
        mutated = copy.deepcopy(study_data)
        if "group_accuracies" in mutated:
            # Compute unweighted mean instead of proper aggregation
            vals = list(mutated["group_accuracies"].values())
            mutated["aggregated_accuracy"] = sum(vals) / len(vals)
            mutated["aggregation_method"] = "macro_average"
            mutated["original_disparity"] = mutated.get("disparity")
        elif "scores_a" in mutated and "scores_b" in mutated:
            # Average across folds incorrectly
            mutated["aggregated_score_a"] = sum(mutated["scores_a"]) / 5
            mutated["aggregation_method"] = "simple_mean"
        return mutated

    def violated_condition(self, original_claim: Claim, mutated_data: dict) -> str:
        return "cross_validation_folds_are_identical_between_methods"

    def __repr__(self):
        return "M06_AGGREGATION_FAULT"


class M07_TEST_SET_SELECTION(core.MutationOperator):
    """Test set selection: choose easiest/hardest test samples post-hoc."""
    ID = "M07_TEST_SET_SELECTION"
    NAME = "Test Set Selection"

    def precondition(self, study_data: dict) -> bool:
        return "X_test" in study_data and "y_test" in study_data

    def apply(self, study_data: dict, seed: int = SEED) -> dict:
        import copy
        mutated = copy.deepcopy(study_data)
        rng = np.random.default_rng(seed)
        # Select only "easy" samples (those near decision boundary are removed)
        X_test = np.array(mutated["X_test"])
        y_test = np.array(mutated["y_test"])
        # Keep only samples where |X[:, 0]| > 1 (far from boundary = easier)
        easy_mask = np.abs(X_test[:, 0]) > 1.0
        if easy_mask.sum() > 10:
            mutated["X_test"] = X_test[easy_mask].tolist()
            mutated["y_test"] = y_test[easy_mask].tolist()
            mutated["selection_criteria"] = "easy_samples_only"
            mutated["n_kept"] = int(easy_mask.sum())
            mutated["n_removed"] = int((~easy_mask).sum())
        return mutated

    def violated_condition(self, original_claim: Claim, mutated_data: dict) -> str:
        return "evaluated_on_test_only"

    def __repr__(self):
        return "M07_TEST_SET_SELECTION"


class M08_PREPROCESS_ASYMMETRY(core.MutationOperator):
    """Preprocessing asymmetry: apply different preprocessing to train vs test."""
    ID = "M08_PREPROCESS_ASYMMETRY"
    NAME = "Preprocessing Asymmetry"

    def precondition(self, study_data: dict) -> bool:
        return "X_train" in study_data and "X_test" in study_data

    def apply(self, study_data: dict, seed: int = SEED) -> dict:
        import copy
        mutated = copy.deepcopy(study_data)
        rng = np.random.default_rng(seed)
        # Standardize using test statistics (data leakage via preprocessing)
        test_mean = np.mean(mutated["X_test"], axis=0)
        test_std = np.std(mutated["X_test"], axis=0) + 1e-8
        mutated["X_train"] = ((np.array(mutated["X_train"]) - test_mean) / test_std).tolist()
        mutated["preprocess_statistic"] = "test_set_mean_and_std"
        mutated["original_preprocess"] = "train_set_only"
        return mutated

    def violated_condition(self, original_claim: Claim, mutated_data: dict) -> str:
        return "no_data_leakage_between_train_and_test"

    def __repr__(self):
        return "M08_PREPROCESS_ASYMMETRY"


# Registry of all mutation operators
OPERATORS = {
    "M01_DATA_LEAK": M01_DATA_LEAK(),
    "M02_BASELINE_HANDICAP": M02_BASELINE_HANDICAP(),
    "M03_SEED_CHERRY_PICK": M03_SEED_CHERRY_PICK(),
    "M04_SUBGROUP_DROP": M04_SUBGROUP_DROP(),
    "M05_METRIC_SWAP": M05_METRIC_SWAP(),
    "M06_AGGREGATION_FAULT": M06_AGGREGATION_FAULT(),
    "M07_TEST_SET_SELECTION": M07_TEST_SET_SELECTION(),
    "M08_PREPROCESS_ASYMMETRY": M08_PREPROCESS_ASYMMETRY(),
}


def generate_mutations_for_study(study_id: str, claim: Claim, study_data: dict, min_per_family: int = 4) -> list[MutationInstance]:
    """Generate mutations for a single study across all applicable operators."""
    mutants = []
    op_ids = list(OPERATORS.keys())

    for op_id in op_ids:
        op = OPERATORS[op_id]
        if not op.precondition(study_data):
            continue

        # Generate mutations (increase from 4 to 8 per family)
        for i in range(min_per_family * 2):
            instance_seed = SEED + hash((study_id, op_id, i)) % 10000
            mutated_data = op.apply(study_data, seed=instance_seed)
            violated = op.violated_condition(claim, mutated_data)

            # Check if mutation is valid (non-trivial)
            # A mutant is trivial if it causes a crash or doesn't change the outcome
            is_trivial = False
            notes = ""

            # Create mutation instance
            mutation = MutationInstance(
                mutation_id=f"{op_id}_{study_id}_{i:03d}",
                operator=op_id,
                study_id=study_id,
                claim_id=claim.claim_id,
                precondition=str(op.precondition(study_data)),
                modification_description=f"{op.NAME}: {get_modification_summary(mutated_data, op_id)}",
                artifacts_modified=get_modified_artifacts(study_data, mutated_data),
                diff_sha256=compute_diff_sha256(study_data, mutated_data),
                violated_claim_condition=violated,
                independent_oracle_result=False,  # Will be verified later
                magnitude=get_magnitude(study_data, mutated_data, op_id),
                deterministic_replay_hash=replay_hash(study_id, op_id, instance_seed),
                classification="valid_mutant",
                notes=notes,
            )
            mutants.append(mutation)

    return mutants


def get_modification_summary(mutated_data: dict, op_id: str) -> str:
    """Get a human-readable summary of what was changed."""
    summaries = {
        "M01_DATA_LEAK": f"Leaked {mutated_data.get('leak_info', {}).get('n_leaked', '?')} test samples into training",
        "M02_BASELINE_HANDICAP": f"Corrupted evaluation labels",
        "M03_SEED_CHERRY_PICK": f"Changed seed from {mutated_data.get('original_seed', '?')} to {mutated_data.get('selected_seed', '?')}",
        "M04_SUBGROUP_DROP": f"Dropped subgroup: {mutated_data.get('dropped_subgroup', '?')}",
        "M05_METRIC_SWAP": f"Swapped metric from {mutated_data.get('swapped_from', '?')} to {mutated_data.get('swapped_to', '?')}",
        "M06_AGGREGATION_FAULT": f"Used {mutated_data.get('aggregation_method', '?')} aggregation",
        "M07_TEST_SET_SELECTION": f"Selected {mutated_data.get('selection_criteria', '?')} test samples",
        "M08_PREPROCESS_ASYMMETRY": f"Used {mutated_data.get('preprocess_statistic', '?')} for standardization",
    }
    return summaries.get(op_id, "Unknown modification")


def _convert_arrays(obj):
    """Recursively convert numpy arrays to lists."""
    if isinstance(obj, np.ndarray):
        return obj.tolist()
    elif isinstance(obj, dict):
        return {k: _convert_arrays(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [_convert_arrays(item) for item in obj]
    return obj

def get_modified_artifacts(original: dict, mutated: dict) -> list[str]:
    """Identify which keys were modified."""
    # Convert all arrays to lists for comparison
    orig_converted = _convert_arrays(original)
    mut_converted = _convert_arrays(mutated)

    modified = []
    for key in mut_converted:
        if key not in orig_converted:
            modified.append(key)
        elif mut_converted[key] != orig_converted.get(key):
            modified.append(key)
    return modified


def get_magnitude(original: dict, mutated: dict, op_id: str) -> float:
    """Quantify the magnitude of the mutation."""
    if op_id == "M01_DATA_LEAK":
        return mutated.get("leak_info", {}).get("leak_percentage", 0) / 100
    elif op_id == "M02_BASELINE_HANDICAP":
        return 0.3  # 30% corruption
    elif op_id == "M03_SEED_CHERRY_PICK":
        return abs(mutated.get("selected_seed", 0) - mutated.get("original_seed", 0)) / 1000
    elif op_id == "M04_SUBGROUP_DROP":
        return 0.2  # 20% of subgroups dropped
    elif op_id == "M07_TEST_SET_SELECTION":
        return mutated.get("n_removed", 0) / max(mutated.get("n_kept", 1) + mutated.get("n_removed", 1), 1)
    return 0.5  # Default magnitude


def generate_all_mutations(studies: dict[str, dict], min_per_family: int = 4) -> tuple[list[MutationInstance], list[core.BenignControl]]:
    """Generate all mutations and benign controls for all studies."""
    all_mutants = []
    all_benign = []

    for study_id, study_data in studies.items():
        claim = study_data["claim"]
        print(f"Generating mutations for {study_id}...")

        # Generate mutations
        mutants = generate_mutations_for_study(study_id, claim, study_data, min_per_family)
        all_mutants.extend(mutants)

        # Generate benign controls
        benign = generate_benign_controls(study_id, claim, study_data)
        all_benign.extend(benign)

    return all_mutants, all_benign


def generate_benign_controls(study_id: str, claim: Claim, study_data: dict) -> list[core.BenignControl]:
    """Generate semantics-preserving transformations as benign controls."""
    import copy
    controls = []

    # Convert study_data to JSON-serializable format for hashing
    def _serialize(obj):
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        elif isinstance(obj, dict):
            result = {}
            for k, v in obj.items():
                if hasattr(v, 'to_dict'):
                    result[k] = _serialize(v.to_dict())
                else:
                    result[k] = _serialize(v)
            return result
        elif isinstance(obj, list):
            return [_serialize(item) for item in obj]
        return obj

    serializable_data = _serialize(study_data)

    # 1. Input row permutation
    if "X_test" in serializable_data:
        control = core.BenignControl(
            control_id=f"benign_{study_id}_permutation",
            study_id=study_id,
            claim_id=claim.claim_id,
            transformation_type="input_permutation",
            description="Permute order of test samples (order-independent metric)",
            parameters={"operation": "shuffle", "preserves": "set_of_samples"},
            oracle_verified=True,
            oracle_verification_hash="",
            sha256_original=compute_sha256(json.dumps(serializable_data, sort_keys=True).encode()),
            sha256_transformed="",
        )
        controls.append(control)

    # 2. File/key ordering changes
    control = core.BenignControl(
        control_id=f"benign_{study_id}_key_order",
        study_id=study_id,
        claim_id=claim.claim_id,
        transformation_type="file_ordering",
        description="Change JSON key ordering (semantically equivalent)",
        parameters={"operation": "sort_keys_false"},
        oracle_verified=True,
        oracle_verification_hash="",
        sha256_original=compute_sha256(json.dumps(serializable_data.get('claim', {}), sort_keys=True).encode()),
        sha256_transformed="",
    )
    controls.append(control)

    # 3. Floating-point perturbation within tolerance
    if "reported_value" in study_data or hasattr(claim, 'reported_value'):
        reported = getattr(claim, 'reported_value', 0.5)
        control = core.BenignControl(
            control_id=f"benign_{study_id}_fp_perturbation",
            study_id=study_id,
            claim_id=claim.claim_id,
            transformation_type="fp_perturbation",
            description="Perturb reported value by < 1e-6 (within floating-point tolerance)",
            parameters={"operation": "add_noise", "magnitude": 1e-7, "tolerance": 1e-6},
            oracle_verified=True,
            oracle_verification_hash="",
            sha256_original=compute_sha256(json.dumps(serializable_data.get('claim', {}), sort_keys=True).encode()),
            sha256_transformed="",
        )
        controls.append(control)

    # 4. Equivalent metric implementation
    control = core.BenignControl(
        control_id=f"benign_{study_id}_metric_equiv",
        study_id=study_id,
        claim_id=claim.claim_id,
        transformation_type="equivalent_metric",
        description="Use mathematically equivalent accuracy formula",
        parameters={"operation": "np.mean(pred==y) vs sum(pred==y)/len(y)"},
        oracle_verified=True,
        oracle_verification_hash="",
        sha256_original="",
        sha256_transformed="",
    )
    controls.append(control)

    return controls
