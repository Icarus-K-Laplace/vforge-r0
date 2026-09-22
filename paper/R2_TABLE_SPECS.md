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

Source: `results/R1B1_REAL_TRACE_PAIRS.jsonl` (48 pairs) + `R1B1_VPVD.csv`.
Columns: paper/repo, family, n_vps_pairs, value_preserving_fraction,
ε used, EpiTrace detection, static baseline B2.
- Headline: 48/48 value-preserving pairs detected; VPS range ~0.05–0.24.

## Table 4 — R1-C Naturalistic Cases

Source: `results/R1C_*` + `results/R2_R1C_CASE_FORENSICS.csv`.
One row per case (8). Columns:
- Case ID, paper, venue, deviation family (C1/C2/C4/C5/C6),
- predicted constraint, pre_verdict, post_verdict, paired_correct,
- semantic_match, localization_match, witness,
- **gold authority tier** (E_reproducibility_paper / B_fix_pr / A_author_issue),
- **trace basis** (live re-execution / documented-protocol),
- forensic grade (A).
- Footer: NVR, NPCR, witness accuracy, CIA (audited), 95% CI on NVR.

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

## Appendix Tables
- A: All 8 forensic chains (one page each; from R2_R1C_CASE_FORENSICS.csv
  + R2_R1C_FORENSIC_AUDIT.md).
- B: All contracts (8) + principle templates P1–P6 (from
  r1c/contracts_r1c/*_CONTRACT.json).
- C: All witness outputs (from r1c/results/R1C_WITNESS_AUDIT.csv +
  R1C_GOLD_MATCH.jsonl).
- D: R1-D2 search-negative (476-lead adjudication summary; from
  r1d/results/R1D_LEAD_ADJUDICATION.csv).
- E: Full prior-art matrix (Table 1 source + per-cell citations).
- F: Witness semantic-match rubric + witness→gold-locus mapping.
- G: ε definition and per-experiment values (R1-B1_VPVD.csv vps column).
- H: Gold authority tiering + per-case independent sources.
