# EpiTrace: Figure Specifications (V0)

Design notes for ≥4 figures. Each figure has a one-line "visual thesis" it
must communicate.

---

## Figure 1 — Concept (the visual thesis of the paper)

**Thesis:** Two executions of the same code on the same data yield the
same reported scalar, but only one is admissible evidence for the claim.

Layout:
- Left: paper P → claim C → epistemic contract Φ_C (auto-compiled).
- Center: two execution traces T+ and T− (same code, same data).
- Right: both T+ and T− report y ≈ y (numerical agreement, |y+−y−| ≤ ε).
- Bottom: EpiTrace verdicts — G_{T+} ⊨ Φ_C → PASS (valid evidence);
  G_{T−} ⊭ Φ_C → FAIL (witness: protocol.selection_target).
- A red "value check is blind here" annotation on |y+−y−|.

Style: horizontal pipeline, two parallel trace lanes merging into one
scalar, diverging into PASS/FAIL verdicts. Single accent color for the
FAIL lane. No 3D. This is the figure a reader must be able to
re-explain in one sentence.

---

## Figure 2 — Identifiability (why the trace matters)

**Thesis:** A static verifier and EpiTrace receive identical *non-trace*
information; only EpiTrace receives the execution trace, and only it
separates the pair.

Layout:
- Top: one paper, one repository, two execution traces (clean / invalid).
- Two verifier boxes: "Static auditor B2" and "EpiTrace."
- Inputs to B2: paper text + repo code + declared settings (no trace).
- Inputs to EpiTrace: the same inputs + the typed execution trace G_T.
- Outputs: B2 → both PASS (0% discrimination); EpiTrace → PASS / FAIL.
- Highlight the delta input (the trace) in the only place the two
  boxes differ.

Purpose: shows the *information difference* is what drives the result,
answering "is this just a better static check?"

---

## Figure 3 — Evidence ladder (external validity)

**Thesis:** Controlled → real public traces → natural historical
corrections → search-negative control, increasing external validity.

Layout: four rungs, each labeled with the tier and its role:
1. R1-A controlled identifiability (30 pairs, capability).
2. R1-B1 real public traces, constructed deviations (48 pairs, bridge).
3. R1-C natural historical corrections (8 cases, external validity).
4. R1-D2 search-negative control (476 leads, specificity).
Each rung carries its headline number (PSD, VPS-detection, NVR/NPCR,
0-confirmed). Arrows emphasize the increasing-externality gradient.

---

## Figure 4 — A single naturalistic case (strongest Grade-A)

**Thesis:** The full forensic chain of one real correction, end to end.

Preferred case: **CAND-08 CenterNet** (visually simplest: a single
undocumented `flip_test=True` flag inflated Table 1 AP; clean pre/post
commits 1e920d3 → 4a3f120; author-confirmed on Issues #7/#53).

Layout (vertical chain):
- Paper statement: "Table 1, single-scale test AP (no TTA)."
- Pre-fix trace: flip_test=True silently active (violation).
- Induced contract: RUNTIME_PROTOCOL_FIDELITY → protocol.
  test_time_augmentation predicate.
- Violating path: the flip-augmented test pass in the trace.
- EpiTrace prediction (blind): FAIL, witness = flip_test flag.
- Independent gold: author confirmation + fix commit 4a3f120.
- Post-fix trace: flip_test documented/removed; recheck PASS.
- Timestamps: contract frozen (T0) → blind prediction (T1) → gold
  reveal (T2), with T0 < T1 < T2 shown.

Purpose: one page, one real case, the entire chain a skeptical reviewer
(C1) can follow. All other 7 cases go to Appendix A in the same format.

---

## Figure 5 (optional) — Naturalistic case-selection flow (§4 CONSORT-like)

**Thesis:** The 8 cases are survivors of a filter, not a hand-pick.

Layout: funnel —
discovered (476 leads) → scientific-paper-linked → gold-confirmed →
recoverable pre-fix → sufficient execution evidence → blind-evaluable
(8). Side branches show exclusion counts and reasons. An explicit
caption: "The 476 leads were *discovered/adjudicated*; they were not
each run through EpiTrace."

---

## Shared style
- Flat, single-accent palette; no decorative 3D.
- Every number in a figure must trace to a frozen artifact
  (R1A_PAIR_RESULTS.jsonl, R1B1_VPVD.csv, R1C_*, R1D_*).
- Figure captions state the source artifact for each number.
