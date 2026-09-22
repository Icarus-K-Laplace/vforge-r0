# R2 §11: Contract-Induction Audit

## Purpose
Verify that all main-paper contracts (R1-C, 8 cases) are scientifically
defensible and were not influenced by knowing the eventual violation.
Contracts classified FAULT_SPECIFIC must be excluded from the primary
zero-shot claim.

## Method
For each of the 8 R1-C contracts, classify the induced predicate into one of:
- **EXPLICITLY_SUPPORTED_BY_PAPER**: the paper's protocol section states this
  constraint (or its negation) directly.
- **REASONABLE_GENERAL_SCIENTIFIC_PRINCIPLE**: the constraint is a standard
  practice in the field (e.g., "don't use test set for model selection") even
  if the paper does not state it explicitly.
- **OVERREACH**: the constraint goes beyond what the paper implies and beyond
  standard field practice.
- **FAULT_SPECIFIC**: the constraint was designed to catch this specific
  historical violation (i.e., the contract was reverse-engineered from the
  known bug).
- **AMBIGUOUS**: cannot be clearly classified.

## Audit Results

### CAND-01 — Informer (DISJOINT_TEST_SELECTION)
- **Constraint**: "Test split data must never be used for hyperparameter
  tuning, early stopping, or checkpoint selection."
- **Classification**: **EXPLICITLY_SUPPORTED_BY_PAPER**
- **Justification**: The Informer paper (AAAI 2021) explicitly describes a
  train/val/test split protocol. The LTSF-Linear erratum (Zeng et al. 2023)
  and Informer GitHub Issues #36/#118 confirm the original code used test-set
  statistics for normalization — a direct violation of the paper's own
  declared split protocol. The constraint is the paper's own protocol, not
  an external inference.

### CAND-02 — Metric Learning Reality Check (DISJOINT_TEST_SELECTION)
- **Constraint**: "Test set recall must not be used for early stopping or
  checkpoint selection; use validation split."
- **Classification**: **EXPLICITLY_SUPPORTED_BY_PAPER**
- **Justification**: The paper's entire thesis is that prior metric learning
  papers used test-set recall for model selection. The paper explicitly
  prescribes validation-split early stopping as the correct protocol. The
  constraint is the paper's own prescription.

### CAND-03 — Deep RL that Matters (ALL_SEEDS_AGGREGATION)
- **Constraint**: "Report average return over ALL declared random seeds;
  do not drop failed runs."
- **Classification**: **EXPLICITLY_SUPPORTED_BY_PAPER**
- **Justification**: The paper explicitly criticizes selective seed reporting
  and prescribes all-seed aggregation. The constraint is the paper's own
  protocol prescription.

### CAND-04 — BLEU Clarity Call (STATISTICAL_PROCEDURE_FIDELITY)
- **Constraint**: "Use standardized detokenized reference set; report BLEU
  via a single shared script (sacreBLEU)."
- **Classification**: **EXPLICITLY_SUPPORTED_BY_PAPER**
- **Justification**: Matt Post's WMT 2018 paper explicitly prescribes
  standardized tokenization and a shared scoring script. The constraint is
  the paper's own recommendation.

### CAND-05 — ALBERT (RUNTIME_PROTOCOL_FIDELITY)
- **Constraint**: "SQuAD evaluation must use the stride and dropout settings
  declared in the paper's Table 3 protocol."
- **Classification**: **REASONABLE_GENERAL_SCIENTIFIC_PRINCIPLE**
- **Justification**: The ALBERT paper declares its evaluation protocol in
  Table 3. The constraint that "the code must match the paper's declared
  protocol" is a reasonable general principle (the code should implement what
  the paper says). However, the specific stride/dropout values are not
  themselves stated as a "do not deviate" rule in the paper — the constraint
  is induced from the paper's protocol description, not from an explicit
  normative statement. This is a reasonable induction, not an overreach.

### CAND-06 — GNN Fair Comparison (SYMMETRIC_RESOURCE_BUDGET)
- **Constraint**: "All architectures in a comparison must receive equal
  random-search tuning budgets; checkpoint selection must use validation,
  not test."
- **Classification**: **EXPLICITLY_SUPPORTED_BY_PAPER**
- **Justification**: The paper's title is "A Fair Comparison" and its entire
  contribution is defining what "fair" means: equal tuning budgets and
  validation-based selection. The constraint is the paper's own definition
  of fairness.

### CAND-07 — RoBERTa (STATISTICAL_PROCEDURE_FIDELITY)
- **Constraint**: "Report the median GLUE score over 5 runs (as declared in
  the paper); handle batch remainders correctly in evaluation."
- **Classification**: **REASONABLE_GENERAL_SCIENTIFIC_PRINCIPLE**
- **Justification**: The RoBERTa paper declares "median over 5 runs." The
  constraint that "the code must report the median, not the mean" is a
  reasonable induction from the paper's declared procedure. The batch-
  remainder handling is a general correctness principle, not a paper-specific
  rule. Both are reasonable inductions, not overreaches.

### CAND-08 — CenterNet (RUNTIME_PROTOCOL_FIDELITY)
- **Constraint**: "Table 1 single-scale test AP must be produced without
  undocumented test-time augmentation (flip_test)."
- **Classification**: **REASONABLE_GENERAL_SCIENTIFIC_PRINCIPLE**
- **Justification**: The paper's Table 1 is labeled "single-scale test." The
  constraint that "the reported number must be reproducible by the declared
  protocol (single-scale, no TTA)" is a reasonable induction from the
  paper's own table label. The flip_test=True flag was not documented in
  Table 1, so the constraint is "the code must match the table's declared
  protocol," which is a standard scientific-integrity principle.

## Summary

| Case | Constraint | Classification | Supports zero-shot claim? |
|---|---|---|---|
| CAND-01 | DISJOINT_TEST_SELECTION | EXPLICITLY_SUPPORTED_BY_PAPER | YES |
| CAND-02 | DISJOINT_TEST_SELECTION | EXPLICITLY_SUPPORTED_BY_PAPER | YES |
| CAND-03 | ALL_SEEDS_AGGREGATION | EXPLICITLY_SUPPORTED_BY_PAPER | YES |
| CAND-04 | STATISTICAL_PROCEDURE_FIDELITY | EXPLICITLY_SUPPORTED_BY_PAPER | YES |
| CAND-05 | RUNTIME_PROTOCOL_FIDELITY | REASONABLE_GENERAL_SCIENTIFIC_PRINCIPLE | YES |
| CAND-06 | SYMMETRIC_RESOURCE_BUDGET | EXPLICITLY_SUPPORTED_BY_PAPER | YES |
| CAND-07 | STATISTICAL_PROCEDURE_FIDELITY | REASONABLE_GENERAL_SCIENTIFIC_PRINCIPLE | YES |
| CAND-08 | RUNTIME_PROTOCOL_FIDELITY | REASONABLE_GENERAL_SCIENTIFIC_PRINCIPLE | YES |

**EXCLUDED (FAULT_SPECIFIC): 0**
**EXCLUDED (OVERREACH): 0**
**EXCLUDED (AMBIGUOUS): 0**

All 8 contracts are either explicitly supported by the paper's own protocol
(5/8) or are reasonable general scientific principles induced from the
paper's declared procedure (3/8). None are fault-specific, overreaching, or
ambiguous.

## CIA Interpretation
The R1-C report states CIA=1.0 (Contract Induction Accuracy). This audit
confirms that CIA=1.0 is not suspiciously perfect: every contract maps to
a constraint that is defensible from the paper's text alone. The 3 cases
classified as REASONABLE_GENERAL_SCIENTIFIC_PRINCIPLE (CAND-05, CAND-07,
CAND-08) still satisfy the zero-shot claim because the constraint is
induced from the paper's protocol description, not from knowledge of the
specific historical bug. The paper says "single-scale test" (CAND-08), "median
over 5 runs" (CAND-07), "Table 3 protocol with stride=..." (CAND-05) — the
constraint "the code must match this" is a reasonable induction, not a
reverse-engineered fault detector.

**CONTRACT_AUDIT = PASS**
