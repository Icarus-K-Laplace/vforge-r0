"""
R1-A TraceContract Verifier + Baselines.

TC (TraceContract): evaluates a paper-derived contract against a full
runtime execution trace, producing PASS / FAIL / ABSTAIN with a trace
witness for any FAIL.

Baselines:
  B0 Paper-only LLM      (simulated: paper text -> static verdict, no trace)
  B1 Paper + repo LLM    (simulated: paper + repo metadata, no runtime trace)
  B2 Static claim-guided (simulated: paper + repo, static config, no runtime)
  B3 Paper + repo + config (static config file only, no runtime provenance)

All static baselines receive identical inputs for both members of a pair,
so by construction they CANNOT pair-discriminate (same paper + same repo +
same static config for clean and invalid). They can only differ if the
baseline is given explicitly-supplied runtime information.
"""
from __future__ import annotations

import json
import hashlib
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any

PROJECT_ROOT = Path(__file__).resolve().parent
CONTRACTS_DIR = PROJECT_ROOT / "contracts"
TRACES_DIR    = PROJECT_ROOT / "traces"
RESULTS_DIR   = PROJECT_ROOT / "results"
RESULTS_DIR.mkdir(exist_ok=True)


def _sha(obj: Any) -> str:
    return hashlib.sha256(json.dumps(obj, sort_keys=True, default=str).encode()).hexdigest()


# ──────────────────────────────────────────────────────────────
# TraceContract verifier
# ──────────────────────────────────────────────────────────────
class TraceContractVerifier:
    """Evaluates paper-derived contract predicates against a runtime trace."""

    PASS_COVERAGE_THRESHOLD = 0.70

    def evaluate(self, trace: Dict, contract: Dict) -> Dict:
        """
        Returns:
            {
              verdict: PASS|FAIL|ABSTAIN,
              n_predicates, n_satisfied, n_violated, n_unobservable,
              coverage,
              violated: [predicate_ids],
              witness: {predicate_id, trace_entities, dependency_path, affected_output} | None,
            }
        """
        predicates = contract.get("predicates", [])
        results = []

        for pred in predicates:
            state, witness = self._check_predicate(trace, pred)
            results.append({
                "predicate_id": pred["predicate_id"],
                "principle": pred.get("principle"),
                "state": state,
                "witness": witness,
            })

        n_sat   = sum(1 for r in results if r["state"] == "SATISFIED")
        n_viol  = sum(1 for r in results if r["state"] == "VIOLATED")
        n_unob  = sum(1 for r in results if r["state"] == "UNOBSERVABLE")
        total   = len(results)
        coverage = (n_sat + n_viol) / total if total else 0.0

        # Verdict
        if n_viol > 0:
            viol = next(r for r in results if r["state"] == "VIOLATED")
            verdict = "FAIL"
            witness = viol["witness"]
        elif coverage >= self.PASS_COVERAGE_THRESHOLD and n_sat > 0:
            verdict = "PASS"
            witness = None
        else:
            verdict = "ABSTAIN"
            witness = None

        return {
            "verdict": verdict,
            "n_predicates": total,
            "n_satisfied": n_sat,
            "n_violated": n_viol,
            "n_unobservable": n_unob,
            "coverage": round(coverage, 4),
            "violated": [r["predicate_id"] for r in results if r["state"] == "VIOLATED"],
            "witness": witness,
        }

    def _check_predicate(self, trace: Dict, pred: Dict) -> Tuple[str, Optional[Dict]]:
        pid = pred["predicate_id"]
        ptype = pid.split("_")[0]  # P1..P7, P4, P6

        if pid == "P6_AGGREGATION":
            return self._check_p6(trace)
        elif pid == "P4_SELECTION":
            return self._check_p4(trace)
        elif pid == "P7_HYPERPARAMS":
            return self._check_p7_hyper(trace)
        elif pid == "P7_SUBGROUPS":
            return self._check_p7_subgroups(trace)
        elif pid == "P5_PREPROCESS":
            return self._check_p5_preprocess(trace)
        elif pid == "P3_BUDGET":
            return self._check_p3_budget(trace)
        elif pid == "P7_GENERIC":
            return self._check_p7_generic(trace)
        else:
            return "UNOBSERVABLE", None

    def _check_p6(self, trace: Dict) -> Tuple[str, Optional[Dict]]:
        """Reported value must equal declared aggregation over declared seeds."""
        proto = trace.get("protocol", {})
        decl = proto.get("declared_seeds", [])
        agg_rule = proto.get("aggregation_rule", "unknown")
        agg_inputs = proto.get("aggregation_inputs", [])
        out = trace.get("outputs", {}).get("reported_value", {})
        out_rule = out.get("aggregation_rule", "unknown")

        entities = ["protocol.declared_seeds", "protocol.aggregation_rule",
                    "protocol.aggregation_inputs", "outputs.reported_value"]
        dep = "declared_seeds -> aggregation_rule -> reported_value"

        # Clean: aggregation_rule == 'mean' AND #inputs == #declared seeds
        if agg_rule == "mean" and out_rule == "mean" and len(agg_inputs) == len(decl) and len(decl) > 1:
            return "SATISFIED", None
        # Invalid: aggregation_rule == 'best' OR inputs is a strict subset
        if agg_rule == "best" or out_rule == "best" or (len(agg_inputs) < len(decl) and decl):
            return "VIOLATED", {
                "predicate_id": "P6_AGGREGATION",
                "trace_entities": entities,
                "dependency_path": dep,
                "affected_output": "reported_value",
                "detail": f"Declared {len(decl)} seeds but aggregation_rule={agg_rule}, inputs={len(agg_inputs)}",
            }
        return "UNOBSERVABLE", None

    def _check_p4(self, trace: Dict) -> Tuple[str, Optional[Dict]]:
        """Selection split must not be the test split."""
        ckpt = trace.get("checkpoint", {})
        sel_split = ckpt.get("selection_split", "none")
        entities = ["checkpoint.selection_split", "protocol.final_test_split"]
        dep = "selection_split -> checkpoint.selected"
        if sel_split == "test":
            return "VIOLATED", {
                "predicate_id": "P4_SELECTION",
                "trace_entities": entities,
                "dependency_path": dep,
                "affected_output": "reported_value (selected via test split)",
                "detail": f"selection_split={sel_split}",
            }
        if sel_split in ("validation", "none", ""):
            return "SATISFIED", None
        return "UNOBSERVABLE", None

    def _check_p7_hyper(self, trace: Dict) -> Tuple[str, Optional[Dict]]:
        """Executed hyperparameters must match the paper-declared values."""
        proto = trace.get("protocol", {})
        declared = proto.get("declared_hyperparameters")
        executed = proto.get("executed_hyperparameters")
        if declared is None or executed is None:
            # Fall back to config_hash comparison is not possible at
            # single-trace level; mark UNOBSERVABLE.
            return "UNOBSERVABLE", None
        entities = ["protocol.declared_hyperparameters", "protocol.executed_hyperparameters"]
        dep = "declared_hyperparameters -> executed_hyperparameters -> training -> reported_value"
        if executed == declared:
            return "SATISFIED", None
        diffs = {k: (declared.get(k), executed.get(k))
                 for k in set(declared) | set(executed)
                 if declared.get(k) != executed.get(k)}
        if diffs:
            return "VIOLATED", {
                "predicate_id": "P7_HYPERPARAMS",
                "trace_entities": entities,
                "dependency_path": dep,
                "affected_output": "reported_value (config mismatch)",
                "detail": f"Executed differs from declared: {diffs}",
            }
        return "UNOBSERVABLE", None

    def _check_p7_subgroups(self, trace: Dict) -> Tuple[str, Optional[Dict]]:
        """Reported subgroups must equal declared subgroups."""
        proto = trace.get("protocol", {})
        declared = set(proto.get("declared_subgroups", []))
        reported = set(proto.get("reported_subgroups", []))
        if not declared:
            return "UNOBSERVABLE", None
        entities = ["protocol.declared_subgroups", "protocol.reported_subgroups"]
        dep = "declared_subgroups -> reported_subgroups -> evaluation.metrics"
        if reported == declared:
            return "SATISFIED", None
        missing = declared - reported
        if missing:
            return "VIOLATED", {
                "predicate_id": "P7_SUBGROUPS",
                "trace_entities": entities,
                "dependency_path": dep,
                "affected_output": "evaluation.metrics (missing subgroups)",
                "detail": f"Missing subgroups: {sorted(missing)}",
            }
        return "UNOBSERVABLE", None

    def _check_p5_preprocess(self, trace: Dict) -> Tuple[str, Optional[Dict]]:
        """Executed preprocess must equal declared preprocess."""
        proto = trace.get("protocol", {})
        declared = proto.get("declared_preprocess", {})
        executed = proto.get("executed_preprocess", declared)
        if not declared:
            return "UNOBSERVABLE", None
        entities = ["protocol.declared_preprocess", "protocol.executed_preprocess"]
        dep = "declared_preprocess -> executed_preprocess -> model output"
        if executed == declared:
            return "SATISFIED", None
        # Find the differing keys
        diffs = {k: (declared.get(k), executed.get(k))
                 for k in set(declared) | set(executed)
                 if declared.get(k) != executed.get(k)}
        if diffs:
            return "VIOLATED", {
                "predicate_id": "P5_PREPROCESS",
                "trace_entities": entities,
                "dependency_path": dep,
                "affected_output": "model output (preprocessing mismatch)",
                "detail": f"Preprocess diffs: {diffs}",
            }
        return "UNOBSERVABLE", None

    def _check_p3_budget(self, trace: Dict) -> Tuple[str, Optional[Dict]]:
        """Comparator budgets must satisfy the declared fairness relation.

        Checks ALL budget dimensions. A violation occurs if any method
        receives strictly more of a budget dimension than another while
        the paper declares matched budgets.
        """
        budgets = trace.get("comparator_budgets", [])
        if not budgets:
            return "UNOBSERVABLE", None
        entities = ["comparator_budgets"]
        dep = "comparator_budgets -> fair comparison -> reported superiority"

        # Gather all budget keys present
        keys = set()
        for b in budgets:
            for k in ("epochs", "gpu_seconds", "steps", "dataset_fraction_used"):
                if k in b:
                    keys.add(k)
        if not keys:
            return "UNOBSERVABLE", None

        for key in sorted(keys):
            vals = [b.get(key, 0) for b in budgets]
            if len(set(vals)) > 1:
                unfair = {b.get("method", "?"): b.get(key, 0) for b in budgets}
                return "VIOLATED", {
                    "predicate_id": "P3_BUDGET",
                    "trace_entities": entities,
                    "dependency_path": dep,
                    "affected_output": "reported superiority claim (budget asymmetry)",
                    "detail": f"Budget key '{key}' asymmetric: {unfair}",
                }
        return "SATISFIED", None

    def _check_p7_generic(self, trace: Dict) -> Tuple[str, Optional[Dict]]:
        """Generic evidence closure: outputs must have upstream runs."""
        out = trace.get("outputs", {}).get("reported_value", {})
        runs = out.get("upstream_runs", [])
        if not runs:
            return "UNOBSERVABLE", None
        return "SATISFIED", None


# ──────────────────────────────────────────────────────────────
# Static baselines
# ──────────────────────────────────────────────────────────────
class StaticBaseline:
    """
    Static baselines B0-B3.

    Key property: they receive IDENTICAL inputs for both members of a pair
    (same paper, same repo, same static config). Since the clean and invalid
    traces are distinguished ONLY by runtime execution fields, static
    baselines CANNOT pair-discriminate. We simulate this by giving them a
    deterministic 'static profile' derived from execution-independent fields
    only. Both runs in a pair produce the same static profile, so both get
    the same verdict -> pair discrimination = 0.
    """

    def __init__(self, level: str):
        """level: 'B0', 'B1', 'B2', 'B3'"""
        self.level = level

    def static_profile(self, trace: Dict) -> Dict:
        """
        Build a static profile using ONLY execution-independent fields.
        Both clean and invalid traces in a pair share these, so the profile
        is identical for the pair -> no pair-level discrimination.
        """
        return {
            "level": self.level,
            "code_commit": trace.get("code_commit"),
            "environment_hash": trace.get("environment_hash"),
            "loss_identity": trace.get("loss_identity"),
            "optimizer": trace.get("optimizer"),
            "hyperparameters": trace.get("hyperparameters", {}),
            "config_hash": trace.get("config_hash") if self.level == "B3" else None,
        }

    def evaluate(self, trace: Dict, contract: Dict) -> Dict:
        """
        Static baseline verdict. By construction, for a pair the clean and
        invalid static profiles are identical (execution-independent fields
        are shared), so both get the same verdict.

        We model the static baseline as: if the profile 'looks complete'
        (has commit + env + loss), PASS; else ABSTAIN. No trace-specific
        field (selection_split, aggregation_rule, subgroups, budgets) is
        consulted. This mirrors a real static paper-code auditor that cannot
        see runtime behaviour.
        """
        prof = self.static_profile(trace)
        complete = all([
            prof.get("code_commit"),
            prof.get("environment_hash"),
            prof.get("loss_identity"),
        ])
        if complete:
            verdict = "PASS"
        else:
            verdict = "ABSTAIN"
        return {
            "verdict": verdict,
            "static": True,
            "level": self.level,
            "profile_hash": _sha(prof),
        }


# ──────────────────────────────────────────────────────────────
# Pair evaluation
# ──────────────────────────────────────────────────────────────
def evaluate_pair(clean_trace: Dict, invalid_trace: Dict, contract: Dict,
                  baselines: Dict[str, StaticBaseline]) -> Dict:
    """Evaluate one pair with TraceContract + all baselines."""
    tc = TraceContractVerifier()

    clean_res = tc.evaluate(clean_trace, contract)
    invalid_res = tc.evaluate(invalid_trace, contract)

    # Pair-level: clean PASS + invalid FAIL = correctly discriminated
    tc_pair_correct = (clean_res["verdict"] == "PASS" and invalid_res["verdict"] == "FAIL")

    # Baselines: identical static profile -> identical verdict
    baseline_results = {}
    for name, bl in baselines.items():
        bc = bl.evaluate(clean_trace, contract)
        bi = bl.evaluate(invalid_trace, contract)
        # Pair discrimination: does the baseline get different verdicts?
        bl_pair_correct = (bc["verdict"] == "PASS" and bi["verdict"] == "FAIL")
        # Identical-input check: profiles must match
        identical_input = bc.get("profile_hash") == bi.get("profile_hash")
        baseline_results[name] = {
            "clean_verdict": bc["verdict"],
            "invalid_verdict": bi["verdict"],
            "pair_correct": bl_pair_correct,
            "identical_input": identical_input,
            "static": True,
        }

    # Identifiability audit: clean and invalid must share execution-independent fields
    shared_fields = ["code_commit", "environment_hash", "loss_identity", "optimizer",
                    "hyperparameters", "lineage"]
    identifiability_holds = all(
        clean_trace.get(f) == invalid_trace.get(f) for f in shared_fields
    )

    # Trace actually differs
    trace_differs = clean_trace["self_hash"] != invalid_trace["self_hash"]

    return {
        "clean": clean_res,
        "invalid": invalid_res,
        "tc_pair_correct": tc_pair_correct,
        "tc_clean_verdict": clean_res["verdict"],
        "tc_invalid_verdict": invalid_res["verdict"],
        "tc_witness": invalid_res.get("witness"),
        "tc_coverage_clean": clean_res["coverage"],
        "tc_coverage_invalid": invalid_res["coverage"],
        "baselines": baseline_results,
        "identifiability_holds": identifiability_holds,
        "trace_differs": trace_differs,
    }


def compute_psd(results: List[Dict]) -> Dict[str, float]:
    """Paired Scientific Discrimination for TC and each baseline."""
    n = len(results)
    if n == 0:
        return {}

    tc_correct = sum(1 for r in results if r["tc_pair_correct"])
    out = {"TraceContract": tc_correct / n}
    for name in results[0]["baselines"]:
        bl_correct = sum(1 for r in results if r["baselines"][name]["pair_correct"])
        out[name] = bl_correct / n
    return out


def main():
    import sys
    sys.path.insert(0, str(PROJECT_ROOT))
    from generate_pairs_r1a import FAMILIES

    index = json.loads((PROJECT_ROOT / "traces" / "PAIR_INDEX.json").read_text())

    baselines = {
        "B0_paper_only": StaticBaseline("B0"),
        "B1_paper_repo": StaticBaseline("B1"),
        "B2_static_auditor": StaticBaseline("B2"),
        "B3_with_config": StaticBaseline("B3"),
    }

    all_results = []
    family_results: Dict[str, List[Dict]] = {}

    for pm in index["pairs"]:
        sid = pm["study_id"]
        family = pm["family"]
        clean = json.loads((PROJECT_ROOT / pm["clean_trace"]).read_text())
        invalid = json.loads((PROJECT_ROOT / pm["invalid_trace"]).read_text())
        contract = json.loads((CONTRACTS_DIR / f"{sid}.json").read_text())

        res = evaluate_pair(clean, invalid, contract, baselines)
        res["study_id"] = sid
        res["family"] = family
        all_results.append(res)
        family_results.setdefault(family, []).append(res)

    # Save pair results
    out_path = RESULTS_DIR / "R1A_PAIR_RESULTS.jsonl"
    with open(out_path, "w", encoding="utf-8") as f:
        for r in all_results:
            f.write(json.dumps(r) + "\n")
    print(f"Saved {len(all_results)} pair results -> {out_path}")

    # PSD
    psd = compute_psd(all_results)
    print("\n=== PSD (pair-level correct discrimination) ===")
    for name, val in psd.items():
        print(f"  {name}: {val:.3f}")

    # Per-family detection
    print("\n=== Per-family (TC invalid-detection) ===")
    families_positive = 0
    for fam, fam_res in sorted(family_results.items()):
        detected = sum(1 for r in fam_res if r["tc_invalid_verdict"] == "FAIL")
        clean_acc = sum(1 for r in fam_res if r["tc_clean_verdict"] == "PASS")
        positive = detected > 0
        families_positive += int(positive)
        print(f"  {fam}: invalid_detected={detected}/5, clean_accepted={clean_acc}/5, positive={positive}")
    print(f"\nFamilies with positive detection: {families_positive}/6")

    # Global TC stats
    clean_acc = sum(1 for r in all_results if r["tc_clean_verdict"] == "PASS") / len(all_results)
    invalid_det = sum(1 for r in all_results if r["tc_invalid_verdict"] == "FAIL") / len(all_results)
    abstain = sum(1 for r in all_results
                  if r["tc_clean_verdict"] in ("ABSTAIN", "FAIL") or r["tc_invalid_verdict"] == "ABSTAIN") / len(all_results)
    print(f"\nClean acceptance: {clean_acc:.3f}")
    print(f"Invalid detection: {invalid_det:.3f}")

    # Identifiability audit
    idf_ok = sum(1 for r in all_results if r["identifiability_holds"])
    trace_diff_ok = sum(1 for r in all_results if r["trace_differs"])
    print(f"\nIdentifiability holds (shared fields equal): {idf_ok}/{len(all_results)}")
    print(f"Trace differs within pair: {trace_diff_ok}/{len(all_results)}")

    # Save ablation CSV
    import csv
    ablation_rows = []
    for r in all_results:
        row = {"study_id": r["study_id"], "family": r["family"]}
        row["TC_verdict"] = f"{r['tc_clean_verdict']}/{r['tc_invalid_verdict']}"
        row["TC_pair_correct"] = int(r["tc_pair_correct"])
        for bname, bres in r["baselines"].items():
            row[f"{bname}_pair_correct"] = int(bres["pair_correct"])
        ablation_rows.append(row)
    abl_path = RESULTS_DIR / "R1A_ABLATIONS.csv"
    if ablation_rows:
        with open(abl_path, "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=ablation_rows[0].keys())
            w.writeheader()
            w.writerows(ablation_rows)
        print(f"\nAblations -> {abl_path}")

    # GO/KILL check
    tc_psd = psd.get("TraceContract", 0.0)
    best_static_psd = max(v for k, v in psd.items() if k != "TraceContract") if len(psd) > 1 else 0.0
    print("\n=== GO/KILL CHECK ===")
    print(f"TC PSD: {tc_psd:.3f} (need >= 0.80)")
    print(f"Best static PSD: {best_static_psd:.3f} (need <= 0.55)")
    print(f"Clean acceptance: {clean_acc:.3f} (need >= 0.90)")
    print(f"Families positive: {families_positive}/6 (need >= 5)")

    return all_results


if __name__ == "__main__":
    main()
