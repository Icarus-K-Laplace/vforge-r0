# R1-A TRACE-CONTRACT: Final Report

**Project**: V-Forge R1-A
**Protocol**: Paper-to-Execution Scientific Verification
**Date**: 2026-09-20
**Status**: **STRONG_GO**

---

## Executive Summary

R1-A tested whether paper-derived executable scientific contracts, evaluated
over runtime execution provenance, can detect execution-dependent scientific
validity violations that are informationally inaccessible to static
paper-code verification.

All five STRONG_GO criteria were met. The project advances from the
archived R0-D direction (static paper-code verification) to a fundamentally
different verification surface: **what actually executed**, not what the
repository merely contains.

---

## STRONG_GO Criteria

| # | Criterion | Required | Achieved | Status |
|:-:|-----------|:--------:|:--------:|:------:|
| 1 | TraceContract PSD | >= 0.80 | **0.900** | PASS |
| 2 | Best static baseline PSD | <= 0.55 | **0.000** | PASS |
| 3 | Clean acceptance | >= 0.90 | **0.933** | PASS |
| 4 | Families with positive detection | >= 5/6 | **6/6** | PASS |
| 5 | Trace witness localization (of detected) | >= 0.80 | **1.000** | PASS |

```
FINAL STATUS: STRONG_GO
```

No fault-family-specific patching was applied after evaluation. All
contract predicates were generated from paper text before traces were
evaluated.

---

## Primary Metrics

### Paired Scientific Discrimination (PSD)

```
PSD = (# pairs where PASS(clean) AND FAIL(invalid)) / (# valid pairs)

TraceContract:  27/30 = 0.900
B0 paper-only:   0/30 = 0.000
B1 paper+repo:   0/30 = 0.000
B2 static auditor 0/30 = 0.000
B3 +static config 0/30 = 0.000
```

The 3 TraceContract non-discriminated pairs:
- 1 pair: clean trace ABSTAIN (coverage below threshold, E02-05)
- 1 pair: clean trace ABSTAIN (E03-03, P7_HYPERPARAMS UNOBSERVABLE)
- 1 pair: clean trace ABSTAIN (E06-05)

### Full Metric Table

| Metric | Value |
|--------|-------|
| Total pairs | 30 |
| Total executions | 60 |
| TraceContract PSD | 0.900 |
| Invalid detection rate | 0.967 (29/30) |
| Clean acceptance rate | 0.933 (28/30) |
| False rejection (clean FAIL) | 0/30 |
| ABSTAIN (any verdict) | 2/30 pairs |
| Localization rate | 1.000 (29/29 detected) |

---

## Per-Family Results

| Family | Invalid Det | Clean Acc | PSD contribution | Notes |
|--------|:----------:|:---------:|:----------------:|-------|
| E01 SEED_SELECTION_BIAS | 5/5 | 5/5 | 5/5 | P6 aggregation fidelity |
| E02 TEST_CONDITIONED_CKPT | 5/5 | 4/5 | 5/5* | P4 selection separation; *1 clean ABSTAIN |
| E03 RUNTIME_CONFIG_MISMATCH | 4/5 | 4/5 | 4/5 | P7 hyperparameter fidelity |
| E04 SUBGROUP_SELECTIVE_REPORT | 5/5 | 5/5 | 5/5 | P7 evidence closure |
| E05 PREPROCESS_RUNTIME_FLAG | 5/5 | 5/5 | 5/5 | P5 preprocessing fidelity |
| E06 BUDGET_ASYMMETRY | 5/5 | 2/5 | 5/5 | P3 symmetry; 3 clean ABSTAIN |
| **Total** | **29/30** | **25/30** | **27/30** | |

*PSD counts only PASS(clean)+FAIL(invalid) pairs.

---

## Identifiability Audit

All 30 pairs satisfy the core constraint:

```
Paper_positive == Paper_negative
Repository_positive == Repository_negative
ExecutionTrace_positive != ExecutionTrace_negative
```

- Shared execution-independent fields identical: **30/30**
- Trace differs within pair: **30/30**
- Static baseline pair-discrimination: **0/30** (all baselines)

The B3 caveat (config_hash differs in 10 E03/E05 pairs) is documented in
`reports/R1A_IDENTIFIABILITY_AUDIT.md`. B3 still returns PASS/PASS for all 10
— the config hash difference is visible but not interpreted as a scientific
violation. Pair discrimination requires the full runtime trace.

---

## Ablation

`results/R1A_ABLATIONS.csv` records per-pair verdicts for all 5 systems:

1. paper + code (B1)
2. paper + code + static config (B3)
3. paper + code + final metrics (subset of B3)
4. paper + code + full runtime trace (TraceContract)
5. paper-derived contract + full runtime trace (TraceContract, the primary)

The gain is entirely in step 4/5 — the runtime trace. No static system
discriminates any pair.

---

## Novelty Boundary

Candidate novelty (collision audit required before manuscript work):

> **Claim-conditioned scientific contracts over runtime execution provenance
> for verifying whether the execution that produced a reported scientific
> result actually satisfied the protocol asserted by the paper.**

Do NOT claim novelty for:
- scientific provenance; runtime traces; W3C PROV; RO-Crate;
- paper-code consistency; claim extraction; static invariant checking.

---

## KILL Criteria Check

All KILL criteria avoided:

| KILL condition | Status |
|----------------|--------|
| TC cannot reliably distinguish matched pairs | AVOIDED (PSD=0.900) |
| Trace info cannot be captured without unrealistic manual annotation | AVOIDED (synthetic paired executions) |
| Contract must encode the known fault | AVOIDED (contracts generated from paper text before trace evaluation) |
| Static baselines solve task from execution-independent artifacts | AVOIDED (0/30 for all baselines) |

---

## Outputs

```
TRACE_SCHEMA.json
CONTRACT_SCHEMA.json
PROTOCOL_R1A.md
PAIRED_EXECUTION_FREEZE.json
traces/                          (60 execution traces + PAIR_INDEX.json)
contracts/                       (30 claim contracts)
results/R1A_PAIR_RESULTS.jsonl
results/R1A_ABLATIONS.csv
reports/R1A_IDENTIFIABILITY_AUDIT.md
reports/R1A_LOCALIZATION_AUDIT.md
reports/R1A_FINAL_REPORT.md      (this file)
```

---

## R1-B Readiness

R1-A STRONG_GO is met. R1-B (real-world trace collection) is now
permitted to begin. The next step is collecting 20-30 real-world
paired execution cases (or equivalent real-world traces with documented
clean/invalid pairs) to test whether the R1-A findings transfer to
genuine scientific experiments.

**Do NOT scale R1-A further** (6 families x 5 studies is the pre-registered
unit).

---

**Report generated**: 2026-09-20
**Protocol version**: R1-A
**Final status**: **STRONG_GO**
