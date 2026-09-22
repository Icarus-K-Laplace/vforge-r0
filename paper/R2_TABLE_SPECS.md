# EpiTrace: Table Specifications (V0)

---

## Table 1 — Prior-Art Capability Matrix

Source: `results/R2_PRIOR_ART_MATRIX.csv` (10 systems × 10 axes).
- Rows: P-PLAN, Workflow Run RO-Crate, Validity Constraints 2024,
  MLflow2PROV, CiteArk CAP, Scientific Admissibility / execution-
  evidence, AI-assisted spec-to-exec, paper-code discrepancy, EpiTrace.
- Columns: captures runtime provenance / represents intended workflow /
  supports constraints / auto-induces from paper protocol / epistemic (not
  operational) / checks actual execution / same-paper-same-code paired
  discrimination / detects value-preserving violation / localizes witness /
  validated on natural historical corrections.
- Every cell backed by a source or marked UNKNOWN (never downgraded to NO).
- EpiTrace row is the claim row; the paper's novelty is the only row that
  is YES on auto-induction + epistemic + VPVD + naturalistic validation.

## Table 2 — R1-A Controlled Identifiability

Source: `results/R1A_PAIR_RESULTS.jsonl` (30 pairs) + `R1A_ABLATIONS.csv`.
Columns: family, n_pairs, EpiTrace PSD, B0 paper-only, B1 paper+repo,
B2 static auditor, B3/B4 random/generic, A3 provenance-w/o-contract,
ABSTAIN count.
- Headline: EpiTrace PSD = 1.0 (30/30); all baselines 0.0; A3 = 0.
- Report the 2 ABSTAIN cases (E03-03, E06-05) explicitly.

## Table 3 — R1-B1 Real-Trace Cross-Paper

Source: `results/R1B1_REAL_TRACE_PAIRS.jsonl` (48 claim-level pairs) +
`R1B1_VPVD.csv` (36 strict value-preserving pairs).
Columns: paper/repo, family, n_pairs, strict-VPS subset (VPS ≤ 0.25),
EpiTrace PSD, B2 static, B3 provenance-only, B4 result-matching.
- Sources: 2 public-trace repositories (ViewBatchModel CVPR'25,
  RevisitDML ICML'20); 48 claim-level pairs total.
- **Headline: EpiTrace PSD = 48/48 = 1.0 (95% CI [0.926, 1.000]);
  strict value-preserving subset = 36/36 (95% CI [0.903, 1.000]);
  B2/B3/B4 all = 0/48.** VPS range [0.052, 0.651]; strict-VPS
  range [0.052, 0.246], mean 0.181.

## Table 4 — R1-C Naturalistic Cases (polished)

Source: `results/R1C_*` + `results/R2_R1C_CASE_FORENSICS.csv` +
`paper/R2_CI_VALUES.json` + `paper/R2_EPS_DEFINITION.md`.

One row per case (8). Columns (in order):

| Column | Notes |
|---|---|
| Case ID | CAND-01 … CAND-08 |
| Paper | title (short form) |
| Venue | e.g., AAAI 2021 |
| Family | C1 / C2 / C4 / C5 / C6 |
| Predicted constraint | e.g., DISJOINT_TEST_SELECTION |
| Pre / Post verdict | FAIL / PASS |
| Paired correct | True/False |
| Semantic / Loc match | both TRUE for all 8 |
| **Gold tier** | E_reproducibility_paper (5) / B_explicit_fix_pr (1) / A_author_github_issue (2). Primary evidential weight on E and B; A corroborates. |
| **Trace basis** | All 8 = documented_protocol_reconstruction (no live pre-fix re-execution available; E02=TRACE_INSUFFICIENT). Flagged per case, not hidden. |
| **Value-preserving?** | 2 of 8 flagged VP (from `R1C_NATURALISTIC_METRICS.json`). The remaining 6 are process-violating but not value-preserving. |
| Forensic grade | All A |

**Footer (statistics at n = 8 — do NOT report only "8/8 = 100%"):**
- NVR = 8/8 = 1.0; **95% Clopper–Pearson CI = [0.631, 1.000]**
- NPCR = 8/8 = 1.0; **95% CI = [0.631, 1.000]**
- Witness Accuracy = 8/8 = 1.0; **95% CI = [0.631, 1.000]**
- CIA = 8/8 = 1.0 (audited: 5 EXPLICIT, 3 PRINCIPLE-INDUCED, 0 fault-specific); **95% CI = [0.631, 1.000]**
- ε / value-preserving threshold: see Appendix G (`R2_EPS_DEFINITION.md`).
- Note: "1.0" is a *detectability* point estimate at n = 8; the CI
  [0.631, 1.000] is the honest inferential statement. We do NOT claim
  population recall = 1.0.

## Table 5 — Ablations (consolidated, §10)

Source: `results/R1A_ABLATIONS.csv` + R1-C baseline columns.
Rows = ablation conditions, Columns = PSD / detection on VP pairs:
- A1 paper + result only
- A2 paper + static code
- A3 full provenance **without** epistemic contract
- A4 result matching
- A5 EpiTrace (full)
- (manual/generic invariant where existing experiments support it)
Key comparisons called out in the body: **A3 vs A5** (is the contribution
the trace or the constraint?) and **A4 vs A5 on VP cases** (can result
matching see process invalidity?).
- Report PSD with 95% CI: EpiTrace PSD = 30/30 = 1.0, **95% CI =
  [0.884, 1.000]**; baselines B0–B4 = 0/30 = 0.0, **95% CI = [0.000, 0.116]**.

## Appendix Tables
- A: All 8 forensic chains (one page each; from R2_R1C_CASE_FORENSICS.csv
  + R2_R1C_FORENSIC_AUDIT.md).
- B: All contracts (8) + principle templates P1–P6 (from
  r1c/contracts_r1c/*_CONTRACT.json).
- C: All witness outputs (from r1c/results/R1C_WITNESS_AUDIT.csv +
  R1C_GOLD_MATCH.jsonl).
- D: R1-D2 search-negative (476-lead adjudication summary; from
  r1d/results/R1D_LEAD_ADJUDICATION.csv). Report 0/476 confirmed with
  **95% CI on the upper bound = [0.000, 0.008]** (specificity).
- E: Full prior-art matrix (Table 1 source + per-cell citations).
- F: Witness semantic-match rubric + witness→gold-locus mapping.
- G: ε definition and per-experiment values (`R2_EPS_DEFINITION.md` +
  R1B1_VPVD.csv vps column, range [0.052, 0.246]).
- H: Gold authority tiering + per-case independent sources.
- I: Trace self-hash verification note: the 16 frozen pre/post trace
  files carry `self_hash` fields that do NOT recompute under any
  standard JSON serialization (insertion-order compact, sorted-key
  compact, or sorted-key pretty). This is recorded as a forensic
  finding: the trace hashes are opaque integrity markers from the
  original build run; the trace *content* itself is verified consistent
  with the gold evidence and the paired-correction results. This is a
  limitation, not a failure — it means trace-level cryptographic
  integrity is not independently verifiable post-hoc, which §9
  (Limitations) states explicitly.
