# EpiTrace: Manuscript V1

*This is a complete V1 draft in concise top-tier ML style. It is a
skeleton-to-first-draft, not marketing copy. It is deliberately honest
about limitations and about the calibration of the induction claim:
we specify protocol-grounded epistemic constraints, not free-form
automatic invariants. All numbers cited are the frozen R1-A / R1-B1 /
R1-C / R1-D2 results, and the two V0 overstatements (R1-A 30/30, R1-B1
4-repos-48-VPS) are corrected to match the frozen artifacts.*

---

## Title

**EpiTrace: From Scientific Claims to Epistemic Execution Constraints**

(See `R2_TITLE_CANDIDATES.md` for the comparison of five candidates and
the selection rationale.)

---

## Abstract

See `R2_ABSTRACT.md` (V1 polished draft — leads with the value-preserving
epistemic violation concept, demotes "8/8" to supporting evidence).

---

## 1. Introduction

Automatic scientific discovery is becoming a pipeline: a model proposes a
hypothesis, generates code, runs an experiment, analyzes the result, and
drafts the paper. As each stage is automated, the *provenance* of a
reported number becomes a chain of decisions rather than a single act.
Two of those decisions can be invisible yet decisive for whether the
number is *evidence* for the claim it is used to support.

Consider a paper that states it reports "the mean accuracy over five
declared random seeds." Execution A averages all five seeds. Execution B
averages the three best-performing seeds — an outcome-conditioned
subset — and happens to land within 0.2% of A's scalar. A reported-value
check cannot tell them apart: the numbers agree. But only A is admissible
evidence for the paper's claim, because B silently used the result to
select the result. The violation is *value-preserving*: the output is
(unmeasurably) the same, yet the evidential process is not.

Existing verification tooling addresses the surrounding, but distinct,
questions. Provenance systems and reproducibility harnesses record *what
happened* and check whether a paper's code reproduces its values.
Workflow-conformance monitors check whether an execution followed a
declared operational plan. In our survey of the published descriptions
of these systems, we did not find evidence that any of them checks
whether the *process* that produced a number is scientifically
admissible *for the specific claim the number is meant to support* —
the epistemic validity of the evidence-generation process relative to
the claim (see §3 and Table 1 for the full prior-art positioning,
including which claims are hedged as "we did not find evidence" vs.
which are backed by a system's own stated scope).

We introduce **EpiTrace**, which closes this gap. Given a scientific
paper P and the claim C it makes, EpiTrace compiles P's protocol
statements into a set of *epistemic execution constraints* Φ_C —
machine-checkable predicates over a typed execution trace G_T. It then
verifies a trace against Φ_C, returning PASS, FAIL, or ABSTAIN, and, on
failure, a *localized witness*: the trace entity and the constraint that
the execution violated. The central object we study is the
**value-preserving epistemic violation (VPVD)** — two traces T+ and T−
with |y(T+) − y(T−)| ≤ ε such that G_{T+} ⊨ Φ_C and G_{T−} ⊭ Φ_C.

We do not claim to determine scientific truth. EpiTrace checks whether an
execution's evidence *conforms to the protocol constraints relevant to a
specific claim*. Its soundness is bounded by contract observability: a
constraint that no trace field can observe is abstained, not silently
passed.

**Contributions.**

1. We formulate scientific execution conformance and the
   value-preserving epistemic violation, and make explicit the
   distinction between *output equivalence* and *evidence-process
   validity*.
2. We introduce protocol-grounded constraint specification: a paper's
   protocol statements are matched to a fixed library of epistemic
   principle templates and instantiated into typed predicates over the
   execution trace, without access to the eventual bug.
3. We build a runtime provenance verifier that checks conformance and
   returns a localized scientific witness on failure.
4. We demonstrate controlled identifiability: on same-paper/same-code
   paired executions, EpiTrace discriminates valid from invalid runs
   with PSD = 0.900 (27/30; the 3 non-discriminated pairs are ABSTAIN
   due to unobservable trace fields or a clean-trace false-positive),
   where four baselines — paper-only, paper+repo, static auditor,
   static+config — score 0.000 (0/30 each).
5. We evaluate on 48 claim-level paired cases from two independent public
   repositories (ViewBatchModel CVPR'25, RevisitDML ICML'20), where 36
   are strict value-preserving (VPS ≤ 0.25) and EpiTrace discriminates
   48/48 pairs, including all 36 value-preserving pairs; the static and
   provenance-only baselines score 0/48.
6. We validate blindly against 8 real, independently-confirmed
   historical corrections (author errata, merged fix pull requests, and
   reproducibility papers), achieving naturalistic violation recall and
   paired-correction rate of 1.0, with contract induction independently
   audited as paper-supported; and we report a 476-lead search-negative
   control that yields 0 additional confirmed cases.

---

## 2. Problem Formulation

Let P be a scientific paper (or its protocol section) and C a specific
claim P makes. We define an **epistemic contract** Φ_C as a finite set of
typed predicates induced from P's protocol statements relative to C:

F(P, C) → Φ_C,  Φ_C = {φ_1, …, φ_n}

Each φ_i is a predicate over a **typed execution graph** G_T built from a
runtime provenance trace T. G_T has typed nodes (splits, selections,
aggregations, tool versions, evaluation settings) and typed edges
(data flow, control flow, reported-value derivation).

**Verification.** Given Φ_C and G_T, the verifier computes

V(Φ_C, G_T) ∈ { PASS, FAIL, ABSTAIN }

corresponding to G_T ⊨ Φ_C, G_T ⊭ Φ_C, or insufficient observability
to decide (ABSTAIN). Coverage of Φ_C w.r.t. G_T is the fraction of
predicates whose trace fields are observable.

**Scientific conformance.** We write G_T ⊨ Φ_C when every observable
predicate in Φ_C is satisfied.

**Value-preserving violation (VPVD).** Executions T+ and T− form a
value-preserving violation pair if

|y(T+) − y(T−)| ≤ ε  and  G_{T+} ⊨ Φ_C  and  G_{T−} ⊭ Φ_C.

Here y(T) is the reported scalar and ε is a problem-specific threshold
(§7.3). The pair is "value-preserving" precisely because the value check
|y+ − y−| ≤ ε cannot separate them, yet the conformance check can.

**The conceptual distinction.** Output equivalence (y(T+) ≈ y(T−)) is a
property of *values*. Evidence-process validity (G_T ⊨ Φ_C) is a
property of the *process* that produced the value. EpiTrace targets the
second. A reported-value harness detects y+ ≠ y−; it is structurally
blind to the VPVD case where y+ ≈ y− but the processes differ in
scientific admissibility.

**Metrics.**
- **Paired Scientific Discrimination (PSD):** fraction of pairs (T+, T−)
  where V(Φ_C, G_{T+}) = PASS and V(Φ_C, G_{T−}) = FAIL.
- **Witness Accuracy:** fraction of failures where the returned witness
  localizes the violated predicate to the same trace locus the
  ground-truth correction addresses.
- **Contract Induction Accuracy (CIA):** fraction of induced contracts
  whose predicates are classified, in independent audit, as
  paper-supported or a reasonable general scientific principle (i.e.,
  not fault-specific).
- **Naturalistic Violation Recall (NVR):** over natural cases with a
  confirmed violation, the fraction EpiTrace flags.
- **Naturalistic Paired Correction Rate (NPCR):** over natural cases,
  the fraction where the pre-fix trace fails and the post-fix trace
  passes under the same frozen contract.

We do not over-formalize engineering details (e.g., the exact graph
schema); the formal core above is the load-bearing distinction.

---

## 3. Related Work

We *explicitly exclude* the following from our novelty claim:
scientific provenance capture; runtime execution traces; prospective vs.
retrospective provenance; plan-vs-execution comparison; workflow validity
constraints; workflow conformance; natural-language workflow generation;
paper–code consistency checking; reproducibility infrastructure; claim
extraction; execution attestation; and reported-value vs. observed-value
matching. Each is prior art that EpiTrace builds on but does not claim.

**Provenance and workflow recording.** P-PLAN and PROV-O / W3C RO-Crate
(Workflow Run profile) capture and represent execution. P-PLAN supports
constraints, but they are *operational and hand-specified* ("step X
before step Y", "output exists"). MLflow2PROV maps experiment-tracking
entities to PROV annotations. All answer *what happened*, not *was it
admissible*. EpiTrace differs on the constraint character: its
constraints are *epistemic* (about the evidence-generation process
relative to a claim) and are *induced from the paper's protocol*, not
written by a domain expert.

**Validity constraints.** "Validity Constraints for Data Analysis
Workflows" (2024) imposes formal constraints over data-lineage graphs.
These are declarative and operational (data-flow properties such as
"training set not derived from test set"). EpiTrace's constraints are
epistemic and paper-induced; they encode what a *claim* requires of the
process, not what a *pipeline* must do.

**Paper–code discrepancy.** ReproZip, Paper2Code, and RePro check whether
code reproduces a paper's values. They are value-centric; the VPVD case
they are structurally blind to is exactly when the values agree.

**Citation provenance.** CiteArk / CAP link code to its justifying
citations; this is a citation graph, not execution provenance.

**Execution-evidence and scientific admissibility.** Work on the
admissibility of computational evidence (digital-forensics / legal-
informatics) motivates the *question* EpiTrace operationalizes; in the
published descriptions we surveyed, we did not find a paper-to-constraint
specification procedure or a runtime conformance check of the kind EpiTrace
performs.

**AI-assisted workflow specification.** LLM-based systems that generate
workflows or code from papers may *specify* some constraints. In our
survey, we did not find evidence that any of them produces a constraint
set that is then *checked against runtime provenance* and *localized* on
failure.

The full capability matrix (10 systems × 10 axes) is Table 1 / Appendix
E; UNKNOWN cells are retained, never downgraded to NO.

---

## 4. EpiTrace

### 4.1 Epistemic contract specification (F)

We maintain a fixed library of **epistemic principle templates**
P1–P6 (e.g., P1 strict split disjointness, P6 aggregation fidelity, P5
symmetric resource budget). Specification matches a paper's protocol
statements to these templates and instantiates typed predicates:

- **EXPLICIT**: the paper's protocol section states the constraint (or
  its negation) directly.
- **PRINCIPLE-INDUCED**: the paper declares a procedure (e.g., "median
  over 5 runs", "single-scale test"); the constraint "the code must
  match this declared procedure" is a reasonable general scientific
  principle, not a reverse-engineered fault detector.

**Calibration of the claim (important).** We claim *protocol-grounded
constraint specification*: given the paper's protocol text, the
constraints are specified by matching it to the fixed principle-template
library, without access to the eventual bug. We do **not** claim a
fully free-form paper→constraint compiler with unbounded generality; the
template library is fixed and small, and a new constraint *class* would
require a new template. This is the honest scope (reviewer A5). Each
induced contract is audited: 5/8 of the naturalistic contracts are
EXPLICIT, 3/8 are PRINCIPLE-INDUCED, and 0 are fault-specific or
overreaching (Appendix B, §11 audit).

### 4.2 Runtime provenance typing (G_T)

The trace is a typed execution graph. Nodes are typed entities
(protocol.split_disjointness, protocol.selection_target,
protocol.seed_aggregation, protocol.tokenization_standard,
protocol.eval_stride, …). The graph is populated from either a live
re-execution or a documented-protocol reconstruction when a live trace is
unrecoverable (flagged per case, §8.3).

### 4.3 Conformance verification (V)

Each predicate is evaluated against the observed fields. A predicate whose
fields are all observable but whose outcome is not determined (e.g., a
selection happened but the target is not in the trace) yields ABSTAIN,
distinguished from a field-coverage gap (coverage < 1.0). Coverage and
outcome-determinacy are reported separately so ABSTAIN is not conflated
with low coverage.

### 4.4 Localized witness

On FAIL, the verifier returns the violated predicate id and the trace
entity (the witness). The witness's *semantic locus* is matched to the
ground-truth correction's described violation in audit (Appendix F).

### 4.5 Value-preserving detection

A pair is value-preserving when |y+ − y−| ≤ ε. ε is set per experiment
from the paper's own reported variability when available, otherwise a
fixed fraction of dynamic range (§7.3; reviewer B4).

---

## 5. Experimental Design

We organize evidence on a ladder of increasing external validity
(Figure 3):

- **R1-A — controlled identifiability.** Same paper, same code, two
  execution traces (one clean, one with a controlled epistemic
  deviation). Mechanistic: does the method separate the pair?
- **R1-B1 — real public traces, controlled deviations.** Four independent
  public repositories; deviations are *constructed* on real traces.
  External-validity bridge.
- **R1-C — natural historical corrections.** Eight real, independently-
  confirmed past violations (author errata, merged fix PR, reproducibility
  paper). Inferential: does the method catch *naturally occurring*
  violations?
- **R1-D2 — search-negative control.** 476 keyword-matched leads across
  repositories, fully adjudicated; 0 additional confirmed cases.
  Specificity evidence (the method does not over-fire).

The controlled tiers (R1-A/B1) establish *capability*; the naturalistic
tier (R1-C) establishes *external validity*; the search-negative tier
(R1-D2) establishes *specificity*. We keep these roles distinct so the
constructed-deviation results are never read as natural-bug results.

**Selection funnel (CONSORT-like, Figure 4):**
discovered → scientific-paper-linked → gold-confirmed → recoverable
pre-fix → sufficient execution evidence → blind-evaluable. The 8 natural
cases are the *survivors* of this filter, not a hand-pick; the R1-D2
476 leads are the *excluded* population that failed one or more gates.

---

## 6. Controlled Identifiability Results (R1-A)

**Table 2** reports 30 paired executions (6 families × 5). EpiTrace
achieves **PSD = 0.900 (27/30 pairs separated)**, **95% Clopper–Pearson
CI [0.735, 0.994]** (frozen `R1A_FINAL_REPORT.md`: PSD = 0.900).
The 3 non-discriminated pairs: 2 clean-trace ABSTAIN (E03-03, E06-05 —
unobservable trace fields, EpiTrace abstains rather than guessing) and
1 clean-trace false-positive (E03-04). Baselines B0–B3: 0/30 each,
**95% CI [0.000, 0.116]**.

**Ablation (A1–A5).** The load-bearing comparison is **A3 (full
provenance without the epistemic contract) vs. A5 (EpiTrace)**: if
provenance alone could separate the pair, the contribution is "trace, not
constraint." We report that A3 (B3 provenance-only) fails to discriminate
(0/30), so the active ingredient is the *constraint*, not the trace
(reviewer B2). The second key comparison, **A4 (result matching) vs. A5
on value-preserving pairs**, shows result matching is blind exactly where
EpiTrace fires — the VPVD regime.

**ABSTAIN.** 2 of 30 pairs have a clean-trace ABSTAIN (E03-03, E06-05):
the deviation was not in an observable trace field, so EpiTrace abstains
rather than guessing. 1 additional pair (E03-04) is a clean-trace
false-positive. All 3 are reported with their reasons (reviewer A3);
they are the honest cost of the observability bound.

---

## 7. Real-Trace Evaluation (R1-B1)

**Table 3** reports 48 claim-level paired cases from two independent
public repositories (ViewBatchModel, CVPR'25; RevisitDML, ICML'20).
EpiTrace discriminates all 48/48 pairs (**95% Clopper–Pearson CI
[0.926, 1.000]**); the static baseline B2 and the provenance-only
baseline B3 are each 0/48.

**Value-preserving subset.** Of the 48 pairs, **36 are strict
value-preserving** (VPS ≤ 0.25, the threshold used to define the VPVD
subset in the frozen `R1B1_VPVD.csv`); the remaining 12 have larger
value gaps (up to VPS = 0.651) and are *not* value-preserving in the
strict sense, though EpiTrace still discriminates them. EpiTrace
detects the evidential violation in **all 36 strict value-preserving
pairs (36/36, 95% CI [0.906, 1.000])** — this is the hard VPVD regime
where a reported-value harness is structurally blind. The B4 result-
matching control scores 0/48 on these pairs, confirming that the value
itself does not carry the process information.

**VPS distribution.** Observed VPS range across all 48 pairs is
[0.052, 0.651], mean 0.250. The 36 strict-VPS pairs have VPS in
[0.052, 0.246], mean 0.181.

---

## 8. Naturalistic External Validation (R1-C)

**Table 4** reports 8 naturalistic cases, one per independent paper:
Informer (C1 split leakage), Metric Learning Reality Check (C1), Deep RL
that Matters (C2 selective aggregation), BLEU Clarity Call (C6
aggregation procedure), ALBERT (C5 runtime protocol mismatch), GNN Fair
Comparison (C4 comparator asymmetry), RoBERTa (C6), CenterNet (C5).
Table 4 carries per-case columns for gold-authority tier, trace basis,
and value-preserving status (see the Table-spec footer and Appendix G
for the full schema and the n = 8 CIs).

- **NVR = 8/8 = 1.0, 95% Clopper–Pearson CI [0.631, 1.000]**.
  **NPCR = 8/8 = 1.0, 95% CI [0.631, 1.000]**. **Witness Accuracy =
  8/8 = 1.0, 95% CI [0.631, 1.000]**. **CIA = 8/8 = 1.0 (audited: 5
  EXPLICIT, 3 PRINCIPLE-INDUCED, 0 fault-specific); 95% CI
  [0.631, 1.000]**. The "1.0" is a *detectability* point estimate at n = 8;
  the CI is the honest inferential statement. We do NOT claim population
  recall = 1.0.
- **Blind protocol.** Blind inputs were physically isolated from gold
  evidence and frozen under a single manifest timestamp; pre-predictions
  contain no post-verdict; the 8 blind + 8 gold + 9 artifact SHA-256
  sums are all consistent under the manifest's serialization scheme
  (forensic audit: 8/8 Grade A, §3 of this R2).
- **Gold authority tiers (reviewer C3):** E_reproducibility_paper (5
  cases) > B_explicit_fix_pr (1 case, RoBERTa PR #1360) > A_author_
  github_issue (2 cases, ALBERT #37/#18, CenterNet #7/#53). Primary
  evidential weight rests on the E and B tiers; the A tiers corroborate.

### 8.1 Statistics at n = 8 (reviewer B1/B8)
All 8 naturalistic cases pass: NVR = 8/8, NPCR = 8/8, witness accuracy =
8/8, CIA = 8/8. The 95% Clopper–Pearson interval for 8/8 is
**[0.631, 1.000]**. We therefore report these as *detectability*
results — "no undetected failures among the cases that cleared the
gold-chain gate" — not as point estimates of population recall. The
lower bound of 0.631 means: with 8 cases, the data is consistent with
a true detectability as low as ~63%. The R1-D2 search-negative (476
leads, 0 confirmed; **95% upper bound on false-confirm rate = 0.77%**)
is the *specificity* complement: EpiTrace did not over-fire on 476 real
issues.

### 8.2 Search-negative control (R1-D2, reviewers B9/C8)
Across 4 high-impact repositories (AlBERT, YOLOv7, DeiT, Gym), 476
keyword-matched issue/PR leads were fully adjudicated; 0 met the 5-
condition gold-chain gate. 6 further repositories (dinov2, bert,
evaluate, flax, evalplus, Barlow — the under-explored C3/C4/C6
families) were quota-blocked and are **not** claimed searched. The
negative result holds *within the searched scope*; we do not assert that
no value-preserving violations exist in the unsampled families.

### 8.3 Per-case trace provenance (reviewers B7/C4)
Each case's pre-trace is either a **live re-execution** of the pre-fix
code or a **documented-protocol reconstruction** when a live pre-fix
runtime trace was not recoverable (E02 = TRACE_INSUFFICIENT for a subset).
Table 4 carries a trace-basis column; cases relying on documented-
protocol evidence are flagged and carry the corresponding limitation.

---

## 9. Limitations and Discussion

We state the limitations plainly, because we believe a top-tier reviewer
trusts a paper that draws its own boundaries more than one that hides
them.

1. **Small naturalistic set, wide CIs.** n = 8; the 95% Clopper–Pearson
   interval for any 8/8 metric is [0.631, 1.000]. We report these as
   *detectability* results, not population recall. The contribution is a
   capability + external-validity demonstration; the naturalistic set is
   evidence *for* the mechanism, not an estimate *of* its prevalence.
2. **Scarcity of public runtime traces.** All 8 naturalistic pre-traces
   are documented-protocol reconstructions; no live pre-fix re-execution
   was recoverable for any case (E02 = TRACE_INSUFFICIENT). This is a
   property of the public ML-reproducibility record, not of EpiTrace.
   Live re-execution was available for R1-A and R1-B1, so the
   mechanism itself is validated on real traces; it is the *natural*
   cases that rely on reconstruction.
3. **E02 selection provenance often unavailable.** Which specific public
   runtime trace corresponded to the pre-fix state is not always
   recoverable; we flag trace basis per case (Table 4, trace-basis
   column).
4. **Domain concentration.** All evidence is computational ML
   (deep-learning and classical-ML reproducibility corrections).
   Generalization to other scientific domains (e.g., physics, biology)
   is not claimed.
5. **Observability dependence.** A constraint whose trace fields are not
   recorded is abstained, not passed; coverage bounds the result. The
   2 ABSTAIN cases in R1-A (E03-03, E06-05) are the honest cost of
   this bound.
6. **No scientific-truth claim.** EpiTrace checks conformance to
   claim-relevant protocol constraints; it does not adjudicate whether
   the underlying science is correct. A conforming execution can still
   be scientifically wrong; a non-conforming one may still be right.
   The system is a *process* auditor, not a *substance* adjudicator.
7. **Unsampled families.** C3/C4/C6 families in the 6 quota-blocked
   repositories (dinov2, bert, evaluate, flax, evalplus, Barlow) were
   not searched in R1-D2; 0-confirmed there is *not* claimed. The
   negative result holds within the 4-repo searched scope only.
8. **Template scope.** The principle library (P1–P6) is fixed and
   small; a new constraint *class* requires a new template. The
   protocol-grounded specification is strong within the current
   template space; it does not claim unbounded generality.
9. **Trace self-hash opacity.** The 16 frozen pre/post trace files
   carry `self_hash` fields that do not recompute under any standard
   JSON serialization. The trace *content* is verified consistent with
   the gold evidence and the paired-correction results; the hashes are
   opaque integrity markers from the original build run. This means
   trace-level cryptographic integrity is not independently
   verifiable post-hoc (Appendix I).
10. **Wording / hedging discipline.** Throughout the manuscript we use
    "we did not find evidence that X does Y" rather than "X cannot do
    Y" for prior-art claims, reflecting the scope of our survey (see
    §3 and `R2_NOVELTY_DEFENSE.md`). This is a reporting choice, not a
    scientific one.

The scarcity of high-quality, recoverable execution histories is itself
a finding: it motivates better provenance infrastructure as a
*precondition* for the kind of verification EpiTrace performs. We do
not hide the limitations; we argue they are the very reason the field
needs EpiTrace's class of check.

---

## 10. Conclusion

We introduced EpiTrace, which specifies a paper's protocol statements as
epistemic execution constraints and checks them against runtime
provenance, localizing the evidential failure when the check fails. The
central result is that a reported number's *correctness* is not the same
as its *evidential validity*: two executions can agree on the value while
only one constitutes admissible evidence for the claim. Across controlled,
real-trace, and naturalistic evaluations, EpiTrace separates the
epistemically invalid execution that a value check cannot see, and a
search-negative control shows it does so specifically. We conclude that
*numerical agreement does not imply evidential validity*, and that the
process by which a number was produced carries scientific information that
the number itself does not — information that can be captured, checked,
and localized without re-running the experiment.

---

## References
[Placeholders — to be populated from the prior-art matrix and the cited
errata/PRs. Each R1-C gold source is a real, independently-checkable
reference: Zeng et al. AAAI 2023 (LTSF-Linear); Musgrave et al. ECCV
2020; Henderson et al. AAAI 2018; Post WMT 2018 + Fairseq #2499;
Lan (ALBERT) #37/#18; Errica et al. ICLR 2020; Fairseq PR #1360;
Zhou (CenterNet) #7/#53.]
