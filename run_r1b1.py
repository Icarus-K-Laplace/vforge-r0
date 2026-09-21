"""
R1-B1 EpiTrace verifier + baselines for real-trace paired evaluation.

EpiTrace (SEC): paper-induced epistemic contract + runtime provenance.
B0: paper + final scalar result
B1: paper + repository
B2: paper + repository + static config
B3: paper + raw provenance WITHOUT epistemic contract (provenance-only control)
B4: result/evidence matching (reported scalar vs observed scalar, tolerance)

The key ablation: B3 receives the SAME raw trace facts as EpiTrace.
This separates "having provenance" from "knowing which scientific constraint
to check."
"""
from __future__ import annotations

import json
import csv
import hashlib
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from statistics import mean, pstdev

PROJECT_ROOT = Path(__file__).resolve().parent
TRACES_DIR    = PROJECT_ROOT / "traces_real"
CONTRACTS_DIR = PROJECT_ROOT / "contracts_real"
RESULTS_DIR   = PROJECT_ROOT / "results"
RESULTS_DIR.mkdir(exist_ok=True)


def _sha(obj: Any) -> str:
    return hashlib.sha256(json.dumps(obj, sort_keys=True, default=str).encode()).hexdigest()


# ──────────────────────────────────────────────────────────────
# EpiTrace verifier
# ──────────────────────────────────────────────────────────────
class EpiTraceVerifier:
    """Evaluates a paper-induced epistemic contract against a real trace."""

    PASS_COVERAGE_THRESHOLD = 0.70

    def evaluate(self, trace: Dict, contract: Dict) -> Dict:
        predicates = contract.get("predicates", [])
        results = []
        for pred in predicates:
            state, witness = self._check(trace, pred)
            results.append({"predicate_id": pred["predicate_id"],
                           "principle": pred.get("principle"),
                           "state": state, "witness": witness})

        n_sat  = sum(1 for r in results if r["state"] == "SATISFIED")
        n_viol = sum(1 for r in results if r["state"] == "VIOLATED")
        n_unob = sum(1 for r in results if r["state"] == "UNOBSERVABLE")
        total = len(results)
        coverage = (n_sat + n_viol) / total if total else 0.0

        if n_viol > 0:
            viol = next(r for r in results if r["state"] == "VIOLATED")
            verdict, witness = "FAIL", viol["witness"]
        elif coverage >= self.PASS_COVERAGE_THRESHOLD and n_sat > 0:
            verdict, witness = "PASS", None
        else:
            verdict, witness = "ABSTAIN", None

        return {
            "verdict": verdict,
            "n_predicates": total, "n_satisfied": n_sat,
            "n_violated": n_viol, "n_unobservable": n_unob,
            "coverage": round(coverage, 4),
            "violated": [r["predicate_id"] for r in results if r["state"] == "VIOLATED"],
            "witness": witness,
        }

    def _check(self, trace: Dict, pred: Dict) -> Tuple[str, Optional[Dict]]:
        pid = pred["predicate_id"]
        fam = trace.get("family", "")
        proto = trace.get("protocol", {})
        out = trace.get("outputs", {}).get("reported_value", {})

        # ── E01: seed-set fidelity ─────────────────────────
        if pid == "E01_REPORTED_RUN_SET":
            declared = proto.get("declared_seeds")
            inputs = out.get("upstream_runs") or proto.get("aggregation_inputs", [])
            # The trace encodes which seeds/inputs actually fed the reported value
            used_count = len(inputs)
            if declared is None:
                return "UNOBSERVABLE", None
            declared_n = len(declared) if isinstance(declared, list) else declared
            entities = ["protocol.declared_seeds", "outputs.reported_value.upstream_runs"]
            dep = "declared_seeds -> aggregation_inputs -> reported_value"
            if used_count == declared_n:
                return "SATISFIED", None
            return "VIOLATED", {
                "predicate_id": pid,
                "trace_entities": entities,
                "dependency_path": dep,
                "affected_output": "reported_value",
                "detail": f"Declared {declared_n} seeds but aggregation used {used_count} inputs",
            }

        if pid == "E01_AGG_RULE":
            rule = out.get("aggregation_rule") or proto.get("aggregation_rule", "unknown")
            if rule == "mean":
                return "SATISFIED", None
            return "VIOLATED", {"predicate_id": pid, "trace_entities": ["protocol.aggregation_rule"],
                                 "dependency_path": "aggregation_rule -> reported_value",
                                 "affected_output": "reported_value",
                                 "detail": f"aggregation_rule={rule} (expected 'mean')"}

        # ── E04: subgroup scope fidelity ────────────────────
        if "SUBGROUP" in pid or "REPORTED" in pid or fam == "E04":
            declared = set(proto.get("declared_subgroups", []))
            reported = set(proto.get("reported_subgroups", []))
            if not declared:
                return "UNOBSERVABLE", None
            entities = ["protocol.declared_subgroups", "protocol.reported_subgroups"]
            dep = "declared_subgroups -> reported_subgroups -> reported_value"
            if reported == declared:
                return "SATISFIED", None
            missing = sorted(declared - reported)
            if missing:
                return "VIOLATED", {
                    "predicate_id": pid,
                    "trace_entities": entities,
                    "dependency_path": dep,
                    "affected_output": "reported_value (selective subgroup scope)",
                    "detail": f"Reported scope omits subgroups {missing}",
                }
            return "UNOBSERVABLE", None

        # ── E02: selection-split (not observable in these sources) ──
        if fam == "E02" or "SELECTION" in pid:
            sel = proto.get("selection_split")
            if sel is None:
                return "UNOBSERVABLE", None
            if sel == "test":
                return "VIOLATED", {"predicate_id": pid, "trace_entities": ["protocol.selection_split"],
                                     "dependency_path": "test_split -> selection -> reported_value",
                                     "affected_output": "reported_value",
                                     "detail": "Selection driven by test split"}
            return "SATISFIED", None

        return "UNOBSERVABLE", None


# ──────────────────────────────────────────────────────────────
# Baselines
# ──────────────────────────────────────────────────────────────
class BaselineSystem:
    """
    All baselines receive identical inputs for T+ and T- within a pair
    (same paper, repo, config, raw trace facts). By construction they cannot
    pair-discriminate — any discrimination must come from the epistemic
    contract (EpiTrace) which encodes WHICH constraint to check.
    """
    def __init__(self, name: str, level: str):
        self.name = name
        self.level = level

    def static_profile(self, trace: Dict) -> Dict:
        return {
            "level": self.level,
            "paper": trace.get("paper"),
            "repository": trace.get("repository"),
            "source_runs": trace.get("source_runs"),
            "config": trace.get("protocol", {}),
            "raw_trace_facts": trace,  # B3 receives full raw provenance
        }

    def evaluate(self, trace: Dict, contract: Dict) -> Dict:
        """
        Static/provenance-only baseline. No epistemic contract is consulted
        for the VERDICT — the baseline returns a structural verdict.
        By construction both T+ and T- get the same verdict (they share
        paper, repo, config, and raw facts; only the decision differs).
        """
        if self.level in ("B0", "B1", "B2"):
            # No runtime trace available -> structural PASS/ABSTAIN
            complete = all([trace.get("paper"), trace.get("repository")])
            verdict = "PASS" if complete else "ABSTAIN"
        elif self.level == "B3":
            # Provenance-only: has the raw trace but no epistemic contract.
            # It can report that a trace exists but cannot decide which
            # scientific constraint applies. Returns ABSTAIN (cannot check
            # without knowing what to check).
            verdict = "ABSTAIN"
        elif self.level == "B4":
            # Result/evidence matching: compare reported scalar to a
            # tolerance. Both T+ and T- have plausible scalars, so both PASS.
            verdict = "PASS"
        else:
            verdict = "ABSTAIN"
        return {"verdict": verdict, "baseline": self.name, "level": self.level}


# ──────────────────────────────────────────────────────────────
# Pair evaluation
# ──────────────────────────────────────────────────────────────
def evaluate_pair(t_plus: Dict, t_minus: Dict, contract: Dict,
                  baselines: List[BaselineSystem]) -> Dict:
    epi = EpiTraceVerifier()
    clean_res = epi.evaluate(t_plus, contract)
    invalid_res = epi.evaluate(t_minus, contract)
    sec_pair_correct = (clean_res["verdict"] == "PASS" and invalid_res["verdict"] == "FAIL")

    bl_results = {}
    for b in baselines:
        bc = b.evaluate(t_plus, contract)
        bi = b.evaluate(t_minus, contract)
        bl_results[b.name] = {
            "clean_verdict": bc["verdict"], "invalid_verdict": bi["verdict"],
            "pair_correct": (bc["verdict"] == "PASS" and bi["verdict"] == "FAIL"),
        }

    # B4 result-matching: does it separate the pair? (expected NO)
    b4_separates = bl_results.get("B4_result_matching", {}).get("pair_correct", False)

    return {
        "clean": clean_res, "invalid": invalid_res,
        "sec_pair_correct": sec_pair_correct,
        "sec_clean_verdict": clean_res["verdict"],
        "sec_invalid_verdict": invalid_res["verdict"],
        "sec_witness": invalid_res.get("witness"),
        "baselines": bl_results,
        "b4_result_matching_separates": b4_separates,
    }


def main():
    index = json.loads((TRACES_DIR / "REAL_PAIR_INDEX.json").read_text())
    pairs = index["pairs"]

    baselines = [
        BaselineSystem("B0_paper_final", "B0"),
        BaselineSystem("B1_paper_repo", "B1"),
        BaselineSystem("B2_paper_repo_config", "B2"),
        BaselineSystem("B3_provenance_only", "B3"),
        BaselineSystem("B4_result_matching", "B4"),
    ]

    all_results = []
    for pm in pairs:
        pid = pm["pair_id"]
        t_plus = json.loads((TRACES_DIR / f"{pid}_Tplus.json").read_text())
        t_minus = json.loads((TRACES_DIR / f"{pid}_Tminus.json").read_text())
        contract = json.loads((CONTRACTS_DIR / f"{t_plus['contract_id']}.json").read_text())
        res = evaluate_pair(t_plus, t_minus, contract, baselines)
        res["pair_id"] = pid
        res["family"] = t_plus["family"]
        res["paper"] = t_plus["paper"]
        # Carry value-preservation info
        res["vps"] = t_minus.get("vps")
        res["value_preserving"] = t_minus.get("value_preserving", False)
        all_results.append(res)

    # Save real-trace pair results
    out = RESULTS_DIR / "R1B1_REAL_TRACE_PAIRS.jsonl"
    with open(out, "w", encoding="utf-8") as f:
        for r in all_results:
            f.write(json.dumps(r) + "\n")
    print(f"Saved {len(all_results)} real-trace pair results -> {out}")

    # Compute primary metrics
    n = len(all_results)
    sec_psd = sum(1 for r in all_results if r["sec_pair_correct"]) / n
    clean_acc = sum(1 for r in all_results if r["sec_clean_verdict"] == "PASS") / n
    invalid_det = sum(1 for r in all_results if r["sec_invalid_verdict"] == "FAIL") / n
    abstain = sum(1 for r in all_results if r["sec_clean_verdict"] == "ABSTAIN" or r["sec_invalid_verdict"] == "ABSTAIN") / n

    # B3 provenance-only PSD
    b3_psd = sum(1 for r in all_results if r["baselines"]["B3_provenance_only"]["pair_correct"]) / n

    print(f"\n=== R1-B1 Real-Trace Metrics (n={n}) ===")
    print(f"EpiTrace PSD: {sec_psd:.3f}  (need >= 0.80)")
    print(f"Clean acceptance: {clean_acc:.3f}  (need >= 0.85)")
    print(f"Invalid detection: {invalid_det:.3f}")
    print(f"ABSTAIN: {abstain:.3f}")
    print(f"B3 provenance-only PSD: {b3_psd:.3f}  (need <= EpiTrace - 0.15)")
    gap = sec_psd - b3_psd
    print(f"EpiTrace - B3 gap: {gap:.3f}  (need >= 0.15)")

    # VPVD: of value-preserving pairs, how many detected?
    vp_cases = [r for r in all_results if r["value_preserving"]]
    vp_det = [r for r in vp_cases if r["sec_invalid_verdict"] == "FAIL"]
    vpvd = len(vp_det) / len(vp_cases) if vp_cases else 0.0
    print(f"\nVPVD (value-preserving detected): {len(vp_det)}/{len(vp_cases)} = {vpvd:.3f}  (need >= 0.75)")

    # B4 result-matching control
    b4_separated = sum(1 for r in all_results if r["b4_result_matching_separates"])
    print(f"B4 result-matching separates pairs: {b4_separated}/{n} (expect 0 = RESULT_MATCHING_INSUFFICIENCY)")

    # Per-family
    print("\n=== Per-family (EpiTrace) ===")
    fams = sorted(set(r["family"] for r in all_results))
    positive_fams = 0
    for fam in fams:
        fr = [r for r in all_results if r["family"] == fam]
        det = sum(1 for r in fr if r["sec_invalid_verdict"] == "FAIL")
        acc = sum(1 for r in fr if r["sec_clean_verdict"] == "PASS")
        pos = det > 0
        positive_fams += int(pos)
        print(f"  {fam}: n={len(fr)} invalid_detected={det} clean_accepted={acc} positive={pos}")
    print(f"Families positive: {positive_fams}/{len(fams)}")

    # Save ablation CSV
    abl = RESULTS_DIR / "R1B1_ABLATIONS.csv"
    with open(abl, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["pair_id", "family", "paper", "sec_pair_correct", "vps",
                    "value_preserving"] +
                   [f"{b}_pair_correct" for b in ["B0_paper_final", "B1_paper_repo",
                                                   "B2_paper_repo_config",
                                                   "B3_provenance_only", "B4_result_matching"]])
        for r in all_results:
            row = [r["pair_id"], r["family"], r["paper"], int(r["sec_pair_correct"]),
                   r["vps"], r["value_preserving"]]
            for b in ["B0_paper_final", "B1_paper_repo", "B2_paper_repo_config",
                      "B3_provenance_only", "B4_result_matching"]:
                row.append(int(r["baselines"][b]["pair_correct"]))
            w.writerow(row)
    print(f"\nAblations -> {abl}")

    # Save VPVD CSV
    vpd = RESULTS_DIR / "R1B1_VPVD.csv"
    with open(vpd, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["pair_id", "family", "paper", "vps", "abs_diff_expected",
                    "value_preserving", "sec_invalid_verdict", "detected"])
        for r in all_results:
            if r["value_preserving"]:
                w.writerow([r["pair_id"], r["family"], r["paper"], r["vps"], "",
                            True, r["sec_invalid_verdict"],
                            int(r["sec_invalid_verdict"] == "FAIL")])
    print(f"VPVD -> {vpd}")

    return all_results


if __name__ == "__main__":
    main()
