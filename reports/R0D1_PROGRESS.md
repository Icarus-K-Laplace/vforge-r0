# R0-D1 Experiment Progress Report

## Status: IN PROGRESS (Background Execution)

### Completed Components

#### 1. Data Acquisition ✅
- Downloaded SciCoQA v1.1 from HuggingFace
- Real split: **92 samples**
- Synthetic split: 543 samples
- Pooled split: 129 samples
- Created blind projection with 7 safe fields
- **Leakage audit**: PASSED

#### 2. Framework Implementation ✅
- Paper Claim Miner (`paper_claim_miner.py`)
- Normative Contract Builder (`sciinvariant_r0d.py`)
- Protocol Graph Extractor
- Two-channel verification system

#### 3. Frozen Artifacts
- `SCIENTIFIC_VALIDITY_ONTOLOGY_V1.json` - Frozen principles
- `external/scicoqa/blind/scicoqa_real_blind.jsonl` - Blind data
- `external/scicoqa/raw_gold/` - Sealed gold data

### Pipeline Status

| Component | Status |
|-----------|--------|
| Dataset download | ✅ Complete |
| Blind projection | ✅ Created |
| Paper mining | 🔄 Running |
| Repository cloning | 🔄 Running |
| Contract building | ⏳ Pending |
| Graph extraction | ⏳ Pending |
| Prediction freeze | ⏳ Pending |
| Gold reveal | ⏳ Pending |
| Metrics computation | ⏳ Pending |

### Expected Output Files

```
E:/VForge-R0/
├── papers/                    # Downloaded papers
├── repositories/              # Cloned repos
├── claims/                    # Mined claims (frozen)
├── contracts/                 # Normative contracts
├── graphs/                    # Protocol graphs
├── results/
│   ├── R0D1_PREDICTIONS_FROZEN.jsonl  # Predictions (will be frozen)
│   ├── R0D1_PREDICTION_FREEZE.json    # Freeze documentation
│   └── R0D1_EXTERNAL_METRICS.json     # Evaluation metrics
├── reports/
│   ├── R0D1_LEAKAGE_AUDIT.md
│   ├── R0D1_ERROR_ANALYSIS.md
│   └── R0D1_FINAL_REPORT.md
└── external/scicoqa/
    ├── blind/
    │   └── scicoqa_real_blind.jsonl
    └── raw_gold/
        └── scicoqa_real_v1.1.jsonl
```

### Current Metrics (Pre-computation)

- Total samples: 92
- Expected processing time: ~30-60 minutes (due to repo cloning)
- Bottleneck: GitHub clone operations

### Next Steps (After Pipeline Completion)

1. Reveal gold data
2. Match predictions to gold discrepancies
3. Compute Real Discrepancy Recall (RDR)
4. Compare to baselines
5. Generate final report with GO/KILL verdict

---
**Last Updated**: 2026-09-20T04:15:00
**Pipeline Status**: Running in background
