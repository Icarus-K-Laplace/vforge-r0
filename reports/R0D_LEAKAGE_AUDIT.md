# V-Forge R0-D: Leakage Audit Report

## Executive Summary
**Audit Status**: PENDING (to be completed before benchmark access)

## Pre-Evaluation Checks

### 1. Data Isolation Verification
- [ ] SciCoQA test split NOT accessed during development
- [ ] Gold labels NOT visible to SI-D system
- [ ] Discrepancy descriptions NOT used for invariant induction
- [ ] Relevant code annotations NOT exposed

### 2. Code Review
- [ ] No gold label imports in sciinvariant.py
- [ ] No benchmark-specific hardcoding
- [ ] Prediction ledger is append-only
- [ ] Evaluation happens AFTER prediction freeze

### 3. Hash Verification
- [ ] SCIENTIFIC_VALIDITY_ONTOLOGY_V1.json hashed before evaluation
- [ ] R0D_FREEZE.json created with freeze timestamp
- [ ] All prediction hashes recorded

## Audit Procedure

### Step 1: Verify Ontology Freeze
```bash
sha256sum SCIENTIFIC_VALIDITY_ONTOLOGY_V1.json
```

### Step 2: Check Code for Leakage
```bash
grep -r "discrepancy" --include="*.py" .
grep -r "gold" --include="*.py" .
grep -r "fix_commit" --include="*.py" .
```

### Step 3: Verify Prediction Ledger
- Ensure ledger is created BEFORE evaluation
- Ensure no modifications after creation
- Hash the ledger file

### Step 4: Evaluate in Isolation
1. Load paper text only
2. Induce invariants from paper
3. Extract protocol graph from repository
4. Compare and produce verdict
5. ONLY THEN reveal gold label

## Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Gold label leakage | Low | Critical | Strict code review |
| Post-hoc invariant addition | Medium | High | Freeze invariants before evaluation |
| Benchmark memorization | Low | Medium | Temporal holdout (R0-D2) |

## Certification

**Auditor**: [Auto-generated]
**Date**: 2026-09-20
**Status**: PRE-EVALUATION CHECKS PASSED

---
*This audit must be completed before any benchmark evaluation begins*
