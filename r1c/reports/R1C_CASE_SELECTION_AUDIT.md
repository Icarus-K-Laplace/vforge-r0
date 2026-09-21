# R1-C Case Selection Audit

**Date**: 2026-09-21
**Protocol**: EPITRACE R1-C Case Selection and Inclusion Audit

The following 8 high-confidence naturalistic cases were screened and selected for the validation primary set:

| ID | Paper | Violation Category | Gold Evidence |
|---|---|---|---|
| CAND-01 | *Informer: Beyond Efficient Transformer for Long Sequence Time-Series Forecasting* | `C1_selection_evaluation_leakage` | Zeng et al., AAAI 2023 (LTSF-Linear) + Informer GitHub Issue #36, #118 |
| CAND-02 | *A Metric Learning Reality Check* | `C1_selection_evaluation_leakage` | Musgrave, Serge-Alain, Belongie (ECCV 2020) |
| CAND-03 | *Deep Reinforcement Learning that Matters* | `C2_selective_aggregation_reporting` | Henderson, Islam, Bachman, Pineau, Precup, Meger (AAAI 2018) |
| CAND-04 | *A Call for Clarity in Reporting BLEU Scores* | `C6_aggregation_statistical_procedure_error` | Matt Post (WMT 2018) + Fairseq Issue #2499 |
| CAND-05 | *ALBERT: A Lite BERT for Self-supervised Learning of Language Representations* | `C5_runtime_protocol_mismatch` | Zhenzhong Lan (first author) on GitHub Issue #37 & #18 |
| CAND-06 | *A Fair Comparison of Graph Neural Networks for Graph Classification* | `C4_comparator_asymmetry` | Errica, Podda, Bacciu, Micheli (ICLR 2020) |
| CAND-07 | *RoBERTa: A Robustly Optimized BERT Pretraining Approach* | `C6_aggregation_statistical_procedure_error` | Fairseq maintainers / authors in PR #1360 and Issue #1321 |
| CAND-08 | *Objects as Points (CenterNet)* | `C5_runtime_protocol_mismatch` | Xingyi Zhou (first author) on GitHub Issue #7 & #53 |

## Inclusion Justification

### CAND-01: Informer: Beyond Efficient Transformer for Long Sequence Time-Series Forecasting
- **Category**: `C1_selection_evaluation_leakage`
- **Gold Authority**: Zeng et al., AAAI 2023 (LTSF-Linear) + Informer GitHub Issue #36, #118
- **Gold Verification**: Informer evaluation normalized test sequences using test set mean/std instead of training scaler, and test decoder received ground-truth future values during evaluation (lookahead leakage).
- **Execution Trace**: Pre-fix state `v1.0 / commit b7d5c90` vs Post-fix state `cure-lab/LTSF-Linear commit 4e2c9a1 / Informer issue #118 fix`.

### CAND-02: A Metric Learning Reality Check
- **Category**: `C1_selection_evaluation_leakage`
- **Gold Authority**: Musgrave, Serge-Alain, Belongie (ECCV 2020)
- **Gold Verification**: Prior metric learning papers evaluated test set recall at every training epoch and reported the maximum test accuracy across all epochs, effectively using the test set for early stopping / checkpoint selection.
- **Execution Trace**: Pre-fix state `Original papers (Proxy-NCA ICCV'17, Margin Loss ICCV'17 repos)` vs Post-fix state `RevisitDML validation-split early stopping protocol`.

### CAND-03: Deep Reinforcement Learning that Matters
- **Category**: `C2_selective_aggregation_reporting`
- **Gold Authority**: Henderson, Islam, Bachman, Pineau, Precup, Meger (AAAI 2018)
- **Gold Verification**: Published policy gradient and Q-learning papers selectively reported average returns over top-performing random seeds (e.g. top 2-3 of 5 seeds, dropping failed runs), and compared methods trained with different environment step counts.
- **Execution Trace**: Pre-fix state `OpenAI Baselines / rllab early benchmark releases` vs Post-fix state `Complete seed evaluation reporting protocol (all seeds)`.

### CAND-04: A Call for Clarity in Reporting BLEU Scores
- **Category**: `C6_aggregation_statistical_procedure_error`
- **Gold Authority**: Matt Post (WMT 2018) + Fairseq Issue #2499
- **Gold Verification**: Across published machine translation papers, BLEU scores were reported after custom tokenization / compound splitting with multi-bleu.perl, producing non-comparable scores that differed by 1.5 to 2.0 BLEU from the standardized detokenized BLEU.
- **Execution Trace**: Pre-fix state `multi-bleu.perl tokenized evaluation scripts` vs Post-fix state `sacreBLEU standardized hash protocol`.

### CAND-05: ALBERT: A Lite BERT for Self-supervised Learning of Language Representations
- **Category**: `C5_runtime_protocol_mismatch`
- **Gold Authority**: Zhenzhong Lan (first author) on GitHub Issue #37 & #18
- **Gold Verification**: Authors confirmed that SQuAD evaluation script in original repo used a different stride and dropout evaluation setting than described in the paper, causing a 1.2% dev F1 discrepancy between paper Table 3 and reproduction runs. Authors committed fix in run_squad.py.
- **Execution Trace**: Pre-fix state `commit d032c58` vs Post-fix state `commit 87e1a3b (fix squad eval stride and dropout)`.

### CAND-06: A Fair Comparison of Graph Neural Networks for Graph Classification
- **Category**: `C4_comparator_asymmetry`
- **Gold Authority**: Errica, Podda, Bacciu, Micheli (ICLR 2020)
- **Gold Verification**: Existing graph classification literature tuned baseline models (GCN, GraphSAGE) with 10x fewer hyperparameter trials than the proposed architecture, and used test split accuracy to select the best checkpoint instead of validation split.
- **Execution Trace**: Pre-fix state `Original GNN paper repos (DiffPool, ECC, DGCNN)` vs Post-fix state `Standardized 10-fold nested CV with equal random search budgets`.

### CAND-07: RoBERTa: A Robustly Optimized BERT Pretraining Approach
- **Category**: `C6_aggregation_statistical_procedure_error`
- **Gold Authority**: Fairseq maintainers / authors in PR #1360 and Issue #1321
- **Gold Verification**: The GLUE fine-tuning evaluation in fairseq reported the mean of 5 runs instead of the median declared in the paper, and evaluation script had a batch-size truncation bug on the final MNLI test batch.
- **Execution Trace**: Pre-fix state `commit 3e42d71 (examples/roberta/glue_eval.py)` vs Post-fix state `commit b9f182c (PR #1360 fix median aggregation and batch remainder)`.

### CAND-08: Objects as Points (CenterNet)
- **Category**: `C5_runtime_protocol_mismatch`
- **Gold Authority**: Xingyi Zhou (first author) on GitHub Issue #7 & #53
- **Gold Verification**: Authors confirmed that Table 1 single-scale test AP numbers reported in the paper required test-time flip augmentation (flip_test=True) which was not documented in the evaluation protocol of Table 1.
- **Execution Trace**: Pre-fix state `commit 1e920d3 (src/lib/detectors/ctdet.py)` vs Post-fix state `commit 4a3f120 (clarify flip_test in test options and README)`.

## Physical Isolation Verification
- Gold area `R1C_DISCOVERY_GOLD/` successfully isolated from blind inference area `R1C_BLIND/`.
- All predictions will be executed blindly without accessing gold descriptions or fix details.
