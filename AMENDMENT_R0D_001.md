# R0-D1 Amendment

## Amendment R0D_001: Evaluation Interface Correction

### Issue Identified
The previous R0-D framework accepted a "target claim" as input, which could potentially be derived from gold discrepancy descriptions. This creates a leakage path.

### Correction Applied
Changed the pipeline from:
```
paper + supplied target claim → normative contract
```
to:
```
full paper → implementation-relevant claim/protocol mining → claim-conditioned normative contracts
```

### Implementation Changes

1. **ClaimMiner Component**
   - Input: Full paper text only (no gold claims)
   - Output: Implementation-relevant scientific claims
   - Claim classes: MODEL_ARCHITECTURE, ALGORITHM, LOSS, DATA_USAGE, PREPROCESSING, TRAINING, OPTIMIZATION, HYPERPARAMETER_PROTOCOL, SELECTION, EVALUATION, METRIC, AGGREGATION, STATISTICS

2. **Two-Stage Pipeline**
   - Stage 1: PaperClaimMiner extracts claims from paper text
   - Stage 2: NormativeContractBuilder induces invariants from extracted claims + frozen ontology

3. **Freeze Protocol**
   - Mined claims are frozen and hashed before repository analysis
   - Invariants are induced from frozen claims only
   - No post-hoc claim addition after seeing failures

### Files Modified
- `sciinvariant_r0d.py`: Added ClaimMiner class
- `protocols/R0D_AMENDMENT.md`: This document

### Verification
- No gold-derived claims are used
- Claim extraction uses only paper text
- Ontology remains frozen (P1-P8)
- All hashes recorded in prediction ledger

---
**Amendment Status**: APPLIED
**Date**: 2026-09-20
**Version**: R0-D1-v1
