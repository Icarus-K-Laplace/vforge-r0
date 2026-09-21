# R1-C §? Error Analysis

**Date**: 2026-09-21

## Overall Performance

- Total naturalistic cases evaluated: 8
- Pre-fix FAIL detections (NVR numerator): 8/8
- Paired pre->FAIL, post->PASS corrections (NPCR numerator): 8/8

## Per-Case Results

| Case | Pre-verdict | Post-verdict | Paired Correct |
|---|---|---|---|
| CAND-01 | FAIL | PASS | True |
| CAND-02 | FAIL | PASS | True |
| CAND-03 | FAIL | PASS | True |
| CAND-04 | FAIL | PASS | True |
| CAND-05 | FAIL | PASS | True |
| CAND-06 | FAIL | PASS | True |
| CAND-07 | FAIL | PASS | True |
| CAND-08 | FAIL | PASS | True |

## Baseline Comparison

- All baselines B0-B4 achieved 0/8 paired-correction detection vs EpiTrace 8/8.
- The primary B3 vs EpiTrace comparison confirmed that raw runtime provenance, without an induced paper-derived epistemic contract, is insufficient to automatically localize naturalistic scientific protocol violations.

## Value-Preserving Naturalistic Cases (Flagship)

- CAND-04 (BLEU reporting) and CAND-07 (RoBERTa GLUE aggregation) identified as naturalistic value-preserving violations (VPV) where the reported final scalar difference between pre-fix and post-fix states was minimal or zero, but the epistemic validity of the execution changed.

## Errors / Misses

- No false positives: all pre-verdicts matching 'FAIL' corresponded to documented gold violations; all post-verdicts matching 'PASS' corresponded to fixed corrections.
- No cases were dropped post-hoc based on EpiTrace performance (case set was frozen prior to evaluation, per protocol §8).