# R1-B1 Witness Audit

**Protocol**: R1-B1 — Real-Trace Value-Preserving Epistemic Conformance
**Date**: 2026-09-20
**Scope**: All 48 real-trace paired cases (43 E01 + 5 E04)

---

## Requirement

For every detected failure (verdict = FAIL), EpiTrace must produce a trace
witness identifying:

1. Contract predicate violated
2. Trace entities involved
3. Dependency path
4. Reported output affected

A generic FAIL without a trace witness is rejected.

---

## Result

```
FAIL cases:              48/48
With complete witness:   48/48 = 1.000
Missing witness:         0
Witness accuracy:        1.000  (need >= 0.80)  PASS
```

---

## Per-Family Witness Structure

| Family | FAIL count | Witnesses present | Predicate | Dependency path |
|--------|:----------:|:-----------------:|-----------|-----------------|
| E01 | 43 | 43 | `E01_REPORTED_RUN_SET` | `declared_seeds -> aggregation_inputs -> reported_value` |
| E04 | 5 | 5 | `E04_REPORTED_SCOPE` | `declared_subgroups -> reported_subgroups -> reported_value` |

---

## Sample Witness (E01, ViewBatchModel r4 hard_aug)

```json
{
  "predicate_id": "E01_REPORTED_RUN_SET",
  "trace_entities": [
    "protocol.declared_seeds",
    "outputs.reported_value.upstream_runs"
  ],
  "dependency_path": "declared_seeds -> aggregation_inputs -> reported_value",
  "affected_output": "reported_value",
  "detail": "Declared 3 seeds but aggregation used 2 inputs"
}
```

## Sample Witness (E04, ViewBatchModel r4 none)

```json
{
  "predicate_id": "E04_REPORTED_SCOPE",
  "trace_entities": [
    "protocol.declared_subgroups",
    "protocol.reported_subgroups"
  ],
  "dependency_path": "declared_subgroups -> reported_subgroups -> reported_value",
  "affected_output": "reported_value (selective subgroup scope)",
  "detail": "Reported scope omits subgroups [2, 1]"
}
```

---

## Real-Data Verification

The witnesses reference **authentic** W&B run data. For ViewBatchModel
`r4 hard_aug`:

- Raw W&B `RESULT_class_mean_accs` for seeds 1993/1996/1997:
  `[67.22, 67.87, 66.38]` (real values, not fabricated).
- T+ faithful mean (all 3 seeds): `67.1567`.
- T- selective subset (best-2, seeds 1996+1997): `67.1250`.
- VPS = `|67.1250 - 67.1567| / σ_clean = 0.0519` → value-preserving.

The witness correctly localizes the violation to the seed-set fidelity
predicate, not to a value mismatch (which is preserved).

---

## Verdict

```
WITNESS_AUDIT = PASS (1.000 of detected cases localized)
```
