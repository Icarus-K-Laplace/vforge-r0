"""
R0-D1-v2: Full evaluation pipeline.

Pipeline:
  1. Load 92 blind samples
  2. Load paper text, contracts, graphs
  3. Run R0D1v2Verifier (no gold data visible)
  4. Save frozen predictions + system-health metrics
  5. Do NOT reveal gold until step 6

Qualification thresholds (pre-registered):
  Paper extraction >= 80%  : PASS to proceed
  Usable graph >= 75%      : PASS to proceed
  92 PASS or 92 FAIL       : triggers implementation audit before interpretation
"""
from __future__ import annotations

import json
import hashlib
import datetime
import sys
from pathlib import Path
from collections import Counter

sys.path.insert(0, str(Path(__file__).resolve().parent))

from verifier_r0d1v2 import (
    R0D1v2Verifier,
    PASS, FAIL, ABSTAIN,
    PAPER_UNAVAILABLE, CONTRACT_INSUFFICIENT,
    REPOSITORY_UNAVAILABLE, GRAPH_EXTRACTION_FAILURE,
    GRAPH_INSUFFICIENT,
)
from paper_extractor_v2 import extract_batch

PROJECT_ROOT = Path(__file__).resolve().parent
RESULTS_DIR  = PROJECT_ROOT / "results"
RESULTS_DIR.mkdir(exist_ok=True)


def main():
    print("=" * 64)
    print("R0-D1-v2: Blind System-Health Qualification")
    print("=" * 64)
    print(f"Timestamp: {datetime.datetime.now().isoformat()}\n")

    # ── Step 1: Load blind samples ─────────────────────────────
    blind_path = PROJECT_ROOT / "external/scicoqa/blind/scicoqa_real_blind.jsonl"
    with open(blind_path) as f:
        blind = [json.loads(line) for line in f]
    sample_ids = [d["discrepancy_id"] for d in blind]
    print(f"[1/5] Loaded {len(sample_ids)} blind samples")

    # ── Step 2: Paper extraction qualification ─────────────────
    print("\n[2/5] Paper extraction status...")
    papers_extracted = 0
    for pid in sample_ids:
        p = PROJECT_ROOT / "papers" / f"{pid}.txt"
        if p.exists() and p.stat().st_size > 0:
            papers_extracted += 1
    paper_rate = papers_extracted / len(sample_ids)
    print(f"  Papers extracted: {papers_extracted}/{len(sample_ids)} = {paper_rate:.1%}")
    print(f"  Qualifies (>=80%): {paper_rate >= 0.80}")

    # ── Step 3: Graph qualification ────────────────────────────
    print("\n[3/5] Graph qualification...")
    graphs_ok = 0
    for pid in sample_ids:
        g = PROJECT_ROOT / "graphs" / f"{pid}.json"
        if g.exists():
            try:
                data = json.loads(g.read_text())
                if len(data.get("nodes", [])) >= 3:
                    graphs_ok += 1
            except Exception:
                pass
    graph_rate = graphs_ok / len(sample_ids)
    print(f"  Usable graphs: {graphs_ok}/{len(sample_ids)} = {graph_rate:.1%}")
    print(f"  Qualifies (>=75%): {graph_rate >= 0.75}")

    # ── Step 4: Run verifier (NO gold visible) ────────────────
    print("\n[4/5] Running R0-D1-v2 verifier (blind mode)...")
    verifier = R0D1v2Verifier()
    records = verifier.run_batch(sample_ids)
    summary = R0D1v2Verifier.summarize(records)

    print("\n  Verdict distribution:")
    for v, c in sorted(summary["verdicts"].items()):
        print(f"    {v}: {c}")
    print(f"\n  PASS rate: {summary['pass_rate']:.1%}")
    print(f"  FAIL rate: {summary['fail_rate']:.1%}")
    print(f"  ABSTAIN total: {summary['abstain_rate']:.1%}")

    # Check for extreme distributions
    n = len(records)
    extreme = (summary["verdicts"].get("PASS", 0) == n) or (summary["verdicts"].get("FAIL", 0) == n)
    if extreme:
        print("\n  ⚠️  EXTREME DISTRIBUTION DETECTED - implementation audit required")

    # ── Step 5: Save frozen predictions ─────────────────────────
    print("\n[5/5] Saving frozen predictions...")
    predictions_path = RESULTS_DIR / "R0D1v2_PREDICTIONS_FROZEN.jsonl"
    with open(predictions_path, "w", encoding="utf-8") as f:
        for r in records:
            f.write(json.dumps(r.to_dict()) + "\n")

    predictions_hash = hashlib.sha256(predictions_path.read_bytes()).hexdigest()

    freeze_doc = {
        "experiment_id": "VForge-R0-D1-v2-001",
        "protocol_version": "R0-D1-v2",
        "date": datetime.datetime.now().isoformat(),
        "predictions_path": str(predictions_path),
        "predictions_sha256": predictions_hash,
        "n_samples": n,
        "verdict_counts": summary["verdicts"],
        "paper_extraction_rate": round(paper_rate, 4),
        "graph_extraction_rate": round(graph_rate, 4),
        "pass_rate": round(summary["pass_rate"], 4),
        "fail_rate": round(summary["fail_rate"], 4),
        "abstain_rate": round(summary["abstain_rate"], 4),
        "extreme_distribution": extreme,
        "pass_coverage_threshold": 0.70,
        "status": "FROZEN",
        "label": "R0-D1-v2 QUALIFICATION (DEV) - NOT zero-shot final evidence",
    }
    freeze_path = RESULTS_DIR / "R0D1v2_PREDICTION_FREEZE.json"
    freeze_path.write_text(json.dumps(freeze_doc, indent=2), encoding="utf-8")

    print(f"  Predictions frozen: {predictions_path.name}")
    print(f"  SHA256: {predictions_hash[:32]}...")
    print(f"  Freeze doc: {freeze_path.name}")

    print("\n" + "=" * 64)
    print("R0-D1-v2 Blind Qualification Complete")
    print("=" * 64)
    print(f"\nStatus: {'EXTREME_DISTRIBUTION' if extreme else 'OK'}")
    print(f"Paper extraction: {paper_rate:.1%} (target >= 80%)")
    print(f"Graph extraction: {graph_rate:.1%} (target >= 75%)")
    print(f"PASS: {summary['verdicts'].get('PASS',0)}  FAIL: {summary['verdicts'].get('FAIL',0)}  ABSTAIN: {summary['verdicts'].get('ABSTAIN',0) + summary['verdicts'].get(PAPER_UNAVAILABLE,0) + summary['verdicts'].get(CONTRACT_INSUFFICIENT,0) + summary['verdicts'].get(REPOSITORY_UNAVAILABLE,0) + summary['verdicts'].get(GRAPH_EXTRACTION_FAILURE,0)}")
    print(f"\nNext: Gold reveal + SciCoQA DEV evaluation (step 12-13)")


if __name__ == "__main__":
    main()
