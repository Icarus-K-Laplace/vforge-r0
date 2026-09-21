"""
Cross-paper source-level aggregation for R1-B1 Stage1b.

The primary evaluation unit is (paper, constraint-class), NOT
individual pairs. This script re-aggregates the pair-level results
to the source level, then computes the cross-source metrics
required for the STRONG_GO decision:

  - source-level PSD
  - source-level B3 gap
  - source-level VPVD
  - source-level CIA
  - source-level clean acceptance
  - source-level witness accuracy

A source "succeeds" for a constraint class if:
  - at least 1 pair for that (paper, class) has sec_pair_correct
  - AND clean acceptance for that class >= 0.80

STRONG_GO requires:
  - >= 4 independent papers with at least one successful class
  - >= 3 core semantic classes stable across >= 2 papers each
"""
from __future__ import annotations
import json
from pathlib import Path
from collections import defaultdict
from statistics import mean

PROJECT_ROOT = Path(__file__).resolve().parent.parent  # E:/VForge-R0
RESULTS_DIR  = PROJECT_ROOT / "stage1b" / "results"


def load_stage1b_pairs() -> list[dict]:
    """Load the Stage1b pair results + Stage1 pairs for the cross-source view."""
    # Stage1b: DiffSynth (27 pairs)
    stage1b = [json.loads(l) for l in (RESULTS_DIR / "R1B1_REAL_TRACE_PAIRS.jsonl").read_text().splitlines() if l.strip()]
    return stage1b


def source_level_metrics(pairs: list[dict]) -> dict:
    """
    Aggregate to (paper, family) units.
    Returns a dict keyed by (paper, family) with:
      n_pairs, sec_correct, b3_correct, clean_pass, invalid_fail,
      vp_cases, vp_detected, clean_acc, sec_psd, source_success
    """
    units = defaultdict(lambda: {"n": 0, "sec_correct": 0, "b3_correct": 0,
                                  "clean_pass": 0, "invalid_fail": 0,
                                  "vp_cases": 0, "vp_detected": 0,
                                  "witness_ok": 0, "witness_cases": 0})
    for p in pairs:
        key = (p["paper"], p["family"])
        u = units[key]
        u["n"] += 1
        u["sec_correct"] += int(p["sec_pair_correct"])
        u["b3_correct"] += int(p["baselines"]["B3_provenance_only"]["pair_correct"])
        u["clean_pass"] += int(p["sec_clean_verdict"] == "PASS")
        u["invalid_fail"] += int(p["sec_invalid_verdict"] == "FAIL")
        if p["value_preserving"]:
            u["vp_cases"] += 1
            u["vp_detected"] += int(p["sec_invalid_verdict"] == "FAIL")
        if p["sec_invalid_verdict"] == "FAIL":
            u["witness_cases"] += 1
            u["witness_ok"] += int(bool(p["sec_witness"]))

    for key, u in units.items():
        n = u["n"]
        u["clean_acc"] = u["clean_pass"] / n if n else 0
        u["sec_psd"] = u["sec_correct"] / n if n else 0
        u["b3_psd"] = u["b3_correct"] / n if n else 0
        u["vpvd"] = u["vp_detected"] / u["vp_cases"] if u["vp_cases"] else None
        u["witness_acc"] = u["witness_ok"] / u["witness_cases"] if u["witness_cases"] else None
        # Source-level success: class is "stable" if >= 1 pair correct AND clean >= 0.80
        u["stable"] = (u["sec_correct"] >= 1 and u["clean_acc"] >= 0.80)
    return dict(units)


def cross_source_view(stage1b_pairs: list[dict]) -> dict:
    """
    Combine Stage1 (ViewBatchModel + RevisitDML) and Stage1b (DiffSynth)
    for a cross-paper view. Stage1 pairs live in the top-level results dir;
    Stage1b pairs live in the stage1b results dir.
    """
    s1_dir  = PROJECT_ROOT / "results" / "R1B1_REAL_TRACE_PAIRS.jsonl"
    s1b_dir = PROJECT_ROOT / "stage1b" / "results" / "R1B1_REAL_TRACE_PAIRS.jsonl"

    def _load(p: Path) -> list[dict]:
        if not p.exists():
            return []
        return [json.loads(l) for l in p.read_text().splitlines() if l.strip()]

    s1_pairs  = _load(s1_dir)
    s1b_pairs = _load(s1b_dir) if stage1b_pairs is None else stage1b_pairs
    all_pairs  = s1_pairs + s1b_pairs

    units = source_level_metrics(all_pairs)

    # Group by paper
    by_paper: dict[str, dict] = defaultdict(dict)
    for (paper, fam), u in units.items():
        by_paper[paper][fam] = u

    result = {
        "n_papers": len(by_paper),
        "papers": {},
        "n_papers_with_stable_class": 0,
        "stable_classes": {},
        "n_stable_class_papers": defaultdict(int),
        "global": {
            "sec_psd": mean([u["sec_psd"] for u in units.values()]),
            "b3_psd": mean([u["b3_psd"] for u in units.values()]),
            "clean_acc": mean([u["clean_acc"] for u in units.values()]),
            "vpvd_overall": (lambda c, d: d / c if c else None)(
                sum(u["vp_detected"] for u in units.values()),
                sum(u["vp_cases"] for u in units.values())),
            "witness_acc_overall": (lambda c, d: d / c if c else None)(
                sum(u["witness_ok"] for u in units.values()),
                sum(u["witness_cases"] for u in units.values())),
        },
    }
    result["global"]["b3_gap"] = result["global"]["sec_psd"] - result["global"]["b3_psd"]

    for paper, fams in by_paper.items():
        stable = {f: u for f, u in fams.items() if u["stable"]}
        result["papers"][paper] = {
            "families": {f: {"n": u["n"], "sec_psd": u["sec_psd"], "stable": u["stable"],
                             "clean_acc": u["clean_acc"], "vpvd": u["vpvd"]}
                         for f, u in fams.items()},
            "n_stable_classes": len(stable),
        }
        if len(stable) >= 1:
            result["n_papers_with_stable_class"] += 1
        for f in stable:
            result["stable_classes"][f] = result["stable_classes"].get(f, 0) + 1
            result["n_stable_class_papers"][f] += 1

    # STRONG_GO check
    g = result["global"]
    checks = {
        "4_papers": result["n_papers"] >= 4,
        "3_classes_stable_across_2papers": len([f for f, c in result["stable_classes"].items() if result["n_stable_class_papers"].get(f, 0) >= 2]) >= 3,
        "psd_ge_080": g["sec_psd"] >= 0.80,
        "b3_gap_ge_015": g["b3_gap"] >= 0.15,
        "vpvd_ge_075": (g["vpvd_overall"] or 0) >= 0.75,
        "clean_ge_085": g["clean_acc"] >= 0.85,
        "witness_ge_080": (g["witness_acc_overall"] or 0) >= 0.80,
    }
    result["strong_go_checks"] = checks
    result["strong_go"] = all(checks.values())
    return result


def main():
    view = cross_source_view(None)

    out = RESULTS_DIR / "R1B1_CROSS_PAPER_SOURCE_METRICS.json"
    out.write_text(json.dumps(view, indent=2, default=str))
    print(f"Cross-paper source-level metrics -> {out}")

    print(f"\n=== Cross-Source View ===")
    print(f"Papers: {view['n_papers']}  (need >= 4)")
    print(f"Papers with >=1 stable class: {view['n_papers_with_stable_class']}")
    print(f"\nPer-paper:")
    for paper, info in view["papers"].items():
        print(f"  {paper}: {info['n_stable_classes']} stable class(es)")
        for fam, f in info["families"].items():
            mark = "STABLE" if f["stable"] else "no"
            print(f"    {fam}: n={f['n']} psd={f['sec_psd']:.2f} clean={f['clean_acc']:.2f} [{mark}]")
    print(f"\nStable classes (paper count):")
    for f, c in sorted(view["stable_classes"].items()):
        print(f"  {f}: {c} paper(s)  [{'OK' if c >= 2 else 'insufficient'}]")
    print(f"\nGlobal: PSD={view['global']['sec_psd']:.3f} B3gap={view['global']['b3_gap']:.3f} "
          f"clean={view['global']['clean_acc']:.3f} VPVD={view['global']['vpvd_overall']} "
          f"witness={view['global']['witness_acc_overall']}")
    print(f"\nSTRONG_GO checks:")
    for k, v in view["strong_go_checks"].items():
        print(f"  {k}: {'PASS' if v else 'FAIL'}")
    print(f"\nSTRONG_GO = {view['strong_go']}")

    return view


if __name__ == "__main__":
    main()
