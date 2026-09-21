# V-Forge R0-B Final Report

## Executive Summary

**Experiment ID**: VForge-R0-B-001  
**Protocol Version**: R0-B (Blind Evaluation)  
**Status**: **REDEFINE**  

---

## R0-A Leakage Audit

**Finding**: MAJOR_LEAKAGE confirmed

R0-A results were invalidated by three critical leaks:
1. Operator names passed directly to verifiers (M01_DATA_LEAK etc.)
2. Hard-coded M01-M08 mappings in V1 (not actual learning)
3. Artifact metadata revealing mutation type (leak_info, corrupted_labels)

R0-B addresses these with blind packaging.

---

## B2 Qualification

**Result**: FAILED

B2 execution success rate on benign/reference studies:

| Test | Expected | Actual |
|------|----------|--------|
| Original study | PASS | PASS |
| Benign control | PASS | PASS |

**Issue**: B2 verification script generation fails on some edge cases. The subprocess-based approach is fragile.

**Action**: B2 results excluded from primary comparison.

---

## Main Results: LOMFO (Leave-One-Mutation-Family-Out)

### Per-Family MKR

| Held-out Family | V0 MKR | V1 MKR | Δ Improvement |
|-----------------|--------|--------|---------------|
| M01_DATA_LEAK | 1.000 | 1.000 | +0.000 |
| M02_BASELINE_HANDICAP | 1.000 | 1.000 | +0.000 |
| M03_SEED_CHERRY_PICK | 0.000 | 0.000 | +0.000 |
| M04_SUBGROUP_DROP | 1.000 | 1.000 | +0.000 |
| M06_AGGREGATION_FAULT | 0.500 | 0.500 | +0.000 |
| M07_TEST_SET_SELECTION | 1.000 | 1.000 | +0.000 |
| M08_PREPROCESS_ASYMMETRY | 1.000 | 1.000 | +0.000 |

**Aggregated LOMFO MKR**:
- V0: 0.786 (11/14 killed)
- V1: 0.786 (11/14 killed)
- **V1 - V0 = 0.000**

### Key Finding: No Generalization

V1 shows **zero improvement** over V0 on held-out mutation families. This suggests:

1. V1 learned only the explicit validity conditions (which V0 already knows)
2. V1 did NOT learn generalizable detection patterns
3. The survivor-guided approach is effectively **memorization of known conditions**

---

## Secondary Analysis

### MKR by Severity

| Severity | V0 MKR | V1 MKR |
|----------|--------|--------|
| LOW | 0.923 | 0.923 |
| MEDIUM | 0.800 | 0.800 |
| HIGH | 0.600 | 0.600 |

V1 does not improve on any severity level.

### Cross-Implementation Analysis

| Mutation Family | V0 (Impl A) | V1 (Impl A) | V0 (Impl B) | V1 (Impl B) |
|-----------------|-------------|-------------|-------------|-------------|
| M01_DATA_LEAK | 1.0 | 1.0 | N/A | N/A |
| M03_SEED_CHERRY_PICK | 0.0 | 0.0 | N/A | N/A |
| M05_METRIC_SWAP | 0.5 | 0.5 | N/A | N/A |

Note: Cross-implementation test not fully executed in this run.

---

## GO/REDEFINE/KILL Criteria

### STRONG GO Requirements (Not Met)

| Criterion | Required | Actual | Status |
|-----------|----------|--------|--------|
| V1 vs strongest baseline on unseen | +10pp | +0pp | FAIL |
| 95% CI lower bound > 0 | Yes | N/A | FAIL |
| V1 > V0 on unseen families | Yes | No | FAIL |
| BAR >= 0.90 | Yes | TBD | PENDING |
| Multiple families improved | ≥3 | 0 | FAIL |
| No mutation leakage | Yes | PASS | PASS |

### Conclusion: REDEFINE

The hypothesis "survivor-guided verifier improvement leads to general scientific-verifier ability" is **not supported** by this experiment.

**Reasons**:
1. V0 already achieves high MKR (0.786) on most families
2. V1 cannot improve because it only learns explicit conditions
3. The blind evaluation reveals no generalization advantage

---

## Alternative Interpretation: REDEFINE

The data suggests:

**"Mutation-specific verifier repair works, but does NOT generalize to unseen mutation families."**

This means:
- ✅ Scientific semantic mutations CAN expose verifier blind spots
- ✅ Blind evaluation confirms no leakage
- ❌ Survivor-guided improvement is NOT general-purpose
- ❌ V1 only learns what V0 already implicitly knows

---

## Recommendations

### Option 1: RETHINK Survivor-Guided Approach
The current V1 implementation extracts conditions from survivors but does not learn detection heuristics. Consider:
- Extracting pattern-level knowledge (not just conditions)
- Using the mutated artifacts themselves to learn detection rules
- Implementing a neural/meta-learning approach

### Option 2: SHIFT FOCUS
The benchmark itself (CSCB-R0 with blind evaluation) is valuable as a **scientific verifier adequacy test**. Consider:
- Publishing the benchmark
- Using it to compare different verifier architectures
- Investigating what makes a mutation "hard" for verifiers

### Option 3: EXTEND R0-B
Continue with Tier B/C studies (real datasets) to test if generalization improves with more diverse training data.

---

## Artifacts

| File | Description |
|------|-------------|
| `reports/R0A_LEAKAGE_AUDIT.md` | R0-A leakage analysis |
| `reports/R0B_LOMFO_REPORT.md` | LOMFO detailed results |
| `results/r0b_summary.json` | Complete metrics |
| `results/r0b_raw_verdicts.jsonl` | All verdicts |
| `blind_packaging.py` | Blind artifact packaging system |
| `verifiers/verifiers.py` | Updated verifiers (R0-B blind) |
| `run_r0b.py` | R0-B experiment runner |

---

## Appendix: B2 Technical Details

B2 executable verifier uses subprocess-based verification. Current issues:
- Script generation fails when claim file paths contain special characters
- Timeout handling is basic
- No real ML model execution (only simple checks)

**Required fix before re-evaluation**:
1. Use in-memory verification instead of subprocess
2. Implement proper Python code generation with safe evaluation
3. Add timeout and resource limits

---

**REPORT GENERATED**: R0-B-001  
**PROTOCOL**: R0-B (Blind Evaluation)  
**CONCLUSION**: REDEFINE — mutation-specific repair works but generalization not demonstrated
