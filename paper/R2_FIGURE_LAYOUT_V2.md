# R2V2 Phase 6: Figure / Table Final Layout

Main-paper priority: 4 visual objects. Two-column ICML; each object's
one-line visual thesis. Figures 1–4 already rendered as SVG in
`paper/figures/` (V1); this doc finalizes their content and the two
main tables.

---

## Figure 1 — Core thesis (REQUIRED first-page object)

**Visual thesis: SAME REPORTED RESULT, DIFFERENT EVIDENTIAL VALIDITY.**
Must be understood in ~30 s without the caption.

Layout (two stacked execution panels sharing a common "reported value"
badge in the middle):

- Left panel "Execution A (admissible)": split diagram shows 5 seeds all
  fed into the mean; badge `ȳ = 0.731`.
- Right panel "Execution B (not admissible)": 5 seeds, but 2 greyed /
  struck-through (outcome-conditioned); the surviving 3 fed into the
  mean; badge `ȳ = 0.732` (≈ same).
- Center: an `≡` on the value row (`0.731 ≈ 0.732 → value check: PASS`)
  and a `⊥` on the process row (`A: 5/5 seeds ⊨, B: 3/5 seeds ⊭
  SEED_AGGREGATION → EpiTrace: A PASS, B FAIL`).
- Bottom strip: `same result ≠ same evidential validity`.

The number pair must visually read as *equal at face value* (the 0.1
difference rendered as `≈`). No caption dependence: panel labels carry
the argument.

SVG: `paper/figures/figure1_concept.svg` (V1 version used a generic
Φ_C box; final layout replaces the generic pipeline with the explicit
seeds example above so the VPVD is concrete on first read).

## Figure 2 — Same-paper / same-code identifiability

**Visual thesis: static information identical, runtime trace differs.**
Two columns (clean | invalid) with three rows:
- Row 1 "Static (paper + repo)": identical, both stamped `✓ same`.
- Row 2 "Runtime trace": diverge icon (selection node differs: all-seeds
  vs. best-3).
- Row 3 "Static verifier": both `ABSTAIN/IDENTICAL` (a static auditor
  sees no difference); "EpiTrace": clean `PASS`, invalid `FAIL`.
Caption one-liner: a static verifier is blind to the difference; only
the trace carries it.

SVG: `paper/figures/figure2_identifiability.svg`.

## Main Results Table — combined controlled + real-trace

Single combined table (avoid many tiny tables). Columns:

| TIER | source | n pairs | EpiTrace PSD (95% CI) | strict-VPS (n) | B0 | B1 | B2 | B3 | B4 |
|---|---|---|---|---|---|---|---|---|---|
| R1-A controlled | same-paper/same-code, 6 families | 30 | **27/30 = 0.900** [0.735, 0.994] | — | 0/30 | 0/30 | 0/30 | 0/30 | 0/30 |
| R1-B1 real-trace | 2 public repos (ViewBatchModel CVPR'25, RevisitDML ICML'20) | 48 | **48/48 = 1.000** [0.926, 1.000] | 36/36 [0.903, 1.000] | 0/48 | 0/48 | 0/48 | 0/48 | 0/48 |

Footnote under the table: "PSD = fraction of pairs with clean PASS /
invalid FAIL. R1-A's 30/30 is the pair-*construction* property (static
info identical; only the trace differs), not a discrimination score.
Strict-VPS = VPS ≤ 0.25 (frozen criterion, Appendix G). B0 paper-final,
B1 paper+repo, B2 +config (static), B3 provenance-only, B4 result-
matching. 95% CIs are Clopper–Pearson."

This single table replaces the V1 separate Table 2 / Table 3; the
naturalistic table (below) is the only other main-paper table.

## Naturalistic Table (R1-C, 8 cases compact)

Columns per brief: `case | violation class | trace basis | gold tier |
pre-fix verdict | post-fix verdict | semantic match`. Rows:

| case | class | trace basis | gold tier | pre | post | sem.match |
|---|---|---|---|---|---|---|
| Informer (AAAI'21) | C1 | recon | E | FAIL | PASS | ✓ |
| Metric Learn. Reality (ECCV'20) | C1 | recon | E | FAIL | PASS | ✓ |
| Deep RL that Matters (AAAI'18) | C2 | recon | E | FAIL | PASS | ✓ |
| BLEU Clarity Call (WMT'18) | C6 | recon | E | FAIL | PASS | ✓ |
| ALBERT (ICLR'20) | C5 | recon | A | FAIL | PASS | ✓ |
| GNN Fair Comparison (ICLR'20) | C4 | recon | E | FAIL | PASS | ✓ |
| RoBERTa (arXiv'19) | C6 | recon | B | FAIL | PASS | ✓ |
| CenterNet (CVPR'19) | C5 | recon | A | FAIL | PASS | ✓ |

Caption: "8 frozen naturalistic cases, one per independent paper.
recon = documented-protocol reconstruction (E02 = TRACE_INSUFFICIENT; no
live pre-fix re-execution recoverable for any case). Gold tiers: E
reproducibility paper (5), B explicit fix PR (1), A author issue (2).
Pre/post verdicts under the same frozen contract; all 8 pre-fix FAIL,
post-fix PASS. NVR = NPCR = witness = CIA = 8/8 (95% CI [0.631, 1.000])
— detectability in this selected set, not population recall."

Note: the "semantic match" column is the frozen `semantic_match=True`
for all 8; "witness present" also True for all 8 (Appendix F detail).

## Figure 4 — strongest forensic case (if space permits)

Single-case forensic chain for **CAND-08 CenterNet** (cleanest Grade-A:
explicit author issue #7, single localized fix, documented pre/post).
Vertical chain: `author issue #7 (gold) → blind prediction (pre-freeze,
no gold fields) → pre-trace FAIL (CTDET flip_test) → post-trace PASS →
semantic-locus match → SHA chain (blind/gold file hashes)`. One line:
"the strongest single forensic record: full blind-prediction isolation,
independent gold, and a localized witness."

SVG: `paper/figures/figure4_centernet_case.svg`.

---

## Rendering / space budget

- Figure 1: full-width top of page 1 (after abstract) — the hook.
- Figure 2: half-width, §6.
- Main Results Table: full-width, §6.
- Naturalistic Table: full-width, §7.
- Figure 4: half-width §7 *only if* the 8-page budget has room;
  otherwise move to Appendix A.
- Figure 3 (evidence ladder, V1 SVG) moves to **§5 Experimental Design**
  or Appendix; it is a design map, not a result.
