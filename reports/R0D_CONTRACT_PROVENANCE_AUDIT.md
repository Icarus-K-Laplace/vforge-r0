# R0-D Contract Provenance Audit

**Date**: 2026-09-20
**Experiment**: VForge-R0-D1 (INVALID RUN, preserved for audit)

---

## Key Numbers

| Metric | Count |
|--------|-------|
| Total samples | 92 |
| Papers extracted successfully | 33 |
| Contracts generated | 92 |
| Graphs extracted | 76 |

## Discrepancy Analysis

**59 contracts** were generated for papers where **no text was extracted**.

These contracts fall into two categories:

### 1. Universal-Only Contracts (59 samples)

For papers where extraction failed, the system generated a default universal
principle contract with `source_span: "global"` — meaning **no paper evidence**.

Example:
```json
{
  "invariant_id": "INV_001",
  "source_principle": "P6_AGGREGATION_FIDELITY",
  "natural_language": "Reported metrics must faithfully represent computations",
  "source_paper_span": "global"
}
```

This is **INVALID** per R0-D1-v2 protocol:

> A contract without a valid source span from successfully extracted paper text
> is: INVALID_CONTRACT, unless explicitly classified as a pre-registered
> universal principle.

These 59 contracts should be **INVALID_CONTRACT** → ABSTAIN, not PASS.

### 2. Paper-Derived Contracts (33 samples)

For the 33 successfully extracted papers, contracts were derived from actual
paper text. These are the only valid paper-derived contracts.

---

## Required Audit Table

Generated: `results/R0D_CONTRACT_PROVENANCE_AUDIT.csv`

| paper_id | paper_extracted | contract_exists | paper_derived_contract_count | universal_rule_count | invalid_contract_count | status |
|----------|:---------------:|:---------------:|:---------------------------:|:--------------------:|:----------------------:|--------|
| 33 papers | YES | YES | [varies] | 0 | 0 | VALID_PAPER_DERIVED |
| 59 papers | NO | YES | 0 | 1 | 1 | INVALID_CONTRACT |

---

## Verdict

```
CONTRACT_PROVENANCE_VALID = 33/92 (36%)
CONTRACT_PROVENANCE_INVALID = 59/92 (64%)
STATUS = REPAIR_REQUIRED
```

Before R0-D1-v2 evaluation:
1. Separate universal ontology (P1-P8) from paper-induced contracts
2. Mark 59 contracts without paper evidence as INVALID_CONTRACT
3. These 59 samples → ABSTAIN, not PASS
