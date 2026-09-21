# V-Forge R0-D1-v2 FINAL REPORT — ARCHIVED

## Project Transition Notice

**Date**: 2026-09-20
**Status**: ARCHIVED — Direction Superseded by R1-A (TRACE-CONTRACT)

---

## R0-D1-v2 Final Status

### Summary
The generic paper-code verification direction is concluded. R0-D1-v2 DEV qualification was completed with:

- Paper extraction: 74/92 (80.4%) — qualified
- Graph extraction: 76/92 (82.6%) — qualified
- RDR (DEV): 0/92 = 0.000
- All 8 adversarial unit tests (T1-T8) passed
- Verdict distribution: ABSTAIN=74, PAPER_UNAVAILABLE=18, PASS=0, FAIL=0
- Predictions frozen: SHA256 `3cb78f631cff...`

### Decision: REDEFINE

The scientific gap identified: graph extractor produces structurally valid but
semantically empty protocol graphs. Without semantic attributes
(loss function, metric, seed count, selection source), the verifier correctly
returns ABSTAIN for all samples — it cannot detect any discrepancy.

### Prior Conclusions
- Controlled protocol invariants (R0-C STRONG_GO, MKR=1.0) showed promise
  on synthetic mutations.
- Static real-world transfer to SciCoQA failed in current implementation.
- Generic paper-code auditing is now strongly occupied by SciCoQA, CodeCheck,
  BioCon, and related systems.

---

## Transition to R1-A: TRACE-CONTRACT

### New Research Question

> Can scientific claims be verified against the **execution that actually
> produced the reported result**, rather than merely against the repository
> containing possible implementations?

### Why This Is Different
The new direction targets a fundamentally different verification surface:
- **Old**: paper claims vs. repository code (static)
- **New**: paper claims vs. runtime execution trace (dynamic, provenance-aware)

The same paper and same repository can produce **positive** and **negative**
scientific outcomes depending on which execution path was taken, which
configurations were active, and which data splits were used at runtime.
Static code auditing cannot distinguish these cases.

### Core Identifiability Constraint
```
Paper_positive == Paper_negative
Repository_positive == Repository_negative
ExecutionTrace_positive != ExecutionTrace_negative
```

This same-paper/same-code constraint prevents degeneration into a
paper-code discrepancy benchmark.

### Primary Hypothesis (H1)
Paper-derived executable scientific contracts, evaluated over runtime
provenance, can detect execution-dependent scientific validity violations
that are **informationally inaccessible** to static paper-code verification.

H1 must be killed if runtime traces do not show a clear advantage.

---

## Required R1-A Outputs (To Be Created)

| Output | Status |
|--------|:------:|
| `TRACE_SCHEMA.json` | TODO |
| `CONTRACT_SCHEMA.json` | TODO |
| `PROTOCOL_R1A.md` | TODO |
| `PAIRED_EXECUTION_FREEZE.json` | TODO |
| `traces/` | TODO |
| `contracts/` | TODO |
| `results/R1A_PAIR_RESULTS.jsonl` | TODO |
| `results/R1A_ABLATIONS.csv` | TODO |
| `reports/R1A_IDENTIFIABILITY_AUDIT.md` | TODO |
| `reports/R1A_LOCALIZATION_AUDIT.md` | TODO |
| `reports/R1A_FINAL_REPORT.md` | TODO |

### R1-A Scale
- 6 execution-dependent fault families (E01-E06)
- 5 independent studies per family
- 30 paired cases, 60 executions
- Do not scale further until central effect exists

### GO Criteria
STRONG_GO requires:
- TraceContract PSD ≥ 0.80
- Best static baseline PSD ≤ 0.55
- Clean acceptance ≥ 0.90
- ≥ 5/6 fault families show positive detection
- Trace witnesses correctly localize in ≥ 0.80 of detected cases

### KILL Criteria
KILL if:
- TraceContract cannot reliably distinguish matched execution pairs
- Required trace information cannot be captured without unrealistic manual annotation
- Scientific contract must encode the known fault rather than being derivable from paper claims
- Static baselines can solve the task from artifacts that should theoretically be execution-independent

---

## R1-A Decision

**Do NOT start R1-B** (real-world trace collection) unless R1-A passes.
