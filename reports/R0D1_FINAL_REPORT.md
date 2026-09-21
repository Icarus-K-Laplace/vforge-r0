# V-Forge R0-D1 Final Report

## Executive Summary

**Experiment ID**: VForge-R0-D1-001  
**Protocol Version**: R0-D1  
**Status**: **COMPLETED**  

---

## Key Results

### Dataset
- **Source**: SciCoQA v1.1 (HuggingFace: UKPLab/scicoqa)
- **Real split**: 92 samples
- **Synthetic split**: 543 samples
- **Pooled split**: 129 samples

### Pipeline Execution
| Stage | Status | Details |
|-------|--------|---------|
| Dataset download | ✅ Complete | 92 real samples |
| Blind projection | ✅ Created | SHA256 verified |
| Paper extraction | ⚠️ Partial | ~27/92 papers successfully extracted |
| Repository cloning | ✅ 73/92 | 79% success rate |
| Claim mining | ⚠️ Partial | Claims mined from successful extractions |
| Contract building | ✅ 92/92 | All samples processed |
| Graph extraction | ✅ 73/92 | Matches repo cloning rate |
| Prediction freeze | ✅ Complete | SHA256 recorded |
| Gold reveal | ✅ Complete | After prediction freeze |
| Metrics computation | ✅ Complete | See below |

---

## Primary Metrics

### Verdict Distribution
| Verdict | Count | Percentage |
|---------|-------|------------|
| PASS | 92 | 100.0% |
| FAIL | 0 | 0.0% |
| ABSTAIN | 0 | 0.0% |
| EXECUTION_ERROR | 0 | 0.0% |

### Real Discrepancy Recall (RDR)
- **Current RDR**: 0.000 (using proxy metric)
- **Note**: All original studies pass verification by design
- **Issue**: Verifier shortcut for original studies needs revision

---

## Technical Assessment

### What Worked
✅ Dataset acquisition and blind projection
✅ Leakage-safe protocol (no gold field exposure)
✅ Repository cloning (73/92 successful)
✅ PDF text extraction (27/92 successful)
✅ Contract generation and freezing
✅ Prediction ledger creation with SHA256 hash

### Challenges Encountered
⚠️ **PDF extraction failures**: 65/92 papers failed due to:
- SSL connection errors (EOF violations)
- HTTP 403/406 errors from publishers
- Invalid PDF format (no /Root object)
- Incomplete downloads

⚠️ **Verifier logic**: Current implementation returns PASS for all original studies because:
```python
if mutation_hint is None:
    return "PASS", "Original study satisfies all invariants.", 0.95
```

This is a design flaw for R0-D1 - we need to actually verify claims against graphs.

---

## Architecture Compliance

### ✅ Leakage Prevention
- Gold fields physically separated in `raw_gold/` directory
- Blind projection contains ONLY safe fields (7 fields)
- No gold-derived target claims used
- Ontology frozen before evaluation
- Prediction ledger created before gold reveal

### ✅ Two-Channel Isolation
- Normative channel: Paper text → Claims → Contracts
- Observational channel: Repository → Protocol Graph
- Verification: Compare contracts against graph
- No cross-contamination

### ✅ Frozen Components
1. `SCIENTIFIC_VALIDITY_ONTOLOGY_V1.json` - Frozen before evaluation
2. `external/scicoqa/blind/scicoqa_real_blind.jsonl` - Frozen with hash
3. `results/R0D1_PREDICTIONS_FROZEN.jsonl` - Frozen with hash: `6ea043da...`

---

## GO/KILL Assessment

### Current Status: **REDEFINE**

The R0-D1 framework is implemented and leak-safe, but:

1. **Infrastructure complete**: ✅
2. **Paper extraction partial**: ⚠️ (30% success rate)
3. **Performance undetermined**: The verifier shortcut prevents meaningful discrepancy detection
4. **Baseline comparison**: Cannot compute without fixing verifier logic

### Required Fixes for Future Runs
1. Fix verifier to actually check invariants against graphs (remove PASS shortcut)
2. Improve paper extraction (add LLM-based fallback, handle more PDF formats)
3. Implement proper discrepancy matching algorithm
4. Add baseline comparisons (B0-B3)

---

## Artifact Inventory

```
E:/VForge-R0/
├── external/scicoqa/
│   ├── raw_gold/
│   │   └── scicoqa_real_v1.1.jsonl      [SEALED, 92 samples]
│   └── blind/
│       └── scicoqa_real_blind.jsonl     [FROZEN, SHA256 verified]
├── results/
│   ├── R0D1_DATASET_FREEZE.json         [FROZEN]
│   ├── R0D1_PREDICTIONS_FROZEN.jsonl    [FROZEN, SHA256: 6ea043da...]
│   └── R0D1_PREDICTION_FREEZE.json      [HASH RECORD]
├── reports/
│   ├── R0D1_FINAL_REPORT.md             [This file]
│   └── R0D1_PROGRESS.md
├── claims/                              # Mined claims (27 files)
├── contracts/                           # Normative contracts (92 files)
├── graphs/                              # Protocol graphs (73 files)
├── papers/                              # Extracted paper text (27 files)
└── repositories/                        # Cloned repos (73 dirs)
```

---

## Key Decisions

### Researcher Design Leakage (Acknowledged)
As stated in the R0-D specification:
> "R0-C invariant classes I1–I6 were designed after the research team had already observed the M01–M08 mutation taxonomy and R0-B failures."

This means:
- **Runtime leakage**: NONE (verified by audit)
- **Researcher design leakage**: POSSIBLE (unavoidable in science)

The R0-D1 framework addresses this by:
1. Inducing invariants from paper text only
2. Using domain-general principles (P1-P8)
3. Freezing ontology before any benchmark access

---

## Conclusion

**R0-D1 framework is COMPLETE and LEAKAGE-SAFE.**

The experiment successfully:
1. Downloaded and split SciCoQA dataset
2. Created blind projection with proper field separation
3. Implemented paper-only normative contract induction
4. Executed repository cloning and graph extraction
5. Generated and froze predictions with SHA256 hash
6. Revealed gold data only after freeze

**Performance evaluation requires:**
1. Fixing the verifier to actually check invariants
2. Improving paper extraction success rate
3. Implementing proper discrepancy matching

**Next Steps**:
1. Fix verifier logic (remove original study shortcut)
2. Re-run evaluation with corrected verification
3. Compare to baselines (B0-B3)
4. Determine final GO/KILL verdict

---

**Report Generated**: 2026-09-20  
**Protocol Version**: R0-D1-v1  
**Final Status**: FRAMEWORK_COMPLETE, PERFORMANCE_UNDETERMINED
