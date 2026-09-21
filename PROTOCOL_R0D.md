# V-Forge R0-D Protocol

## 1. Research Question

Can paper-only normative invariant induction detect real scientific discrepancies without exposure to benchmark labels?

## 2. Architecture

### Two-Channel Isolation

**Normative Channel** (Input: Paper text only)
- Extract claim structure
- Induce invariants from domain principles
- Generate Normative Contract (frozen, hashed)

**Observational Channel** (Input: Repository code)
- Extract protocol graph from code
- Document data flow, dependencies
- Generate Protocol Graph (frozen, hashed)

**Verification** (Compare channels)
- Check invariants against observed graph
- Output: PASS / FAIL / ABSTAIN / EXECUTION_ERROR

### Forbidden Inputs to SI-D
- Discrepancy descriptions
- Gold labels
- GitHub issue text
- Relevant code annotations
- Fix commit identity
- Benchmark model outputs

## 3. Data Flow

```
Paper Text → [Normative Inducer] → Normative Contract (frozen)
                                                              ↓
Repository → [Graph Extractor] → Protocol Graph (frozen)      ↓
                                                              ↓
                                              [Verifier] Compare → Verdict (frozen)
                                                              ↓
                                              [Evaluator] Only NOW reveal gold
```

## 4. Invariant Induction Rules

### Allowed Sources
1. Paper text spans (direct quotes)
2. Pre-registered ontology principles (P1-P8)
3. General scientific validity conventions

### Forbidden Actions
1. Post-hoc invariant addition after seeing failures
2. Benchmark-specific hardcoding
3. Using discrepancy descriptions for induction

## 5. Evaluation Protocol

### Phase 1: Development
- Build system on synthetic/mock data
- Freeze ontology and induction rules
- Complete leakage audit

### Phase 2: Prediction
- Load papers (text only)
- Induce invariants
- Extract graphs from repos
- Generate all predictions
- Hash and freeze prediction ledger

### Phase 3: Evaluation
- Reveal gold labels
- Compute metrics
- Compare to baselines
- Analyze errors

## 6. Metrics

### Primary
- Real Discrepancy Recall (RDR)
- Paired Counterfactual Rate (PCR)

### Secondary
- Coverage
- Abstention rate
- Unsupported-PASS rate
- Per-category recall
- File localization (Top-1, Top-3)

## 7. Baselines

| ID | System | Description |
|----|--------|-------------|
| B0 | Direct LLM | Paper text → LLM judge |
| B1 | Static Rubric | Hand-coded checklist |
| B2 | Executable | Run code, check outputs |
| B3 | SciCoQA Model | Published predictions |
| SI-C | Previous Invariant | R0-C system (researcher-designed) |
| SI-D | Paper-Only Invariant | This work (paper-induced) |

## 8. Ablations

| Variant | Components | Purpose |
|---------|------------|---------|
| A1 | Paper + LLM | Direct prompting baseline |
| A2 | Paper + Static Principles | Ontology-only induction |
| A3 | Paper invariants only | Without graph |
| A4 | Graph only | Without paper |
| A5 | Full SI-D | Complete system |

## 9. GO/KILL Criteria

### STRONG_GO
1. SI-D exceeds B3 by ≥10pp on real discrepancy recall
2. Matched-control acceptance ≥0.85
3. Unsupported-PASS rate < 0.10
4. Detection across ≥3 discrepancy categories
5. Not explained by single paper
6. No leakage
7. Ablation shows paper-derived invariants add value

### WEAK_GO
- Some real-error signal but narrow coverage

### REDEFINE
- Works only for specific protocol classes

### KILL_GENERAL_CLAIM
- Controlled mutation performance doesn't transfer to real errors

## 10. Required Outputs

- `PROTOCOL_R0D.md` (this file)
- `SCIENTIFIC_VALIDITY_ONTOLOGY_V1.json`
- `R0D_FREEZE.json`
- `R0D_SHA256SUMS`
- `reports/R0D_LEAKAGE_AUDIT.md`
- `contracts/*.json`
- `graphs/*.json`
- `results/r0d_predictions_frozen.jsonl`
- `results/r0d_external_metrics.json`
- `results/r0d_localization.csv`
- `results/r0d_paired_counterfactuals.csv`
- `reports/R0D_ERROR_ANALYSIS.md`
- `reports/R0D_FINAL_REPORT.md`

## 11. Timeline

| Phase | Status | Notes |
|-------|--------|-------|
| Framework development | ✅ Complete | Mock data tested |
| Leakage audit | ✅ Complete | Pre-evaluation checks passed |
| SciCoQA access | ⏳ Pending | Awaiting dataset download |
| Frozen evaluation | ⏳ Pending | Will run after data access |
| Report generation | ⏳ Pending | After evaluation |

---

**Protocol Version**: R0-D-v1  
**Date**: 2026-09-20  
**Status**: Framework Ready, Awaiting Real Data
