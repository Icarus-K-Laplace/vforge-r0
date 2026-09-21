"""
R1-B1 Trace Observability Score (TOS).

For each claim C:
  R_C = required runtime fields implied by the contract
  O_C = observed fields in the real trace
  TOS(C) = |R_C ∩ O_C| / |R_C|

No hallucination of missing provenance.
TOS >= 0.70 required for a pair to enter the main evaluation.
"""
from __future__ import annotations

import json
import csv
from pathlib import Path
from typing import Dict, List

PROJECT_ROOT = Path(__file__).resolve().parent
TRACES_DIR   = PROJECT_ROOT / "traces_real"
CONTRACTS_DIR = PROJECT_ROOT / "contracts_real"
RESULTS_DIR   = PROJECT_ROOT / "results"


def required_fields(contract: Dict, family: str) -> List[str]:
    """Required runtime fields implied by the contract + family."""
    req = []
    for pred in contract.get("predicates", []):
        for tf in pred.get("trace_fields", []):
            if tf not in req:
                req.append(tf)
    # Family-specific required fields
    if family == "E01":
        for f in ["protocol.declared_seeds", "protocol.aggregation_inputs",
                  "protocol.aggregation_rule", "outputs.reported_value"]:
            if f not in req:
                req.append(f)
    elif family == "E04":
        for f in ["protocol.declared_subgroups", "protocol.reported_subgroups",
                  "outputs.reported_value"]:
            if f not in req:
                req.append(f)
    elif family == "E02":
        for f in ["checkpoint.selection_split", "checkpoint.candidates",
                  "checkpoint.selected", "protocol.final_test_split"]:
            if f not in req:
                req.append(f)
    elif family == "E06":
        for f in ["comparator_budgets"]:
            if f not in req:
                req.append(f)
    return req


def observed_fields(trace: Dict) -> List[str]:
    """Which required trace fields are actually present in the real trace."""
    obs = []
    proto = trace.get("protocol", {})
    out = trace.get("outputs", {}).get("reported_value", {})

    # Flatten the trace into a set of dotted paths that are present
    present = set()
    if "declared_seeds" in proto:
        present.add("protocol.declared_seeds")
    if "aggregation_inputs" in proto or "upstream_runs" in out:
        present.add("protocol.aggregation_inputs")
    if "aggregation_rule" in proto or "aggregation_rule" in out:
        present.add("protocol.aggregation_rule")
    if "reported_value" in trace.get("outputs", {}):
        present.add("outputs.reported_value")
    if "declared_subgroups" in proto:
        present.add("protocol.declared_subgroups")
    if "reported_subgroups" in proto:
        present.add("protocol.reported_subgroups")
    if "upstream_tasks" in out:
        present.add("outputs.upstream_tasks")
    # E02 fields (usually not observable in W&B summaries)
    if "selection_split" in proto:
        present.add("protocol.selection_split")
    if "candidates" in trace.get("checkpoint", {}):
        present.add("checkpoint.candidates")
    if "selected" in trace.get("checkpoint", {}):
        present.add("checkpoint.selected")
    if "selection_split" in trace.get("checkpoint", {}):
        present.add("checkpoint.selection_split")
    if "comparator_budgets" in trace:
        present.add("comparator_budgets")

    for f in required_fields_from_req(present):
        if f in present:
            obs.append(f)
    return obs


def required_fields_from_req(present: set) -> List[str]:
    return ["protocol.declared_seeds", "protocol.aggregation_inputs",
            "protocol.aggregation_rule", "outputs.reported_value",
            "protocol.declared_subgroups", "protocol.reported_subgroups",
            "protocol.selection_split", "checkpoint.candidates",
            "checkpoint.selected", "comparator_budgets"]


def compute_tos(trace: Dict, contract: Dict, family: str) -> Dict:
    req = required_fields(contract, family)
    # Re-derive observed for this specific required set
    proto = trace.get("protocol", {})
    out = trace.get("outputs", {}).get("reported_value", {})
    present = set()
    if "declared_seeds" in proto:
        present.add("protocol.declared_seeds")
    if "aggregation_inputs" in proto or "upstream_runs" in out:
        present.add("protocol.aggregation_inputs")
    if "aggregation_rule" in proto or "aggregation_rule" in out:
        present.add("protocol.aggregation_rule")
    if "reported_value" in trace.get("outputs", {}):
        present.add("outputs.reported_value")
    if "declared_subgroups" in proto:
        present.add("protocol.declared_subgroups")
    if "reported_subgroups" in proto:
        present.add("protocol.reported_subgroups")
    if "upstream_tasks" in out:
        present.add("outputs.upstream_tasks")
    if "selection_split" in proto:
        present.add("protocol.selection_split")
    if "candidates" in trace.get("checkpoint", {}):
        present.add("checkpoint.candidates")
    if "selected" in trace.get("checkpoint", {}):
        present.add("checkpoint.selected")
    if "comparator_budgets" in trace:
        present.add("comparator_budgets")

    observed = [f for f in req if f in present]
    missing = [f for f in req if f not in present]
    tos = len(observed) / len(req) if req else 0.0
    return {
        "n_required": len(req),
        "n_observed": len(observed),
        "observed": observed,
        "missing": missing,
        "TOS": round(tos, 4),
        "qualifies": tos >= 0.70,
    }


def main():
    index = json.loads((TRACES_DIR / "REAL_PAIR_INDEX.json").read_text())
    rows = []
    n_qualify = 0
    n_total = 0
    for pm in index["pairs"]:
        pid = pm["pair_id"]
        family = pm["family"]
        for side in ("Tplus", "Tminus"):
            trace = json.loads((TRACES_DIR / f"{pid}_{side}.json").read_text())
            contract = json.loads((CONTRACTS_DIR / f"{trace['contract_id']}.json").read_text())
            r = compute_tos(trace, contract, family)
            r.update({"pair_id": pid, "side": side, "family": family,
                     "paper": trace.get("paper")})
            rows.append(r)
            n_total += 1
            if r["qualifies"]:
                n_qualify += 1

    # Per-pair TOS (use the max of the two sides)
    pair_tos: Dict[str, float] = {}
    for r in rows:
        pid = r["pair_id"]
        pair_tos[pid] = max(pair_tos.get(pid, 0), r["TOS"])

    import statistics
    tos_values = [v for v in pair_tos.values() if v > 0]
    median_tos = statistics.median(tos_values) if tos_values else 0.0
    print(f"Pair-level TOS: median={median_tos:.3f}  "
          f"(qualifying >=0.70: {sum(1 for v in pair_tos.values() if v>=0.70)}/{len(pair_tos)})")

    # Save TOS CSV
    out = RESULTS_DIR / "R1B1_TRACE_OBSERVABILITY.csv"
    with open(out, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["pair_id", "side", "family", "paper",
                                          "n_required", "n_observed",
                                          "TOS", "qualifies",
                                          "observed", "missing"])
        w.writeheader()
        for r in rows:
            row = {k: r[k] for k in ["pair_id", "side", "family", "paper",
                                     "n_required", "n_observed", "TOS", "qualifies"]}
            row["observed"] = "|".join(r["observed"])
            row["missing"] = "|".join(r["missing"])
            w.writerow(row)
    print(f"TOS -> {out}")

    # Also save E02 observability record
    e02_rec = index.get("e02_attempt", {})
    e02_tos_path = RESULTS_DIR / "R1B1_E02_TOS_RECORD.json"
    e02_tos_path.write_text(json.dumps({
        "family": "E02",
        "status": e02_rec.get("status"),
        "TOS": 0.0,
        "qualifies": False,
        "reason": e02_rec.get("reasoning"),
    }, indent=2), encoding="utf-8")
    print(f"E02 TOS record -> {e02_tos_path}")

    return pair_tos


if __name__ == "__main__":
    main()
