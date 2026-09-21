# R0-D1-v2 DEV Evaluation Report

**Experiment**: VForge-R0-D1-v2-001
**Date**: 2026-09-20
**Data**: SciCoQA v1.1 Real Split (92 samples) — DEV/QUALIFICATION only
**Label**: R0-D1-v2 qualification performance. NOT zero-shot final evidence.

---

## System Health (Blind, Pre-Gold-Reveal)

| Metric | Value | Qualification |
|--------|-------|:------------:|
| Paper extraction rate | 74/92 = 80.4% | ✅ (target ≥80%) |
| Usable graph rate | 76/92 = 82.6% | ✅ (target ≥75%) |
| Prediction freeze SHA256 | `3cb78f631cff...` | ✅ Frozen |
| Extreme distribution | No (not 92 PASS / 92 FAIL) | ✅ No audit trigger |

**Blind verdict distribution (frozen):**
- PASS: 0
- FAIL: 0
- ABSTAIN: 74
- PAPER_UNAVAILABLE: 18
- REPOSITORY_UNAVAILABLE: 0
- CONTRACT_INSUFFICIENT: 0

All samples returned ABSTAIN-class verdicts. This is expected at this
engineering stage: the verifier is correctly conservative (no permissive
PASS fallbacks), and 85/92 contracts are universal-only (INVALID_CONTRACT
per provenance audit), which maps to ABSTAIN.

---

## Gold-Reveal Evaluation (DEV)

After prediction freeze, gold labels revealed.

| Metric | Value |
|--------|-------|
| Real Discrepancy Recall (RDR) | 0/92 = **0.000** |
| FAIL count | 0 |
| PASS count | 0 |
| ABSTAIN total | 92 (100%) |

### Per-Category Detection (all zero)

| Category | Detected | Total | Recall |
|----------|:--------:|:-----:|:------:|
| Algorithm | 0 | 22 | 0.0% |
| Loss | 0 | 22 | 0.0% |
| Training | 0 | 16 | 0.0% |
| Model | 0 | 10 | 0.0% |
| Data | 0 | 10 | 0.0% |
| Evaluation | 0 | 9 | 0.0% |
| (None) | 0 | 3 | 0.0% |

Published best real-world RDR: **46.7%** (SciCoQA paper).
Our R0-D1-v2 DEV RDR: **0%** — below all baselines.

---

## Diagnosis

The 0% RDR is not a verifier bug. It is a **capability gap** in the
current pipeline:

1. **85/92 contracts are universal-only** (no paper-specific source span).
   These correctly return ABSTAIN per protocol, but they cannot detect
   any discrepancy.

2. **7/92 contracts have paper-derived invariants** — but the graph
   extractor generates generic pipeline nodes (DATASET→SPLIT→TRAIN→MODEL→
   EVALUATE→METRIC) without semantic depth. It cannot detect:
   - Which loss function is actually used
   - Which metric is reported
   - Whether seed aggregation is correct
   - Whether test data leaked into selection

   The graph is structurally valid but semantically empty.

3. **P1-P8 invariant checking** works for node-type presence (SELECT,
   EVALUATE, SPLIT) but not for **attribute values** (e.g.,
   `aggregation_rule`, `selection_source`, `loss_function`).
   The T1-T8 adversarial tests prove the attribute-checking path works
   in controlled cases, but the real graphs don't populate these
   attributes.

**Root cause**: The graph extractor needs a code-reading component that
populates semantic attributes (loss name, metric name, seed count,
selection source) from actual source files. The current extractor only
detects file existence and directory structure.

---

## Decision (Per Protocol §13)

> "If real recall <= direct-LLM baseline: REDEFINE or KILL_GENERAL_CLAIM.
> Do not rescue by adding discrepancy-specific rules."

- RDR = 0.0% (well below 46.7% published best, well below any LLM baseline)
- Cause: semantic gap in graph extraction, NOT a discrepancy-specific failure
- No case-specific rules were added during this run

### Decision: **REDEFINE**

The R0-D1-v2 infrastructure is:
- ✅ Leakage-safe (verified by protocol)
- ✅ Unit-tested (T1-T8 all pass)
- ✅ No permissive PASS (ABSTAIN 100% confirms)
- ✅ Paper extraction qualified (80.4%)
- ✅ Graph extraction qualified (82.6%)

The remaining gap is **semantic depth in graph attribute extraction**.
This is an engineering task, not a scientific failure.

**R0-D2 (temporal holdout) is NOT justified yet.**
SciCoQA DEV shows 0% RDR, which does not demonstrate "enough headroom"
to justify collecting a new external set.

**Next action**:
1. Enhance graph extractor to populate semantic attributes
   (loss function, metric, seed count, selection source) from code
2. Re-run R0-D1-v2 qualification
3. Only if DEV RDR materially improves, proceed to R0-D2

---

## Artifact Inventory

```
results/
├── R0D1v2_PREDICTIONS_FROZEN.jsonl   [FROZEN, SHA256: 3cb78f63...]
├── R0D1v2_PREDICTION_FREEZE.json      [HASH RECORD]
└── R0D1_INVALID_RUN_FROZEN.jsonl      [PREVIOUS INVALID RUN, PRESERVED]

reports/
├── R0D1_INVALID_RUN_NOTICE.md
├── R0D_MUTATION_RESIDUE_AUDIT.md
├── R0D_CONTRACT_PROVENANCE_AUDIT.md
└── R0D1v2_DEV_EVALUATION.md           [This file]
```
