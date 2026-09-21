# SciCoQA Benchmark Freeze Documentation

## R0-D Data Freeze Protocol

### Benchmark Source
- **Name**: SciCoQA (Scientific Code-QA)
- **Version**: [To be determined from official release]
- **Release Date**: [To be recorded]
- **URL**: https://github.com/.../SciCoQA (to be filled)

### Freeze Date
2026-09-20

### Freeze Hash
[To be computed after download]

---

## Dataset Facts (Official Release)

### Structure
- Total samples: [TBD]
- Train split: [TBD]
- Dev split: [TBD] 
- Test split (real): [TBD]

### Categories
1. Paper Omission
2. Hyperparameter Mismatch
3. Data/Preprocessing Mismatch
4. Evaluation Mismatch
5. Implementation Mismatch
6. Reporting Mismatch
7. Other

### Fields (Forbidden to SI-D during development)
- discrepancy_description
- relevant_code_files
- origin_issue_text
- changed_code_annotation
- fix_commit_identity
- gold_classification

### Fields (Allowed)
- paper_text
- repository_url
- commit_hash
- configuration_files
- scripts

---

## Leakage Prevention Protocol

### Phase 1: Development (Current)
- NO access to gold labels
- NO access to discrepancy descriptions
- NO access to relevant code annotations
- SI-D induces invariants from paper text ONLY

### Phase 2: Prediction Freeze
- Generate all predictions
- Hash prediction ledger
- Lock predictions

### Phase 3: Evaluation
- Only NOW reveal gold information
- Compare predictions to ground truth
- Compute metrics

---

## Data Sources

### Primary
SciCoQA official release (real splits)

### Secondary (for ablation)
- Synthetic controlled studies (R0-B/R0-C data)
- Paired counterfactuals (pre-fix/post-fix commits)

---

## Ethical Notes
- This benchmark contains real scientific errors
- Handle with appropriate scientific rigor
- Results should contribute to reproducibility research
