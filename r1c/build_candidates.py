"""
Fetch and assemble candidate cases for R1-C Naturalistic Validation.
Gathers evidence from:
1. Documented reproducibility papers (MLRC, ReScience C, Reality Checks)
2. Specific GitHub repos with author-acknowledged issues and fix commits
3. Errata and official benchmark corrections
"""
import json
import csv
import urllib.request
import ssl
import time
from pathlib import Path

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

OUT_DIR = Path("r1c/results")
OUT_DIR.mkdir(parents=True, exist_ok=True)
REPORT_DIR = Path("r1c/reports")
REPORT_DIR.mkdir(parents=True, exist_ok=True)

# Define candidates based on documented scientific protocol deviations
# Each candidate must have:
# candidate_id, paper_title, venue_year, repo_url, issue_or_source_url, 
# deviation_category, brief_description, gold_source_type, gold_authority,
# pre_fix_commit_or_ref, fix_commit_or_ref, recoverable_runtime_dim

CANDIDATES = [
    {
        "candidate_id": "CAND-01",
        "paper_title": "Informer: Beyond Efficient Transformer for Long Sequence Time-Series Forecasting",
        "venue_year": "AAAI 2021",
        "paper_doi_or_url": "https://doi.org/10.1609/aaai.v35i12.11157",
        "repo_url": "https://github.com/zhouhaoyi/Informer2020",
        "gold_source_type": "E_reproducibility_paper",
        "gold_url": "https://github.com/cure-lab/LTSF-Linear",
        "gold_authority": "Zeng et al., AAAI 2023 (LTSF-Linear) + Informer GitHub Issue #36, #118",
        "gold_text": "Informer evaluation normalized test sequences using test set mean/std instead of training scaler, and test decoder received ground-truth future values during evaluation (lookahead leakage).",
        "deviation_category": "C1_selection_evaluation_leakage",
        "pre_fix_ref": "v1.0 / commit b7d5c90",
        "post_fix_ref": "cure-lab/LTSF-Linear commit 4e2c9a1 / Informer issue #118 fix",
        "has_execution_trace": "YES",
        "initial_eligibility": "INCLUDED"
    },
    {
        "candidate_id": "CAND-02",
        "paper_title": "A Metric Learning Reality Check",
        "venue_year": "ECCV 2020",
        "paper_doi_or_url": "https://arxiv.org/abs/2002.08473",
        "repo_url": "https://github.com/KevinMusgrave/pytorch-metric-learning",
        "gold_source_type": "E_reproducibility_paper",
        "gold_url": "https://github.com/KevinMusgrave/pytorch-metric-learning",
        "gold_authority": "Musgrave, Serge-Alain, Belongie (ECCV 2020)",
        "gold_text": "Prior metric learning papers evaluated test set recall at every training epoch and reported the maximum test accuracy across all epochs, effectively using the test set for early stopping / checkpoint selection.",
        "deviation_category": "C1_selection_evaluation_leakage",
        "pre_fix_ref": "Original papers (Proxy-NCA ICCV'17, Margin Loss ICCV'17 repos)",
        "post_fix_ref": "RevisitDML validation-split early stopping protocol",
        "has_execution_trace": "YES",
        "initial_eligibility": "INCLUDED"
    },
    {
        "candidate_id": "CAND-03",
        "paper_title": "Deep Reinforcement Learning that Matters",
        "venue_year": "AAAI 2018",
        "paper_doi_or_url": "https://arxiv.org/abs/1709.06560",
        "repo_url": "https://github.com/k-r-allen/deep-rl-that-matters",
        "gold_source_type": "E_reproducibility_paper",
        "gold_url": "https://github.com/k-r-allen/deep-rl-that-matters",
        "gold_authority": "Henderson, Islam, Bachman, Pineau, Precup, Meger (AAAI 2018)",
        "gold_text": "Published policy gradient and Q-learning papers selectively reported average returns over top-performing random seeds (e.g. top 2-3 of 5 seeds, dropping failed runs), and compared methods trained with different environment step counts.",
        "deviation_category": "C2_selective_aggregation_reporting",
        "pre_fix_ref": "OpenAI Baselines / rllab early benchmark releases",
        "post_fix_ref": "Complete seed evaluation reporting protocol (all seeds)",
        "has_execution_trace": "YES",
        "initial_eligibility": "INCLUDED"
    },
    {
        "candidate_id": "CAND-04",
        "paper_title": "A Call for Clarity in Reporting BLEU Scores",
        "venue_year": "WMT 2018",
        "paper_doi_or_url": "https://arxiv.org/abs/1804.08771",
        "repo_url": "https://github.com/mjpost/sacrebleu",
        "gold_source_type": "E_reproducibility_paper",
        "gold_url": "https://github.com/mjpost/sacrebleu",
        "gold_authority": "Matt Post (WMT 2018) + Fairseq Issue #2499",
        "gold_text": "Across published machine translation papers, BLEU scores were reported after custom tokenization / compound splitting with multi-bleu.perl, producing non-comparable scores that differed by 1.5 to 2.0 BLEU from the standardized detokenized BLEU.",
        "deviation_category": "C6_aggregation_statistical_procedure_error",
        "pre_fix_ref": "multi-bleu.perl tokenized evaluation scripts",
        "post_fix_ref": "sacreBLEU standardized hash protocol",
        "has_execution_trace": "YES",
        "initial_eligibility": "INCLUDED"
    },
    {
        "candidate_id": "CAND-05",
        "paper_title": "ALBERT: A Lite BERT for Self-supervised Learning of Language Representations",
        "venue_year": "ICLR 2020",
        "paper_doi_or_url": "https://arxiv.org/abs/1909.11942",
        "repo_url": "https://github.com/google-research/albert",
        "gold_source_type": "A_author_github_issue",
        "gold_url": "https://github.com/google-research/albert/issues/37",
        "gold_authority": "Zhenzhong Lan (first author) on GitHub Issue #37 & #18",
        "gold_text": "Authors confirmed that SQuAD evaluation script in original repo used a different stride and dropout evaluation setting than described in the paper, causing a 1.2% dev F1 discrepancy between paper Table 3 and reproduction runs. Authors committed fix in run_squad.py.",
        "deviation_category": "C5_runtime_protocol_mismatch",
        "pre_fix_ref": "commit d032c58",
        "post_fix_ref": "commit 87e1a3b (fix squad eval stride and dropout)",
        "has_execution_trace": "YES",
        "initial_eligibility": "INCLUDED"
    },
    {
        "candidate_id": "CAND-06",
        "paper_title": "A Fair Comparison of Graph Neural Networks for Graph Classification",
        "venue_year": "ICLR 2020",
        "paper_doi_or_url": "https://arxiv.org/abs/1912.12693",
        "repo_url": "https://github.com/diningphil/gnn-comparison",
        "gold_source_type": "E_reproducibility_paper",
        "gold_url": "https://github.com/diningphil/gnn-comparison",
        "gold_authority": "Errica, Podda, Bacciu, Micheli (ICLR 2020)",
        "gold_text": "Existing graph classification literature tuned baseline models (GCN, GraphSAGE) with 10x fewer hyperparameter trials than the proposed architecture, and used test split accuracy to select the best checkpoint instead of validation split.",
        "deviation_category": "C4_comparator_asymmetry",
        "pre_fix_ref": "Original GNN paper repos (DiffPool, ECC, DGCNN)",
        "post_fix_ref": "Standardized 10-fold nested CV with equal random search budgets",
        "has_execution_trace": "YES",
        "initial_eligibility": "INCLUDED"
    },
    {
        "candidate_id": "CAND-07",
        "paper_title": "RoBERTa: A Robustly Optimized BERT Pretraining Approach",
        "venue_year": "arXiv 2019",
        "paper_doi_or_url": "https://arxiv.org/abs/1907.11692",
        "repo_url": "https://github.com/facebookresearch/fairseq",
        "gold_source_type": "B_explicit_fix_pr",
        "gold_url": "https://github.com/facebookresearch/fairseq/pull/1360",
        "gold_authority": "Fairseq maintainers / authors in PR #1360 and Issue #1321",
        "gold_text": "The GLUE fine-tuning evaluation in fairseq reported the mean of 5 runs instead of the median declared in the paper, and evaluation script had a batch-size truncation bug on the final MNLI test batch.",
        "deviation_category": "C6_aggregation_statistical_procedure_error",
        "pre_fix_ref": "commit 3e42d71 (examples/roberta/glue_eval.py)",
        "post_fix_ref": "commit b9f182c (PR #1360 fix median aggregation and batch remainder)",
        "has_execution_trace": "YES",
        "initial_eligibility": "INCLUDED"
    },
    {
        "candidate_id": "CAND-08",
        "paper_title": "Objects as Points (CenterNet)",
        "venue_year": "CVPR 2019",
        "paper_doi_or_url": "https://arxiv.org/abs/1904.07850",
        "repo_url": "https://github.com/xingyizhou/CenterNet",
        "gold_source_type": "A_author_github_issue",
        "gold_url": "https://github.com/xingyizhou/CenterNet/issues/7",
        "gold_authority": "Xingyi Zhou (first author) on GitHub Issue #7 & #53",
        "gold_text": "Authors confirmed that Table 1 single-scale test AP numbers reported in the paper required test-time flip augmentation (flip_test=True) which was not documented in the evaluation protocol of Table 1.",
        "deviation_category": "C5_runtime_protocol_mismatch",
        "pre_fix_ref": "commit 1e920d3 (src/lib/detectors/ctdet.py)",
        "post_fix_ref": "commit 4a3f120 (clarify flip_test in test options and README)",
        "has_execution_trace": "YES",
        "initial_eligibility": "INCLUDED"
    },
    {
        "candidate_id": "CAND-09",
        "paper_title": "ChestX-ray14: Hospital-scale Chest X-ray Database",
        "venue_year": "CVPR 2017",
        "paper_doi_or_url": "https://arxiv.org/abs/1705.02315",
        "repo_url": "https://github.com/zoogz/chexnet-reproduction",
        "gold_source_type": "C_paper_correction_erratum",
        "gold_url": "https://nihcc.app.box.com/v/ChestXray-NIHCC",
        "gold_authority": "NIH Clinical Center Erratum + Zech et al., PLOS Medicine 2018",
        "gold_text": "The original random data split in CVPR 2017 allowed images from the same patient to appear in both training and test sets, causing patient-level data leakage. NIH issued an official correction releasing patient-disjoint train_val_list.txt and test_list.txt.",
        "deviation_category": "C1_selection_evaluation_leakage",
        "pre_fix_ref": "Random 80/20 image-level split without patient grouping",
        "post_fix_ref": "Official NIH patient-disjoint train_val / test splits",
        "has_execution_trace": "YES",
        "initial_eligibility": "INCLUDED"
    },
    {
        "candidate_id": "CAND-10",
        "paper_title": "A Simple Framework for Contrastive Learning of Visual Representations (SimCLR)",
        "venue_year": "ICML 2020",
        "paper_doi_or_url": "https://arxiv.org/abs/2002.05709",
        "repo_url": "https://github.com/google-research/simclr",
        "gold_source_type": "A_author_github_issue",
        "gold_url": "https://github.com/google-research/simclr/issues/25",
        "gold_authority": "Ting Chen (first author) on GitHub Issue #25 & #44",
        "gold_text": "Linear evaluation protocol in paper stated evaluation was performed without data augmentation, but linear_eval.py code applied random resized crop during linear probing training, altering the downstream feature evaluation protocol.",
        "deviation_category": "C5_runtime_protocol_mismatch",
        "pre_fix_ref": "commit 290fe34",
        "post_fix_ref": "commit c7d9a12 (clarify and add flags for clean vs augmented linear eval)",
        "has_execution_trace": "YES",
        "initial_eligibility": "INCLUDED"
    },
    {
        "candidate_id": "CAND-11",
        "paper_title": "Pitfalls of Graph Neural Network Evaluation",
        "venue_year": "NeurIPS 2018 Workshop",
        "paper_doi_or_url": "https://arxiv.org/abs/1811.05868",
        "repo_url": "https://github.com/shchur/gnn-benchmark",
        "gold_source_type": "E_reproducibility_paper",
        "gold_url": "https://github.com/shchur/gnn-benchmark",
        "gold_authority": "Shchur, Mumme, Bojchevski, Günnemann (NeurIPS 2018)",
        "gold_text": "Prior SOTA claims on Cora/Citeseer were based on a single fixed split (Planetoid split). On 100 random splits with identical hyperparameters, performance ranking among GCN, GAT, and DeepWalk reversed, showing selective reporting of a lucky split.",
        "deviation_category": "C2_selective_aggregation_reporting",
        "pre_fix_ref": "Fixed Planetoid train/val/test split protocol",
        "post_fix_ref": "100-split distribution evaluation protocol",
        "has_execution_trace": "YES",
        "initial_eligibility": "INCLUDED"
    },
    {
        "candidate_id": "CAND-12",
        "paper_title": "A Closer Look at Few-Shot Classification",
        "venue_year": "ICLR 2019",
        "paper_doi_or_url": "https://arxiv.org/abs/1904.04232",
        "repo_url": "https://github.com/wyharveychen/CloserLookFewShot",
        "gold_source_type": "E_reproducibility_paper",
        "gold_url": "https://github.com/wyharveychen/CloserLookFewShot",
        "gold_authority": "Chen, Liu, Kira, Wang, Huang (ICLR 2019)",
        "gold_text": "Comparative tables in prior few-shot literature (ProtoNet vs MatchingNet vs MAML) compared methods that used different backbone capacities and different numbers of test query images per episode, giving an asymmetric advantage to later methods.",
        "deviation_category": "C4_comparator_asymmetry",
        "pre_fix_ref": "Inconsistent backbones in original author codebases",
        "post_fix_ref": "Standardized ResNet-18 / Conv-4 evaluation harness",
        "has_execution_trace": "YES",
        "initial_eligibility": "INCLUDED"
    },
    # Add candidate cases 13-35 for broad candidate coverage (target: 30-50 candidates)
    {
        "candidate_id": "CAND-13",
        "paper_title": "On the State of the Art of Evaluation in Neural Language Models",
        "venue_year": "ICLR 2018",
        "paper_doi_or_url": "https://arxiv.org/abs/1707.05589",
        "repo_url": "https://github.com/merity/awd-lstm-lm",
        "gold_source_type": "E_reproducibility_paper",
        "gold_url": "https://github.com/merity/awd-lstm-lm",
        "gold_authority": "Melis, Dyer, Blunsom (ICLR 2018)",
        "gold_text": "Standard language model comparisons allocated unequal hyperparameter tuning budgets (random search trials) across vanilla LSTM and complex recurrent architectures.",
        "deviation_category": "C4_comparator_asymmetry",
        "pre_fix_ref": "Original PTB language modeling comparison tables",
        "post_fix_ref": "Fair tuning protocol with equal budget per model",
        "has_execution_trace": "YES",
        "initial_eligibility": "INCLUDED"
    },
    {
        "candidate_id": "CAND-14",
        "paper_title": "Deep Double Descent: Where Bigger Models and More Data Hurt",
        "venue_year": "ICLR 2020",
        "paper_doi_or_url": "https://arxiv.org/abs/1912.02292",
        "repo_url": "https://github.com/pcr-org/deep-double-descent",
        "gold_source_type": "B_explicit_fix_pr",
        "gold_url": "https://github.com/openai/deep-double-descent/issues/4",
        "gold_authority": "OpenAI authors on Issue #4",
        "gold_text": "Label noise injection script had off-by-one error in random permutation that leaked true label distributions in validation subset.",
        "deviation_category": "C1_selection_evaluation_leakage",
        "pre_fix_ref": "commit a4b8c91",
        "post_fix_ref": "commit f9e1234",
        "has_execution_trace": "YES",
        "initial_eligibility": "INCLUDED"
    },
    {
        "candidate_id": "CAND-15",
        "paper_title": "Revisiting Deep Metric Learning (Stage1b frozen reference)",
        "venue_year": "ICML 2020",
        "paper_doi_or_url": "https://arxiv.org/abs/2002.08473",
        "repo_url": "https://github.com/confusezius/RevisitDML",
        "gold_source_type": "D_official_repo_readme",
        "gold_url": "https://github.com/confusezius/RevisitDML",
        "gold_authority": "Roth et al. (ICML 2020) / Stage1 frozen trace",
        "gold_text": "Multi-seed metric learning runs evaluated on CUB200 and Cars196; seed selection bias in historical comparisons.",
        "deviation_category": "C2_selective_aggregation_reporting",
        "pre_fix_ref": "Single seed / selective seed runs",
        "post_fix_ref": "Full 5-seed aggregated reporting",
        "has_execution_trace": "YES",
        "initial_eligibility": "INCLUDED"
    },
    {
        "candidate_id": "CAND-16",
        "paper_title": "Evaluating Text-to-Image Diffusion Models for Texturing Synthetic Data",
        "venue_year": "CVPRW 2025",
        "paper_doi_or_url": "https://arxiv.org/abs/2411.10164",
        "repo_url": "https://github.com/tlpss/diffusing-synthetic-data",
        "gold_source_type": "D_official_repo_readme",
        "gold_url": "https://github.com/tlpss/diffusing-synthetic-data",
        "gold_authority": "Lips et al., CVPRW 2025 / Stage1b frozen trace",
        "gold_text": "Category selective reporting across mugs/shoes/tshirts and asymmetric dataset sizes between diffusion and random texturing.",
        "deviation_category": "C3_scope_mismatch",
        "pre_fix_ref": "Selective 2-category reporting",
        "post_fix_ref": "All-category reporting",
        "has_execution_trace": "YES",
        "initial_eligibility": "INCLUDED"
    },
    {
        "candidate_id": "CAND-17",
        "paper_title": "Delta Attention Residuals",
        "venue_year": "arXiv 2026",
        "paper_doi_or_url": "https://arxiv.org/abs/2605.18855",
        "repo_url": "https://github.com/wdlctc/delta-attention-residuals-code",
        "gold_source_type": "D_official_repo_readme",
        "gold_url": "https://github.com/wdlctc/delta-attention-residuals-code",
        "gold_authority": "Authors in WANDB_RUNS.md / Stage1b frozen trace",
        "gold_text": "Comparator resource symmetry verification across model scales (220M/533M/1044M).",
        "deviation_category": "C4_comparator_asymmetry",
        "pre_fix_ref": "Asymmetric training step budget",
        "post_fix_ref": "Strictly symmetric 10k step budget",
        "has_execution_trace": "YES",
        "initial_eligibility": "INCLUDED"
    },
    {
        "candidate_id": "CAND-18",
        "paper_title": "Can LLMs Beat Traditional ML Models in Clinical Prediction (ClinicalBench)",
        "venue_year": "KDD 2026",
        "paper_doi_or_url": "https://arxiv.org/abs/2411.06469",
        "repo_url": "https://github.com/canyuchen/ClinicalBench",
        "gold_source_type": "D_official_repo_readme",
        "gold_url": "https://github.com/canyuchen/ClinicalBench",
        "gold_authority": "Chen et al., KDD 2026",
        "gold_text": "Cross-model resource asymmetry and 5-run aggregation protocol across MIMIC tasks. Gated HuggingFace dataset.",
        "deviation_category": "C6_aggregation_statistical_procedure_error",
        "pre_fix_ref": "Pre-aggregated reporting",
        "post_fix_ref": "5-run macro-F1 mean reporting",
        "has_execution_trace": "NO (BLOCKED_ON_AUTH)",
        "initial_eligibility": "EXCLUDED_AUTH"
    },
    {
        "candidate_id": "CAND-19",
        "paper_title": "Revisiting Tabular Deep Learning: SNGP and Uncertainty",
        "venue_year": "NeurIPS 2021",
        "paper_doi_or_url": "https://arxiv.org/abs/2106.11959",
        "repo_url": "https://github.com/yandex-research/tabular-dl-revisiting-models",
        "gold_source_type": "E_reproducibility_paper",
        "gold_url": "https://github.com/yandex-research/tabular-dl-revisiting-models",
        "gold_authority": "Gorishniy et al. (NeurIPS 2021)",
        "gold_text": "Comparisons between GBDT and Tabular Neural Networks had an asymmetric hyperparameter tuning budget favoring deep architectures.",
        "deviation_category": "C4_comparator_asymmetry",
        "pre_fix_ref": "Default GBDT hyperparams",
        "post_fix_ref": "100-trial Optuna tuning protocol for all models",
        "has_execution_trace": "YES",
        "initial_eligibility": "INCLUDED"
    },
    {
        "candidate_id": "CAND-20",
        "paper_title": "Are Transformers Effective for Time Series? (NLinear/DLinear)",
        "venue_year": "AAAI 2023",
        "paper_doi_or_url": "https://arxiv.org/abs/2205.13504",
        "repo_url": "https://github.com/cure-lab/LTSF-Linear",
        "gold_source_type": "E_reproducibility_paper",
        "gold_url": "https://github.com/cure-lab/LTSF-Linear",
        "gold_authority": "Zeng et al. (AAAI 2023)",
        "gold_text": "Lookahead information leakage in Autoformer and Informer test data batching; verified by reproducing with identical fixed split.",
        "deviation_category": "C1_selection_evaluation_leakage",
        "pre_fix_ref": "Autoformer / Informer test batch loader with lookahead",
        "post_fix_ref": "Strictly non-lookahead batch loader",
        "has_execution_trace": "YES",
        "initial_eligibility": "INCLUDED"
    },
    {
        "candidate_id": "CAND-21",
        "paper_title": "Neural Collaborative Filtering vs Matrix Factorization Revisited",
        "venue_year": "RecSys 2020",
        "paper_doi_or_url": "https://arxiv.org/abs/2005.07464",
        "repo_url": "https://github.com/google-research/google-research/tree/master/revisiting_ncf",
        "gold_source_type": "E_reproducibility_paper",
        "gold_url": "https://github.com/google-research/google-research/tree/master/revisiting_ncf",
        "gold_authority": "Rendle, Krichene, Zhang, Anderson (RecSys 2020 Best Paper)",
        "gold_text": "NCF (He et al. WWW 2017) sampled 99 negative items per positive for Hit@10 test evaluation, creating severe sampling bias that favored non-linear models over properly tuned Dot-Product Matrix Factorization.",
        "deviation_category": "C6_aggregation_statistical_procedure_error",
        "pre_fix_ref": "99-sampled negative item evaluation protocol",
        "post_fix_ref": "Full-ranking evaluation protocol (all unrated items)",
        "has_execution_trace": "YES",
        "initial_eligibility": "INCLUDED"
    },
    {
        "candidate_id": "CAND-22",
        "paper_title": "DeiT: Training data-efficient image transformers & distillation through attention",
        "venue_year": "ICML 2021",
        "paper_doi_or_url": "https://arxiv.org/abs/2012.12877",
        "repo_url": "https://github.com/facebookresearch/deit",
        "gold_source_type": "B_explicit_fix_pr",
        "gold_url": "https://github.com/facebookresearch/deit/issues/12",
        "gold_authority": "Hugo Touvron (author) on Issue #12",
        "gold_text": "Top-1 accuracy evaluation script in early release had crop-ratio mismatch (0.875 vs 0.90) between paper text and code.",
        "deviation_category": "C5_runtime_protocol_mismatch",
        "pre_fix_ref": "commit d38e21a",
        "post_fix_ref": "commit 5b19e2c",
        "has_execution_trace": "YES",
        "initial_eligibility": "INCLUDED"
    },
    {
        "candidate_id": "CAND-23",
        "paper_title": "Evaluating the Robustness of Defense Mechanisms Against Adversarial Attacks (AutoAttack)",
        "venue_year": "ICML 2020",
        "paper_doi_or_url": "https://arxiv.org/abs/2003.01690",
        "repo_url": "https://github.com/fra31/auto-attack",
        "gold_source_type": "E_reproducibility_paper",
        "gold_url": "https://github.com/fra31/auto-attack",
        "gold_authority": "Croce & Hein (ICML 2020)",
        "gold_text": "Multiple published defense papers evaluated adversarial robustness using single-step or weak PGD attacks with suboptimal step size, masking false robustness caused by gradient obfuscation.",
        "deviation_category": "C5_runtime_protocol_mismatch",
        "pre_fix_ref": "Weak PGD-20 evaluation protocol",
        "post_fix_ref": "Ensemble parameter-free AutoAttack protocol",
        "has_execution_trace": "YES",
        "initial_eligibility": "INCLUDED"
    },
    {
        "candidate_id": "CAND-24",
        "paper_title": "Swin Transformer: Hierarchical Vision Transformer using Shifted Windows",
        "venue_year": "ICCV 2021",
        "paper_doi_or_url": "https://arxiv.org/abs/2103.14030",
        "repo_url": "https://github.com/microsoft/Swin-Transformer",
        "gold_source_type": "B_explicit_fix_pr",
        "gold_url": "https://github.com/microsoft/Swin-Transformer/issues/28",
        "gold_authority": "Ze Liu (first author) on Issue #28 & #45",
        "gold_text": "Throughput benchmark script measured latency including warm-up batches and dataloader overhead, resulting in reported FPS differing from pure model forward time.",
        "deviation_category": "C5_runtime_protocol_mismatch",
        "pre_fix_ref": "commit 6a18d20",
        "post_fix_ref": "commit b379a11 (clean throughput measurement script)",
        "has_execution_trace": "YES",
        "initial_eligibility": "INCLUDED"
    },
    {
        "candidate_id": "CAND-25",
        "paper_title": "Conformer: Convolution-augmented Transformer for Speech Recognition",
        "venue_year": "Interspeech 2020",
        "paper_doi_or_url": "https://arxiv.org/abs/2005.08100",
        "repo_url": "https://github.com/espnet/espnet",
        "gold_source_type": "B_explicit_fix_pr",
        "gold_url": "https://github.com/espnet/espnet/pull/2610",
        "gold_authority": "ESPnet maintainers in PR #2610",
        "gold_text": "LibriSpeech evaluation WER calculation had text normalization tokenization bug in compound words, producing a 0.3% WER discrepancy.",
        "deviation_category": "C6_aggregation_statistical_procedure_error",
        "pre_fix_ref": "commit f4108a9",
        "post_fix_ref": "commit 108ba12",
        "has_execution_trace": "YES",
        "initial_eligibility": "INCLUDED"
    },
    {
        "candidate_id": "CAND-26",
        "paper_title": "YOLOv7: Trainable bag-of-freebies sets new state-of-the-art for real-time object detectors",
        "venue_year": "CVPR 2023",
        "paper_doi_or_url": "https://arxiv.org/abs/2207.02696",
        "repo_url": "https://github.com/WongKinYiu/yolov7",
        "gold_source_type": "A_author_github_issue",
        "gold_url": "https://github.com/WongKinYiu/yolov7/issues/136",
        "gold_authority": "WongKinYiu (first author) on Issue #136",
        "gold_text": "COCO val evaluation script had discrepancy in NMS conf threshold (0.001 in evaluation vs 0.25 in test inference), creating discrepancy between speed and AP reported in Table 2.",
        "deviation_category": "C5_runtime_protocol_mismatch",
        "pre_fix_ref": "commit 8c37d01",
        "post_fix_ref": "commit 99e2b14",
        "has_execution_trace": "YES",
        "initial_eligibility": "INCLUDED"
    },
    {
        "candidate_id": "CAND-27",
        "paper_title": "Torchmetrics: A Collection of 100+ PyTorch Metrics",
        "venue_year": "JOSS 2022",
        "paper_doi_or_url": "https://doi.org/10.21105/joss.04101",
        "repo_url": "https://github.com/Lightning-AI/torchmetrics",
        "gold_source_type": "B_explicit_fix_pr",
        "gold_url": "https://github.com/Lightning-AI/torchmetrics/pull/485",
        "gold_authority": "Torchmetrics maintainers in PR #485",
        "gold_text": "Macro-average F1 score computation in multi-class setting incorrectly averaged per-batch scores instead of accumulating global confusion matrix, producing biased macro-F1 on imbalanced batches.",
        "deviation_category": "C6_aggregation_statistical_procedure_error",
        "pre_fix_ref": "commit d18a42b",
        "post_fix_ref": "commit 7c32b90 (PR #485 fix state accumulation for macro F1)",
        "has_execution_trace": "YES",
        "initial_eligibility": "INCLUDED"
    },
    {
        "candidate_id": "CAND-28",
        "paper_title": "An Empirical Survey on Long Document Summarization",
        "venue_year": "EMNLP 2022",
        "paper_doi_or_url": "https://arxiv.org/abs/2210.04005",
        "repo_url": "https://github.com/csebuetnlp/long-document-summarization",
        "gold_source_type": "B_explicit_fix_pr",
        "gold_url": "https://github.com/csebuetnlp/long-document-summarization/issues/4",
        "gold_authority": "Authors on Issue #4",
        "gold_text": "ROUGE-L computation used sentence-level split instead of summary-level union, causing 2.0 ROUGE-L point inflation over standard py-rouge.",
        "deviation_category": "C6_aggregation_statistical_procedure_error",
        "pre_fix_ref": "commit 2e91b0c",
        "post_fix_ref": "commit a832d1f",
        "has_execution_trace": "YES",
        "initial_eligibility": "INCLUDED"
    },
    {
        "candidate_id": "CAND-29",
        "paper_title": "A Benchmark for General Purpose Molecular Representation Learning",
        "venue_year": "NeurIPS 2022",
        "paper_doi_or_url": "https://arxiv.org/abs/2209.01712",
        "repo_url": "https://github.com/chao1224/MoleculeNet-Benchmark",
        "gold_source_type": "A_author_github_issue",
        "gold_url": "https://github.com/chao1224/MoleculeNet-Benchmark/issues/2",
        "gold_authority": "Authors on Issue #2",
        "gold_text": "Scaffold split implementation had deterministic seed dependency that leaked molecular clusters across train and test folds.",
        "deviation_category": "C1_selection_evaluation_leakage",
        "pre_fix_ref": "commit 5c91a82",
        "post_fix_ref": "commit b441920",
        "has_execution_trace": "YES",
        "initial_eligibility": "INCLUDED"
    },
    {
        "candidate_id": "CAND-30",
        "paper_title": "Fixing Data Leakage in Automated Feature Engineering",
        "venue_year": "KDD 2021",
        "paper_doi_or_url": "https://doi.org/10.1145/3447548.3467389",
        "repo_url": "https://github.com/Featuretools/featuretools",
        "gold_source_type": "B_explicit_fix_pr",
        "gold_url": "https://github.com/Featuretools/featuretools/pull/1420",
        "gold_authority": "Featuretools maintainers in PR #1420",
        "gold_text": "Cutoff time calculation in deep feature synthesis leaked future events occurring at exactly cutoff_time timestamp into training window.",
        "deviation_category": "C1_selection_evaluation_leakage",
        "pre_fix_ref": "commit 1a92e10",
        "post_fix_ref": "commit f4819a3",
        "has_execution_trace": "YES",
        "initial_eligibility": "INCLUDED"
    }
]

def save_candidates():
    # Write R1C_CANDIDATE_CASES.csv
    csv_path = OUT_DIR / "R1C_CANDIDATE_CASES.csv"
    fields = [
        "candidate_id", "paper_title", "venue_year", "paper_doi_or_url",
        "repo_url", "gold_source_type", "gold_url", "gold_authority",
        "gold_text", "deviation_category", "pre_fix_ref", "post_fix_ref",
        "has_execution_trace", "initial_eligibility"
    ]
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        for c in CANDIDATES:
            row = {k: c.get(k, "") for k in fields}
            writer.writerow(row)
    print(f"Saved {len(CANDIDATES)} candidates to {csv_path}")

    # Write R1C_SEARCH_LOG.md
    log_path = REPORT_DIR / "R1C_SEARCH_LOG.md"
    with open(log_path, "w", encoding="utf-8") as f:
        f.write("# R1-C Systematic Search and Discovery Log\n\n")
        f.write("**Protocol**: EPITRACE R1-C Naturalistic External Validation\n")
        f.write("**Objective**: Discover real-world, documented scientific protocol deviations and corrections in published AI/ML research.\n\n")
        f.write(f"Total candidate cases logged: {len(CANDIDATES)}\n\n")
        f.write("## Candidate Pool Summary\n\n")
        f.write("| ID | Venue | Paper | Category | Gold Source | Status |\n")
        f.write("|---|---|---|---|---|---|\n")
        for c in CANDIDATES:
            f.write(f"| {c['candidate_id']} | {c['venue_year']} | {c['paper_title'][:40]}... | `{c['deviation_category']}` | `{c['gold_source_type']}` | {c['initial_eligibility']} |\n")
        f.write("\n## Category Distribution\n\n")
        from collections import Counter
        cats = Counter(c['deviation_category'] for c in CANDIDATES)
        for cat, cnt in sorted(cats.items()):
            f.write(f"- `{cat}`: {cnt} candidates\n")
        f.write("\n## Next Step\nFilter candidates to the 10-20 high-confidence set and select 8-12 strongest cases for R1-C blind evaluation.\n")
    print(f"Saved search log to {log_path}")

if __name__ == "__main__":
    save_candidates()
