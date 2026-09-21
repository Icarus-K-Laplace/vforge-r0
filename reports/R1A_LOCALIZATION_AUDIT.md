# R1-A Localization Audit

**Protocol**: R1-A TRACE-CONTRACT
**Date**: 2026-09-20

---

## Requirement

For every detected failure (verdict = FAIL), the system must identify:

1. Contract predicate violated
2. Trace entities involved
3. Dependency path
4. Reported output affected

A generic FAIL without a trace witness is rejected.

---

## Result

```
Invalid cases with FAIL verdict:    29/30
Of those, with complete witness:    29/29 = 1.000
Localization rate (of detected):    1.000  (need >= 0.80)  PASS
```

---

## Per-Family Localization

| Family | Invalid FAIL | Witnesses present | Example witness |
|--------|:-----------:|:-----------------:|-----------------|
| E01 | 5/5 | 5/5 | `P6_AGGREGATION`: declared_seeds → aggregation_rule → reported_value |
| E02 | 5/5 | 5/5 | `P4_SELECTION`: selection_split=test → checkpoint.selected |
| E03 | 4/5 | 4/4 | `P7_HYPERPARAMS`: declared vs executed hyperparameters differ |
| E04 | 5/5 | 5/5 | `P7_SUBGROUPS`: missing subgroups in reported outputs |
| E05 | 5/5 | 5/5 | `P5_PREPROCESS`: executed_preprocess diverges from declared |
| E06 | 5/5 | 5/5 | `P3_BUDGET`: comparator_budgets asymmetric |

The 1 E03 non-FAIL case is a clean-ABSTAIN (coverage below threshold), not
a localization failure.

---

## Witness Structure Example (E01-01 invalid)

```json
{
  "predicate_id": "P6_AGGREGATION",
  "trace_entities": [
    "protocol.declared_seeds",
    "protocol.aggregation_rule",
    "protocol.aggregation_inputs",
    "outputs.reported_value"
  ],
  "dependency_path": "declared_seeds -> aggregation_rule -> reported_value",
  "affected_output": "reported_value",
  "detail": "Declared 5 seeds but aggregation_rule=best, inputs=1"
}
```

---

## Verdict

```
LOCALIZATION_AUDIT = PASS (1.000 of detected cases localized)
```
