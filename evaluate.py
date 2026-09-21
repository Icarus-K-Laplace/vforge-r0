"""
V-Forge R0: Evaluation Metrics and Result Analysis
Computes MKR, BAR, VA metrics and generates reports.
"""
from __future__ import annotations
import json
import numpy as np
from pathlib import Path
from typing import Any
import core
from core import Verdict, MutationInstance, BenignControl, SEED


def compute_mkr(verdicts: list[Verdict], mutants: list[MutationInstance]) -> float:
    """Compute Mutation Kill Rate: killed_valid_mutants / all_valid_mutants."""
    valid_mutants = [m for m in mutants if m.classification == "valid_mutant"]
    if not valid_mutants:
        return 0.0

    killed = 0
    for mutant in valid_mutants:
        # Find verdict for this mutant
        matching = [v for v in verdicts if v.mutation_id == mutant.mutation_id and not v.is_benign_control]
        if matching:
            verdict = matching[0]
            if verdict.verdict == "FAIL":
                killed += 1

    return killed / len(valid_mutants)


def compute_bar(verdicts: list[Verdict], controls: list[BenignControl]) -> float:
    """Compute Benign Acceptance Rate: accepted_benign / all_benign."""
    if not controls:
        return 0.0

    accepted = 0
    for control in controls:
        matching = [v for v in verdicts if v.is_benign_control and v.benign_control_id == control.control_id]
        if matching and matching[0].verdict == "PASS":
            accepted += 1

    return accepted / len(controls)


def compute_va(mkr: float, bar: float) -> float:
    """Compute Verifier Adequacy: VA = MKR + BAR - 1."""
    return mkr + bar - 1


def compute_per_family_mkr(verdicts: list[Verdict], mutants: list[MutationInstance]) -> dict[str, float]:
    """Compute MKR per mutation family."""
    families = {}
    for mutant in mutants:
        if mutant.classification != "valid_mutant":
            continue
        family = mutant.operator
        if family not in families:
            families[family] = {"total": 0, "killed": 0}
        families[family]["total"] += 1
        matching = [v for v in verdicts if v.mutation_id == mutant.mutation_id]
        if matching and matching[0].verdict == "FAIL":
            families[family]["killed"] += 1

    result = {}
    for family, counts in families.items():
        result[family] = counts["killed"] / counts["total"] if counts["total"] > 0 else 0.0
    return result


def compute_bootstrap_ci(mkr_values: list[float], n_bootstrap: int = 1000, confidence: float = 0.95) -> tuple[float, float, float]:
    """Compute bootstrap confidence interval for MKR."""
    if not mkr_values:
        return 0.0, 0.0, 0.0

    rng = np.random.default_rng(SEED)
    bootstrap_means = []
    for _ in range(n_bootstrap):
        sample = rng.choice(mkr_values, size=len(mkr_values), replace=True)
        bootstrap_means.append(np.mean(sample))

    mean_mkr = np.mean(bootstrap_means)
    lower_idx = int((1 - confidence) / 2 * n_bootstrap)
    upper_idx = int((1 + confidence) / 2 * n_bootstrap)
    sorted_means = np.sort(bootstrap_means)
    lower_ci = sorted_means[lower_idx]
    upper_ci = sorted_means[upper_idx]

    return float(mean_mkr), float(lower_ci), float(upper_ci)


def analyze_results(verdicts_by_verifier: dict[str, list[Verdict]],
                    mutants: list[MutationInstance],
                    benign_controls: list[BenignControl]) -> dict[str, Any]:
    """Compute all evaluation metrics."""
    results = {}

    for verifier_name, verdicts in verdicts_by_verifier.items():
        mkr = compute_mkr(verdicts, mutants)
        bar = compute_bar(verdicts, benign_controls)
        va = compute_va(mkr, bar)
        per_family = compute_per_family_mkr(verdicts, mutants)

        # Count abstentions and errors
        abstentions = sum(1 for v in verdicts if v.verdict == "ABSTAIN")
        execution_errors = sum(1 for v in verdicts if v.verdict == "EXECUTION_ERROR")
        timeouts = sum(1 for v in verdicts if v.verdict == "TIMEOUT")

        # Compute token cost
        total_tokens = sum(v.token_cost or 0 for v in verdicts)

        results[verifier_name] = {
            "MKR": round(mkr, 4),
            "BAR": round(bar, 4),
            "VA": round(va, 4),
            "per_family_MKR": {k: round(v, 4) for k, v in per_family.items()},
            "abstention_rate": round(abstentions / len([v for v in verdicts if not v.is_benign_control]), 4) if verdicts else 0,
            "execution_errors": execution_errors,
            "timeouts": timeouts,
            "total_tokens": total_tokens,
            "total_verdicts": len(verdicts),
        }

    return results


def check_go_kill_criteria(results: dict[str, dict]) -> tuple[str, str, list[str]]:
    """Check GO/KILL criteria and return (status, headroom, issues)."""
    issues = []
    headroom = "NO"

    # Find strongest baseline (best MKR among B0, B1, B2)
    baselines = {k: v for k, v in results.items() if k.startswith("B")}
    if not baselines:
        return "KILL", "NO", ["No baselines found"]

    strongest_baseline = max(baselines.items(), key=lambda x: x[1]["MKR"])

    # Check V1 vs strongest baseline
    v1_result = results.get("V1")
    v0_result = results.get("V0")

    if v1_result and strongest_baseline:
        v1_mkr = v1_result["MKR"]
        baseline_mkr = strongest_baseline[1]["MKR"]
        improvement = v1_mkr - baseline_mkr

        if improvement >= 0.15:
            issues.append(f"V1 MKR improvement over {strongest_baseline[0]}: {improvement:.4f} (>= 0.15 ✓)")
        else:
            issues.append(f"V1 MKR improvement over {strongest_baseline[0]}: {improvement:.4f} (< 0.15 ✗)")

        # Check BAR
        bar_v1 = v1_result["BAR"]
        if bar_v1 >= 0.90:
            issues.append(f"BAR(V1) = {bar_v1:.4f} (>= 0.90 ✓)")
        else:
            issues.append(f"BAR(V1) = {bar_v1:.4f} (< 0.90 ✗)")

        # Check V1 vs V0
        if v0_result:
            v1_vs_v0 = v1_result["MKR"] - v0_result["MKR"]
            if v1_vs_v0 >= 0.10:
                issues.append(f"V1 vs V0 improvement: {v1_vs_v0:.4f} (>= 0.10 ✓)")
            else:
                issues.append(f"V1 vs V0 improvement: {v1_vs_v0:.4f} (< 0.10 ✗)")

        # Check multiple families
        families_improved = sum(1 for f, v in v1_result.get("per_family_MKR", {}).items()
                               if v > v0_result.get("per_family_MKR", {}).get(f, 0))
        if families_improved >= 2:
            issues.append(f"Improvement from {families_improved} mutation families (>= 2 ✓)")
            headroom = "YES"
        else:
            issues.append(f"Improvement from only {families_improved} mutation families (< 2 ✗)")
    else:
        issues.append("Missing V1 or baseline results")

    # Determine status
    all_pass = all("✓" in i for i in issues if "MKR" in i or "BAR" in i or "improvement" in i or "families" in i)
    if all_pass and headroom == "YES":
        status = "GO"
    elif any("✗" in i for i in issues):
        status = "KILL"
    else:
        status = "REDEFINE"

    return status, headroom, issues
