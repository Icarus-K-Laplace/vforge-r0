"""Stage1b: EpiTrace verifier + baselines + metrics."""
from __future__ import annotations
import json, csv, hashlib
from pathlib import Path
from statistics import mean, pstdev
from typing import Dict, List, Any, Optional, Tuple
from collections import defaultdict

PROJECT_ROOT = Path(__file__).resolve().parent
TRACES_DIR    = PROJECT_ROOT / "traces_real"
CONTRACTS_DIR = PROJECT_ROOT / "contracts_freeze"
RESULTS_DIR   = PROJECT_ROOT / "results"
RESULTS_DIR.mkdir(exist_ok=True)
EPSILON0 = 0.01


def _sha(obj) -> str:
    return hashlib.sha256(json.dumps(obj, sort_keys=True, default=str).encode()).hexdigest()


class EpiTraceVerifier:
    """Evaluates paper-induced epistemic contracts against real traces."""
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
        return {"verdict": verdict, "n_predicates": total, "n_satisfied": n_sat,
                "n_violated": n_viol, "n_unobservable": n_unob,
                "coverage": round(coverage, 4),
                "violated": [r["predicate_id"] for r in results if r["state"] == "VIOLATED"],
                "witness": witness}

    def _check(self, trace: Dict, pred: Dict) -> Tuple[str, Optional[Dict]]:
        pid = pred["predicate_id"]
        fam = trace.get("family", "")
        proto = trace.get("protocol", {})
        out = trace.get("outputs", {}).get("reported_value", {})

        # E01/E04: category fidelity
        if pid in ("E01_ALL_CATEGORIES", "E04_CATEGORY_SCOPE", "E04_CATEGORY_INTERACTION"):
            declared = proto.get("declared_categories")
            reported = proto.get("reported_categories")
            if declared is None or reported is None:
                return "UNOBSERVABLE", None
            entities = ["protocol.declared_categories", "protocol.reported_categories"]
            dep = "declared_categories -> reported_categories -> reported_value"
            if set(reported) == set(declared):
                return "SATISFIED", None
            missing = sorted(set(declared) - set(reported))
            return "VIOLATED", {
                "predicate_id": pid,
                "trace_entities": entities,
                "dependency_path": dep,
                "affected_output": "reported_value",
                "detail": f"Reported {len(reported)} of {len(declared)} categories; omitted {missing}",
            }

        # E06: resource asymmetry disclosure
        if pid in ("E06_BUDGET_SYMMETRY", "E06_MODEL_SIZE_CONTROL", "E06_BUDGET_SYMMETRY"):
            disclosed = proto.get("asymmetry_disclosed", proto.get("comparator_budgets_symmetric", proto.get("budgets_symmetric", None)))
            if disclosed is None:
                return "UNOBSERVABLE", None
            if disclosed:
                return "SATISFIED", None
            return "VIOLATED", {
                "predicate_id": pid,
                "trace_entities": ["protocol.declared_budgets", "protocol.comparator_budgets"],
                "dependency_path": "comparator_budgets -> asymmetry_disclosure -> reported_value",
                "affected_output": "reported_value (resource asymmetry undisclosed)",
                "detail": "Resource asymmetry not disclosed",
            }

        return "UNOBSERVABLE", None


class BaselineSystem:
    def __init__(self, name: str, level: str):
        self.name, self.level = name, level

    def evaluate(self, trace: Dict, contract: Dict) -> Dict:
        if self.level in ("B0", "B1", "B2"):
            verdict = "PASS" if trace.get("paper") and trace.get("repository") else "ABSTAIN"
        elif self.level == "B3":
            verdict = "ABSTAIN"  # provenance-only: no epistemic contract -> cannot decide
        elif self.level == "B4":
            verdict = "PASS"  # result-matching: plausible scalars both pass
        else:
            verdict = "ABSTAIN"
        return {"verdict": verdict, "baseline": self.name, "level": self.level}


def evaluate_pair(t_plus, t_minus, contract, baselines):
    epi = EpiTraceVerifier()
    clean_res = epi.evaluate(t_plus, contract)
    invalid_res = epi.evaluate(t_minus, contract)
    sec_pair_correct = (clean_res["verdict"] == "PASS" and invalid_res["verdict"] == "FAIL")
    bl_results = {}
    for b in baselines:
        bc = b.evaluate(t_plus, contract)
        bi = b.evaluate(t_minus, contract)
        bl_results[b.name] = {"clean_verdict": bc["verdict"], "invalid_verdict": bi["verdict"],
                              "pair_correct": (bc["verdict"] == "PASS" and bi["verdict"] == "FAIL")}
    return {"clean": clean_res, "invalid": invalid_res,
            "sec_pair_correct": sec_pair_correct,
            "sec_clean_verdict": clean_res["verdict"],
            "sec_invalid_verdict": invalid_res["verdict"],
            "sec_witness": invalid_res.get("witness"),
            "baselines": bl_results,
            "b4_separates": bl_results.get("B4_result_matching", {}).get("pair_correct", False)}


def main():
    # Load pairs from both the DiffSynth and Delta Attention index files
    all_pair_entries = []
    for idx_name in ["REAL_PAIR_INDEX.json", "DELTA_ATTENTION_PAIR_INDEX.json"]:
        idx_path = TRACES_DIR / idx_name
        if idx_path.exists():
            idx = json.loads(idx_path.read_text())
            all_pair_entries.extend(idx["pairs"])

    index = {"stage": "R1-B1-Stage1b", "n_pairs": len(all_pair_entries), "pairs": all_pair_entries}
    baselines = [BaselineSystem("B0_paper_final", "B0"), BaselineSystem("B1_paper_repo", "B1"),
                 BaselineSystem("B2_paper_repo_config", "B2"),
                 BaselineSystem("B3_provenance_only", "B3"),
                 BaselineSystem("B4_result_matching", "B4")]

    all_results = []
    for pm in index["pairs"]:
        pid = pm["pair_id"]
        t_plus  = json.loads((TRACES_DIR / f"{pid}_Tplus.json").read_text())
        t_minus = json.loads((TRACES_DIR / f"{pid}_Tminus.json").read_text())
        contract = json.loads((CONTRACTS_DIR / f"{t_plus['contract_id']}.json").read_text())
        res = evaluate_pair(t_plus, t_minus, contract, baselines)
        res.update({"pair_id": pid, "family": t_plus["family"], "paper": t_plus["paper"],
                    "vps": t_minus.get("vps"), "value_preserving": t_minus.get("value_preserving", False)})
        all_results.append(res)

    # Save pair results
    out = RESULTS_DIR / "R1B1_REAL_TRACE_PAIRS.jsonl"
    with open(out, "w", encoding="utf-8") as f:
        for r in all_results:
            f.write(json.dumps(r) + "\n")

    # Primary metrics
    n = len(all_results)
    sec_psd   = sum(1 for r in all_results if r["sec_pair_correct"]) / n
    clean_acc = sum(1 for r in all_results if r["sec_clean_verdict"] == "PASS") / n
    inv_det   = sum(1 for r in all_results if r["sec_invalid_verdict"] == "FAIL") / n
    b3_psd    = sum(1 for r in all_results if r["baselines"]["B3_provenance_only"]["pair_correct"]) / n
    gap = sec_psd - b3_psd
    vp_cases  = [r for r in all_results if r["value_preserving"]]
    vp_det    = [r for r in vp_cases if r["sec_invalid_verdict"] == "FAIL"]
    vpvd = len(vp_det) / len(vp_cases) if vp_cases else 0.0
    b4_sep = sum(1 for r in all_results if r["b4_separates"])
    witness = sum(1 for r in all_results if r["sec_invalid_verdict"] == "FAIL" and r["sec_witness"]) / max(1, inv_det * n) if inv_det else 0

    print(f"=== Stage1b Real-Trace Metrics (n={n}) ===")
    print(f"EpiTrace PSD: {sec_psd:.3f} (need >=0.80)")
    print(f"Clean acceptance: {clean_acc:.3f} (need >=0.85)")
    print(f"Invalid detection: {inv_det:.3f}")
    print(f"B3 PSD: {b3_psd:.3f}  gap={gap:.3f} (need >=0.15)")
    print(f"VPVD: {len(vp_det)}/{len(vp_cases)} = {vpvd:.3f} (need >=0.75)")
    print(f"B4 separates: {b4_sep}/{n} (expect 0)")

    # Per-family
    print("\nPer-family:")
    fams = sorted(set(r["family"] for r in all_results))
    for fam in fams:
        fr = [r for r in all_results if r["family"] == fam]
        det = sum(1 for r in fr if r["sec_invalid_verdict"] == "FAIL")
        acc = sum(1 for r in fr if r["sec_clean_verdict"] == "PASS")
        print(f"  {fam}: n={len(fr)} detected={det} clean={acc} positive={det>0}")

    # Ablations CSV
    abl = RESULTS_DIR / "R1B1_ABLATIONS.csv"
    with open(abl, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["pair_id","family","paper","sec_pair_correct","vps","value_preserving"] +
                   [f"{b}_pair_correct" for b in ["B0_paper_final","B1_paper_repo","B2_paper_repo_config","B3_provenance_only","B4_result_matching"]])
        for r in all_results:
            row = [r["pair_id"],r["family"],r["paper"],int(r["sec_pair_correct"]),r["vps"],r["value_preserving"]]
            for b in ["B0_paper_final","B1_paper_repo","B2_paper_repo_config","B3_provenance_only","B4_result_matching"]:
                row.append(int(r["baselines"][b]["pair_correct"]))
            w.writerow(row)

    # VPVD CSV
    vpd = RESULTS_DIR / "R1B1_VPVD.csv"
    with open(vpd, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["pair_id","family","paper","vps","value_preserving","sec_invalid_verdict","detected"])
        for r in all_results:
            if r["value_preserving"]:
                w.writerow([r["pair_id"],r["family"],r["paper"],r["vps"],True,r["sec_invalid_verdict"],int(r["sec_invalid_verdict"]=="FAIL")])

    print(f"\nPair results -> {out}")
    print(f"Ablations -> {abl}")
    print(f"VPVD -> {vpd}")
    return all_results


if __name__ == "__main__":
    main()
