# V-Forge R0-D Final Report (Preliminary)

## Executive Summary

**Experiment ID**: VForge-R0-D-001  
**Protocol Version**: R0-D  
**Status**: **FRAMEWORK_COMPLETE**  

**Note**: This is a preliminary report. The complete evaluation with real SciCoQA data is pending dataset access.

---

## What Was Accomplished

### 1. Framework Implementation
- ✅ Paper-only normative contract inducer
- ✅ Repository protocol graph extractor
- ✅ Two-channel isolation architecture
- ✅ Leakage-safe verification pipeline
- ✅ 8 domain-independent scientific validity principles

### 2. Components Created

| Component | File | Status |
|-----------|------|--------|
| Main system | `sciinvariant_r0d.py` | ✅ Complete |
| Ontology | `SCIENTIFIC_VALIDITY_ONTOLOGY_V1.json` | ✅ Frozen |
| Protocol | `PROTOCOL_R0D.md` | ✅ Complete |
| Freeze doc | `R0D_FREEZE.md` | ✅ Complete |
| Leakage audit | `reports/R0D_LEAKAGE_AUDIT.md` | ✅ Complete |

### 3. Mock Testing
- Tested on 3 synthetic papers
- Successfully induced 4, 2, 1 invariants respectively
- Correctly classified originals as PASS
- Pipeline is functional

---

## R0-D Specific Challenges

### Researcher Design Leakage (Admitted)

As stated in the R0-D specification:

> "R0-C invariant classes I1–I6 were designed after the research team had already observed the M01–M08 mutation taxonomy and R0-B failures."

This means:
- **Runtime leakage**: NONE (verified by audit)
- **Researcher design leakage**: POSSIBLE (unavoidable in science)

The R0-D framework addresses this by:
1. Inducing invariants from paper text only
2. Using domain-general principles (not benchmark-specific)
3. Freezing ontology before any benchmark access

### Can't Test Without Data

The full R0-D evaluation requires:
1. SciCoQA benchmark access
2. Real paper-text + repository pairs
3. Gold discrepancy labels (only revealed AFTER prediction freeze)

Without this data, we can only report **framework readiness**, not **performance**.

---

## Current Capabilities

### What SI-D CAN Do
- Extract claim structure from paper text
- Induce invariants from domain principles
- Build protocol graphs from repositories
- Compare normative expectations vs. observed behavior
- Produce PASS/FAIL/ABSTAIN verdicts with evidence

### What SI-D CANNOT (Yet) Do
- Report real discrepancy recall rates
- Compare to published SciCoQA baselines
- Validate on held-out real errors
- Compute paired counterfactual metrics

---

## GO/KILL Assessment

**Current Status**: **UNDETERMINED**

The framework is built and tested on mock data. To determine GO/KILL, we need:

1. **Access to SciCoQA real split**
2. **Run frozen prediction pipeline**
3. **Compute metrics against gold labels**

Based on R0-C success (MKR=1.0 on synthetic), we have **optimistic headroom** but cannot claim STRONG_GO without real-data validation.

---

## Path Forward

### Immediate Next Steps
1. Obtain SciCoQA dataset
2. Run full frozen evaluation
3. Generate R0D_EXTERNAL_METRICS.json
4. Produce final GO/KILL verdict

### Alternative Path (If SciCoQA Unavailable)
1. Use R0-B/R0-C synthetic data as proxy
2. Add noise/variation to simulate real-world complexity
3. Report as "synthetic validation" not "real error detection"

---

## Artifact Inventory

```
E:/VForge-R0/
├── sciinvariant_r0d.py              # R0-D main implementation
├── PROTOCOL_R0D.md                  # Protocol documentation
├── R0D_FREEZE.md                    # Freeze documentation
├── SCIENTIFIC_VALIDITY_ONTOLOGY_V1.json  # Frozen principles
├── reports/
│   └── R0D_LEAKAGE_AUDIT.md         # Leakage audit
└── results/
    ├── r0d_mock_results.json        # Mock test results
    └── r0d_summary.json             # Experiment summary
```

---

## Conclusion

**R0-D framework is READY.** 

The paper-only normative invariant induction system has been implemented, tested on synthetic data, and verified for leakage safety. The critical next step is obtaining SciCoQA benchmark access to run the real evaluation.

**Recommendation**: Proceed with real-data evaluation. If successful, this constitutes strong evidence that protocol invariants induced from paper text generalize beyond researcher-designed systems.

---

**REPORT VERSION**: R0-D-v1 (Preliminary)  
**FINAL REPORT**: Pending real-data evaluation  
**NEXT ACTION**: Obtain SciCoQA dataset and run frozen pipeline
