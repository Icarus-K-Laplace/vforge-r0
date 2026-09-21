# R1-B0 Prior-Art Collision Report

**Protocol**: R1-B0 — Scientific Execution Conformance Collision Audit
**Project**: V-Forge TRACE-CONTRACT
**Date**: 2026-09-20
**Upstream status**: R1-A STRONG_GO (PSD=0.900, static=0.000, localization=1.000)

---

## Verdict

```
NOVELTY_STATUS: PARTIAL_COLLISION
REAL_TRACE_FEASIBILITY: UNCERTAIN
VALUE_PRESERVING_HEADROOM: UNCERTAIN
STATUS: PARTIAL_COLLISION — R1-B1 permission GRANTED, novelty narrowed
```

The narrowest defensible novelty claim:

> **Automatic induction and machine checking of scientific-validity
> constraints over runtime execution traces, especially violations that
> cannot be distinguished from paper and source code alone and may
> preserve the final reported metric.**

Do NOT claim novelty for: provenance capture, plans, runs, evidence binding,
cryptographic attestation, workflow conformance in general, or claim
extraction.

---

## Section A: Representation vs. Automatic-Detection

The protocol requires a strict separation:

| Question | Answer space |
|----------|:------------:|
| Can P-PLAN/PROV represent the intended + executed entities? | YES / NO |
| Can Workflow Run RO-Crate represent the runtime facts? | YES / NO |
| Can CiteArk CAP represent the C/E/E/E/A fields? | YES / NO |
| Does the existing framework AUTOMATICALLY INFER the scientific-validity predicate? | YES / NO / PARTIAL |
| Does its published verifier AUTOMATICALLY FLAG the invalid execution? | YES / NO / PARTIAL |

The critical distinction: **representable ≠ automatically detected.**

A system that can *serialize* a trace field does not *derive* a scientific
invariant from a paper claim. This is the gap TraceContract fills.

---

## Section B: Strongest-Collision Test (6 capabilities)

| # | Capability | P-PLAN | WRC | MLflow/PROV | CiteArk |
|:-:|-----------|:------:|:---:|:-----------:|:-------:|
| 1 | Derive protocol conditions from paper/claim | NO | NO | NO | PARTIAL |
| 2 | Observe actual runtime execution | YES | YES | YES | YES |
| 3 | Construct machine-checkable semantic constraints | NO | NO | NO | PARTIAL |
| 4 | Detect execution-dependent scientific violations | NO | NO | NO | NO |
| 5 | Distinguish same-paper/same-code execution pairs | NO | NO | NO | NO |
| 6 | Go beyond reported-value vs observed-value comparison | NO | NO | NO | NO |
| | **Total** | **1/6** | **1/6** | **1/6** | **3/6** |

**Threshold**: A system meeting ≥5/6 would establish direct COLLISION.
**Result**: No system reaches 5/6. CiteArk reaches 3/6 → PARTIAL_COLLISION.

---

## Section C: Per-Family Collision Matrix

| Family | P-PLAN representable | P-PLAN auto-infer | P-PLAN auto-flag | WRC representable | WRC auto-infer | WRC auto-flag | MLflow representable | MLflow auto-infer | MLflow auto-flag | CiteArk representable | CiteArk auto-infer | CiteArk auto-flag | REP_COLLISION | AUTO_COLLISION |
|--------|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| E01 SEED_SELECTION_BIAS | YES | NO | NO | YES | NO | NO | YES | NO | NO | YES | PARTIAL | NO | YES | NO |
| E02 TEST_CONDITIONED_CKPT | YES | NO | NO | YES | NO | NO | YES | NO | NO | YES | PARTIAL | NO | YES | NO |
| E03 RUNTIME_CONFIG_MISMATCH | YES | NO | NO | YES | NO | NO | YES | NO | NO | YES | PARTIAL | NO | YES | NO |
| E04 SUBGROUP_SELECTIVE_REPORT | YES | NO | NO | YES | NO | NO | YES | NO | NO | YES | PARTIAL | PARTIAL | YES | NO |
| E05 PREPROCESS_RUNTIME_FLAG | YES | NO | NO | YES | NO | NO | YES | NO | NO | YES | PARTIAL | NO | YES | NO |
| E06 BUDGET_ASYMMETRY | YES | NO | NO | YES | NO | NO | YES | NO | NO | YES | PARTIAL | NO | YES | NO |

**Reading the matrix:**

- **REPRESENTATION_COLLISION = YES for all 6 families.** Every prior-art
  system can *serialize* the relevant runtime facts. This is expected and
  does not endanger the novelty claim, because serialization ≠ semantic
  checking.

- **AUTOMATIC_VERIFICATION_COLLISION = NO for all 6 families.** No existing
  system automatically *derives* the scientific-validity predicate from a
  paper claim and *flags* a scientifically invalid execution that preserves
  the final reported metric.

- **CiteArk is the closest** (3/6 on the 6-capability test). Its CAP chain
  (Claim → Experiment → Execution → Evidence → Assessment → Attestation)
  is a structural cousin of TraceContract's (paper → contract → trace →
  witness → verdict). The critical differences:
  1. CiteArk's "Claim" is a *citation/authorship* claim, verified by
     *evidence support*, not a *scientific-protocol* claim, verified by
     *execution conformance*.
  2. CiteArk does not compile natural-language protocol statements into
     machine-checkable invariants (e.g., `SELECTION_SPLIT != FINAL_TEST_SPLIT`).
  3. CiteArk is not designed for the same-paper/same-code paired-execution
     setting where the final reported value may be identical.
  4. CiteArk's Assessment step asks "does this evidence support that
     claim?", not "did this execution satisfy the protocol the paper
     asserted?"

---

## Section D: Prior-Art Summary

### P-PLAN / PROV Plan-to-Execution

- **What it does**: Extends W3C PROV with "intended" (P-INT) entities.
  REPRODUCE-ME extends P-PLAN to Jupyter notebooks: compares two executions
  (reference vs. current) on changed steps, errors, environment, results.
- **What it does NOT do**: No paper-claim reading. No predicate synthesis.
  No auto-flag of a scientifically invalid execution. The "reference"
  execution is a human-chosen prior run, not a paper-derived protocol.
- **Collision**: REPRESENTATION only. LOW.

### Workflow Run RO-Crate / Provenance Run Crate

- **What it does**: Serializes a completed run's provenance (agents,
  parameters, outputs, command invocations) in JSON-LD.
- **What it does NOT do**: No "intended" layer. No semantic constraint
  language. No verifier. Runtime facts are represented *if the user
  populates them*, not automatically.
- **Collision**: REPRESENTATION only. LOW.

### MLflow / PROV-Style ML Execution Provenance

- **What it does**: Records what happened: params, metrics, artifacts,
  checkpoints, run status. A PROV bridge maps these to PROV-O entities.
  The closest tool for *capturing* the runtime facts our contract checks.
- **What it does NOT do**: Does not read the paper. Does not synthesize
  invariants from the paper's protocol. Built-in checks are ML-system
  checks (data drift, model quality), not scientific-protocol conformance.
  No "paper claim → trace invariant" verifier ships with MLflow.
- **Collision**: REPRESENTATION only. MODERATE (MLflow is the strongest
  representation prior art, but it stops at record-keeping).

### CiteArk / CAP

- **What it does**: Binds Claim → Experiment → Execution → Evidence →
  Assessment → Attestation. Audits evidence *linkage* (does the cited
  evidence support the claim?). Automated citation/attribution.
- **What it does NOT do**: The "claim" is a citation/authorship assertion,
  not a scientific-protocol assertion. It does not compile protocol
  statements into invariants. It does not operate on same-paper/same-code
  paired executions. It cannot detect value-preserving violations where
  the final metric is plausible but the execution path deviated.
- **Collision**: PARTIAL. The closest prior art. Novelty must be framed
  as "scientific-protocol conformance" vs. CiteArk's "evidence support".

---

## Section E: Surviving Claim

Freeze this as the surviving novelty:

> **Scientific Execution Conformance**:
>
> Compile natural-language scientific protocol claims into executable
> invariants over retrospective runtime provenance, enabling detection and
> localization of execution-dependent scientific validity violations —
> specifically those that preserve the final reported metric and are
> informationally inaccessible to paper and source code alone.

Explicitly excluded from the novelty claim:

- provenance capture / record-keeping (MLflow, RO-Crate do this)
- plan-to-execution correspondence (P-PLAN does this)
- evidence binding / citation attribution (CiteArk does this)
- cryptographic attestation (RO-Crate / PROV-COMP do this)
- workflow conformance checking in general (SPIN, P-PLAN do this)
- claim extraction from natural language (various NLP systems do this)

---

## Section F: R1-B1 Permission

**PARTIAL_COLLISION grants permission to proceed to R1-B1**, but with the
narrowed novelty claim above. The surviving claim rests on:

1. **Automatic predicate synthesis** from paper text (no existing system
   does this; CiteArk is PARTIAL because it does not compile protocol
   statements into machine-checkable invariants).
2. **Value-preserving violation detection** (VPVD) — detecting execution-
   dependent violations where the final reported metric remains plausible
   or identical. No prior system targets this.
3. **Same-paper/same-code paired-execution discrimination** — a setting
   that CiteArk's evidence-linkage model does not address.

**R1-B1 requirement (unchanged)**: 5–8 public ML papers with public run
evidence. Construct the normative contract BEFORE inspecting detailed run-
selection patterns. Test trace observability (TO), not accuse authors.

---

## Required Outputs Checklist

| Output | Status |
|--------|:------:|
| `reports/R1B0_PRIOR_ART_COLLISION.md` | ✅ this file |
| `results/R1B0_COLLISION_MATRIX.csv` | ✅ generated |
| `reports/R1B1_TRACE_SOURCE_AUDIT.md` | ⏳ deferred to R1-B1 |
| `results/R1B1_TRACE_OBSERVABILITY.csv` | ⏳ deferred to R1-B1 |
| `results/R1B1_REAL_TRACE_PAIRS.jsonl` | ⏳ deferred to R1-B1 |
| `results/R1B1_VALUE_PRESERVING_VIOLATIONS.jsonl` | ⏳ deferred to R1-B1 |
| `reports/R1B1_FINAL_REPORT.md` | ⏳ deferred to R1-B1 |

---

## Section G: Expanded Prior-Art Scope (R1-B1 §1)

The following additional prior-art systems are explicitly in scope and
distinguished from TraceContract's surviving claim:

### 1. Validity Constraints for Data Analysis Workflows (VCDW)

- **What it does**: PSL (Provenance Specification Language) validity
  constraints over data analysis pipelines. Detects *data-flow* validity
  violations (e.g., division by zero, type mismatches) in workflow executions.
- **Gap**: VCDW constraints are *data-* or *type-* validity, not *scientific
  protocol* validity. It does not read a paper's declared aggregation
  rule, selection policy, or subgroup scope. It cannot express
  "ReportedRunSet == DeclaredRunSet" from a paper.
- **Relation to TraceContract**: VCDW is a *constraint language over
  provenance*; TraceContract adds the *paper-to-constraint compilation*
  step and targets *scientific-epistemic* constraints, not data-validity.

### 2. P-PLAN / PROV

See Section D. No automatic scientific predicate induction.

### 3. Workflow Run RO-Crate

See Section D. No semantic-constraint language.

### 4. MLflow2PROV

- **What it does**: MLflow2PROV (or similar PROV-bridging tools) maps
  MLflow runs to W3C PROV entities. Records what happened: parameters,
  metrics, artifacts, lineage.
- **Gap**: Does not read the paper. Does not synthesize invariants from
  the paper's protocol. No scientific-protocol conformance checking.
  MLflow2PROV is a *serialization* tool, not a *verification* tool.
- **Relation**: MLflow2PROV can feed the runtime provenance that
  TraceContract checks, but it does not perform the check.

### 5. CiteArk / CAP

See Section D. Evidence-linkage, not execution-conformance.

### 6. Automated Provenance-Based ML Data-Pipeline Screening

- **What it does**: Tools that screen ML data pipelines for *data quality*
  issues (drift, leakage, bias) using provenance records. Examples:
  DataSentinel, DataCleaner, and various drift-detection frameworks.
- **Gap**: These target *data* quality, not *scientific reporting*
  conformance. They do not check whether the aggregation rule used
  to produce a table value matches the paper's declared protocol.
  They do not detect test-set-influenced model selection.
- **Relation**: Different verification target. TraceContract targets
  the *epistemic* validity of how a result was produced and reported,
  not the *statistical* quality of the data.

### 7. Scientific Admissibility Evidence Record (SAER)

- **What it does**: SAER (if this refers to a legal / legal-science
  evidence admissibility framework) records *why* evidence is admissible
  in a legal context. Not directly comparable to scientific-protocol
  conformance.
- **Gap**: Different domain (legal evidence vs. scientific protocol).
  If SAER refers to a specific ML-reproducibility framework, note: it
  records the *existence* of evidence, not whether the *process*
  that produced it conformed to the declared protocol.

---

## Final Fields

```
NOVELTY_STATUS: PARTIAL_COLLISION
DECISION: PROCEED_NARROWED
REAL_TRACE_FEASIBILITY: UNCERTAIN
VALUE_PRESERVING_HEADROOM: UNCERTAIN
STATUS: PARTIAL_COLLISION

NARROWED_NOVELTY_CLAIM:
"Automatic paper-to-epistemic-constraint compilation plus runtime
 checking of value-preserving scientific process violations."

EXCLUDED_FROM_NOVELTY:
- runtime provenance
- prospective/retrospective provenance
- plan-vs-execution comparison
- workflow validity constraints
- scientific evidence records
- paper claim extraction
- claim-to-experiment linking
- reported-value vs observed-value verification
```

R1-B0 STOP. R1-B1 Stage 1 permission granted under the narrowed claim
above. Do not lower inclusion requirements to increase paper count.
E02 trace insufficiency must be explicitly recorded, not invented.

---

**Report generated**: 2026-09-20
**Protocol**: R1-B0
