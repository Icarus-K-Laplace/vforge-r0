# R0-D Universal Principles Ontology (Frozen)

Frozen before SciCoQA R0-D1-v2 evaluation. These are abstract scientific
validity principles. They are NOT paper-specific requirements.

Paper-induced contracts derive concrete requirements FROM ACTUAL PAPER TEXT.
Universal principles may motivate the type of requirement, but the specific
values and conditions must come from the paper.

---

## P1_INDEPENDENCE
**Statement**: The sets of data used for training, validation, and final
evaluation must be disjoint where the paper claims independent evaluation.

**Observable evidence**: Split/holdout nodes; disjoint ID sets; data
partition records.

**Failure mode**: Test data used for training, validation, or model selection.

---

## P2_NO_LEAKAGE
**Statement**: No information from the evaluation set may influence model
parameters, architecture, or hyperparameter selection reported in results.

**Observable evidence**: Selection procedure records; checkpoint provenance.

**Failure mode**: Hyperparameters tuned on test set; early stopping on test metrics.

---

## P3_SYMMETRY
**Statement**: When comparing methods, all methods must be evaluated under
equivalent conditions (same data splits, same compute budget, same
evaluation protocol) unless a specific asymmetry is declared.

**Observable evidence**: Config parity; identical data splits across comparisons.

**Failure mode**: One method gets extra data or compute; different split sizes.

---

## P4_SELECTION_SEPARATION
**Statement**: Model selection (checkpoint, architecture, hyperparameters)
must be performed on data that is not the final evaluation set.

**Observable evidence**: Separate SELECT and EVALUATE nodes; selection source
attribute must not be "test".

**Failure mode**: Best checkpoint selected using test-set accuracy.

---

## P5_DETERMINISM_OR_SEEDS
**Statement**: If stochastic methods are used and a single number is reported,
the paper must declare the number of random seeds and the aggregation rule
(mean, median, best).

**Observable evidence**: Seed count attribute; aggregation rule attribute.

**Failure mode**: Best seed reported as "the result"; undefined seed count.

---

## P6_AGGREGATION_FIDELITY
**Statement**: The reported aggregate value must correspond to the declared
aggregation rule applied to the declared seed population.

**Observable evidence**: aggregation_rule attribute == declared rule; seed_count
attribute == declared count.

**Failure mode**: Paper says "mean over 5 seeds", code reports best seed.

---

## P7_EVIDENCE_CLOSURE
**Statement**: Every quantitative claim in the paper must be traceable to
a reproducible computation in the code repository.

**Observable evidence**: Metric computation nodes; data file references.

**Failure mode**: Reported number not computed anywhere in the codebase.

---

## P8_STATISTICAL_SUFFICIENCY
**Statement**: Statistical comparisons (A > B, p < alpha) must be supported
by an appropriate test and sample size declared in the paper.

**Observable evidence**: Test statistic computation; declared sample size.

**Failure mode**: Claim of "significant improvement" without statistical test.

---

## Frozen Metadata

```
ontology_id: SCIENTIFIC_VALIDITY_ONTOLOGY_V1
frozen: 2026-09-20
n_principles: 8
sha256_note: Frozen before R0-D1-v2 prediction freeze
```
