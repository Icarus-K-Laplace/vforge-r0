# EpiTrace: Appendix Plan

Appendices support the main paper without expanding its length. Each
appendix lists source, content, and the reviewer objection it answers.

## Appendix A — All 8 Naturalistic Forensic Chains
- **Source**: `reports/R2_R1C_FORENSIC_AUDIT.md` +
  `results/R2_R1C_CASE_FORENSICS.csv`.
- **Content**: One page per case (CAND-01 … CAND-08) with the full
  20-field chain: paper, claim, protocol statement, paper hash, pre-fix
  repo/commit, runtime/provenance evidence, contract-generation timestamp
  + hash, blind-prediction timestamp + hash, predicted violated
  constraint, predicted witness, gold evidence source + authority type,
  gold-reveal timestamp, gold violation semantics, fix PR/commit/erratum,
  post-fix state, post-fix verdict, semantic match, localization match,
  leakage audit status.
- **Answers**: C1 (leakage), C4 (post-trace provenance).

## Appendix B — All Contracts + Principle Templates
- **Source**: `r1c/contracts_r1c/CAND-{01..08}_CONTRACT.json` +
  `reports/R2_CONTRACT_AUDIT.md`.
- **Content**: Full 8 contracts (predicate, natural-language statement,
  trace fields, condition, confidence), the P1–P6 principle template
  definitions, and the audit classification (EXPLICIT / PRINCIPLE-INDUCED
  / OVERREACH / FAULT_SPECIFIC / AMBIGUOUS) per contract.
- **Answers**: A5 (induction scope), B6 (CIA=1.0 defensibility).

## Appendix C — All Witness Outputs
- **Source**: `r1c/results/R1C_WITNESS_AUDIT.csv` +
  `R1C_GOLD_MATCH.jsonl`.
- **Content**: For each of the 8 cases: the predicted witness (predicate
  id + trace entities + detail) and the gold violation locus, with the
  semantic-match and localization-match judgment.
- **Answers**: A9 (witness epistemic content), C5 (match rubric), C9
  (localization to own schema).

## Appendix D — R1-D2 Search-Negative Control
- **Source**: `r1d/results/R1D_LEAD_ADJUDICATION.csv` +
  `reports/R1D_EXPANSION_REPORT.md`.
- **Content**: 476/476 leads adjudicated; status distribution
  (0 CONFIRMED, 428 non-scientific, 15 no-paper-link, 24 no-gold-
  confirmation, 9 no-recoverable-prefix); the 6 quota-blocked repos
  (C3/C4/C6 families) explicitly marked unsampled; the 8 API-call fetch
  accounting.
- **Answers**: B9 (unsearched families), C2/C8 (cherry-picking /
  fragility).

## Appendix E — Full Prior-Art Matrix
- **Source**: `results/R2_PRIOR_ART_MATRIX.csv` +
  `reports/R2_NOVELTY_DEFENSE.md`.
- **Content**: 9-system × 10-axis matrix with per-cell source
  citations; UNKNOWN cells retained; nearest-neighbor diff paragraphs.
- **Answers**: A1 (P-PLAN overlap), novelty positioning.

## Appendix F — Witness Match Rubric + Locality Mapping
- **Content**: The exact rubric for "semantic match = TRUE" (predicted
  predicate vs. gold violation locus), who/what judged it, and the
  witness-node → gold-violation-locus mapping for all 8 cases.
- **Answers**: C5, C9, A9.

## Appendix G — ε Definition and Per-Experiment Values
- **Source**: `results/R1B1_VPVD.csv` (vps column).
- **Content**: Formal ε definition, per-experiment ε values (from
  paper-reported seed variability where available, else fixed fraction
  of dynamic range), and the VPS distribution (range ~0.05–0.24).
- **Answers**: A7, B4.

## Appendix H — Gold Authority Tiering + Independent Sources
- **Content**: Tier ordering (E_reproducibility_paper > B_explicit_fix_pr
  > A_author_github_issue), per-case primary vs. corroborating gold, and
  the ≥2-source requirement per case (issues paired with author/PR/paper).
- **Answers**: C3, C10.

---

## Ordering & Length Budget
Main paper (10 sections + 5 tables + 4–5 figures) targets ~9 pages.
Appendices A–H are unpaginated references. The heaviest are A (8 pages,
one per case) and E (matrix + 9 paragraphs); the rest are short.

## Cross-Reference Rule
Every number in a main table or figure cites its frozen artifact in the
caption. No number appears that is not in a `results/` or `r1d/results/`
file. This keeps the paper reproducible from the repo alone.
