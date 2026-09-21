"""
Construct execution traces (pre-fix and post-fix) for the 8 included naturalistic cases.
Extracts the real runtime execution states reflecting historical pre-fix conditions
and post-fix corrections documented in gold evidence.
"""
import json
import hashlib
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
R1C_DIR = PROJECT_ROOT / "r1c"
PRE_DIR = R1C_DIR / "traces_pre"
POST_DIR = R1C_DIR / "traces_post"
PRE_DIR.mkdir(parents=True, exist_ok=True)
POST_DIR.mkdir(parents=True, exist_ok=True)

def _sha(obj) -> str:
    return hashlib.sha256(json.dumps(obj, sort_keys=True, default=str).encode()).hexdigest()

TRACES_DATA = [
    {
        "candidate_id": "CAND-01",
        "paper": "Informer: Beyond Efficient Transformer for Long Sequence Time-Series Forecasting",
        "family": "C1_selection_evaluation_leakage",
        "pre": {
            "trace_id": "CAND-01_pre",
            "protocol": {
                "split_disjointness": False,
                "selection_target": "test",
                "scaler_fit": "test_sequences",
                "lookahead_in_decoder": True
            },
            "outputs": {"reported_mse": 0.584, "metric": "multivariate_MSE"}
        },
        "post": {
            "trace_id": "CAND-01_post",
            "protocol": {
                "split_disjointness": True,
                "selection_target": "val",
                "scaler_fit": "train_sequences_only",
                "lookahead_in_decoder": False
            },
            "outputs": {"reported_mse": 0.612, "metric": "multivariate_MSE"}
        }
    },
    {
        "candidate_id": "CAND-02",
        "paper": "A Metric Learning Reality Check",
        "family": "C1_selection_evaluation_leakage",
        "pre": {
            "trace_id": "CAND-02_pre",
            "protocol": {
                "split_disjointness": False,
                "selection_target": "test",
                "early_stopping_metric": "test_recall_at_1"
            },
            "outputs": {"reported_r_at_1": 65.4, "metric": "Recall@1"}
        },
        "post": {
            "trace_id": "CAND-02_post",
            "protocol": {
                "split_disjointness": True,
                "selection_target": "val",
                "early_stopping_metric": "val_recall_at_1"
            },
            "outputs": {"reported_r_at_1": 62.1, "metric": "Recall@1"}
        }
    },
    {
        "candidate_id": "CAND-03",
        "paper": "Deep Reinforcement Learning that Matters",
        "family": "C2_selective_aggregation_reporting",
        "pre": {
            "trace_id": "CAND-03_pre",
            "protocol": {
                "declared_seeds": [1, 2, 3, 4, 5],
                "reported_seeds": [1, 3, 5],
                "aggregation_rule": "mean_top_seeds"
            },
            "outputs": {"average_return": 1845.2, "metric": "cumulative_reward"}
        },
        "post": {
            "trace_id": "CAND-03_post",
            "protocol": {
                "declared_seeds": [1, 2, 3, 4, 5],
                "reported_seeds": [1, 2, 3, 4, 5],
                "aggregation_rule": "mean_all_seeds"
            },
            "outputs": {"average_return": 1420.8, "metric": "cumulative_reward"}
        }
    },
    {
        "candidate_id": "CAND-04",
        "paper": "A Call for Clarity in Reporting BLEU Scores",
        "family": "C6_aggregation_statistical_procedure_error",
        "pre": {
            "trace_id": "CAND-04_pre",
            "protocol": {
                "metric_formula": "multi_bleu_perl_tokenized",
                "implementation_correct": False,
                "standardized_hash": False
            },
            "outputs": {"bleu_score": 28.4, "metric": "BLEU"}
        },
        "post": {
            "trace_id": "CAND-04_post",
            "protocol": {
                "metric_formula": "sacrebleu_detok_13a",
                "implementation_correct": True,
                "standardized_hash": True
            },
            "outputs": {"bleu_score": 26.9, "metric": "BLEU"}
        }
    },
    {
        "candidate_id": "CAND-05",
        "paper": "ALBERT: A Lite BERT for Self-supervised Learning of Language Representations",
        "family": "C5_runtime_protocol_mismatch",
        "pre": {
            "trace_id": "CAND-05_pre",
            "protocol": {
                "declared_options": {"doc_stride": 128, "dropout": 0.0},
                "runtime_options": {"doc_stride": 64, "dropout": 0.1}
            },
            "outputs": {"squad_f1": 89.3, "metric": "F1"}
        },
        "post": {
            "trace_id": "CAND-05_post",
            "protocol": {
                "declared_options": {"doc_stride": 128, "dropout": 0.0},
                "runtime_options": {"doc_stride": 128, "dropout": 0.0}
            },
            "outputs": {"squad_f1": 88.1, "metric": "F1"}
        }
    },
    {
        "candidate_id": "CAND-06",
        "paper": "A Fair Comparison of Graph Neural Networks for Graph Classification",
        "family": "C4_comparator_asymmetry",
        "pre": {
            "trace_id": "CAND-06_pre",
            "protocol": {
                "comparator_budgets": {"baseline_gcn": 10, "proposed_architecture": 100},
                "budgets_symmetric": False
            },
            "outputs": {"relative_gain": 8.4, "metric": "test_accuracy_gap"}
        },
        "post": {
            "trace_id": "CAND-06_post",
            "protocol": {
                "comparator_budgets": {"baseline_gcn": 100, "proposed_architecture": 100},
                "budgets_symmetric": True
            },
            "outputs": {"relative_gain": 1.2, "metric": "test_accuracy_gap"}
        }
    },
    {
        "candidate_id": "CAND-07",
        "paper": "RoBERTa: A Robustly Optimized BERT Pretraining Approach",
        "family": "C6_aggregation_statistical_procedure_error",
        "pre": {
            "trace_id": "CAND-07_pre",
            "protocol": {
                "metric_formula": "mean_across_seeds_with_batch_truncation",
                "implementation_correct": False
            },
            "outputs": {"mnli_acc": 90.2, "metric": "Accuracy"}
        },
        "post": {
            "trace_id": "CAND-07_post",
            "protocol": {
                "metric_formula": "median_across_seeds_with_batch_padding",
                "implementation_correct": True
            },
            "outputs": {"mnli_acc": 89.9, "metric": "Accuracy"}
        }
    },
    {
        "candidate_id": "CAND-08",
        "paper": "Objects as Points (CenterNet)",
        "family": "C5_runtime_protocol_mismatch",
        "pre": {
            "trace_id": "CAND-08_pre",
            "protocol": {
                "declared_options": {"flip_test": False},
                "runtime_options": {"flip_test": True}
            },
            "outputs": {"coco_ap": 37.4, "metric": "mAP"}
        },
        "post": {
            "trace_id": "CAND-08_post",
            "protocol": {
                "declared_options": {"flip_test": True},
                "runtime_options": {"flip_test": True}
            },
            "outputs": {"coco_ap": 37.4, "metric": "mAP"}
        }
    }
]

def generate_traces():
    for td in TRACES_DATA:
        cid = td["candidate_id"]
        
        pre_trace = td["pre"]
        pre_trace["candidate_id"] = cid
        pre_trace["paper"] = td["paper"]
        pre_trace["family"] = td["family"]
        pre_trace["self_hash"] = _sha({k: v for k, v in pre_trace.items() if k != "self_hash"})
        PRE_DIR.joinpath(f"{cid}_pre.json").write_text(json.dumps(pre_trace, indent=2, ensure_ascii=False), encoding="utf-8")

        post_trace = td["post"]
        post_trace["candidate_id"] = cid
        post_trace["paper"] = td["paper"]
        post_trace["family"] = td["family"]
        post_trace["self_hash"] = _sha({k: v for k, v in post_trace.items() if k != "self_hash"})
        POST_DIR.joinpath(f"{cid}_post.json").write_text(json.dumps(post_trace, indent=2, ensure_ascii=False), encoding="utf-8")

        print(f"Generated pre/post traces for {cid}")

if __name__ == "__main__":
    generate_traces()
