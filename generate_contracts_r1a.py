"""
R1-A Claim Contract Generator.

Generates machine-readable scientific contracts from paper text BEFORE
traces are evaluated. One contract per study (shared by clean + invalid
executions, since both share the same paper).

Only paper-derived predicates are generated. No fault-specific rules are
added after observing negative executions.
"""
from __future__ import annotations

import json
import re
import hashlib
from pathlib import Path
from typing import Dict, List, Any

PROJECT_ROOT = Path(__file__).resolve().parent
CONTRACTS_DIR = PROJECT_ROOT / "contracts"
CONTRACTS_DIR.mkdir(exist_ok=True)


def _sha(obj: Any) -> str:
    return hashlib.sha256(json.dumps(obj, sort_keys=True, default=str).encode()).hexdigest()


def generate_contract(study_id: str, family: str, paper_text: str) -> Dict:
    """Generate a paper-derived claim contract for one study."""
    p = paper_text

    predicates: List[Dict] = []
    universal: List[str] = []

    # ── P5/P6: seed aggregation fidelity (E01) ─────────────
    if "mean" in p.lower() and "seed" in p.lower():
        m = re.search(r"(\d+)\s*(?:random\s*)?seeds?\b|seeds?\s*(?:\(\d+\s*-\s*\d+\)|\(\d{1,2},?\s*\d{1,2},?\s*\d{1,2})\)", p)
        m2 = re.search(r"(\d+)\s*(?:random\s*)?seeds?", p)
        seed_count = int(m2.group(1)) if m2 else None
        preds = [
            {
                "predicate_id": "P6_AGGREGATION",
                "principle": "P6_AGGREGATION_FIDELITY",
                "natural_language": f"Reported value must equal the declared mean aggregation over all {seed_count or 'N'} declared seeds.",
                "trace_fields": ["protocol", "aggregation_rule", "protocol", "aggregation_inputs", "protocol", "declared_seeds"],
                "condition": "protocol.aggregation_rule == 'mean' AND len(protocol.aggregation_inputs) == len(protocol.declared_seeds)",
                "source_span": p,
                "confidence": 0.9,
            }
        ]
        predicates.extend(preds)
        universal += ["P5_DETERMINISM_OR_SEEDS", "P6_AGGREGATION_FIDELITY"]

    # ── P4: selection separation (E02) ────────────────────
    if "validation" in p.lower() and "test" in p.lower():
        predicates.append({
            "predicate_id": "P4_SELECTION",
            "principle": "P4_SELECTION_SEPARATION",
            "natural_language": "Model selection must use the validation split, not the test split.",
            "trace_fields": ["checkpoint", "selection_split", "protocol", "final_test_split"],
            "condition": "checkpoint.selection_split != 'test' AND checkpoint.selection_split != protocol.final_test_split",
            "source_span": p,
            "confidence": 0.9,
        })
        universal.append("P4_SELECTION_SEPARATION")

    # ── P3/P7: hyperparameter fidelity (E03) ─────────────
    # Only fire when the paper declares a specific hyperparameter VALUE
    # (name + number). This avoids spurious predicates on papers that
    # merely mention a concept without a concrete declared value.
    _hp_value_patterns = [
        r"learning rate\s+\d", r"lr\s*[=:]?\s*\d",
        r"\d+\s+epochs", r"epochs\s*[=:]?\s*\d",
        r"batch size\s+\d", r"weight decay\s*\d",
        r"\d+(?:\.\d+)?\s*epochs",
    ]
    declares_hp_value = any(re.search(pat, p.lower()) for pat in _hp_value_patterns)
    if declares_hp_value:
        predicates.append({
            "predicate_id": "P7_HYPERPARAMS",
            "principle": "P7_EVIDENCE_CLOSURE",
            "natural_language": "Executed hyperparameters must match the paper-declared values.",
            "trace_fields": ["protocol", "declared_hyperparameters", "protocol", "executed_hyperparameters"],
            "condition": "protocol.executed_hyperparameters == protocol.declared_hyperparameters",
            "source_span": p,
            "confidence": 0.8,
        })
        universal.append("P7_EVIDENCE_CLOSURE")

    # ── P7: subgroup evidence closure (E04) ───────────────
    # Only fire when the paper explicitly declares a set of subgroups
    # to be reported.
    _subgroup_kw = ["subgroup", "cohort", "per-", "demographic", "clinical",
                    "language family", "tissue type", "all four", "all five",
                    "all three", "per cohort", "per subgroup"]
    if any(k in p.lower() for k in _subgroup_kw):
        predicates.append({
            "predicate_id": "P7_SUBGROUPS",
            "principle": "P7_EVIDENCE_CLOSURE",
            "natural_language": "All declared subgroups must appear in the reported outputs.",
            "trace_fields": ["protocol", "declared_subgroups", "protocol", "reported_subgroups"],
            "condition": "set(protocol.reported_subgroups) == set(protocol.declared_subgroups)",
            "source_span": p,
            "confidence": 0.85,
        })
        universal.append("P7_EVIDENCE_CLOSURE")

    # ── P5: preprocessing fidelity (E05) ──────────────────
    _preproc_kw = ["normali", "augment", "preprocess", "mask", "resample",
                   "padded", "truncat", "to length", "oversampl"]
    if any(k in p.lower() for k in _preproc_kw):
        predicates.append({
            "predicate_id": "P5_PREPROCESS",
            "principle": "P5_DETERMINISM_OR_SEEDS",
            "natural_language": "Executed preprocessing must match the paper-declared preprocessing.",
            "trace_fields": ["protocol", "declared_preprocess", "protocol", "executed_preprocess"],
            "condition": "protocol.executed_preprocess == protocol.declared_preprocess",
            "source_span": p,
            "confidence": 0.8,
        })
        universal.append("P5_DETERMINISM_OR_SEEDS")

    # ── P3: compute budget symmetry (E06) ──────────────────
    if "fair" in p.lower() or "matched" in p.lower() or "same" in p.lower() or "equivalent" in p.lower():
        predicates.append({
            "predicate_id": "P3_BUDGET",
            "principle": "P3_SYMMETRY",
            "natural_language": "Compared methods must be matched on the declared training/compute budget.",
            "trace_fields": ["comparator_budgets"],
            "condition": "max(budget_value across comparator_budgets) - min(budget_value across comparator_budgets) == 0",
            "source_span": p,
            "confidence": 0.8,
        })
        universal.append("P3_SYMMETRY")

    # If no predicate matched, add a generic P7 closure requirement
    if not predicates:
        predicates.append({
            "predicate_id": "P7_GENERIC",
            "principle": "P7_EVIDENCE_CLOSURE",
            "natural_language": "All reported outputs must be traceable to upstream entities.",
            "trace_fields": ["outputs", "reported_value", "upstream_runs"],
            "condition": "len(outputs.reported_value.upstream_runs) > 0",
            "source_span": p,
            "confidence": 0.5,
        })

    contract = {
        "contract_id": f"CONTRACT_{study_id}",
        "source_paper": study_id,
        "family": family,
        "paper_text_hash": _sha(p),
        "source_span": p,
        "predicates": predicates,
        "universal_principles": sorted(set(universal)),
        "coverage_threshold": 0.70,
        "self_hash": "",
    }
    payload = {k: v for k, v in contract.items() if k != "self_hash"}
    contract["self_hash"] = _sha(payload)

    out = CONTRACTS_DIR / f"{study_id}.json"
    out.write_text(json.dumps(contract, indent=2), encoding="utf-8")
    return contract


def generate_all_contracts() -> Dict:
    """Generate one contract per study (shared across the pair)."""
    import sys
    sys.path.insert(0, str(PROJECT_ROOT))
    from generate_pairs_r1a import FAMILIES
    from pathlib import Path as _P
    idx_path = PROJECT_ROOT / "traces" / "PAIR_INDEX.json"
    index = json.loads(idx_path.read_text())

    generated = 0
    for pair_meta in index["pairs"]:
        sid = pair_meta["study_id"]
        # Load the paper text (from the trace, but paper_text is execution-independent)
        clean_trace_path = PROJECT_ROOT / pair_meta["clean_trace"]
        clean = json.loads(clean_trace_path.read_text())
        # paper text was saved in the pair index; re-derive from FAMILIES
        fam = pair_meta["family"]
        study_num = int(sid.split("-")[1])
        study = FAMILIES[fam][study_num - 1]
        paper_text = study["paper_text"]

        # If contract already exists, skip (frozen)
        existing = CONTRACTS_DIR / f"{sid}.json"
        if not existing.exists():
            generate_contract(sid, fam, paper_text)
            generated += 1

    print(f"Contracts: {generated} generated ({len(index['pairs'])} total pairs)")
    return {"generated": generated, "total": len(index["pairs"])}


if __name__ == "__main__":
    result = generate_all_contracts()
    print(result)
