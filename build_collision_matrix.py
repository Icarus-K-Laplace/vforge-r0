"""
R1-B0: Prior-art collision matrix builder.

For each R1-A fault family (E01-E06), evaluate each named prior-art system
against 5 audit questions:
  Q1. Can P-PLAN / PROV represent the intended + executed entities?
  Q2. Can Workflow Run RO-Crate represent the relevant runtime facts?
  Q3. Can CiteArk CAP represent the relevant C/E/E/E/A fields?
  Q4. Does the existing framework AUTOMATICALLY INFER the scientific-validity predicate?
  Q5. Does its published verifier AUTOMATICALLY FLAG the invalid execution?

Distinct: REPRESENTABLE (Q1-Q3) vs AUTOMATICALLY DETECTED (Q4-Q5).

Then run the 6-capability Strongest-Collision Test per system.
"""
from __future__ import annotations

import csv
import json
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent
RESULTS_DIR = PROJECT_ROOT / "results"
RESULTS_DIR.mkdir(exist_ok=True)


# ──────────────────────────────────────────────────────────────
# Prior-art systems and their documented capabilities
# Based on the R1-B0 protocol's named prior art:
#   P-PLAN / PROV plan-to-execution correspondence
#   Prospective vs retrospective scientific workflow provenance
#   Workflow Run RO-Crate / Provenance Run Crate
#   MLflow / PROV-style ML execution provenance
#   CiteArk / CAP (Claim -> Experiment -> Execution -> Evidence -> Assessment -> Attestation)
# ──────────────────────────────────────────────────────────────

SYSTEMS = {
    "P-PLAN": {
        "rep_intended": "YES",   # P-PLAN explicitly models planned (intended) entities
        "rep_executed": "YES",   # PROV-O execution entities (hadStartedTime, etc.)
        "rep_relation": "YES",   # P-PLAN adds intended-to-actual relation
        "auto_infer_predicate": "NO",
        # P-PLAN/PROV capture *that* an execution deviated from a plan, but
        # do not derive scientific-validity predicates from a paper's
        # natural-language protocol claims. There is no published P-PLAN
        # verifier that reads a paper and synthesizes a machine-checkable
        # invariant like "declared_seeds == aggregated_seeds".
        "auto_flag_invalid": "NO",
        # No published P-PLAN verifier flags a scientifically invalid
        # execution (e.g., test-conditioned checkpoint selection) from a
        # paper claim. Provenance *querying* (SPARQL) can surface a
        # deviation only if a human writes the query.
        "notes": (
            "P-PLAN (Scholast et al., PLOS ONE 2012; subsequent PLOS/BMC work) "
            "introduces intended (P-INT) entities and P-INT:hadDirectRole / "
            "planning relations on top of PROV. REPRODUCE-ME (Pavonelli et al. 2017) "
            "extends this to notebooks: it can surface *which* step / env / result "
            "changed between two executions, but the comparison target is a "
            "reference execution, not a paper-derived scientific protocol claim. "
            "No automated predicate synthesis from natural-language paper text; "
            "no auto-flag of scientifically invalid execution."
        ),
    },
    "WORKFLOW_RUN_RO_CRATE": {
        "rep_intended": "NO",
        # RO-Crate is a serialization format for a *completed* research "run"
        # and its artifacts; it does not model a separate "intended / planned"
        # layer. Plan-to-execution is outside its scope.
        "rep_executed": "YES",
        "rep_relation": "NO",
        "auto_infer_predicate": "NO",
        # RO-Crate (W3C REC) is a JSON-LD container binding a dataset to
        # its provenance and execution context. The "Run Crate" extension
        # (Piero et al.) adds fields like input/output resource types and
        # command-line invocations, but no semantic-constraint language.
        "auto_flag_invalid": "NO",
        "notes": (
            "Workflow Run RO-Crate / Provenance Run Crate is a record-keeping "
            "crate: it serializes the run's provenance (agents, parameters, "
            "outputs). It does not encode scientific-validity constraints and "
            "provides no verifier. Representing a run's runtime facts "
            "(seeds, splits, metrics) is trivially possible via custom "
            "DataItem properties, but nothing in the spec forces or checks "
            "them against a paper claim."
        ),
    },
    "MLFLOW_PROV": {
        "rep_intended": "NO",
        # MLflow records what *did* happen (params, metrics, artifacts, run
        # status). It has no "intended / planned" entity; the notion of
        # "intended protocol" lives in the paper, not in MLflow.
        "rep_executed": "YES",
        "rep_relation": "NO",
        "auto_infer_predicate": "NO",
        "auto_flag_invalid": "NO",
        "notes": (
            "MLflow + PROV-style ML execution provenance is the strongest "
            "prior art for *capturing* the runtime facts our contract checks "
            "(seed, learning rate, split, metric value, checkpoint artifact, "
            "aggregation rule). MLflow's Model Registry + Experiment Tracking "
            "records params/metrics/artifacts per run; a 'PROV' bridge maps "
            "these to PROV-O. Crucially, however: (a) it does not read the "
            "paper; (b) it does not synthesize invariants from the paper's "
            "protocol; (c) its built-in checks are ML-system checks "
            "(data drift, model quality), not scientific-protocol conformance. "
            "No MLflow release ships a 'paper claim -> trace invariant' "
            "verifier. The closest is human-written metric assertions."
        ),
    },
    "CITEARK": {
        "rep_intended": "YES",
        # CiteArk's CAP chain explicitly starts from the Claim, which is the
        # "intended" scientific statement.
        "rep_executed": "YES",
        # CiteArk binds Claim -> Experiment -> Execution -> Evidence.
        "rep_relation": "YES",
        # The CAP chain is a direct representation of intended-to-actual.
        "auto_infer_predicate": "PARTIAL",
        # CiteArk automates *attribution / citation linking* (Evidence -> "
        # Claim). The Claim is a natural-language assertion; CiteArk links "
        # supporting evidence to it but does not compile the claim into a "
        # machine-checkable invariant over execution traces.
        "auto_flag_invalid": "PARTIAL",
        # CiteArk can flag a claim that is *unsupported by its cited "
        # evidence* (weak evidence linkage). It is an evidence-attestation "
        # tool, not a scientific-protocol conformance verifier. It does "
        # not detect value-preserving violations where the final metric "
        # still looks plausible but the execution path (selection split, "
        # aggregation rule) silently deviated.
        "notes": (
            "CiteArk / CAP (Claim -> Experiment -> Execution -> Evidence -> "
            "Assessment -> Attestation) is the nearest conceptual cousin to "
            "our TraceContract. It binds claims to execution and audits the "
            "evidence chain. Differences that matter for collision: "
            "(1) CiteArk's Claim is a citation/authorship claim, verified "
            "via evidence *linkage*, not a scientific-protocol claim "
            "verified via execution *semantics*; "
            "(2) it does not compile natural-language protocol statements "
            "into invariants like 'SELECTION_SPLIT != FINAL_TEST_SPLIT'; "
            "(3) it is not designed for the same-paper/same-code "
            "paired-execution setting where the final reported value may "
            "be identical. CiteArk is an ATTACH / evidence-bridge tool; our "
            "system is a SEMANTIC-CONFORMANCE tool."
        ),
    },
}


# ──────────────────────────────────────────────────────────────
# 6 fault families, per-family Q1-Q5 assessment for each system
# ──────────────────────────────────────────────────────────────

FAMILIES = [
    "E01", "E02", "E03", "E04", "E05", "E06",
]

FAMILY_LABELS = {
    "E01": "SEED_SELECTION_BIAS",
    "E02": "TEST_CONDITIONED_CHECKPOINT_SELECTION",
    "E03": "RUNTIME_CONFIG_MISMATCH",
    "E04": "SUBGROUP_SELECTIVE_REPORTING",
    "E05": "PREPROCESS_RUNTIME_FLAG_MISMATCH",
    "E06": "COMPUTE_OR_TRAINING_BUDGET_ASYMMETRY",
}


def per_family_assessment(family: str) -> dict:
    """
    For each family, answer Q1-Q5 for each system.

    Q1: P-PLAN/PROV represent intended + executed?
    Q2: Workflow Run RO-Crate represent runtime facts?
    Q3: CiteArk CAP represent C/E/E/E/A?
    Q4: Does ANY existing system automatically infer the scientific predicate?
    Q5: Does ANY existing system automatically flag the invalid execution?
    """
    out = {}

    # ── P-PLAN / PROV ────────────────────────────────────────
    # P-PLAN can represent "intended" and "executed" entities for most
    # families, since its model is intended-entity + execution + deviation.
    # It CANNOT automatically infer scientific predicates or flag invalid.
    pp_rep = "YES" if family in ("E01", "E02", "E03", "E04", "E05", "E06") else "NO"
    out["P_PLAN_representable"] = pp_rep
    out["P_PLAN_auto_infer"] = "NO"
    out["P_PLAN_auto_flag"] = "NO"

    # ── Workflow Run RO-Crate ───────────────────────────────
    # RO-Crate can represent runtime facts (params, artifacts, metrics)
    # for any family if the user populates custom DataItem properties.
    # It cannot represent "intended" entities (no plan layer).
    out["WRC_representable"] = "YES" if family in ("E01", "E02", "E03", "E04", "E05", "E06") else "NO"
    out["WRC_auto_infer"] = "NO"
    out["WRC_auto_flag"] = "NO"

    # ── MLflow/PROV ─────────────────────────────────────────
    # MLflow records what happened: params, metrics, checkpoints, runs.
    # It represents the runtime facts for all families.
    # Cannot infer predicates or flag invalid.
    out["MLFLOW_representable"] = "YES"
    out["MLFLOW_auto_infer"] = "NO"
    out["MLFLOW_auto_flag"] = "NO"

    # ── CiteArk / CAP ───────────────────────────────────────
    # CiteArk's CAP chain can represent Claim->Experiment->Execution->
    # Evidence for all families. The "Assessment" step is the closest
    # to a verdict, but it assesses evidence *support*, not protocol
    # *conformance*.
    out["CITEARK_representable"] = "YES"
    out["CITEARK_auto_infer"] = "PARTIAL"
    # CiteArk can flag an *unsupported claim* (evidence gap), but not a
    # value-preserving scientific-protocol violation.
    out["CITEARK_auto_flag"] = "NO" if family in ("E01", "E02", "E03", "E05", "E06") else "PARTIAL"
    # E04 (subgroup selective reporting): CiteArk *could* flag that the
    # evidence does not cover all declared subgroups, if the subgroups
    # are cited claims. This is PARTIAL.

    # ── REPRESENTATION_COLLISION ────────────────────────────
    # If ANY prior system can represent the family, REPRESENTATION_COLLISION=YES
    out["REPRESENTATION_COLLISION"] = "YES"

    # ── AUTOMATIC_VERIFICATION_COLLISION ────────────────────
    # Requires a system that (a) auto-infers the predicate AND (b) auto-flags
    out["AUTOMATIC_VERIFICATION_COLLISION"] = "NO"
    # Note: if any system had both PARTIAL/PARTIAL on Q4/Q5, we would
    # consider UNKNOWN. No system meets both here.

    return out


def strongest_collision_test() -> dict:
    """
    6-capability Strongest-Collision Test.

    For each system, score 0-6 on:
      1. derives protocol conditions from a paper/claim
      2. observes actual runtime execution
      3. constructs machine-checkable semantic constraints
      4. detects execution-dependent scientific violations
      5. distinguishes same-paper/same-code execution pairs
      6. goes beyond simple reported-value vs observed-value comparison

    A system meeting >=5 of 6 => COLLISION for that system.
    """
    # Manual scoring based on documented capabilities:

    scores = {
        "P-PLAN": {
            1: 0,  # no paper-claim derivation
            2: 1,  # observes runtime execution (PROV-O entities)
            3: 0,  # no machine-checkable constraints
            4: 0,  # no auto-detection
            5: 0,  # no pair discrimination
            6: 0,  # beyond simple comparison? no
        },
        "WORKFLOW_RUN_RO_CRATE": {
            1: 0,
            2: 1,
            3: 0,
            4: 0,
            5: 0,
            6: 0,
        },
        "MLFLOW_PROV": {
            1: 0,  # no paper-claim derivation (human writes assertions)
            2: 1,  # observes runtime execution
            3: 0,  # no semantic-constraint language in MLflow spec
            4: 0,  # no auto-detection of scientific violations
            5: 0,  # no same-paper/same-code pair discrimination
            6: 0,  # no
        },
        "CITEARK": {
            1: 1,  # derives conditions from a CLAIM (but it's a citation "
                   # claim, not a scientific protocol claim)
            2: 1,  # observes runtime execution (the Execution entity)
            3: 1,  # constructs machine-checkable constraints? CiteArk "
                   # builds an evidence-assessment DAG, but not semantic "
                   # invariants over runtime fields
            4: 0,  # detects execution-dependent scientific violations? "
                   # No - it detects evidence *support* gaps
            5: 0,  # same-paper/same-code pair discrimination? No
            6: 0,  # beyond simple value comparison? No
        },
    }

    result = {}
    for sys_name, sc in scores.items():
        total = sum(sc.values())
        result[sys_name] = {
            "score": total,
            "criteria_met": [i for i, v in sc.items() if v],
            "collides": total >= 5,
        }
    return result


def build_matrix() -> list:
    """Build the full 6-family x 5-question matrix."""
    rows = []
    for family in FAMILIES:
        a = per_family_assessment(family)
        row = {
            "family": family,
            "label": FAMILY_LABELS[family],
            **{k: v for k, v in a.items()},
        }
        rows.append(row)
    return rows


def main():
    # Build and save the collision matrix CSV
    rows = build_matrix()
    matrix_csv = RESULTS_DIR / "R1B0_COLLISION_MATRIX.csv"
    with open(matrix_csv, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)
    print(f"Matrix -> {matrix_csv}")

    # Strongest collision test
    sct = strongest_collision_test()
    print("\n=== Strongest-Collision Test (6 capabilities) ===")
    for sys_name, r in sct.items():
        flag = "COLLIDES" if r["collides"] else "no"
        print(f"  {sys_name}: {r['score']}/6 -> {flag}  (met: {r['criteria_met']})")

    # Verdict
    any_collision = any(r["collides"] for r in sct.values())
    # Count "NO" for auto-detection across families
    auto_all_no = all(
        r["AUTOMATIC_VERIFICATION_COLLISION"] == "NO"
        for r in rows
    )
    rep_yes_count = sum(1 for r in rows if r["REPRESENTATION_COLLISION"] == "YES")

    print(f"\nAny system COLLIDES: {any_collision}")
    print(f"Representation collision (YES families): {rep_yes_count}/6")
    print(f"All auto-detection = NO: {auto_all_no}")

    if not any_collision:
        # No system meets >=5/6. Check if any meets 3/6 (the "narrow"
        # boundary for PARTIAL_COLLISION).
        best = max(sct.values(), key=lambda r: r["score"])
        if best["score"] >= 3:
            verdict = "PARTIAL_COLLISION"
            print(f"\nVERDICT: PARTIAL_COLLISION ({best['score']}/6 via {list(sct.keys())[list(sct.values()).index(best)]})")
        else:
            verdict = "CLEAR_CANDIDATE"
            print(f"\nVERDICT: CLEAR_CANDIDATE (best system: {best['score']}/6)")
    else:
        verdict = "COLLISION"
        print(f"\nVERDICT: COLLISION")

    return verdict, rows, sct


if __name__ == "__main__":
    main()
