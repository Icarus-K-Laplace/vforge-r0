# PROTOCOL R1-A: TRACE-CONTRACT

## Paper-to-Execution Scientific Verification

**Project**: V-Forge R1-A
**Status**: DRAFT PROTOCOL (pre-execution)
**Supersedes**: generic paper-code verification direction (archived in `reports/R0D_FINAL_ARCHIVED_REPORT.md`)

---

## 0. Research Question

> Can scientific claims be verified against the **execution that actually
> produced the reported result**, rather than merely against the repository
> containing possible implementations?

Static paper-code auditing (R0-D) failed to transfer to real-world data in
current form, and the space is strongly occupied (SciCoQA, CodeCheck, BioCon).
R1-A targets a different verification surface: **runtime execution provenance**.

---

## 1. Primary Hypothesis (H1)

Paper-derived executable scientific contracts, evaluated over runtime
provenance, detect execution-dependent scientific validity violations that
are **informationally inaccessible** to static paper-code verification.

**Falsification condition**: H1 is killed if runtime traces provide no clear
advantage over static baselines on matched pairs.

---

## 2. Core Identifiability Design

Paired executions are constructed so that:

```
Paper_positive      == Paper_negative
Repository_positive  == Repository_negative
code_commit+       == code_commit-
environment_hash+  == environment_hash-
ExecutionTrace+    != ExecutionTrace-
```

- **Positive execution**: follows the paper-declared scientific protocol.
- **Negative execution**: violates a scientifically material protocol
  requirement, but through *what actually executed* — not by inserting an
  obvious source-code bug.

The repository must contain **all legitimate code paths** for both outcomes.
The scientific difference arises from runtime configuration, selection
behaviour, aggregation, and data usage — not from a broken or missing
function.

This same-paper/same-code constraint prevents degeneration into another
paper-code discrepancy benchmark.

---

## 3. Execution-Dependent Fault Families (E01–E06)

Each family has matched clean and invalid executions. The repository contains
all legitimate code paths; only the *executed path* differs.

### E01 SEED_SELECTION_BIAS
- Paper: "mean over N seeds."
- Clean: aggregate = mean over all N declared seeds.
- Invalid: aggregate = best seed (or a convenient subset), reported as the
  "mean."
- Detectable trace fields: `protocol.aggregation_rule`,
  `protocol.aggregation_inputs`, `protocol.declared_seeds`,
  `outputs.reported_value`.

### E02 TEST_CONDITIONED_CHECKPOINT_SELECTION
- Paper: "test set used exclusively for final evaluation; model selection on
  validation."
- Clean: `checkpoint.selection_split = validation`.
- Invalid: `checkpoint.selection_split = test` (checkpoint picked by test
  accuracy).
- Detectable trace fields: `checkpoint.selection_split`,
  `checkpoint.selection_criterion`, `protocol.final_test_split`.

### E03 RUNTIME_CONFIG_MISMATCH
- Paper: declared hyperparameters (lr, epochs, batch size).
- Clean: `hyperparameters` executed == paper-declared.
- Invalid: executed `hyperparameters` silently differ (e.g. different lr,
  fewer epochs) while the paper states the declared values.
- Detectable trace fields: `hyperparameters`, `config_hash`,
  `training_budget.epochs`.

### E04 SUBGROUP_SELECTIVE_REPORTING
- Paper: "we report per-subgroup metrics for all K declared subgroups."
- Clean: `protocol.reported_subgroups` == `protocol.declared_subgroups`.
- Invalid: only favourable subgroups reported (biased subset).
- Detectable trace fields: `protocol.reported_subgroups`,
  `protocol.declared_subgroups`, `evaluation.metrics` (per-subgroup keys).

### E05 PREPROCESS_RUNTIME_FLAG_MISMATCH
- Paper: declared preprocessing (normalisation, augmentation, label handling).
- Clean: `protocol.executed_preprocess` == `protocol.declared_preprocess`.
- Invalid: runtime flag disables/augments preprocessing that the paper says
  was applied (or vice-versa).
- Detectable trace fields: `protocol.declared_preprocess`,
  `protocol.executed_preprocess`, `config_hash`.

### E06 COMPUTE_OR_TRAINING_BUDGET_ASYMMETRY
- Paper: fair comparison with matched compute / training budget across
  methods (declared fairness relation).
- Clean: `comparator_budgets` satisfy the declared relation.
- Invalid: proposed method gets extra epochs/GPU-seconds relative to
  baselines, beyond the declared budget.
- Detectable trace fields: `comparator_budgets[*].epochs`,
  `comparator_budgets[*].gpu_seconds`, `training_budget`.

---

## 4. Scale

- 6 fault families (E01–E06)
- 5 independent studies per family
- **30 paired cases**, **60 executions** total
- Do not scale further until the central effect (TraceContract PSD advantage)
  exists.

---

## 5. Trace Emission

Each execution emits a content-addressed trace conforming to
`TRACE_SCHEMA.json`. Minimum required fields:

```
run_id, code_commit, environment_hash, config_hash,
dataset identifiers/hashes, train/validation/test lineage,
seed, hyperparameters, loss_identity, optimizer, training_budget,
checkpoint candidates, checkpoint selected, selection criterion,
selection dataset, evaluation dataset, evaluation metrics,
aggregation inputs, reported outputs, timestamps,
parent/child run relationships
```

Every output records the upstream entities that contributed to it. Existing
provenance standards (W3C PROV concepts: Entity/Activity/Agent; RO-Crate
structure) are used where practical — we do **not** claim a new provenance
representation.

---

## 6. Claim Contracts

From the paper/protocol, generate machine-readable scientific contracts
before paired traces are evaluated (`CONTRACT_SCHEMA.json`).

Examples:

```
DECLARED_SEEDS == AGGREGATED_SEEDS
SELECTION_SPLIT != FINAL_TEST_SPLIT
DECLARED_PREPROCESS == EXECUTED_PREPROCESS
REPORTED_SUBGROUPS == DECLARED_SUBGROUPS
COMPARATOR_TRAINING_BUDGETS satisfy declared fairness relation
REPORTED_VALUE == declared_aggregation(EXECUTION_RESULTS)
```

**Hard rule**: contracts are generated *before* negative executions are seen.
No fault-specific rules are added after observing the invalid trace.

---

## 7. Baselines

| ID | System | Input |
|----|--------|-------|
| B0 | Paper-only LLM | paper |
| B1 | Paper + repository LLM | paper + repo |
| B2 | Strong static claim-guided paper-code auditor | paper + repo |
| B3 | Paper + repo + static config, **no** runtime provenance | paper + repo + config file |
| TC | **TraceContract** | paper-derived contract + full runtime trace |

Static baselines receive **identical** paper and repository for both members
of a pair, and are **not** given hidden execution labels.

---

## 8. Primary Metric

**Paired Scientific Discrimination (PSD)**:

```
PSD = (# pairs where PASS(clean) AND FAIL(invalid)) / (# valid pairs)
```

Also reported:
- clean acceptance
- invalid detection
- ABSTAIN rate
- false rejection
- evidence localization
- contract coverage

Because static inputs are identical within each pair, any pair-level
discrimination by a static system must come only from explicitly supplied
runtime information. **This property must be audited** (see
`reports/R1A_IDENTIFIABILITY_AUDIT.md`). If a static baseline discriminates a
pair without trace input, the pair is broken and must be rejected.

---

## 9. Secondary Metric

**Violation Localization Accuracy.** For every detected failure the system
must identify:

1. the violated contract predicate
2. the trace entities involved
3. the dependency path
4. the reported output affected

A generic FAIL without a trace witness is rejected.

---

## 10. Ablation

Compare, in order:

1. paper + code
2. paper + code + static config
3. paper + code + final metrics
4. paper + code + full runtime trace
5. paper-derived contract + full runtime trace

This determines which execution information creates the gain. Recorded in
`results/R1A_ABLATIONS.csv`.

---

## 11. GO Criteria (STRONG_GO)

ALL required:
- TraceContract PSD >= 0.80
- best static baseline PSD <= 0.55
- clean acceptance >= 0.90
- at least 5/6 fault families show positive detection
- trace witnesses correctly localize the violating execution dependency in
  >= 0.80 of detected cases
- no fault-family-specific patching after evaluation

## 12. KILL Criteria

KILL if ANY:
- TraceContract cannot reliably distinguish matched execution pairs
- required trace information cannot be captured without unrealistic manual
  annotation
- the scientific contract must encode the known fault rather than being
  derivable from paper claims
- static baselines can solve the task from artifacts that should
  theoretically be execution-independent

---

## 13. Novelty Boundary

Do **not** claim novelty for:
- scientific provenance; runtime traces; W3C PROV; RO-Crate;
- paper-code consistency; claim extraction; static invariant checking.

Candidate novelty (collision audit required before manuscript work):
> claim-conditioned scientific contracts over runtime execution provenance
> for verifying whether the execution that produced a reported scientific
> result actually satisfied the protocol asserted by the paper.

---

## 14. Outputs

| Output | Path |
|--------|------|
| `TRACE_SCHEMA.json` | project root |
| `CONTRACT_SCHEMA.json` | project root |
| `PROTOCOL_R1A.md` | project root (this file) |
| `PAIRED_EXECUTION_FREEZE.json` | project root |
| `traces/` | execution traces |
| `contracts/` | claim contracts |
| `results/R1A_PAIR_RESULTS.jsonl` | pair verdicts |
| `results/R1A_ABLATIONS.csv` | ablation table |
| `reports/R1A_IDENTIFIABILITY_AUDIT.md` | identical-input audit |
| `reports/R1A_LOCALIZATION_AUDIT.md` | localization audit |
| `reports/R1A_FINAL_REPORT.md` | final status |

Final status: **STRONG_GO / WEAK_GO / REDEFINE / KILL**

**Do not start R1-B (real-world trace collection) unless R1-A passes.**
