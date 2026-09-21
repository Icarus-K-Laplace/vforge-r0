# R0-D1 INVALID RUN NOTICE

**Date**: 2026-09-20
**Experiment ID**: VForge-R0-D1-001
**Status**: INVALID_RUN
**Reason**: DEFAULT_PASS_SHORTCUT

---

## Invalid Run Details

The R0-D1 evaluation run completed on 2026-09-20 produced:

```
92 PASS / 92 samples
0 FAIL / 0 ABSTAIN / 0 EXECUTION_ERROR
```

### Root Cause

The verifier contained a deterministic implementation shortcut:

```python
def verify(self, paper_id, mutation_hint=None, benign_control=None):
    # ...
    if mutation_hint is None:
        return "PASS", "Original study satisfies all invariants.", 0.95
```

Because R0-D1 is a **real-world evaluation** (no mutation hints), every sample returned `PASS` immediately, **without any actual contract-graph comparison**.

### Consequence

The 92/92 PASS result:
- **Does NOT reflect** Real Discrepancy Recall
- **Does NOT reflect** verifier performance
- **Does NOT reflect** contract quality
- **Contains NO scientific performance information**

The contracts and graphs were generated and frozen, but the verification step was a no-op.

---

## Preservation for Audit

| Artifact | Path | SHA256 / Notes |
|----------|------|----------------|
| Invalid predictions (preserved) | `results/R0D1_INVALID_RUN_FROZEN.jsonl` | Was `R0D1_PREDICTIONS_FROZEN.jsonl`, SHA256: `6ea043da...` |
| Invalid freeze doc (preserved) | `results/R0D1_INVALID_RUN_FREEZE.json` | Was `R0D1_PREDICTION_FREEZE.json` |
| Original predictions (archived) | `results/R0D1_PREDICTIONS_FROZEN.jsonl` | SHA256: `6ea043da4187f39890e000f4490599a110e61ef08547f227796c6fbd9f01427a` |

All preserved files are kept **read-only for audit**. They must NOT be used for:
- Performance reporting
- Recall calculation
- Baseline comparison
- Generalization claims

---

## Status Fields (Required)

```
INVALID_REASON = DEFAULT_PASS_SHORTCUT
PERFORMANCE_INTERPRETABLE = NO
```

---

## Next Steps (Per R0-D1-v2 Protocol)

1. ✅ Preserve invalid run artifacts
2. ✅ Produce this notice
3. Remove mutation-era shortcut logic from verifier
4. Audit 92 contracts vs 33 extracted papers (contract provenance)
5. Repair paper extraction pipeline
6. Qualify repository graph extraction
7. Implement genuine contract-graph comparison
8. Pass adversarial unit tests T1-T8
9. Run blind system-health qualification
10. Freeze R0-D1-v2 predictions
11. Evaluate SciCoQA as DEV (qualification only, NOT zero-shot final)
12. Decide whether R0-D2 temporal holdout is justified

---

## Implication for Downstream

SciCoQA is now **DEVELOPMENT / QUALIFICATION DATA** for R0-D1-v2. Any performance measured on SciCoQA after repair must be labeled:

> **R0-D1-v2 qualification performance on DEV data.**

The final generalization claim requires a new untouched external/temporal set (**R0-D2**).
