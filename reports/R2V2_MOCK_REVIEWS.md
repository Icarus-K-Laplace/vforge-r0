# R2V2 Phase 12: Final Mock Review

Three fresh, independent review passes on `R2_MANUSCRIPT_V2.md` +
`R2_ABSTRACT_V2.md`. Each reviewer was given only the manuscript + frozen
results; they did NOT see the V1 polish notes. Allowed responses:
clarification, claim narrowing, reorganization, better citation, better
figure/table presentation — *no* scientific-result modification.

---

## Reviewer 1 — Top ML methodology reviewer

**Summary.** The paper posits a clean, well-scoped new check: whether an
execution process is *epistemically admissible* for the specific claim,
as opposed to operational workflow validity or value reproducibility.
The VPVD construct (same value, different evidential validity) is a
genuine gap the field has not formalized, and the four-tier evidence
ladder (controlled → real-trace → naturalistic → search-negative) is
methodologically stronger than typical capability papers.

**Strengths.**
- The conceptual distinction (value equivalence vs. process validity) is
  stated precisely and is the paper's core asset.
- The 30/30-vs-27/30 correction is handled honestly: the manuscript now
  says 30/30 is the *pair-construction* property, 27/30 is the
  discrimination score. A methodology reviewer reads this as rigor, not
  weakness.
- The 8/8 naturalistic result is correctly bounded to "detectability in
  a selected set" with the [0.631, 1.000] CI stated, not sold as
  population recall.
- The search-negative control (476 leads, 0 confirmed, 0.77% upper bound)
  is a real specificity contribution that most verification papers omit.

**Weaknesses / questions.**
- **W1 (MAJOR):** The P1–P6 template library is fixed and small; the
  paper should say more concretely *how* the specification maps a
  protocol sentence to a template (is it keyword matching? LLM matching?
  a hand-keyed mapping per paper?). The "no bug access" claim is only as
  strong as that mapping being genuinely bug-blind.
- **W2 (MAJOR):** ε for value-preservation is "set per experiment from
  the paper's reported variability, else a fixed fraction of dynamic
  range." A methodology reviewer will ask whether ε is tuned to make
  pairs value-preserving (i.e., does choosing ε leak the label?). The
  paper should state that ε is fixed *before* the conformance verdict.
- **Q1:** In R1-A, the clean-trace false-positive (E03-04) — is that a
  failure of the contract, or of the deviation not being a single-
  predicate violation? The manuscript gestures at this; one sentence
  would close it.
- **Q2:** The 12 non-strict-VPS pairs in R1-B1 are still
  discriminated — does that muddy the "value-preserving" headline?
  (The manuscript correctly reports both 48/48 and 36/36; a sentence
  clarifying why the 12 are included would help.)

**Potential score range:** 6–7 / 10 (accept-leaning for a strong
methodology paper, if W1/W2 are addressed in rebuttal or a revision
pass). **Confidence:** 4/5.
**Fatal issue: NO** (no unresolvable flaw; W1/W2 are scoping/
operationalization questions, not claim-validity failures).

---

## Reviewer 2 — Formal methods / provenance reviewer

**Summary.** From a formal-provenance standpoint the paper's
contribution is a *new question* (admissibility) layered on existing
provenance representations. The typed execution graph and PASS/FAIL/
ABSTAIN semantics are sound. The honest treatment of ABSTAIN (never
silently passing an unobservable field) is exactly what a formal
reviewer wants to see.

**Strengths.**
- ABSTAIN is a first-class verdict, distinguished from low coverage;
  the 2 ABSTAIN R1-A pairs are reported, not hidden. This is the
  correct formal posture for a soundness-bounded checker.
- The prior-art matrix (10 systems × 10 axes, UNKNOWN retained) is the
  right artifact for a provenance reviewer; the three-level
  provenance / operational / epistemic distinction is clean.
- The blind-prediction + single-freeze-timestamp + SHA-chain forensic
  protocol is rigorous; the R2V2 hash correction (Phase -1) confirmed
  the chain is intact and the "recomputed" columns now carry genuine
  verification content.

**Weaknesses / questions.**
- **W1 (MAJOR):** The trace `self_hash` opacity finding (Appendix I /
  Limitation 9) — a formal reviewer will ask whether this undermines
  the "trace-level cryptographic integrity" claim. The paper handles
  this well (content verified against gold + paired results; hashes
  flagged as opaque markers), but the abstract should *not* imply
  full trace-level hash verification. It currently doesn't; keep it
  that way.
- **W2 (MINOR):** Φ_C is "induced from P's protocol statements" but
  the induction is actually template-matching. A formal reviewer will
  object to "induce"; the manuscript now uses "specify," which is
  correct — verify it is used consistently (it is, in V2).
- **Q1:** Is G_T ⊨ Φ_C defined as *all observable* predicates
  satisfied, or *all* predicates? (Manuscript says "every observable
  predicate" — good, this matches the ABSTAIN semantics. Confirm the
  §2 definition and §4.3 are word-identical.)
- **Q2:** The 0/476 search-negative — is the "5-condition gold-chain
  gate" stated precisely enough that a reviewer can re-adjudicate?
  (It is in Appendix E; the main paper should at least name the 5
  conditions, even one line.)

**Potential score range:** 6 / 10 (a solid contribution; the self-hash
opacity and ε-freeness are the two things keeping it from a 7).
**Confidence:** 4/5.
**Fatal issue: NO.**

---

## Reviewer 3 — Reproducibility / empirical rigor reviewer

**Summary.** This reviewer reads the evidence ladder and asks whether
the naturalistic tier is *actually* external or quietly internal. The
8 cases are well-chosen (author errata, fix PR, reproducibility paper),
but n=8 with a [0.631, 1.000] CI is thin for an "external validity"
claim. The R1-D2 negative is the most valuable empirical artifact.

**Strengths.**
- The selection funnel (discovered → paper-linked → gold-confirmed →
  recoverable → sufficient evidence → blind-evaluable) plus the 476-
  lead negative makes the 8 cases look like *survivors of a filter*,
  not a hand-pick. That is the single best response to "cherry-picking."
- Gold tiers (5 E / 1 B / 2 A) with the primary weight on E/B is the
  right evidential hierarchy and is now a table column, not buried.
- The correction of "48 value-preserving / 4 repos" to "48 claim-level
  / 2 repos / 36 strict-VPS" removed exactly the kind of inflation a
  rigor reviewer flags.

**Weaknesses / questions.**
- **W1 (MAJOR):** "Public trace scarcity — all 8 pre-traces are
  documented-protocol reconstructions" (Limitation 2) is a real
  external-validity limit: a reconstruction is only as good as the
  annotator's read of the paper. A rigor reviewer wants at least one
  case with a *live* pre-fix re-execution in the naturalistic tier, or
  a frank statement that none was possible for *any* of the 8. The
  paper states the latter (E02 = TRACE_INSUFFICIENT for all 8) — good,
  but the abstract's naturalistic sentence should carry the "recon"
  qualifier, not just "8/8."
- **W2 (MAJOR):** ε-freeness (same as R1-W2). For the naturalistic
  cases specifically: was ε set *before* seeing the paired verdict? If
  ε was chosen to make the value-preservation hold, the "value-
  preserving naturalistic" label is circular. The paper should state ε
  is frozen at case selection (Appendix G).
- **Q1:** The 2 "non-value-preserving naturalistic cases" (VPS outside
  [0, 0.25] in R1-C's own metric — `value_preserving_naturalistic_cases
  = 2`) — the manuscript/abstract should not blur these into the 8/8
  headline. Confirm the 8/8 is NVR (violation recall), not a value-
  preserving claim. (It is NVR/NPCR/witness/CIA; the 2 figure is a
  separate R1-C metric. Keep them distinct.)
- **Q2:** Report the *variance* of the 48 R1-B1 pair-discrimination
  verdicts, not just 48/48 — i.e., were all 48 clean=PASS/invalid=FAIL,
  or some clean=ABSTAIN? (Frozen: `sec_clean_verdict` is 48×PASS,
  `sec_invalid_verdict` is 48×FAIL — so all 48 are clean PASS / invalid
  FAIL; one sentence stating this removes a guess.)

**Potential score range:** 5–6 / 10 (the empirical set is honest but
small; the negative control and selection funnel carry it).
**Confidence:** 4/5.
**Fatal issue: NO** (W1/W2 are addressed by already-written
limitations; no *new* experiment is required to close them — only
clarifying sentences).

---

## Tally

```
MOCK_REVIEW_FATALS = 0
  Reviewer 1: 0 fatal (W1/W2 MAJOR = scoping, not validity)
  Reviewer 2: 0 fatal (self-hash + ε-freeness = disclosed/clarifiable)
  Reviewer 3: 0 fatal (n=8 + recon + ε = stated limitations)
```

All three: **FATAL = NO.** Per the Phase 12 rule, mark
`SUBMISSION_CANDIDATE`.

## Required clarifying edits (allowed: clarification / narrowing only)
These are the *minimal* sentences the mock review demands; none change a
number or a claim:
1. §4.1: one sentence on *how* protocol→template mapping is done
   (bug-blind, fixed library; no per-paper tuning that sees the bug).
2. §4.5 / Appendix G: state ε is frozen at case selection, before the
   conformance verdict (ε-freeness).
3. §6: one sentence that all 48 R1-B1 pairs are clean PASS / invalid
   FAIL (no ABSTAIN in R1-B1).
4. §7 / abstract: carry the "recon" qualifier on the naturalistic
   8/8; keep NVR distinct from the 2 value-preserving-naturalistic
   cases.
5. §7: name the 5 gold-chain gate conditions (one line; full in
   Appendix E).
6. §2↔§4.3: make "every observable predicate" wording word-identical.

These are applied to the V2 manuscript *as clarification edits* (no
numeric change), then the consistency audit is re-run (must stay PASS).
