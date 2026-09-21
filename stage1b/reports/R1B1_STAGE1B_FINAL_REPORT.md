# R1-B1 Stage1b Source Audit + Final Report

**Protocol**: R1-B1 — Real-Trace Value-Preserving Epistemic Conformance
**Stage**: 1b (independent, built on frozen Stage1 WEAK_GO)
**Date**: 2026-09-20
**Status**: **STRONG_GO** (upgraded from Stage1 WEAK_GO)

---

## 1. Freeze Integrity
- Stage1 WEAK_GO frozen at `reports/R1B1_STAGE1_FREEZE_MANIFEST.json` (SHA `baeb2337...`), verified intact via `verify_stage1_freeze.py` before Stage1b began. Stage1 files were NOT modified.
- Stage1b is fully independent: `stage1b/{contracts_freeze, traces_real, results, papers, external}`.
- Stage1b results frozen at `stage1b/results/STAGE1B_FREEZE_MANIFEST.json` (SHA `5371376a...`).

## 2. Source Audit (independent public traces)
| Source | Venue | Public trace | Pairs |
|---|---|---|---|
| ViewBatchModel | CVPR'25 | W&B public runs | 5 (Stage1, frozen) |
| RevisitDML | ICML'20 | W&B public runs (200) | 38 (Stage1, frozen) |
| **DiffSynth** | **CVPRW 2025** | **GitHub CSV traces (84 rows)** | 27 (Stage1b) |
| **Delta Attention** | **arXiv 2605.18855** | **W&B public runs (WANDB_RUNS.md)** | 5 (Stage1b) |

Total: **4 independent papers**, 80 pairs.

## 3. Priority-source status
- **DiffSynth (CVPRW 2025)**: E01/E04/E06 all constructed from authentic run-result CSVs + paper text. 27 pairs.
- **Delta Attention Residuals**: used as the **4th source** (triggered because E06 was only stable on 1 paper before it). E06 comparator-resource-symmetry + E01 cross-method aggregation from W&B mappings. 5 pairs.
- **ClinicalBench (KDD 2026)**: `BLOCKED_ON_AUTH` — its KDD'26 result dataset (`canyuchen/clinicalbench-results`) is gated on HuggingFace and returned HTTP 401 (no token available in this environment). **Not fabricated.** Contracts were still compiled paper-only (`CB_*`) and frozen, but no trace pairs were built because the underlying runs are not publicly reachable without auth. This is the honest documented gap.

## 4. Contract Discipline
- All 8 Stage1b contracts compiled **from paper text/method/appendix only**, before any run outcome was read. SHA256 frozen in `contracts_freeze/STAGE1B_FREEZE_MANIFEST.json`.
- CIA = 8/8 SUPPORTED_BY_PAPER.

## 5. Constraint classes (source-level)
| Class | Stable papers | Stable across ≥2? |
|---|---|---|
| E01 | RevisitDML, ViewBatchModel, DiffSynth | ✓ (3) |
| E04 | ViewBatchModel, DiffSynth | ✓ (2) |
| E06 | DiffSynth, Delta Attention | ✓ (2) |

## 6. Cross-paper metrics (primary unit = paper × constraint-class)
- **PSD = 1.000** (EpiTrace) vs **B3 provenance-only = 0.000** → gap = **1.000**
- **Clean acceptance = 1.000**
- **VPVD = 1.000** (all value-preserving violations detected)
- **Witness accuracy = 1.000**
- **B4 result-matching separates = 0/80** → `RESULT_MATCHING_INSUFFICIENCY = True`

## 7. STRONG_GO gate
```
4_papers                       PASS (4)
3_classes_stable_across_2paper PASS (E01,E04,E06)
psd_ge_080                     PASS (1.000)
b3_gap_ge_015                  PASS (1.000)
vpvd_ge_075                    PASS (1.000)
clean_ge_085                   PASS (1.000)
witness_ge_080                 PASS (1.000)
──────────────────────────────────────
STRONG_GO                      TRUE
```

## 8. Verdict
```
STAGE1_STATUS = WEAK_GO   (frozen, 2 papers)
STAGE1B_STATUS = STRONG_GO (4 papers, 3 stable classes)
FINAL_R1B1_STATUS = STRONG_GO
E02_STATUS = TRACE_INSUFFICIENT (no selection provenance in any public source — not reconstructed)
CLINICALBENCH_STATUS = BLOCKED_ON_AUTH (gated HF dataset; contracts frozen, no trace pairs)
```

## 9. Residual limitations
- **ClinicalBench trace data** is inaccessible without HF auth; the KDD'26 source contributes a *frozen contract* but no evaluated pairs. Its E04/E06/aggregation-semantics pairs would need a user-provided `HF_TOKEN` to materialize.
- E06 on Delta Attention is a **documentation-level** pair (budget symmetry flag), not a value-shifting counterfactual — valid for the class but lower observational depth than DiffSynth's E06.
- E02 remains `TRACE_INSUFFICIENT` across all four sources (documented, not faked).

## 10. Next step (optional, R1-B2)
- If the user supplies a HuggingFace token, ClinicalBench KDD'26 trace pairs can be materialized to add a 5th paper and deepen E04/E06.
- Otherwise Stage1b is a complete, self-contained STRONG_GO on 4 independent papers.