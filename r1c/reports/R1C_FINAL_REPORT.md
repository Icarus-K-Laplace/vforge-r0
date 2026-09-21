# EPITRACE R1-C Final Report — Naturalistic External Validation

**Protocol**: Naturalistic External Validation of Epistemic Execution Conformance
**Stage**: R1-C (first naturalistic external validation of EPITRACE)
**Date**: 2026-09-21
**Verdict**: **STRONG_GO**

---

## 1. Objective

Test whether EpiTrace can, under fully blind evaluation (no access to gold
evidence, issues, errata, or fix commits during inference), automatically
compile paper-declared scientific protocols into epistemic execution
constraints and detect **naturally occurring, externally documented**
scientific execution / evaluation / reporting protocol deviations — not
synthetic counterfactuals.

## 2. Anti-leakage discipline (protocol §7)

- `R1C_DISCOVERY_GOLD/` (issues, errata, fix commits, gold category labels)
  physically isolated from `R1C_BLIND/` (paper title, venue, category,
  target repo only).
- Contract induction (`r1c/induce_contracts.py`) ran **only** on BLIND
  metadata + paper-declared protocol statements. Fix diffs / gold issue
  text were not read.
- `R1C_PRE_PREDICTIONS_FROZEN.jsonl` was written and SHA256-frozen
  **before** gold reveal.
- No case was dropped post-hoc based on EpiTrace performance
  (`R1C_CASE_FREEZE.json` + `R1C_SHA256SUMS`).
- **GOLD_LEAKAGE = NO.**

## 3. Case pool

- 30 candidates logged in `R1C_CANDIDATE_CASES.csv` (C1–C6 categories,
  spanning CV, NLP, GNN, time series, RL, metric learning, translation,
  clinical-adjacent and systems papers).
- 8 included (`CAND-01`…`CAND-08`), frozen in `R1C_INCLUDED_CASES.csv`
  and `R1C_CASE_FREEZE.json`.
- `CAND-18` (ClinicalBench KDD'26) remains `EXCLUDED_AUTH` (gated
  HuggingFace dataset) — carried over as a documented block from
  R1-B1 Stage1b, not re-fabricated.

## 4. Included cases (8 naturalistic cases, all paired pre/post corrections)

| ID | Paper | Category | Gold source class |
|----|-------|----------|-------------------|
| CAND-01 | Informer (AAAI'21) | C1 selection/eval leakage | E (LTSF-Linear) + GitHub #36/#118 |
| CAND-02 | A Metric Learning Reality Check (ECCV'20) | C1 test-conditioned checkpoint selection | E (RevisitDML protocol) |
| CAND-03 | Deep RL that Matters (AAAI'18) | C2 selective seed aggregation | E |
| CAND-04 | A Call for Clarity in Reporting BLEU (WMT'18) | C6 metric tokenization/aggregation | E (sacreBLEU) |
| CAND-05 | ALBERT (ICLR'20) | C5 runtime protocol mismatch | A (author GitHub #37) |
| CAND-06 | Fair GNN Comparison (ICLR'20) | C4 comparator asymmetry | E |
| CAND-07 | RoBERTa | C6 aggregation/batch procedure error | B (fix PR #1360) |
| CAND-08 | CenterNet (CVPR'19) | C5 runtime protocol mismatch | A (author GitHub #7) |

## 5. Blind evaluation result

Pre-fix verdicts (`R1C_PRE_PREDICTIONS_FROZEN.jsonl`): **8/8 FAIL**.
Post-fix verdicts: **8/8 PASS**.
All 8 pairs are correct pre→FAIL / post→PASS differentiations.

| Metric | Value | Threshold | Met |
|--------|-------|-----------|-----|
| NVR (naturalistic violation recall) | **1.000** | ≥ 0.60 | ✓ |
| NPCR (naturalistic paired correction rate) | **1.000** | ≥ 0.70 | ✓ |
| Strongest baseline recall | 0.000 | — | — |
| EpiTrace gain over baselines | **+100 pts** | ≥ 15 pts | ✓ |
| CIA (contract induction accuracy, blind) | **1.000** | ≥ 0.80 | ✓ |
| TOS (trace observability) | **1.000** | — | ✓ |
| Witness semantic/localization accuracy | **1.000** | ≥ 0.70 | ✓ |
| Unsupported FAIL rate | 0/8 | — | ✓ |
| Gold leakage | **NO** | NO | ✓ |

## 6. B3 vs EpiTrace (protocol §16, key comparison)

- **B3 (full raw provenance, no induced contract)**: cannot tell *why* an
  execution is scientifically inadmissible — it only knows what happened.
  Under naturalistic conditions B3 yields **0/8** paired-correction
  detection.
- **EpiTrace**: + induced paper-derived epistemic constraint → **8/8**.
- B3 gap = **1.000**, matching the frozen Stage1b result that
  "raw provenance is inert; the induced epistemic contract is the
  differentiating signal."

## 7. Value-preserving naturalistic cases (flagship, §17)

`R1C_NATURALISTIC_METRICS.json` → `value_preserving_naturalistic_cases = 2`:
- **CAND-04** (BLEU reporting protocol): pre-fix "28.4" vs post-fix
  "26.9" — a ~1.5-pt difference that was the *entire point* of the
  WMT'18 call for clarity, yet the reported final scalar remained in the
  same plausible range in either case; only the *aggregation rule*
  changed.
- **CAND-07** (RoBERTa GLUE aggregation): 90.2 vs 89.9 — a 0.3-pt
  difference with the underlying process (mean vs median, batch
  truncation) being the documented violation.

Both are **naturally occurring**, not synthetically constructed.

## 8. E02 real-world observability (§18)

`r1c/reports/R1C_E02_OBSERVABILITY_REPORT.md`:
- 4 targeted GitHub issue searches executed.
- 0 confirmed public selection-provenance cases found.
- **E02_REAL_WORLD_OBSERVABILITY = LOW.**
- This matches R1-B1's frozen `E02 = TRACE_INSUFFICIENT` result and is
  recorded here as a **scientific finding** (real-world
  test-conditioned-selection leakage typically lacks public
  checkpoint-selection provenance), not as a failure to be "fixed" by
  synthetic construction (which is explicitly forbidden in R1-C §2).

## 9. Novelty boundary (§21)

`r1c/reports/R1C_NOVELTY_UPDATE.md`:
- **NOVELTY_STATUS = CLEAR_CANDIDATE.**
- R1-C introduces no new prior-art collision: the candidate novelty
  ("automatic compilation of scientific protocol statements into
  epistemic execution constraints, detectable in ways invisible to
  provenance-only and value-matching verification") is unchanged, and
  the naturalistic-validation method does not itself claim to be the
  "first provenance system" / "first paper-code checker".

## 10. Final verdict fields

```
STATUS: STRONG_GO
NATURALISTIC_CASES: 8
INDEPENDENT_PAPERS: 8
NATURALISTIC_VIOLATION_RECALL: 1.000
STRONGEST_BASELINE_RECALL: 0.000
EPITRACE_GAIN: +1.000 (100 percentage points)
PAIRED_CORRECTIONS: 8
NPCR: 1.000
CIA: 1.000
TOS: 1.000
WITNESS_ACCURACY: 1.000
E02_REAL_WORLD_STATUS: TRACE_INSUFFICIENT (LOW real-world observability — documented, not faked)
VALUE_PRESERVING_NATURALISTIC_CASES: 2 (CAND-04, CAND-07)
GOLD_LEAKAGE: NO
NOVELTY_STATUS: CLEAR_CANDIDATE
```

## 11. Residual limitations & next steps

- All 8 included cases are drawn from the same 5 deviation families
  (C1, C2, C4, C5, C6); no C3 (scope mismatch) case entered the frozen
  8-case set this round — noted for R1-D candidate expansion.
- 2 value-preserving flagship cases identified, but no additional
  naturalistic VPV case surfaced in this round.
- If a HuggingFace token becomes available, `CAND-18`
  (ClinicalBench KDD'26) can be materialized as a 9th naturalistic case
  with E04/E06/aggregation-semantics coverage.

## 12. Required outputs checklist

All protocol §23 deliverables present under `E:/VForge-R0/r1c/`:

```
reports/R1C_SEARCH_LOG.md                          ✓
results/R1C_CANDIDATE_CASES.csv                    ✓ (30 candidates)
results/R1C_INCLUDED_CASES.csv                     ✓ (8 included)
reports/R1C_CASE_SELECTION_AUDIT.md                 ✓
R1C_CASE_FREEZE.json                                ✓
R1C_SHA256SUMS                                      ✓
contracts_r1c/                                       ✓ (8 blind contracts + manifest, SHA-frozen)
traces_pre/                                          ✓ (8 pre-fix traces)
traces_post/                                         ✓ (8 post-fix traces)
results/R1C_PRE_PREDICTIONS_FROZEN.jsonl            ✓ (frozen before gold reveal)
results/R1C_GOLD_MATCH.jsonl                        ✓
results/R1C_NATURALISTIC_METRICS.json               ✓
results/R1C_PAIRED_CORRECTIONS.csv                  ✓
results/R1C_BASELINES.csv                           ✓
results/R1C_WITNESS_AUDIT.csv                       ✓
reports/R1C_ERROR_ANALYSIS.md                       ✓
reports/R1C_NOVELTY_UPDATE.md                       ✓
reports/R1C_FINAL_REPORT.md                         ✓ (this file)
```
