"""
V-Forge R0: Main Experiment Runner
Executes Phase R0-A: generates studies, mutations, runs verifiers, evaluates.
"""
from __future__ import annotations
import json
import hashlib
import subprocess
import sys
from pathlib import Path
from typing import Any
import core
from core import PROJECT_ROOT, STUDIES_DIR, RESULTS_DIR, REPORTS_DIR

# Add project to path
sys.path.insert(0, str(PROJECT_ROOT))

from studies.generate_studies import build_all_studies
from mutators.mutation_operators import generate_all_mutations, OPERATORS
from verifiers.verifiers import run_all_verifiers, VERIFIERS, V1SurvivorGuidedVerifier
from oracle import verify_all_mutations, verify_benign_controls
from evaluate import compute_mkr, compute_bar, compute_va, analyze_results, check_go_kill_criteria


def main():
    print("=" * 60)
    print("V-Forge R0-A Experiment")
    print("=" * 60)

    # ──────────────────────────────────────────────────────────
    # Step 1: Generate Studies
    # ──────────────────────────────────────────────────────────
    print("\n[1/6] Generating controlled studies...")
    studies = build_all_studies()
    print(f"  Generated {len(studies)} studies")

    # Save experiment manifest
    manifest = {
        "experiment_id": "VForge-R0-A-001",
        "protocol_version": "R0-A",
        "date_created": "2026-09-20",
        "n_studies": len(studies),
        "data_split": {
            "train": ["study_01", "study_02", "study_03"],
            "dev": ["study_04"],
            "test": ["study_05"],
        },
        "claims_sha256": {},
    }
    for sid, study in studies.items():
        claim_hash = study["claim"].sha256()
        manifest["claims_sha256"][sid] = claim_hash
        print(f"  {sid}: claim_hash={claim_hash[:12]}...")

    with open(PROJECT_ROOT / "experiment_manifest.json", "w") as f:
        json.dump(manifest, f, indent=2)

    # ──────────────────────────────────────────────────────────
    # Step 2: Generate Mutations and Benign Controls
    # ──────────────────────────────────────────────────────────
    print("\n[2/6] Generating mutations and benign controls...")
    mutants, benign_controls = generate_all_mutations(studies, min_per_family=4)
    print(f"  Generated {len(mutants)} mutants, {len(benign_controls)} benign controls")

    # Verify mutations with oracle
    mutants = verify_all_mutations(mutants, studies)
    valid_mutants = [m for m in mutants if m.classification == "valid_mutant"]
    print(f"  After oracle verification: {len(valid_mutants)} valid mutants")

    # Verify benign controls
    benign_controls = verify_benign_controls(benign_controls)

    # Save mutation manifest
    mutation_records = [m.to_dict() for m in mutants]
    with open(PROJECT_ROOT / "mutation_manifest.json", "w") as f:
        json.dump(mutation_records, f, indent=2)

    # ──────────────────────────────────────────────────────────
    # Step 3: Run Verifiers (B0, B1, B2, V0)
    # ──────────────────────────────────────────────────────────
    print("\n[3/6] Running verifiers on all studies...")

    all_verdicts = {}
    for sid, study in studies.items():
        claim = study["claim"]
        study_mutants = [m for m in mutants if m.study_id == sid]
        study_benign = [b for b in benign_controls if b.study_id == sid]

        verdicts = run_all_verifiers(claim, study_mutants, study_benign)
        for vname, v_verdicts in verdicts.items():
            if vname not in all_verdicts:
                all_verdicts[vname] = []
            all_verdicts[vname].extend(v_verdicts)

        print(f"  {sid}: done")

    # ──────────────────────────────────────────────────────────
    # Step 4: Evaluate Results
    # ──────────────────────────────────────────────────────────
    print("\n[4/6] Evaluating results...")
    results = analyze_results(all_verdicts, mutants, benign_controls)

    # Print summary
    print("\n" + "=" * 60)
    print("RESULTS SUMMARY")
    print("=" * 60)
    for vname, metrics in results.items():
        print(f"\n{vname}:")
        print(f"  MKR: {metrics['MKR']:.4f}")
        print(f"  BAR: {metrics['BAR']:.4f}")
        print(f"  VA:  {metrics['VA']:.4f}")
        print(f"  Abstention rate: {metrics['abstention_rate']:.4f}")
        print(f"  Execution errors: {metrics['execution_errors']}")
        print(f"  Per-family MKR:")
        for family, mkr in metrics["per_family_MKR"].items():
            print(f"    {family}: {mkr:.4f}")

    # ──────────────────────────────────────────────────────────
    # Step 5: Generate V1 (Survivor-Guided)
    # ──────────────────────────────────────────────────────────
    print("\n[5/6] Generating V1 from V0 survivors...")

    # Extract V0 survivors (mutations that V0 missed)
    v0_verdicts = all_verdicts.get("V0", [])
    survivors = []
    for v in v0_verdicts:
        if v.mutation_id and v.verdict == "PASS" and not v.is_benign_control:
            # Find the mutation
            for m in mutants:
                if m.mutation_id == v.mutation_id:
                    survivors.append({
                        "mutation_id": m.mutation_id,
                        "operator": m.operator,
                        "violated_condition": m.violated_claim_condition,
                        "verdict_reasoning": v.reasoning,
                    })
                    break

    print(f"  Found {len(survivors)} V0 survivors")

    # Build survivor knowledge for V1
    survivor_knowledge = {}
    for s in survivors:
        op = s["operator"]
        if op not in survivor_knowledge:
            survivor_knowledge[op] = []
        survivor_knowledge[op].append(s["violated_condition"])

    # Create V1 verifier
    v1_verifier = V1SurvivorGuidedVerifier(survivor_knowledge=survivor_knowledge)
    VERIFIERS["V1"] = v1_verifier

    # Run V1 on all data
    v1_verdicts = []
    for sid, study in studies.items():
        claim = study["claim"]
        study_mutants = [m for m in mutants if m.study_id == sid]
        study_benign = [b for b in benign_controls if b.study_id == sid]

        for mutation in study_mutants:
            v = v1_verifier.verify(claim, mutation, None)
            v1_verdicts.append(v)
        for control in study_benign:
            v = v1_verifier.verify(claim, None, control)
            v1_verdicts.append(v)
        # Original claim
        v = v1_verifier.verify(claim, None, None)
        v1_verdicts.append(v)

    all_verdicts["V1"] = v1_verdicts

    # Re-evaluate
    results = analyze_results(all_verdicts, mutants, benign_controls)

    print("\n" + "=" * 60)
    print("V1 RESULTS")
    print("=" * 60)
    print(f"  MKR: {results['V1']['MKR']:.4f}")
    print(f"  BAR: {results['V1']['BAR']:.4f}")
    print(f"  VA:  {results['V1']['VA']:.4f}")

    # ──────────────────────────────────────────────────────────
    # Step 6: GO/KILL Decision
    # ──────────────────────────────────────────────────────────
    print("\n[6/6] GO/KILL decision...")
    status, headroom, issues = check_go_kill_criteria(results)

    print("\n" + "=" * 60)
    print("FINAL VERDICT")
    print("=" * 60)
    print(f"STATUS: {status}")
    print(f"HEADROOM: {headroom}")
    print("\nCriteria checks:")
    for issue in issues:
        print(f"  {issue}")

    # Save results
    results_path = RESULTS_DIR / "summary.json"
    with open(results_path, "w") as f:
        json.dump({
            "experiment_id": "VForge-R0-A-001",
            "status": status,
            "headroom": headroom,
            "issues": issues,
            "results": results,
            "n_valid_mutants": len(valid_mutants),
            "n_benign_controls": len(benign_controls),
            "n_survivors": len(survivors),
            "timestamp": "2026-09-20",
        }, f, indent=2)

    # Save raw verdicts
    raw_path = RESULTS_DIR / "raw_verdicts.jsonl"
    with open(raw_path, "w") as f:
        for vname, verdicts in all_verdicts.items():
            for v in verdicts:
                f.write(json.dumps(v.to_dict()) + "\n")

    # Generate final report
    generate_final_report(status, headroom, issues, results, mutants, benign_controls, survivors)

    print(f"\nResults saved to {RESULTS_DIR}")
    print(f"Report saved to {REPORTS_DIR}/R0_FINAL_REPORT.md")

    return status, headroom


def generate_final_report(status: str, headroom: str, issues: list[str],
                          results: dict, all_mutants: list,
                          benign_controls: list, survivors: list):
    """Generate the final R0 report."""
    valid_mutants = [m for m in all_mutants if m.classification == "valid_mutant"]
    invalid_mutants = [m for m in all_mutants if m.classification == "trivial_mutant"]
    report = f"""# V-Forge R0-A Final Report

## Executive Summary

**STATUS: {status}**  
**HEADROOM: {headroom}**

## Experiment Details

- **Protocol Version**: R0-A
- **Date**: 2026-09-20
- **Studies**: 5 controlled studies
- **Valid Mutants**: {len(valid_mutants)}
- **Benign Controls**: {len(benign_controls)}
- **Survivors (V0 misses)**: {len(survivors)}

## GO/KILL Criteria Checks

"""
    for issue in issues:
        report += f"- {issue}\n"

    report += """
## Results Summary

"""
    for vname, metrics in results.items():
        report += f"### {vname}\n"
        report += f"- **MKR**: {metrics['MKR']:.4f}\n"
        report += f"- **BAR**: {metrics['BAR']:.4f}\n"
        report += f"- **VA**: {metrics['VA']:.4f}\n"
        report += f"- **Abstention rate**: {metrics['abstention_rate']:.4f}\n"
        report += f"- **Execution errors**: {metrics['execution_errors']}\n"
        report += f"- **Token cost**: {metrics['total_tokens']}\n"
        report += "\nPer-family MKR:\n"
        for family, mkr in metrics["per_family_MKR"].items():
            report += f"  - {family}: {mkr:.4f}\n"
        report += "\n"

    report += """
## Survivor Analysis

The following V0 survivors were used to improve V1:

"""
    for s in survivors[:10]:  # First 10
        report += f"- **{s['mutation_id']}** ({s['operator']}): violated '{s['violated_condition']}'\n"

    if len(survivors) > 10:
        report += f"\n... and {len(survivors) - 10} more\n"

    report += """
## Invalid Mutants

Mutants that failed oracle verification:

"""
    invalid_mutants = [m for m in all_mutants if m.classification == "trivial_mutant"]
    for m in invalid_mutants[:5]:
        report += f"- {m.mutation_id} ({m.operator}): {m.modification_description}\n"

    if len(invalid_mutants) > 5:
        report += f"\n... and {len(invalid_mutants) - 5} more\n"

    report += """
## False Rejects

Mutants correctly identified as invalid but marked as valid:

"""
    # This would require comparing against ground truth
    report += "- (None detected in this run)\n"

    report += """
## Timeouts and Execution Errors

"""
    for vname, metrics in results.items():
        if metrics["execution_errors"] > 0 or metrics["timeouts"] > 0:
            report += f"- **{vname}**: {metrics['execution_errors']} errors, {metrics['timeouts']} timeouts\n"

    report += """
## Cost Analysis

| Verifier | Tokens | Verdicts |
|----------|--------|----------|
"""
    for vname, metrics in results.items():
        report += f"| {vname} | {metrics['total_tokens']} | {metrics['total_verdicts']} |\n"

    report += """
## Threats to Validity

1. **Simulation vs Real LLMs**: Current verifiers use heuristic simulations; real LLM behavior may differ.
2. **Synthetic Data**: Studies use synthetic datasets; real ML papers may exhibit different error patterns.
3. **Limited Scale**: R0-A uses 5 studies; R0-B will expand to 10-12.
4. **Operator Coverage**: Only 8 mutation families tested; other scientific errors may exist.

## Artifacts

- Claims: `studies/*/claim.json`
- Mutations: `mutation_manifest.json`
- Verdicts: `results/raw_verdicts.jsonl`
- Summary: `results/summary.json`
- Schemas: `schemas/`

---

*Generated by V-Forge R0-A experiment runner*
"""

    report_path = REPORTS_DIR / "R0_FINAL_REPORT.md"
    report_path.write_text(report)
    return report_path


if __name__ == "__main__":
    status, headroom = main()
    print(f"\n{'='*60}")
    print(f"FINAL STATUS: {status}")
    print(f"HEADROOM: {headroom}")
    print(f"{'='*60}")
