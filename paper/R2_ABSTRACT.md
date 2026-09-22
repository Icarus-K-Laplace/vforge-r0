# EpiTrace: Abstract (V1 — polished)

## Draft

Two executions of the same code on the same data can produce nearly the
same reported scalar yet only one constitutes admissible evidence for the
scientific claim under which it was made. We call this phenomenon a
**value-preserving epistemic violation (VPVD)**: numerical agreement
does not imply evidential validity. Existing provenance and
reproducibility tooling answers *what happened*; none of the systems we
surveyed checks *whether what happened was scientifically admissible for
the specific claim being made*.

We introduce **EpiTrace**, which (i) specifies epistemic execution
constraints from a paper's protocol statements by matching them to a
fixed library of principle templates — without access to the eventual
bug — (ii) checks these constraints against runtime provenance, and
(iii) localizes the evidential failure to the execution step that
violated the constraint.

We evaluate EpiTrace along an evidence ladder of increasing external
validity. In controlled same-paper/same-code paired executions, EpiTrace
discriminates valid from invalid runs with PSD = 0.900 (27/30 pairs; 95%
Clopper–Pearson CI [0.735, 0.994]), where four baselines (paper-only,
paper+repo, static auditor, static+config) each score 0/30. On 48
claim-level paired cases from two independent public repositories
(ViewBatchModel CVPR'25, RevisitDML ICML'20), 36 are strict value-
preserving (VPS ≤ 0.25); EpiTrace discriminates all 48/48 pairs,
including all 36 value-preserving pairs (36/36, 95% CI [0.903, 1.000]),
while the result-matching baseline B4 scores 0/48. Blind validation against
8 independently-confirmed historical corrections — author errata, merged
fix pull requests, and a reproducibility paper — yields naturalistic
violation recall and paired-correction rate of 8/8 (95% CI [0.631,
1.000]), with contract induction independently audited as paper-supported
(0 fault-specific contracts). A 476-lead search-negative control
yields 0 additional confirmed cases (95% upper bound on false-confirm
rate: 0.77%).

The 8 naturalistic cases serve as external-validation evidence for the
central mechanism; they are not the contribution. The contribution is
the *distinction* — output equivalence vs. evidence-process validity —
and the *pipeline* that operationalizes it: paper protocol → epistemic
constraint → runtime conformance check → localized witness.

---

## What changed from V0 → V1 (polish notes)
- **Lead is now the phenomenon (VPVD), not "8/8".** The 8 cases are
  explicitly framed as external-validation evidence, not the thesis.
- **All headline numbers now carry 95% CIs** (Clopper–Pearson), per
  B1/B8. The "8/8" is now "8/8 (95% CI [0.631, 1.000])".
- **"compiles" → "specifies"** throughout, consistent with the
  protocol-grounded calibration (A5).
- **"no surveyed system" → "none of the systems we surveyed"** —
  hedged to a survey scope statement, not a universal negative.
- **ε / value-preserving** is tied to the concrete threshold in §4.5 /
  Appendix G, not left floating.
