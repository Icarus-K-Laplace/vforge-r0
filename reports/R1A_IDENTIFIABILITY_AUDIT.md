# R1-A Identifiability Audit

**Protocol**: R1-A TRACE-CONTRACT
**Date**: 2026-09-20
**Scope**: All 30 paired executions (60 traces)

---

## Core Constraint

For every pair:

```
Paper_positive      == Paper_negative
Repository_positive  == Repository_negative
code_commit+       == code_commit-
environment_hash+  == environment_hash-
ExecutionTrace+    != ExecutionTrace-
```

The scientific difference arises from *what actually executed*, not from
source-code modifications.

---

## Audit Results

### Identifiability Holds

```
Identifiability holds (shared fields equal): 30/30
Trace differs within pair:                   30/30
```

All 30 pairs satisfy the core identifiability constraint. Execution-independent
fields (`code_commit`, `environment_hash`, `loss_identity`, `optimizer`,
`hyperparameters`, `lineage`) are identical within each pair. Only runtime
execution fields differ.

### Per-Family Check

| Family | Pairs | Identifiability | Notes |
|--------|:-----:|:--------------:|-------|
| E01 SEED_SELECTION_BIAS | 5 | 5/5 | Only `aggregation_rule` + `aggregation_inputs` differ |
| E02 TEST_CONDITIONED_CHECKPOINT | 5 | 5/5 | Only `checkpoint.selection_split` + `selection_criterion` differ |
| E03 RUNTIME_CONFIG_MISMATCH | 5 | 5/5 | Only `executed_hyperparameters` + `config_hash` differ |
| E04 SUBGROUP_SELECTIVE_REPORTING | 5 | 5/5 | Only `reported_subgroups` differs |
| E05 PREPROCESS_RUNTIME_FLAG | 5 | 5/5 | Only `executed_preprocess` + `config_hash` differ |
| E06 BUDGET_ASYMMETRY | 5 | 5/5 | Only `comparator_budgets` differs |

---

## Static Baseline Identical-Input Audit

The protocol requires: "Because static inputs are identical within each pair,
any pair-level discrimination by static systems must come only from explicitly
supplied runtime information."

### Result

| Baseline | Pair-correct | Identical-input pairs |
|----------|:------------:|:---------------------:|
| B0 paper-only | 0/30 | 30/30 ✅ |
| B1 paper+repo | 0/30 | 30/30 ✅ |
| B2 static auditor | 0/30 | 30/30 ✅ |
| B3 +static config | 0/30 | 20/30 ⚠️ |

**B3 exception (10 pairs)**: For E03 (RUNTIME_CONFIG_MISMATCH) and E05
(PREPROCESS_RUNTIME_FLAG_MISMATCH), the runtime config hash differs between
clean and invalid runs. B3 includes `config_hash` in its static profile, so
its inputs are *not* byte-identical for these 10 pairs.

**However**, B3 still returns PASS for both clean and invalid in all 10 cases
(0 pair-correct). The config hash difference is visible to B3 but B3 does not
interpret it as a scientific violation — it only checks structural completeness.
The *semantic* violation (which aggregation rule was used, which split drove
selection, which subgroups were reported) is invisible to B3 because it does
not receive the full runtime trace.

**Conclusion**: No static baseline discriminates any pair. B3's 10
non-identical-input cases are a known, documented limitation (config_hash
leaks the runtime change into the static profile) but do not produce
pair-correct verdicts. The core claim holds: **pair-level scientific
discrimination requires the full runtime trace, not static artifacts.**

```
STATIC_BASELINE_PAIR_DISCRIMINATION = 0/30 (all baselines)
STATIC_SYSTEMS_INFORMATIONALLY_INACCESSIBLE = CONFIRMED
```

---

## Verdict

```
IDENTIFIABILITY = PASS
STATIC_BASELINE_AUDIT = PASS (with documented B3 config_hash caveat)
```
