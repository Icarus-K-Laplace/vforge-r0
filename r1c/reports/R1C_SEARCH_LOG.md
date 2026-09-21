# R1-C Systematic Search and Discovery Log

**Protocol**: EPITRACE R1-C Naturalistic External Validation
**Objective**: Discover real-world, documented scientific protocol deviations and corrections in published AI/ML research.

Total candidate cases logged: 30

## Candidate Pool Summary

| ID | Venue | Paper | Category | Gold Source | Status |
|---|---|---|---|---|---|
| CAND-01 | AAAI 2021 | Informer: Beyond Efficient Transformer f... | `C1_selection_evaluation_leakage` | `E_reproducibility_paper` | INCLUDED |
| CAND-02 | ECCV 2020 | A Metric Learning Reality Check... | `C1_selection_evaluation_leakage` | `E_reproducibility_paper` | INCLUDED |
| CAND-03 | AAAI 2018 | Deep Reinforcement Learning that Matters... | `C2_selective_aggregation_reporting` | `E_reproducibility_paper` | INCLUDED |
| CAND-04 | WMT 2018 | A Call for Clarity in Reporting BLEU Sco... | `C6_aggregation_statistical_procedure_error` | `E_reproducibility_paper` | INCLUDED |
| CAND-05 | ICLR 2020 | ALBERT: A Lite BERT for Self-supervised ... | `C5_runtime_protocol_mismatch` | `A_author_github_issue` | INCLUDED |
| CAND-06 | ICLR 2020 | A Fair Comparison of Graph Neural Networ... | `C4_comparator_asymmetry` | `E_reproducibility_paper` | INCLUDED |
| CAND-07 | arXiv 2019 | RoBERTa: A Robustly Optimized BERT Pretr... | `C6_aggregation_statistical_procedure_error` | `B_explicit_fix_pr` | INCLUDED |
| CAND-08 | CVPR 2019 | Objects as Points (CenterNet)... | `C5_runtime_protocol_mismatch` | `A_author_github_issue` | INCLUDED |
| CAND-09 | CVPR 2017 | ChestX-ray14: Hospital-scale Chest X-ray... | `C1_selection_evaluation_leakage` | `C_paper_correction_erratum` | INCLUDED |
| CAND-10 | ICML 2020 | A Simple Framework for Contrastive Learn... | `C5_runtime_protocol_mismatch` | `A_author_github_issue` | INCLUDED |
| CAND-11 | NeurIPS 2018 Workshop | Pitfalls of Graph Neural Network Evaluat... | `C2_selective_aggregation_reporting` | `E_reproducibility_paper` | INCLUDED |
| CAND-12 | ICLR 2019 | A Closer Look at Few-Shot Classification... | `C4_comparator_asymmetry` | `E_reproducibility_paper` | INCLUDED |
| CAND-13 | ICLR 2018 | On the State of the Art of Evaluation in... | `C4_comparator_asymmetry` | `E_reproducibility_paper` | INCLUDED |
| CAND-14 | ICLR 2020 | Deep Double Descent: Where Bigger Models... | `C1_selection_evaluation_leakage` | `B_explicit_fix_pr` | INCLUDED |
| CAND-15 | ICML 2020 | Revisiting Deep Metric Learning (Stage1b... | `C2_selective_aggregation_reporting` | `D_official_repo_readme` | INCLUDED |
| CAND-16 | CVPRW 2025 | Evaluating Text-to-Image Diffusion Model... | `C3_scope_mismatch` | `D_official_repo_readme` | INCLUDED |
| CAND-17 | arXiv 2026 | Delta Attention Residuals... | `C4_comparator_asymmetry` | `D_official_repo_readme` | INCLUDED |
| CAND-18 | KDD 2026 | Can LLMs Beat Traditional ML Models in C... | `C6_aggregation_statistical_procedure_error` | `D_official_repo_readme` | EXCLUDED_AUTH |
| CAND-19 | NeurIPS 2021 | Revisiting Tabular Deep Learning: SNGP a... | `C4_comparator_asymmetry` | `E_reproducibility_paper` | INCLUDED |
| CAND-20 | AAAI 2023 | Are Transformers Effective for Time Seri... | `C1_selection_evaluation_leakage` | `E_reproducibility_paper` | INCLUDED |
| CAND-21 | RecSys 2020 | Neural Collaborative Filtering vs Matrix... | `C6_aggregation_statistical_procedure_error` | `E_reproducibility_paper` | INCLUDED |
| CAND-22 | ICML 2021 | DeiT: Training data-efficient image tran... | `C5_runtime_protocol_mismatch` | `B_explicit_fix_pr` | INCLUDED |
| CAND-23 | ICML 2020 | Evaluating the Robustness of Defense Mec... | `C5_runtime_protocol_mismatch` | `E_reproducibility_paper` | INCLUDED |
| CAND-24 | ICCV 2021 | Swin Transformer: Hierarchical Vision Tr... | `C5_runtime_protocol_mismatch` | `B_explicit_fix_pr` | INCLUDED |
| CAND-25 | Interspeech 2020 | Conformer: Convolution-augmented Transfo... | `C6_aggregation_statistical_procedure_error` | `B_explicit_fix_pr` | INCLUDED |
| CAND-26 | CVPR 2023 | YOLOv7: Trainable bag-of-freebies sets n... | `C5_runtime_protocol_mismatch` | `A_author_github_issue` | INCLUDED |
| CAND-27 | JOSS 2022 | Torchmetrics: A Collection of 100+ PyTor... | `C6_aggregation_statistical_procedure_error` | `B_explicit_fix_pr` | INCLUDED |
| CAND-28 | EMNLP 2022 | An Empirical Survey on Long Document Sum... | `C6_aggregation_statistical_procedure_error` | `B_explicit_fix_pr` | INCLUDED |
| CAND-29 | NeurIPS 2022 | A Benchmark for General Purpose Molecula... | `C1_selection_evaluation_leakage` | `A_author_github_issue` | INCLUDED |
| CAND-30 | KDD 2021 | Fixing Data Leakage in Automated Feature... | `C1_selection_evaluation_leakage` | `B_explicit_fix_pr` | INCLUDED |

## Category Distribution

- `C1_selection_evaluation_leakage`: 7 candidates
- `C2_selective_aggregation_reporting`: 3 candidates
- `C3_scope_mismatch`: 1 candidates
- `C4_comparator_asymmetry`: 5 candidates
- `C5_runtime_protocol_mismatch`: 7 candidates
- `C6_aggregation_statistical_procedure_error`: 7 candidates

## Next Step
Filter candidates to the 10-20 high-confidence set and select 8-12 strongest cases for R1-C blind evaluation.
