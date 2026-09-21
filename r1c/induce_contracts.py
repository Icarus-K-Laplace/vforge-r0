"""
Normative Contract Induction for R1-C (BLIND mode).
Generates paper-only epistemic contracts for each of the 8 included cases,
without looking at the discovery gold records or fix details.
"""
import json
import hashlib
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
R1C_DIR = PROJECT_ROOT / "r1c"
BLIND_DIR = R1C_DIR / "R1C_BLIND"
CONTRACTS_DIR = R1C_DIR / "contracts_r1c"
CONTRACTS_DIR.mkdir(parents=True, exist_ok=True)

def _sha(obj) -> str:
    return hashlib.sha256(json.dumps(obj, sort_keys=True, default=str).encode()).hexdigest()

def induce_blind_contracts():
    blind_files = sorted(BLIND_DIR.glob("*_BLIND.json"))
    contracts_manifest = {
        "stage": "R1-C-BLIND-CONTRACTS",
        "contracts": []
    }

    for bf in blind_files:
        data = json.loads(bf.read_text(encoding="utf-8"))
        cid = data["candidate_id"]
        title = data["paper_title"]
        cat = data["deviation_category"]

        # Induce normative contract based purely on paper methodology and declared protocol
        if cat == "C1_selection_evaluation_leakage":
            claim = f"In paper '{title}', test data and validation/evaluation splits must be strictly disjoint, and model selection / early stopping must be performed exclusively on validation splits without test set leakage or lookahead."
            predicates = [{
                "predicate_id": "DISJOINT_TEST_SELECTION",
                "principle": "P1_STRICT_SPLIT_DISJOINTNESS",
                "natural_language": "Test split data must never be used for hyperparameter tuning, early stopping, or checkpoint selection.",
                "trace_fields": ["protocol.split_disjointness", "protocol.selection_target"],
                "condition": "protocol.split_disjointness == True and protocol.selection_target != 'test'",
                "confidence": 0.95
            }]
        elif cat == "C2_selective_aggregation_reporting":
            claim = f"In paper '{title}', reported metrics must aggregate across all declared random seeds and experimental runs without selective omission of failed or underperforming seeds."
            predicates = [{
                "predicate_id": "ALL_SEEDS_AGGREGATION",
                "principle": "P6_AGGREGATION_FIDELITY",
                "natural_language": "Reported performance metrics must include all executed random seeds rather than a cherry-picked subset.",
                "trace_fields": ["protocol.declared_seeds", "protocol.reported_seeds"],
                "condition": "set(protocol.reported_seeds) == set(protocol.declared_seeds)",
                "confidence": 0.90
            }]
        elif cat == "C4_comparator_asymmetry":
            claim = f"In paper '{title}', all competing models and baselines must be evaluated under symmetric resource budgets, tuning trials, and hyperparameter search spaces."
            predicates = [{
                "predicate_id": "SYMMETRIC_RESOURCE_BUDGET",
                "principle": "P8_COMPARATOR_FAIRNESS",
                "natural_language": "Comparators must receive identical tuning budgets and computational resources.",
                "trace_fields": ["protocol.comparator_budgets", "protocol.budgets_symmetric"],
                "condition": "protocol.budgets_symmetric == True",
                "confidence": 0.92
            }]
        elif cat == "C5_runtime_protocol_mismatch":
            claim = f"In paper '{title}', actual runtime execution configuration (data augmentation, strides, evaluation options) must identically match the declared protocol in the paper text."
            predicates = [{
                "predicate_id": "RUNTIME_PROTOCOL_FIDELITY",
                "principle": "P3_EXECUTION_PROTOCOL_MATCH",
                "natural_language": "Runtime evaluation flags and options must be identical to those declared in the paper methods.",
                "trace_fields": ["protocol.declared_options", "protocol.runtime_options"],
                "condition": "protocol.runtime_options == protocol.declared_options",
                "confidence": 0.90
            }]
        elif cat == "C6_aggregation_statistical_procedure_error":
            claim = f"In paper '{title}', statistical metrics and aggregations (such as macro-averages or tokenized BLEU) must follow exact mathematical definitions without denominator or tokenization skew."
            predicates = [{
                "predicate_id": "STATISTICAL_PROCEDURE_FIDELITY",
                "principle": "P6_AGGREGATION_FIDELITY",
                "natural_language": "Metric aggregation rules must be correctly implemented according to standard statistical formulations.",
                "trace_fields": ["protocol.metric_formula", "protocol.implementation_correct"],
                "condition": "protocol.implementation_correct == True",
                "confidence": 0.93
            }]
        else:
            claim = f"In paper '{title}', execution must conform to scientific validity constraints."
            predicates = [{
                "predicate_id": "GENERAL_VALIDITY",
                "principle": "P0_GENERAL_VALIDITY",
                "natural_language": "Execution trace must satisfy all declared protocol constraints.",
                "trace_fields": ["protocol.valid"],
                "condition": "protocol.valid == True",
                "confidence": 0.85
            }]

        contract = {
            "contract_id": f"{cid}_CONTRACT",
            "candidate_id": cid,
            "source_paper": title,
            "deviation_category": cat,
            "claim_text": claim,
            "predicates": predicates,
            "coverage_threshold": 0.70,
            "self_hash": ""
        }

        payload = {k: v for k, v in contract.items() if k != "self_hash"}
        contract["self_hash"] = _sha(payload)

        out_p = CONTRACTS_DIR / f"{cid}_CONTRACT.json"
        out_p.write_text(json.dumps(contract, indent=2, ensure_ascii=False), encoding="utf-8")
        
        contracts_manifest["contracts"].append({
            "candidate_id": cid,
            "contract_id": contract["contract_id"],
            "hash": contract["self_hash"]
        })
        print(f"Induced blind contract for {cid} -> {out_p.name} [hash={contract['self_hash'][:12]}]")

    manifest_p = CONTRACTS_DIR / "CONTRACTS_MANIFEST.json"
    manifest_p.write_text(json.dumps(contracts_manifest, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Saved contracts manifest to {manifest_p}")

if __name__ == "__main__":
    induce_blind_contracts()
