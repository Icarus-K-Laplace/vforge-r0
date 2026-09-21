# R1-B1 Trace Source Audit

**Protocol**: R1-B1 — Real-Trace Value-Preserving Epistemic Conformance
**Project**: V-Forge TRACE-CONTRACT
**Date**: 2026-09-20
**Stage**: 1 (4 confirmed sources; target >=12 paired cases)

---

## Inclusion Criteria (per protocol §3)

A paper enters R1-B1 only if:
1. ✅ a public scientific paper exists
2. ✅ public source code exists
3. ✅ authentic experiment logs / run metadata exist
4. ✅ the runs connect to a specific quantitative paper claim / table / figure
5. ✅ at least one epistemically relevant runtime attribute is observable
6. ✅ no manual reconstruction of the run outcome is necessary

---

## Confirmed Sources (2 papers with genuine public W&B run data)

### Source 1: ViewBatchModel (CVPR'25)

- **Paper**: arXiv 2503.18371, Kang et al. (Ajou / KAIST)
- **Repository**: `hankyul2/ViewBatchModel` (26 stars, public)
- **W&B entity/project**: `gregor99/view_batch_model` (public, **15 runs**)
- **Claim**: Table 6 — ablation over (aug_repeat, flag) × 3 seeds (1993/1996/1997)
- **Authentic run metadata recovered**:
  - `display_name` encodes (aug_repeat, flag, seed): `icarl_r4_ssl_s1993`
  - `summaryMetrics` exposes `RESULT_class_acc_0..4`, `RESULT_task_acc_0..4`, `RESULT_class_mean_accs`, `RESULT_task_mean_accs`
  - Paper protocol: "we run every method three times with different random seeds ... report the mean and variance of three experimental results"
- **Family support**:
  - **E01** (selective seed aggregation): ✅ full 3-seed groups → 5 pairs
  - **E04** (selective task-subgroup reporting): ✅ 5 tasks → 5 pairs
  - **E02** (checkpoint-selection leakage): ❌ not observable (no selection-split provenance in W&B summaryMetrics)
  - **E06** (comparator resource asymmetry): ❌ not observable (no per-run GPU-seconds/budget field in summaryMetrics)

### Source 2: Revisiting Deep Metric Learning (ICML 2020)

- **Paper**: arXiv 2002.08473, Roth et al.
- **Repository**: `Confusezius/Revisiting_Deep_Metric_Learning_PyTorch` (344 stars, public)
- **W&B entity/project**: `confusezius/RevisitDML` (public, **200 runs**)
- **Claim**: Tables 1-3 — per-(dataset, method) seed-group aggregation
- **Authentic run metadata recovered**:
  - `display_name` encodes (dataset, method, seed): `CARS_NPair_s3`
  - 48 (dataset, method) groups; 5-seed groups for NPair/ArcFace_2/Histogram_3 etc., 2-seed groups for others
  - `Result_Evaluations.py` in the repo defines the exact aggregation (mean ± std over group)
- **Family support**:
  - **E01** (selective seed aggregation): ✅ → 38 pairs (5-seed and 3-seed groups)
  - **E02 / E04 / E06**: ❌ not observable in W&B summaryMetrics

---

## Sources NOT entered (insufficient trace observability)

| Named source | Status | Reason |
|-------------|:------:|--------|
| Hivemind multi-cloud | NOT FOUND | No public repo / W&B with paper-linked public logs located |
| TopoBenchmark | NOT FOUND | No public W&B Table-1 logs located |
| Additional papers (4) | NOT ENTERED | Insufficient public run metadata |

The two confirmed sources already yield **48 claim-level paired cases** (target was ≥12), so no lower-tier sources were admitted.

---

## E02 Trace Insufficiency (documented, not invented)

Per protocol §11/§19, E02 (evaluation-to-selection leakage) requires observing:
- checkpoint candidates,
- the selection criterion (which split drove selection),
- the selected checkpoint id.

Neither ViewBatchModel nor RevisitDML W&B `summaryMetrics` expose these fields. Both expose only per-run `RESULT_*_acc_*` scalars and test discriminative metrics. Therefore E02 pairs are **not** constructed from these sources; the insufficiency is recorded in `traces_real/E02_TRACE_INSUFFICIENCY_RECORD.json` and `results/R1B1_E02_TOS_RECORD.json` rather than invented.

```
E02_STATUS = TRACE_INSUFFICIENT (documented)
```

---

## Verdict

```
CONFIRMED_SOURCES = 2
CONFIRMED_PAIRS   = 48   (E01=43, E04=5)
E01_PAIRS         = 43
E04_PAIRS         = 5
E02_PAIRS         = 0    (TRACE_INSUFFICIENT)
E06_PAIRS         = 0    (not observable in these sources)
```

Trace source audit passes the Stage-1 inclusion threshold.
