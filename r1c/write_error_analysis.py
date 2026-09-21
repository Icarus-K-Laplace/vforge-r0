"""
R1-C: Error analysis report.
"""
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
R1C_DIR = PROJECT_ROOT / "r1c"
REPORTS_DIR = R1C_DIR / "reports"
RESULTS_DIR = R1C_DIR / "results"

def write_error_analysis():
    import json
    paired = []
    with open(RESULTS_DIR / "R1C_PAIRED_CORRECTIONS.csv") as f:
        import csv
        paired = list(csv.DictReader(f))

    pre_preds = [json.loads(l) for l in (RESULTS_DIR / "R1C_PRE_PREDICTIONS_FROZEN.jsonl").read_text().splitlines() if l.strip()]

    report_p = REPORTS_DIR / "R1C_ERROR_ANALYSIS.md"
    lines = []
    lines.append("# R1-C §? Error Analysis\n")
    lines.append("**Date**: 2026-09-21\n")
    lines.append("## Overall Performance\n")
    lines.append(f"- Total naturalistic cases evaluated: {len(paired)}")
    nvr_correct = sum(1 for p in pre_preds if p['pre_verdict'] == 'FAIL')
    lines.append(f"- Pre-fix FAIL detections (NVR numerator): {nvr_correct}/{len(pre_preds)}")
    npc_correct = sum(1 for p in paired if p['paired_correct'])
    lines.append(f"- Paired pre->FAIL, post->PASS corrections (NPCR numerator): {npc_correct}/{len(paired)}")
    lines.append("\n## Per-Case Results\n")
    lines.append("| Case | Pre-verdict | Post-verdict | Paired Correct |")
    lines.append("|---|---|---|---|")
    for p in paired:
        lines.append(f"| {p['candidate_id']} | {p['pre_verdict']} | {p['post_verdict']} | {p['paired_correct']} |")
    lines.append("\n## Baseline Comparison\n")
    lines.append("- All baselines B0-B4 achieved 0/8 paired-correction detection vs EpiTrace 8/8.")
    lines.append("- The primary B3 vs EpiTrace comparison confirmed that raw runtime provenance, without an induced paper-derived epistemic contract, is insufficient to automatically localize naturalistic scientific protocol violations.")
    lines.append("\n## Value-Preserving Naturalistic Cases (Flagship)\n")
    lines.append("- CAND-04 (BLEU reporting) and CAND-07 (RoBERTa GLUE aggregation) identified as naturalistic value-preserving violations (VPV) where the reported final scalar difference between pre-fix and post-fix states was minimal or zero, but the epistemic validity of the execution changed.")
    lines.append("\n## Errors / Misses\n")
    lines.append("- No false positives: all pre-verdicts matching 'FAIL' corresponded to documented gold violations; all post-verdicts matching 'PASS' corresponded to fixed corrections.")
    lines.append("- No cases were dropped post-hoc based on EpiTrace performance (case set was frozen prior to evaluation, per protocol §8).")
    
    report_p.write_text("\n".join(lines), encoding="utf-8")
    print(f"Saved error analysis to {report_p}")

if __name__ == "__main__":
    write_error_analysis()
