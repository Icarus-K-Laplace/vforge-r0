# R2V2 Phase 6b: Table Layout (main paper)

Two tables only in the 8-page body. Everything else to Appendix.

## Table 1 — Prior-art positioning (3-level + 10 systems, compact)

One-row-per-axis, three columns (Provenance / Operational / EpiTrace)
with the 10 surveyed systems named under their level; full 10×10
matrix in Appendix D. This keeps Related Work to one paragraph
(§3) + one small table.

| Level (question) | Systems (our survey) | Does EpiTrace do it |
|---|---|---|
| **Provenance** — *what happened?* | P-PLAN, RO-Crate Workflow Run, MLflow2PROV | YES (records G_T) |
| **Operational workflow validity** — *did execution obey the declared plan?* | P-PLAN hand-specified constraints; "Validity Constraints for Data Analysis Workflows" (2024) | YES (checks Φ_C; constraints are epistemic, not operational) |
| **EpiTrace** — *is the process admissible for the claim?* | paper–code: ReproZip, Paper2Code, RePro · citation: CiteArk/CAP · execution-evidence / admissibility · AI workflow spec-to-exec (LLM generators) | YES (derives Φ_C from paper protocol, no bug access; localized witness; naturalistic validation) |

Footnote: "Cells reflect *published descriptions* we surveyed; where
we did not find evidence a system performs a capability we say so
explicitly rather than assert it cannot. UNKNOWN cells in Appendix D are
retained, not downgraded to NO."

## Table 2 — Main results (combined R1-A + R1-B1)

Per `R2_FIGURE_LAYOUT_V2.md`:

| TIER | source | n | EpiTrace PSD (95% CI) | strict-VPS (n) | B0 | B1 | B2 | B3 | B4 |
|---|---|---|---|---|---|---|---|---|---|
| R1-A | same-paper/same-code, 6 families | 30 | **27/30 = 0.900** [0.735, 0.994] | — | 0/30 | 0/30 | 0/30 | 0/30 | 0/30 |
| R1-B1 | 2 public repos | 48 | **48/48 = 1.000** [0.926, 1.000] | 36/36 [0.903, 1.000] | 0/48 | 0/48 | 0/48 | 0/48 | 0/48 |

Footnote: "PSD = fraction of pairs with clean PASS / invalid FAIL.
30/30 (R1-A) is the pair-construction property, not a discrimination
score. Strict-VPS = VPS ≤ 0.25 (Appendix G). B0 paper-final, B1
paper+repo, B2 +config, B3 provenance-only, B4 result-matching. 95%
CIs Clopper–Pearson."

## Table 3 — Naturalistic R1-C (8 cases)

Per `R2_FIGURE_LAYOUT_V2.md` (case, violation class, trace basis, gold
tier, pre/post verdict, semantic match; CIs in caption; all pre FAIL /
post PASS; NVR = NPCR = witness = CIA = 8/8, 95% CI [0.631, 1.000]).

## Appendix tables (not in body)
- Appendix D: full 10-system × 10-axis matrix (source:
  `results/R2_PRIOR_ART_MATRIX.csv` / `R2_NOVELTY_DEFENSE.md` matrix).
- Appendix C: per-pair baseline verdicts (B0–B4 × 78 pairs).
- Appendix E: R1-D2 476-lead adjudication table (428/24/15/9 + gate).
- Appendix F: witness localization per case.
- Appendix G: ε / VPS threshold table (0.25 strict-VPS; observed
  ranges; per-experiment ε rule).
