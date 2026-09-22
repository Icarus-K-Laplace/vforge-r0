# EpiTrace: Manuscript V2 (Submission Candidate)

*ICML-style compact body (≈8 pages, two-column equivalent). Every
numeric claim is traced to a frozen artifact in
`reports/R2V2_MANUSCRIPT_CONSISTENCY.md`. The three claim levels are
frozen in `R2V2_CLAIM_LOCK.md`; no paragraph may exceed them. The two
V0 overstatements remain corrected: R1-A is reported as 27/30 PSD =
0.900 (30/30 is the pair-construction property, not a discrimination
score), and R1-B1 is 48 claim-level pairs from 2 repositories with 36
strict value-preserving — not the V0 "48 value-preserving pairs across
4 repos" wording.*

---

## 1. Introduction

Machine-learning research is increasingly produced as a pipeline: a
hypothesis, generated code, an experiment, an analysis, and a draft.
As each stage is automated, the provenance of a reported number becomes
a chain of decisions rather than a single act. Two of those decisions
can be invisible yet decisive for whether the number is *evidence* for
the claim it supports.

Consider a paper that states it reports "the mean accuracy over five
declared random seeds." Execution A averages all five. Execution B
averages the three best-performing seeds and lands within 0.2% of A's
scalar. A reported-value check cannot tell them apart: the numbers
agree. Only A is admissible evidence for the claim, because B used the
result to select the result. The violation is *value-preserving*: the
output is the same to measurement precision, yet the evidential
process is not. This is the gap we address.

Existing tooling answers adjacent questions. Provenance systems record
*what happened*; reproducibility harnesses check whether a paper's code
reproduces its values; workflow monitors check whether execution
followed a declared plan. In our survey of their published
descriptions, we did not find evidence that any of them checks whether
the *process* that produced a number is scientifically admissible for
the specific claim the number supports. We did not find evidence that
any of them induces claim-relevant constraints from the paper's
protocol and checks a live trace against them.

We introduce **EpiTrace**. Given a paper P and a claim C, EpiTrace
specifies epistemic execution constraints Φ_C from P's protocol
statements (no access to the eventual bug) and evaluates a typed
execution trace against them, returning PASS, FAIL, or ABSTAIN, and on
failure a localized witness. The central object is the **value-
preserving epistemic violation (VPVD)**: two traces T+ and T− with
|y(T+) − y(T−)| ≤ ε such that G_{T+} ⊨ Φ_C and G_{T−} ⊭ Φ_C. EpiTrace
does not determine scientific truth; it checks conformance of the
evidence process to claim-relevant constraints.

**Contributions.**

1. We formulate scientific execution conformance and the VPVD, making
   explicit that output equivalence is not evidence-process validity.
2. We specify protocol-grounded epistemic constraints: a paper's
   protocol statements are matched to a fixed principle-template
   library and instantiated into typed predicates over the execution
   trace, without access to the eventual bug.
3. We build a runtime provenance verifier that returns a localized
   scientific witness on failure.
4. Controlled identifiability (R1-A, 30 pairs): EpiTrace PSD = 0.900
   (27/30; the 30/30 figure is the pair-construction property, not a
   discrimination score), four baselines 0/30.
5. Real public traces (R1-B1, 48 claim-level pairs from 2
   repositories; 36 strict value-preserving): EpiTrace 48/48,
   36/36 strict-VPS; result-matching baseline 0/48.
6. Blind naturalistic validation (R1-C, 8 frozen cases): NVR = NPCR =
   8/8 (95% CI [0.631, 1.000]), contracts audited paper-supported
   (5 EXPLICIT, 3 PRINCIPLE, 0 fault-specific); a 476-lead
   search-negative control (R1-D2) adds 0 confirmed cases.

---

## 2. Problem Formulation

Let P be a paper (or its protocol section) and C a claim P makes. An
**epistemic contract** Φ_C is a finite set of typed predicates specified
from P's protocol statements relative to C: F(P, C) → Φ_C = {φ_1…φ_n}.
Each φ_i is a predicate over a **typed execution graph** G_T built
from a runtime provenance trace T (typed nodes: splits, selections,
aggregations, tool versions, evaluation settings; typed edges: data
flow, control flow, reported-value derivation).

**Verification.** V(Φ_C, G_T) ∈ {PASS, FAIL, ABSTAIN}, corresponding to
G_T ⊨ Φ_C, G_T ⊭ Φ_C, or insufficient observability to decide. ABSTAIN
is distinguished from a coverage gap and is never silently treated as
pass.

**Value-preserving violation.** T+ and T− form a VPVD pair if
|y(T+) − y(T−)| ≤ ε, G_{T+} ⊨ Φ_C, and G_{T−} ⊭ Φ_C. The value check
cannot separate the pair; the conformance check can. A reported-value
harness is structurally blind to this regime.

**Metrics.** PSD: fraction of pairs with clean PASS and invalid FAIL.
Witness accuracy: failures whose witness localizes to the locus the
ground-truth correction addresses. CIA: induced contracts classified in
independent audit as paper-supported or a reasonable general principle,
not fault-specific. NVR / NPCR: over natural cases, the fraction EpiTrace
flags / the fraction where the pre-fix trace fails and the post-fix
trace passes under the same frozen contract.

---

## 3. Related Work (one paragraph + Table 1)

We position on a three-level distinction and against 10 surveyed
systems (Table 1; full 10×10 matrix in Appendix E, UNKNOWN cells
retained). **Provenance** systems answer *what happened* (P-PLAN,
RO-Crate Workflow Run, MLflow2PROV). **Operational workflow validity**
checks whether execution obeyed declared workflow constraints (P-PLAN
hand-specified step-order constraints; "Validity Constraints for Data
Analysis Workflows" 2024 data-lineage rules). **EpiTrace** answers a
third question: does the observed execution satisfy claim-relevant
epistemic constraints derived from the scientific protocol? In our
survey we did not find evidence that any published system (a) derives
constraints from the paper's protocol text rather than hand-specifying
them, (b) checks a live trace against those constraints, and (c)
localizes a scientific witness on failure. Paper–code discrepancy
systems (ReproZip, Paper2Code, RePro) are value-centric and miss the
VPVD regime by construction. Citation provenance (CiteArk/CAP) links
code to justifying citations, not to execution. The closest
neighbors—P-PLAN and the 2024 validity-constraint work—partially
overlap (constraints + checking) on the *operational* axis; their
constraints are hand-specified or data-lineage, not claim-relevant and
not paper-derived. We state this overlap explicitly rather than claim
an absolute absence.

---

## 4. EpiTrace

### 4.1 Protocol-grounded constraint specification (F)

A fixed library of principle templates P1–P6 (P1 split disjointness,
P2 selection disjointness, P3 seed aggregation, P4 tool/version
fidelity, P5 symmetric resource budget, P6 statistical-procedure
fidelity) is the template space. Specification reads P's protocol
statements and instantiates the matching templates into typed
predicates, in two audited modes: **EXPLICIT** (the protocol states the
constraint directly) and **PRINCIPLE-INDUCED** (the protocol declares a
procedure; "the code must match this declared procedure" is a general
scientific principle, not a reverse-engineered fault detector).

*Calibration.* We claim **protocol-grounded constraint specification**,
not unrestricted automatic rule discovery: the template library is fixed
and small, and a new constraint *class* requires a new template.
Within the library the specification is strong and has no bug access.
Concretely, the protocol-to-template mapping is a fixed, bug-blind
matching procedure over the P1–P6 library: it reads P's protocol
statements and selects the matching template by its declared procedure
(e.g., "median over 5 runs" → P6; "single-scale test" → P2), with no
per-paper tuning that consults the eventual bug. Audited on the 8
naturalistic contracts: 5 EXPLICIT, 3 PRINCIPLE, 0 fault-specific, 0
overreaching (Appendix B).

### 4.2–4.5 Runtime typing, verification, witness, VPS check

The trace is a typed execution graph populated from a live re-execution
or, when a live pre-fix trace is unrecoverable, a documented-protocol
reconstruction (flagged per case, Table 4 trace-basis column). Each
predicate is evaluated against observed fields; a predicate whose
fields are unobservable yields ABSTAIN, reported separately from
coverage. G_T ⊨ Φ_C holds when **every observable predicate** in Φ_C
is satisfied (word-identical to the §2 definition); unobservable
predicates are abstained, not passed. On FAIL the verifier returns the
violated predicate id and the trace entity (witness), whose semantic
locus is matched to the correction in audit. A pair is value-
preserving when |y+ − y−| ≤ ε, where ε is **frozen at case selection,
before the conformance verdict** (ε-freeness): it is set per
experiment from the paper's reported variability, else a fixed
fraction of dynamic range, and is not tuned to make a given pair
value-preserving (Appendix G).

---

## 5. Experimental Design

Evidence is organized on a ladder of increasing external validity
(Figure 3). **R1-A — controlled identifiability:** same paper, same
code, clean vs. one controlled deviation; a capability test.
**R1-B1 — real public traces, constructed deviations:** 48 claim-level
pairs from two public repositories (ViewBatchModel, CVPR'25;
RevisitDML, ICML'20); an external-validity bridge. **R1-C — natural
historical corrections:** 8 real, independently confirmed past
violations (author errata, merged fix PR, reproducibility papers); an
inferential test of naturally occurring violations. **R1-D2 —
search-negative control:** 476 keyword-matched leads fully adjudicated,
0 additional cases meeting the strict gold-chain gate; a specificity
test. The controlled tiers establish capability; the naturalistic tier
establishes external validity; the negative tier establishes
specificity. We keep these roles distinct so constructed-deviation
results are never read as natural-bug results.

**Selection funnel (Figure 4).** Discovered → paper-linked → gold-
confirmed → recoverable pre-fix → sufficient execution evidence →
blind-evaluable. The 8 naturalistic cases are the survivors; the 476
leads are the excluded population that failed one or more gates.

---

## 6. Controlled + Real-Trace Results (R1-A, R1-B1)

**R1-A (Table 2).** 30 pairs, 6 deviation families × 5. EpiTrace PSD =
0.900 (**27/30**; 95% Clopper–Pearson CI [0.735, 0.994]). The 30/30
figure is the *pair-construction* property (every pair is built so
static information is identical and only the trace differs); it is not
a discrimination score. The 3 non-discriminated pairs: 2 clean-trace
ABSTAIN (E03-03, E06-05 — unobservable fields; abstain, not guess) and
1 clean-trace false-positive (E03-04). Baselines B0–B3: 0/30 each
(95% CI [0.000, 0.116]). Ablation A3 (full provenance without the
contract) also 0/30: the active ingredient is the constraint, not the
trace. A4 (result matching) is blind exactly in the VPVD regime.

**R1-B1 (Table 2, right block).** 48 claim-level pairs from 2
repositories; 36 are strict value-preserving (VPS ≤ 0.25, the frozen
criterion in `R1B1_VPVD.csv`; the 12 remaining pairs have larger value
gaps, up to VPS = 0.651, and are included for coverage of the
non-strict regime, not for the value-preserving headline). Every one of
the 48 pairs is clean-PASS / invalid-FAIL (no ABSTAIN in R1-B1): EpiTrace
PSD = 48/48 (95% CI [0.926, 1.000]), including 36/36 strict-VPS (95% CI
[0.903, 1.000]); B0–B4 all 0/48. VPS range over all 48 is [0.052, 0.651],
mean 0.250; over the 36 strict-VPS it is [0.052, 0.246], mean 0.181.

---

## 7. Naturalistic Validation (R1-C)

**Table 4** reports the 8 frozen naturalistic cases (one per
independent paper): Informer (C1), Metric Learning Reality Check (C1),
Deep RL that Matters (C2), BLEU Clarity Call (C6), ALBERT (C5), GNN
Fair Comparison (C4), RoBERTa (C6), CenterNet (C5). Columns: case,
violation class, trace basis, gold tier, pre-fix verdict, post-fix
verdict, semantic match; CIs in caption.

Across the eight frozen naturalistic cases satisfying the strict gold-
chain criteria, EpiTrace's observed recall in this selected set is:
**NVR = 8/8, NPCR = 8/8, witness accuracy = 8/8, CIA = 8/8** (each 95%
Clopper–Pearson CI [0.631, 1.000]). These are *detectability* results in
a selected gold set, not population recall: with n = 8 the data are
consistent with true detectability as low as ~63%. Note the distinction:
NVR is violation *recall* over the 8 confirmed cases; a separate R1-C
metric records that 2 of the 8 are additionally value-preserving natural
cases (VPS ≤ 0.25) — the 8/8 headline does not conflate the two. Gold
tiers: E reproducibility paper (5) > B explicit fix PR (1, RoBERTa
#1360) > A author issue (2, ALBERT #37/#18, CenterNet #7/#53); primary
weight rests on E and B. Trace basis: **all 8 pre-traces are
documented-protocol reconstructions** (E02 = TRACE_INSUFFICIENT); no
live pre-fix re-execution was recoverable for any naturalistic case, so
the naturalistic 8/8 is a reconstruction-based result, not a live-
trace one.

**Search-negative control (R1-D2, §8).** 476 fully adjudicated
discovery leads across 4 repositories (ALBERT, YOLOv7, DeiT, Gym); 0
additionally confirmed. A case passes the 5-condition gold-chain gate
only if it is (i) paper-linked, (ii) gold-confirmed by an independent
authority, (iii) has a recoverable pre-fix state, (iv) has sufficient
execution evidence, and (v) is blind-evaluable. This is a negative
result *within the searched scope*: it bounds the false-confirm rate
(95% upper bound 0.77%); it does not estimate the prevalence of real-
world violations. Six repositories (dinov2, bert, evaluate, flax,
evalplus, Barlow — the C3/C4/C6 families) were quota-blocked and are
not claimed searched.

---

## 8. R1-D2 Search-Negative Detail

See §7. The 476 leads decompose as 428 rejected non-scientific, 24
rejected no-gold-confirmation, 15 rejected no-paper-link, 9 rejected
no-recoverable-prefix. None satisfied all five gold-chain conditions.

---

## 9. Limitations

1. **n = 8, wide CIs.** 95% CI for any 8/8 metric is [0.631, 1.000];
   reported as detectability in a selected set, not population recall.
2. **Public trace scarcity.** All 8 naturalistic pre-traces are
   documented-protocol reconstructions (E02 = TRACE_INSUFFICIENT);
   live re-execution was available only for the R1-A/R1-B1 tiers.
3. **E02 observability.** Which public trace matched the pre-fix state
   is not always recoverable; flagged per case.
4. **ML-domain concentration.** All evidence is computational ML; no
   claim of generalization to other domains.
5. **Observability bound.** Unobservable fields abstain, not pass;
   coverage bounds results (R1-A's 2 ABSTAIN are the honest cost).
6. **No truth claim.** EpiTrace audits the process, not the science: a
   conforming execution can still be scientifically wrong.
7. **Unsampled families.** C3/C4/C6 repos not searched in R1-D2; the
   negative result holds in the 4-repo scope only.
8. **Fixed P1–P6 library.** A new constraint class needs a new
   template; specification is strong within the library, not unbounded.
9. **Trace self-hash opacity.** The 16 frozen pre/post trace files'
   `self_hash` fields do not recompute under standard JSON schemes;
   trace content is verified against gold and paired results, but
   trace-level cryptographic integrity is not independently
   re-verifiable post-hoc (Appendix I).
10. **Discovery ≠ prevalence.** The naturalistic set was selected by the
    gold-chain gate; its recall does not estimate how common such
    violations are.

---

## 10. Conclusion

EpiTrace specifies a paper's protocol statements as epistemic execution
constraints and evaluates them against runtime provenance, localizing
the evidential failure when the check fails. The central result: a
reported number's correctness is not its evidential validity — two
executions can agree on the value while only one is admissible
evidence for the claim. Across controlled (27/30), real-trace
(48/48; 36/36 strict-VPS), and naturalistic (8/8 in a selected set,
95% CI [0.631, 1.000]) evaluation, EpiTrace separates the epistemically
invalid execution that a value check cannot see, and a 476-lead
search-negative control shows it does so specifically. We conclude that
*numerical agreement does not imply evidential validity*, and that the
process by which a number was produced carries scientific information
the number itself does not — information that can be captured, checked,
and localized without re-running the experiment.

---

## Appendix Plan (carries; main paper stays 8 pages)

- **A.** Full forensic chains for all 8 cases (blind/gold files,
  timestamps, hash chain, prediction isolation).
- **B.** All contract examples: 5 EXPLICIT + 3 PRINCIPLE, with audit
  verdicts.
- **C.** Additional baselines (B0 paper-final, B1 paper+repo, B2
  +config) with per-pair verdicts.
- **D.** Complete 10-system × 10-axis prior-art matrix (Table 1
  source), UNKNOWN cells retained.
- **E.** R1-D2 full 476-lead adjudication (428/24/15/9 breakdown +
  gold-chain gate definition).
- **F.** Witness localization details (semantic-locus matching).
- **G.** ε / VPS threshold definition (0.25 strict-VPS; observed
  ranges; per-experiment ε rule).
- **H.** Extended reviewer-analysis responses.
- **I.** Trace self-hash opacity finding (full scheme-testing record).
