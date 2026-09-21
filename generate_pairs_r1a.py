"""
R1-A Paired Execution Generator.

Constructs 30 matched pairs (6 fault families x 5 studies = 60 executions).

Each pair shares:
  - the same scientific paper (protocol)
  - the same code repository / code_commit / environment
Only the runtime execution behaviour differs (clean vs invalid).

The traces conform to TRACE_SCHEMA.json. Contracts are generated from the
paper BEFORE traces are evaluated (R1-A rule). No fault-specific rule is
added after seeing the invalid trace.

Design: synthetic-but-realistic study templates per family. Each study has a
distinct paper-declared protocol (seed count, splits, subgroups, budgets) and
two traces that are byte-identical on all execution-independent fields.
"""
from __future__ import annotations

import json
import hashlib
import copy
from pathlib import Path
from typing import Dict, List, Any

PROJECT_ROOT = Path(__file__).resolve().parent
TRACES_DIR   = PROJECT_ROOT / "traces"
TRACES_DIR.mkdir(exist_ok=True)


def _sha(obj: Any) -> str:
    raw = json.dumps(obj, sort_keys=True, default=str).encode()
    return hashlib.sha256(raw).hexdigest()


def _base_environment(study: Dict) -> Dict:
    return {
        "python": study["python"],
        "torch": study["torch"],
        "device": study.get("device", "cuda:0"),
    }


def _base_repo(study: Dict) -> Dict:
    return {
        "code_commit": study["code_commit"],
        "environment_hash": study["env_hash"],
    }


def _lineage(study: Dict, disjoint: bool = True) -> Dict:
    return {
        "train_hash": study["train_hash"],
        "validation_hash": study["val_hash"],
        "test_hash": study["test_hash"],
        "disjoint_split_ids": disjoint,
    }


def make_pair(family: str, study_idx: int, study: Dict) -> Dict:
    """
    Return {'clean': trace, 'invalid': trace, 'contract_justification': str}
    for one study. Clean and invalid share paper+repo+env+commit; only
    runtime fields differ.
    """
    study_id = f"{family}-{study_idx:02d}"

    # Shared execution-independent block (identical across the pair)
    shared = {
        "run_id": study_id,
        "code_commit": study["code_commit"],
        "environment_hash": study["env_hash"],
        "seed": study["seeds"][0],
        "lineage": _lineage(study),
        "loss_identity": study.get("loss", "CrossEntropyLoss"),
        "optimizer": study.get("optimizer", "AdamW"),
        "hyperparameters": dict(study.get("hyperparameters", {})),
        "config_hash": study.get("config_hash_declared", "cfg_default"),
        "training_budget": dict(study.get("budget", {})),
        "timestamps": {"start": study.get("t_start", "2026-01-01T00:00:00Z"),
                        "end": study.get("t_end", "2026-01-01T06:00:00Z")},
    }

    clean = copy.deepcopy(shared)
    invalid = copy.deepcopy(shared)

    if family == "E01":
        # SEED_SELECTION_BIAS
        clean["protocol"] = {
            "declared_seeds": study["seeds"],
            "aggregation_rule": "mean",
            "aggregation_inputs": [f"{study_id}-s{seed}" for seed in study["seeds"]],
            "selection_split": "validation",
            "final_test_split": "test",
            "declared_subgroups": study.get("subgroups", []),
            "reported_subgroups": study.get("subgroups", []),
        }
        clean["outputs"] = {"reported_value": {
            "value": study["reported_mean"],
            "aggregation_rule": "mean",
            "upstream_runs": [f"{study_id}-s{seed}" for seed in study["seeds"]],
        }}
        # Invalid: aggregate BEST seed only, mislabel as mean
        invalid["protocol"] = {
            "declared_seeds": study["seeds"],
            "aggregation_rule": "best",
            "aggregation_inputs": [f"{study_id}-s{study['seeds'][study['best_idx']]}"],
            "selection_split": "validation",
            "final_test_split": "test",
            "declared_subgroups": study.get("subgroups", []),
            "reported_subgroups": study.get("subgroups", []),
        }
        invalid["outputs"] = {"reported_value": {
            "value": study.get("best_value", 0),
            "aggregation_rule": "best",
            "upstream_runs": [f"{study_id}-s{study['seeds'][study['best_idx']]}"],
        }}

    elif family == "E02":
        # TEST_CONDITIONED_CHECKPOINT_SELECTION
        clean["protocol"] = {
            "declared_seeds": study["seeds"],
            "aggregation_rule": "mean",
            "aggregation_inputs": [f"{study_id}-s{seed}" for seed in study["seeds"]],
            "selection_split": "validation",
            "final_test_split": "test",
            "declared_subgroups": study.get("subgroups", []),
            "reported_subgroups": study.get("subgroups", []),
        }
        clean["checkpoint"] = {
            "candidates": study.get("ckpts", []),
            "selected": study.get("ckpts", [])[study.get("clean_ckpt_idx", 0)],
            "selection_criterion": "validation_accuracy",
            "selection_split": "validation",
        }
        clean["outputs"] = {"reported_value": {
            "value": study.get("reported_mean", 0.0), "aggregation_rule": "mean",
            "upstream_runs": [f"{study_id}-s{seed}" for seed in study["seeds"]]}}
        invalid["protocol"] = dict(clean["protocol"])
        invalid["protocol"]["selection_split"] = "test"
        invalid["checkpoint"] = {
            "candidates": study.get("ckpts", []),
            "selected": study.get("ckpts", [])[study.get("invalid_ckpt_idx", 0)],
            "selection_criterion": "test_accuracy",
            "selection_split": "test",
        }
        invalid["outputs"] = {"reported_value": {
            "value": study["invalid_reported"], "aggregation_rule": "mean",
            "upstream_runs": [f"{study_id}-s{seed}" for seed in study["seeds"]]}}

    elif family == "E03":
        # RUNTIME_CONFIG_MISMATCH
        # Execution-INDEPENDENT fields (hyperparameters, training_budget)
        # are held constant across the pair. The scientific difference is
        # the RUNTIME-EXECUTED config, which a trace records as what
        # actually ran vs. what the paper declared. Only config_hash and
        # the protocol-level executed_hyperparameters differ.
        clean["protocol"] = {
            "declared_seeds": study["seeds"],
            "aggregation_rule": "mean",
            "aggregation_inputs": [f"{study_id}-s{seed}" for seed in study["seeds"]],
            "selection_split": "validation",
            "final_test_split": "test",
            "declared_preprocess": study.get("declared_preprocess", {}),
            "executed_preprocess": study.get("declared_preprocess", {}),
            "declared_subgroups": study.get("subgroups", []),
            "reported_subgroups": study.get("subgroups", []),
            "declared_hyperparameters": study.get("hyperparameters_declared", {}),
            "executed_hyperparameters": study.get("hyperparameters_declared", {}),
        }
        clean["config_hash"] = study.get("config_hash_declared", "cfg")
        clean["outputs"] = {"reported_value": {
            "value": study.get("reported_mean", 0.0), "aggregation_rule": "mean",
            "upstream_runs": [f"{study_id}-s{seed}" for seed in study["seeds"]]}}
        # Invalid: runtime-executed hyperparameters differ from declared.
        # Captured in executed_hyperparameters + config_hash (runtime fields).
        invalid["protocol"] = copy.deepcopy(clean["protocol"])
        invalid["protocol"]["executed_hyperparameters"] = study.get("hyperparameters_executed_invalid", {})
        invalid["config_hash"] = study.get("config_hash_invalid", "cfg_invalid")
        invalid["outputs"] = {"reported_value": {
            "value": study.get("invalid_reported", 0.0), "aggregation_rule": "mean",
            "upstream_runs": [f"{study_id}-s{seed}" for seed in study["seeds"]]}}

    elif family == "E04":
        # SUBGROUP_SELECTIVE_REPORTING
        all_sub = study.get("subgroups", [])
        favourable = study.get("favourable_subgroups", all_sub[:1])
        clean["protocol"] = {
            "declared_seeds": study["seeds"],
            "aggregation_rule": "mean",
            "aggregation_inputs": [f"{study_id}-s{seed}" for seed in study["seeds"]],
            "selection_split": "validation",
            "final_test_split": "test",
            "declared_subgroups": all_sub,
            "reported_subgroups": all_sub,
        }
        clean["evaluation"] = {"dataset": "test", "metrics": study.get("all_subgroup_metrics", {})}
        clean["outputs"] = {"reported_value": {
            "value": study["reported_mean"], "aggregation_rule": "mean",
            "upstream_runs": [f"{study_id}-s{seed}" for seed in study["seeds"]]}}
        invalid["protocol"] = copy.deepcopy(clean["protocol"])
        invalid["protocol"]["reported_subgroups"] = favourable
        invalid["evaluation"] = {"dataset": "test", "metrics": {k: v for k, v in study.get("all_subgroup_metrics", {}).items() if k in favourable}}
        invalid["outputs"] = {"reported_value": {
            "value": study["invalid_reported"], "aggregation_rule": "mean",
            "upstream_runs": [f"{study_id}-s{seed}" for seed in study["seeds"]]}}

    elif family == "E05":
        # PREPROCESS_RUNTIME_FLAG_MISMATCH
        clean["protocol"] = {
            "declared_seeds": study["seeds"],
            "aggregation_rule": "mean",
            "aggregation_inputs": [f"{study_id}-s{seed}" for seed in study["seeds"]],
            "selection_split": "validation",
            "final_test_split": "test",
            "declared_preprocess": study.get("declared_preprocess", {}),
            "executed_preprocess": study.get("declared_preprocess", {}),
            "declared_subgroups": study.get("subgroups", []),
            "reported_subgroups": study.get("subgroups", []),
        }
        clean["config_hash"] = study["config_hash_declared"]
        clean["outputs"] = {"reported_value": {
            "value": study["reported_mean"], "aggregation_rule": "mean",
            "upstream_runs": [f"{study_id}-s{seed}" for seed in study["seeds"]]}}
        # Invalid: runtime preprocessing differs from declared
        invalid["protocol"] = copy.deepcopy(clean["protocol"])
        invalid["protocol"]["executed_preprocess"] = study["executed_preprocess_invalid"]
        invalid["config_hash"] = study["config_hash_invalid"]
        invalid["outputs"] = {"reported_value": {
            "value": study["invalid_reported"], "aggregation_rule": "mean",
            "upstream_runs": [f"{study_id}-s{seed}" for seed in study["seeds"]]}}

    elif family == "E06":
        # COMPUTE_OR_TRAINING_BUDGET_ASYMMETRY
        # comparator_budgets is a RUNTIME field (what actually ran), so it
        # legitimately differs between clean and invalid. Execution-independent
        # fields (code_commit, env, loss, optimizer, hyperparameters, lineage)
        # are shared and constant.
        clean["protocol"] = {
            "declared_seeds": study["seeds"],
            "aggregation_rule": "mean",
            "aggregation_inputs": [f"{study_id}-s{seed}" for seed in study["seeds"]],
            "selection_split": "validation",
            "final_test_split": "test",
            "declared_subgroups": study.get("subgroups", []),
            "reported_subgroups": study.get("subgroups", []),
        }
        clean["comparator_budgets"] = study.get("fair_comparator_budgets", [])
        clean["outputs"] = {"reported_value": {
            "value": study.get("reported_mean", 0.0), "aggregation_rule": "mean",
            "upstream_runs": [f"{study_id}-s{seed}" for seed in study["seeds"]]}}
        # Invalid: proposed method gets more budget than baselines (asymmetric)
        invalid["protocol"] = copy.deepcopy(clean["protocol"])
        invalid["comparator_budgets"] = study.get("unfair_comparator_budgets", [])
        invalid["outputs"] = {"reported_value": {
            "value": study.get("invalid_reported", 0.0), "aggregation_rule": "mean",
            "upstream_runs": [f"{study_id}-s{seed}" for seed in study["seeds"]]}}
    else:
        raise ValueError(f"Unknown family {family}")

    # Add self-hash (content-addressed) to both
    for trace in (clean, invalid):
        payload = copy.deepcopy(trace)
        payload.pop("self_hash", None)
        trace["self_hash"] = _sha(payload)

    # Paper justification (for contract generation, from paper text NOT trace)
    paper_text = study["paper_text"]
    return {
        "study_id": study_id,
        "family": family,
        "paper_text": paper_text,
        "paper_text_hash": _sha(paper_text),
        "repo": _base_repo(study),
        "clean": clean,
        "invalid": invalid,
    }


# ──────────────────────────────────────────────────────────────
# Study templates: 5 distinct papers per family
# ──────────────────────────────────────────────────────────────
def _study(**kw) -> Dict:
    d = {
        "code_commit": kw.get("code_commit", "a" * 40),
        "env_hash": kw.get("env_hash", "env" + hashlib.sha256(kw.get("study_tag", "x").encode()).hexdigest()[:16]),
        "seeds": kw.get("seeds", [0, 1, 2]),
        "train_hash": kw.get("train_hash", "train_h1"),
        "val_hash": kw.get("val_hash", "val_h1"),
        "test_hash": kw.get("test_hash", "test_h1"),
        "loss": kw.get("loss", "CrossEntropyLoss"),
        "optimizer": kw.get("optimizer", "AdamW"),
        "python": "3.10.12",
        "torch": kw.get("torch", "2.1.0"),
    }
    d.update({k: v for k, v in kw.items() if k not in d})
    return d


FAMILIES: Dict[str, List[Dict]] = {}

# E01: SEED_SELECTION_BIAS — 5 studies, varying seed count & metric
FAMILIES["E01"] = [
    _study(study_tag="e01a",
           paper_text="We report the mean accuracy across five random seeds (0-4) on the ImageNet subset. Aggregation is arithmetic mean.",
           seeds=[0,1,2,3,4], reported_mean=0.78, best_value=0.81, best_idx=2,
           config_hash_declared="cfg_e01a", hyperparameters={"lr":0.001,"epochs":90},
           hyperparameters_declared={"lr":0.001,"epochs":90},
           ckpts=["ckpt_1","ckpt_2"], clean_ckpt_idx=0,
           all_subgroup_metrics={"overall":0.78},
           budget={"epochs":90}),
    _study(study_tag="e01b",
           paper_text="For each method we report the mean over three seeds on CIFAR-10. Results are averaged across runs.",
           seeds=[11,12,13], reported_mean=0.91, best_value=0.94, best_idx=1,
           config_hash_declared="cfg_e01b",
           hyperparameters={"lr":0.01,"epochs":200},
           hyperparameters_declared={"lr":0.01,"epochs":200},
           all_subgroup_metrics={"overall":0.91},
           budget={"epochs":200}),
    _study(study_tag="e01c",
           paper_text="We evaluate on GLUE with a mean of four seed runs. We average BLEU across the reported seeds.",
           seeds=[7,8,9,10], reported_mean=0.83, best_value=0.86, best_idx=0,
           config_hash_declared="cfg_e01c",
           hyperparameters={"lr":5e-5,"epochs":5},
           hyperparameters_declared={"lr":5e-5,"epochs":5},
           all_subgroup_metrics={"overall":0.83},
           budget={"epochs":5}),
    _study(study_tag="e01d",
           paper_text="Protein folding benchmark: mean CDR over six seeds, reported as the aggregate result.",
           seeds=[1,2,3,4,5,6], reported_mean=0.62, best_value=0.71, best_idx=5,
           config_hash_declared="cfg_e01d",
           hyperparameters={"lr":0.0003,"epochs":30},
           hyperparameters_declared={"lr":0.0003,"epochs":30},
           all_subgroup_metrics={"overall":0.62},
           budget={"epochs":30}),
    _study(study_tag="e01e",
           paper_text="We report the mean AUC across five seeds on the medical imaging set; seeds are fixed and disclosed.",
           seeds=[0,1,2,3,4], reported_mean=0.88, best_value=0.92, best_idx=4,
           config_hash_declared="cfg_e01e",
           hyperparameters={"lr":0.0001,"epochs":100},
           hyperparameters_declared={"lr":0.0001,"epochs":100},
           all_subgroup_metrics={"overall":0.88},
           budget={"epochs":100}),
]

# E02: TEST_CONDITIONED_CHECKPOINT_SELECTION
FAMILIES["E02"] = [
    _study(study_tag="e02a",
           paper_text="Model selection is performed on a held-out validation set; the test set is used exclusively for final evaluation.",
           ckpts=["c_1","c_2","c_3"], clean_ckpt_idx=1, invalid_ckpt_idx=2,
           reported_mean=0.80, invalid_reported=0.85,
           all_subgroup_metrics={"overall":0.80}),
    _study(study_tag="e02b",
           paper_text="We select the best checkpoint by validation loss and report final accuracy on the untouched test partition.",
           ckpts=["m_a","m_b"], clean_ckpt_idx=0, invalid_ckpt_idx=1,
           reported_mean=0.74, invalid_reported=0.79,
           all_subgroup_metrics={"overall":0.74}),
    _study(study_tag="e02c",
           paper_text="Checkpoints are chosen using validation F1; the test split is reserved only for the reported number.",
           ckpts=["k1","k2","k3","k4"], clean_ckpt_idx=3, invalid_ckpt_idx=0,
           reported_mean=0.81, invalid_reported=0.88,
           all_subgroup_metrics={"overall":0.81}),
    _study(study_tag="e02d",
           paper_text="Early stopping is monitored on validation accuracy; test accuracy is never used to pick the epoch.",
           ckpts=["e10","e20","e30"], clean_ckpt_idx=1, invalid_ckpt_idx=2,
           reported_mean=0.69, invalid_reported=0.77,
           all_subgroup_metrics={"overall":0.69}),
    _study(study_tag="e02e",
           paper_text="The held-out validation fold drives all model selection; the test fold is held out until the final evaluation.",
           ckpts=["v1","v2"], clean_ckpt_idx=0, invalid_ckpt_idx=1,
           reported_mean=0.72, invalid_reported=0.80,
           all_subgroup_metrics={"overall":0.72}),
]

# E03: RUNTIME_CONFIG_MISMATCH
FAMILIES["E03"] = [
    _study(study_tag="e03a",
           paper_text="We train for 90 epochs with learning rate 1e-3 and batch size 32, as stated in the appendix.",
           hyperparameters_declared={"lr":0.001,"epochs":90,"batch_size":32},
           hyperparameters={"lr":0.001,"epochs":90,"batch_size":32},
           hyperparameters_executed_invalid={"lr":0.01,"epochs":30,"batch_size":32},
           config_hash_declared="cfg3a", config_hash_invalid="cfg3a_bad",
           reported_mean=0.78, invalid_reported=0.61,
           all_subgroup_metrics={"overall":0.78}),
    _study(study_tag="e03b",
           paper_text="Optimizer is AdamW with weight decay 0.05 and 200 training iterations.",
           hyperparameters_declared={"wd":0.05,"iterations":200},
           hyperparameters={"wd":0.05,"iterations":200},
           hyperparameters_executed_invalid={"wd":0.0,"iterations":100},
           config_hash_declared="cfg3b", config_hash_invalid="cfg3b_bad",
           reported_mean=0.82, invalid_reported=0.70,
           all_subgroup_metrics={"overall":0.82}),
    _study(study_tag="e03c",
           paper_text="Both models are trained for an identical 50 epochs under the same budget.",
           hyperparameters_declared={"epochs":50},
           hyperparameters={"epochs":50},
           hyperparameters_executed_invalid={"epochs":20},
           config_hash_declared="cfg3c", config_hash_invalid="cfg3c_bad",
           reported_mean=0.85, invalid_reported=0.64,
           all_subgroup_metrics={"overall":0.85}),
    _study(study_tag="e03d",
           paper_text="Learning rate is 5e-5 with 5 fine-tuning epochs.",
           hyperparameters_declared={"lr":5e-5,"epochs":5},
           hyperparameters={"lr":5e-5,"epochs":5},
           hyperparameters_executed_invalid={"lr":1e-4,"epochs":15},
           config_hash_declared="cfg3d", config_hash_invalid="cfg3d_bad",
           reported_mean=0.79, invalid_reported=0.71,
           all_subgroup_metrics={"overall":0.79}),
    _study(study_tag="e03e",
           paper_text="Dropout of 0.5 and batch size 64 are used throughout, per the method description.",
           hyperparameters_declared={"dropout":0.5,"batch_size":64},
           hyperparameters={"dropout":0.5,"batch_size":64},
           hyperparameters_executed_invalid={"dropout":0.0,"batch_size":64},
           config_hash_declared="cfg3e", config_hash_invalid="cfg3e_bad",
           reported_mean=0.84, invalid_reported=0.73,
           all_subgroup_metrics={"overall":0.84}),
]

# E04: SUBGROUP_SELECTIVE_REPORTING
FAMILIES["E04"] = [
    _study(study_tag="e04a",
           paper_text="We report per-subgroup accuracy for all four demographic groups (A, B, C, D).",
           subgroups=["A","B","C","D"],
           favourable_subgroups=["A"],
           all_subgroup_metrics={"A":0.90,"B":0.55,"C":0.60,"D":0.45},
           reported_mean=0.63, invalid_reported=0.90),
    _study(study_tag="e04b",
           paper_text="Per-cohort F1 is reported for every cohort in the dataset.",
           subgroups=["c1","c2","c3","c4","c5"],
           favourable_subgroups=["c1","c2"],
           all_subgroup_metrics={"c1":0.88,"c2":0.84,"c3":0.51,"c4":0.49,"c5":0.42},
           reported_mean=0.63, invalid_reported=0.86),
    _study(study_tag="e04c",
           paper_text="We report ROC-AUC for each of the six clinical subgroups.",
           subgroups=["s1","s2","s3","s4","s5","s6"],
           favourable_subgroups=["s1"],
           all_subgroup_metrics={"s1":0.95,"s2":0.70,"s3":0.65,"s4":0.62,"s5":0.58,"s6":0.50},
           reported_mean=0.67, invalid_reported=0.95),
    _study(study_tag="e04d",
           paper_text="All three language families are reported individually.",
           subgroups=["ger","rom","sla"],
           favourable_subgroups=["ger"],
           all_subgroup_metrics={"ger":0.80,"rom":0.55,"sla":0.40},
           reported_mean=0.58, invalid_reported=0.80),
    _study(study_tag="e04e",
           paper_text="We report results across all five tissue types.",
           subgroups=["t1","t2","t3","t4","t5"],
           favourable_subgroups=["t1","t2"],
           all_subgroup_metrics={"t1":0.92,"t2":0.88,"t3":0.55,"t4":0.52,"t5":0.47},
           reported_mean=0.67, invalid_reported=0.90),
]

# E05: PREPROCESS_RUNTIME_FLAG_MISMATCH
FAMILIES["E05"] = [
    _study(study_tag="e05a",
           paper_text="Images are normalised with mean/std and augmented with random crops during training.",
           declared_preprocess={"normalise":True,"crop_augment":True},
           executed_preprocess_invalid={"normalise":True,"crop_augment":False},
           config_hash_declared="cfg5a", config_hash_invalid="cfg5a_bad",
           reported_mean=0.83, invalid_reported=0.66,
           all_subgroup_metrics={"overall":0.83}),
    _study(study_tag="e05b",
           paper_text="Token sequences are masked with a 15% rate before fine-tuning.",
           declared_preprocess={"mask_rate":0.15},
           executed_preprocess_invalid={"mask_rate":0.0},
           config_hash_declared="cfg5b", config_hash_invalid="cfg5b_bad",
           reported_mean=0.79, invalid_reported=0.71,
           all_subgroup_metrics={"overall":0.79}),
    _study(study_tag="e05c",
           paper_text="Training data is balanced with oversampling of the minority class.",
           declared_preprocess={"oversample_minority":True},
           executed_preprocess_invalid={"oversample_minority":False},
           config_hash_declared="cfg5c", config_hash_invalid="cfg5c_bad",
           reported_mean=0.81, invalid_reported=0.58,
           all_subgroup_metrics={"overall":0.81}),
    _study(study_tag="e05d",
           paper_text="Sequences are padded and truncated to length 512.",
           declared_preprocess={"max_len":512},
           executed_preprocess_invalid={"max_len":128},
           config_hash_declared="cfg5d", config_hash_invalid="cfg5d_bad",
           reported_mean=0.84, invalid_reported=0.72,
           all_subgroup_metrics={"overall":0.84}),
    _study(study_tag="e05e",
           paper_text="Audio is resampled to 16 kHz and amplitude-normalised.",
           declared_preprocess={"resample":16000,"amplitude_norm":True},
           executed_preprocess_invalid={"resample":8000,"amplitude_norm":False},
           config_hash_declared="cfg5e", config_hash_invalid="cfg5e_bad",
           reported_mean=0.77, invalid_reported=0.63,
           all_subgroup_metrics={"overall":0.77}),
]

# E06: COMPUTE_OR_TRAINING_BUDGET_ASYMMETRY
FAMILIES["E06"] = [
    _study(study_tag="e06a",
           paper_text="All compared methods are trained for the same number of epochs under a matched compute budget.",
           fair_comparator_budgets=[
               {"method":"ours","epochs":100,"gpu_seconds":3600},
               {"method":"baseline_a","epochs":100,"gpu_seconds":3600}],
           unfair_comparator_budgets=[
               {"method":"ours","epochs":200,"gpu_seconds":7200},
               {"method":"baseline_a","epochs":100,"gpu_seconds":3600}],
           reported_mean=0.80, invalid_reported=0.88,
           all_subgroup_metrics={"overall":0.80}),
    _study(study_tag="e06b",
           paper_text="The proposed method and the two baselines are matched on training steps.",
           fair_comparator_budgets=[
               {"method":"ours","steps":5000},
               {"method":"base1","steps":5000},
               {"method":"base2","steps":5000}],
           unfair_comparator_budgets=[
               {"method":"ours","steps":15000},
               {"method":"base1","steps":5000},
               {"method":"base2","steps":5000}],
           reported_mean=0.75, invalid_reported=0.91,
           all_subgroup_metrics={"overall":0.75}),
    _study(study_tag="e06c",
           paper_text="Each model receives an equivalent GPU-hour budget.",
           fair_comparator_budgets=[
               {"method":"ours","gpu_seconds":7200},
               {"method":"baseline","gpu_seconds":7200}],
           unfair_comparator_budgets=[
               {"method":"ours","gpu_seconds":21600},
               {"method":"baseline","gpu_seconds":7200}],
           reported_mean=0.82, invalid_reported=0.90,
           all_subgroup_metrics={"overall":0.82}),
    _study(study_tag="e06d",
           paper_text="We allocate the same number of training samples to every method.",
           fair_comparator_budgets=[
               {"method":"ours","dataset_fraction_used":1.0},
               {"method":"baseline","dataset_fraction_used":1.0}],
           unfair_comparator_budgets=[
               {"method":"ours","dataset_fraction_used":1.0},
               {"method":"baseline","dataset_fraction_used":0.3}],
           reported_mean=0.78, invalid_reported=0.87,
           all_subgroup_metrics={"overall":0.78}),
    _study(study_tag="e06e",
           paper_text="All approaches are trained for 100 epochs to ensure a fair comparison.",
           fair_comparator_budgets=[
               {"method":"ours","epochs":100},
               {"method":"baseline","epochs":100}],
           unfair_comparator_budgets=[
               {"method":"ours","epochs":300},
               {"method":"baseline","epochs":100}],
           reported_mean=0.76, invalid_reported=0.85,
           all_subgroup_metrics={"overall":0.76}),
]


def generate_all() -> Dict:
    """Generate all 30 pairs / 60 traces, save them, return index."""
    all_pairs = []
    for family, studies in FAMILIES.items():
        for i, study in enumerate(studies, start=1):
            pair = make_pair(family, i, study)
            all_pairs.append(pair)
            # Save individual trace files
            clean_path = TRACES_DIR / f"{pair['study_id']}_clean.json"
            invalid_path = TRACES_DIR / f"{pair['study_id']}_invalid.json"
            clean_path.write_text(json.dumps(pair["clean"], indent=2))
            invalid_path.write_text(json.dumps(pair["invalid"], indent=2))

    # Save the full pair index (paper text per pair for contract generation)
    index_path = PROJECT_ROOT / "traces" / "PAIR_INDEX.json"
    index_payload = {
        "n_pairs": len(all_pairs),
        "n_executions": len(all_pairs) * 2,
        "families": {f: len(FAMILIES[f]) for f in FAMILIES},
        "pairs": [
            {
                "study_id": p["study_id"],
                "family": p["family"],
                "paper_text_hash": p["paper_text_hash"],
                "clean_trace": f"traces/{p['study_id']}_clean.json",
                "invalid_trace": f"traces/{p['study_id']}_invalid.json",
                "code_commit": p["repo"]["code_commit"],
            } for p in all_pairs
        ],
    }
    index_path.write_text(json.dumps(index_payload, indent=2))

    # PAIRED_EXECUTION_FREEZE.json
    freeze = {
        "protocol": "R1-A",
        "frozen_at": "2026-09-20",
        "n_pairs": len(all_pairs),
        "n_executions": len(all_pairs) * 2,
        "identifiability": {
            "shared_paper_per_pair": True,
            "shared_repo_per_pair": True,
            "trace_differs_within_pair": True,
        },
        "index_sha256": _sha(index_payload),
    }
    (PROJECT_ROOT / "PAIRED_EXECUTION_FREEZE.json").write_text(json.dumps(freeze, indent=2))
    return index_payload


if __name__ == "__main__":
    idx = generate_all()
    print(f"Generated {idx['n_pairs']} pairs, {idx['n_executions']} executions.")
    print(f"Families: {idx['families']}")
    print(f"Trace dir: {TRACES_DIR}")
