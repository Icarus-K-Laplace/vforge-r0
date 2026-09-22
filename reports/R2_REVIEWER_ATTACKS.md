# R2 §12: Reviewer Attack Simulation

Three independent reviewer personas. Each gets: top objections, severity,
existing evidence that answers it, missing evidence, minimal repair.

Severity scale: FATAL (blocks acceptance), MAJOR (requires rebuttal /
revision), MINOR (can be addressed in camera-ready).

---

## Reviewer A — Formal Methods / Provenance Expert

*Attacks novelty and the epistemic/operational constraint distinction.*

### A1. "P-PLAN already does provenance + constraints; what is actually new?"
- **Severity**: MAJOR
- **Existing evidence answering**: R2_PRIOR_ART_MATRIX + R2_NOVELTY_DEFENSE.
  P-PLAN uses hand-specified *operational* constraints ("step X before step Y").
  EpiTrace auto-induces *epistemic* constraints from paper protocol and checks
  value-preserving violations. Neither P-PLAN nor RO-Crate targets
  EvidenceValidity(T+) ≠ EvidenceValidity(T−) with Result(T+)≈Result(T−).
- **Missing evidence**: None for the distinction itself, but the paper must
  include the prior-art matrix (Table 1) and 2–3 sentences explicitly
  diffing EpiTrace from P-PLAN on the epistemic axis.
- **Minimal repair**: Add a "Relation to P-PLAN and validity-constraint
  monitors" paragraph in Related Work citing the matrix row.

### A2. "Your 'epistemic constraint' is just a boolean predicate over trace
  fields. Where is the formal characterization?"
- **Severity**: MAJOR
- **Existing evidence answering**: §6 formal core — V(Φ_C, G_T) ∈ {PASS, FAIL,
  ABSTAIN}, G_T ⊨ Φ_C, and the VPVD definition (T+, T− with |y+−y−|≤ε but
  differing conformance). R1-A pairs and R1-B1 VPVD.csv (48 value-preserving
  pairs) instantiate this.
- **Missing evidence**: A soundness/precision argument for the verifier is
  *not* claimed and should not be — the verifier is a decision procedure over a
  finite contract, not a proof system. The paper must state its guarantees
  are *bounded by contract observability* (see §18 limitations).
- **Minimal repair**: One paragraph clarifying the verifier's guarantee class
  ("sound w.r.t. the induced contract, not w.r.t. all scientific validity").

### A3. "ABSTAIN is an admission that the system can't decide. How many
  ABSTAINs, and do they hide false negatives?"
- **Severity**: MAJOR
- **Existing evidence answering**: R1-A ablations show ABSTAIN/FAIL on
  E03-03 and E06-05 (2 of 30 pairs) where the invalid execution was not
  detected (pair_correct=0). R1-C: 0 ABSTAIN. So ABSTAIN is rare and
  honestly reported.
- **Missing evidence**: A principled threshold for when ABSTAIN is
  epistemically justified vs. a coverage gap. The "coverage" field in the
  pair results (1.0 in most) supports observability, but the ABSTAIN cases
  need explanation.
- **Minimal repair**: Footnote the 2 ABSTAIN cases with the reason (e.g.,
  unobservable field in the public trace).

### A4. "You conflate 'workflow conformance' (a well-studied problem) with
  'scientific admissibility'."
- **Severity**: MINOR
- **Existing evidence answering**: The novelty defense explicitly excludes
  workflow conformance and positions EpiTrace on the *epistemic* axis.
- **Missing evidence**: None.
- **Minimal repair**: None.

### A5. "A single-predicate contract per case (1 predicate × 8 cases) is
  thin. Does the compiler actually *induce* or did you hand-write one
  predicate per case?"
- **Severity**: MAJOR (this is the strongest A-attack)
- **Existing evidence answering**: R2_CONTRACT_AUDIT shows each predicate is
  EXPLICITLY_SUPPORTED_BY_PAPER (5/8) or REASONABLE_GENERAL_SCIENTIFIC_
  PRINCIPLE (3/8) — i.e., induced from the paper's text, not reverse-
  engineered from the bug. But the *compiler* F(P,C) is not demonstrated
  to generalize; each contract was induced for a specific (P,C) pair.
- **Missing evidence**: A demonstration that the *same* compiler induces
  the contract from the paper alone without being told which predicate
  applies (i.e., the induction is automatic, not per-case manual selection).
  The current evidence is "a human/agent read the paper and wrote the
  matching predicate" — which is *paper-derived* but not obviously *automatic*.
- **Minimal repair**: If the compiler is a fixed set of principle templates
  (P1 split-disjointness, P6 aggregation, etc.) matched to paper protocol
  statements, say so and show the matching rule. If it was per-case manual,
  claim "protocol-grounded constraint specification" not "fully automatic
  induction," and move the automatic-induction claim to future work.
  **This is the single most important framing decision in the paper.**

### A6. "Same-paper/same-code paired discrimination is trivially satisfied
  if the two traces differ in a field you chose to check."
- **Severity**: MINOR
- **Existing evidence answering**: The static baseline B2 (static auditor
  with identical information) scores 0 across all pairs, so the
  discrimination is not an artifact of trivially-different inputs.
- **Missing evidence**: None.
- **Minimal repair**: None.

### A7. "You cite 'value-preserving' violations but never prove |y+−y−|≤ε
  in the naturalistic cases."
- **Severity**: MAJOR
- **Existing evidence answering**: R1-C marks only 2 of 8 cases as
  value_preserving (value_preserving_naturalistic_cases=2). The R1-B1
  VPVD.csv gives vps values (0.08–0.24 abs diff) for 48 real-trace pairs.
- **Missing evidence**: For the 2 naturalistic VP cases, an explicit
  statement of the measured |y+−y−| and the ε threshold used.
- **Minimal repair**: Report the actual numeric gap for the 2 naturalistic
  VP cases and define ε.

### A8. "ABSTAIN + coverage=1.0 is contradictory: if coverage is 1.0, why
  can the verifier abstain?"
- **Severity**: MINOR
- **Existing evidence answering**: coverage measures the fraction of
  *contract predicates* whose trace fields are observable; ABSTAIN arises
  when a predicate's *outcome* is not determined by observed fields (e.g.,
  a selection happened but the selection target is not in the trace).
- **Missing evidence**: A one-line definition distinguishing field-
  observability (coverage) from outcome-determinacy.
- **Minimal repair**: Define both in §6.

### A9. "The witness is a trace-entity pointer, not a proof. What is its
  epistemic content?"
- **Severity**: MINOR
- **Existing evidence answering**: Witness accuracy=1.0 on R1-C; witness
  localizes to the exact trace field (e.g., protocol.selection_target) that
  the gold correction addresses.
- **Missing evidence**: A semantic-match rubric (how "semantic match=TRUE"
  was judged — automated or human?).
- **Minimal repair**: State the witness-match protocol in the appendix.

### A10. "You claim novelty over 'reported-value vs observed-value
  matching' but that exclusion is doing a lot of work."
- **Severity**: MINOR
- **Existing evidence answering**: The exclusion is explicit (§2 of the brief);
  the paper states EpiTrace targets the process, not the value.
- **Missing evidence**: None.
- **Minimal repair**: None.

**Reviewer A verdict: 0 FATAL, 4 MAJOR, 6 MINOR.**
The MAJOR items are addressable by *framing* (A5 especially: automatic vs.
protocol-grounded induction), not by new experiments. A5 is the one to
resolve before locking the manuscript.

---

## Reviewer B — ML Empirical-Methodology Reviewer

*Attacks scale, baselines, and statistics.*

### B1. "8 naturalistic cases is too few to claim NVR=1.0."
- **Severity**: FATAL (in the reviewer's mind) → arguably MAJOR with
  honest framing.
- **Existing evidence answering**: R1-D2 shows the *search space* is not
  infinite: 476 keyword-matched leads across 10 high-impact repos were
  fully adjudicated, yielding 0 additional confirmed cases. This is a
  *search-negative result* — the 8 cases are not cherry-picked from a
  small pool; they are essentially all the confirmed naturalistic cases
  available under the strict 5-condition gold-chain gate.
- **Missing evidence**: A confidence interval on NVR for n=8 is trivially
  [0.44, 1.0] (95%, Clopper-Pearson). The paper must report this and
  interpret NVR=1.0 as "no detected failures," not "true recall is 1.0."
- **Minimal repair**: Report the CI, reframe NVR as a *lower-bound
  detectability* result, and lead with R1-D2's 476-lead search-negative
  as evidence against cherry-picking. This converts FATAL→MAJOR.

### B2. "Strongest-baseline recall 0.0 vs EpiTrace 1.0 — but your
  baselines (B0–B4) may be strawmen."
- **Severity**: MAJOR
- **Existing evidence answering**: B0=paper+result only, B1=paper+repo,
  B2=static auditor (identical information to EpiTrace minus trace), B3/B4
  = random/generic. The ablation ladder (A1–A5) is principled: the key
  comparison is A3 (full provenance *without* contract) vs A5 (EpiTrace),
  which isolates the contribution of the *constraint*, not just the trace.
- **Missing evidence**: A3 (full provenance without contract) result. The
  R1A_ABLATIONS.csv shows B0/B1/B2 but the brief asks for A1–A5. Need to
  confirm A3 (provenance-only, no contract) is reported — if a provenance
  monitor *without* the epistemic contract also scores 0, that proves the
  *constraint* (not the trace) is the active ingredient.
- **Minimal repair**: Ensure the ablation table includes A3 vs A5 and
  state that trace-without-contract fails to discriminate.

### B3. "30 controlled pairs (R1-A) and 48 real-trace pairs (R1-B1) —
  what is the statistical power?"
- **Severity**: MAJOR
- **Existing evidence answering**: The controlled experiments are
  *identifiability* demonstrations (can the method separate the pair?),
  not population estimates. The naturalistic n=8 is the external-
  validity estimate; its CI is the relevant statistic.
- **Missing evidence**: An explicit power analysis or, better, a statement
  that the controlled experiments are mechanistic (not statistical) and
  the naturalistic set is the inferential contribution.
- **Minimal repair**: One paragraph distinguishing the two roles.

### B4. "The value-preserving metric (vps, abs_diff) — how is ε chosen?
  Arbitrary ε makes 'value-preserving' unfalsifiable."
- **Severity**: MAJOR
- **Existing evidence answering**: R1-B1 VPVD.csv reports vps per pair;
  the definition |y+−y−|≤ε is in §6.
- **Missing evidence**: The concrete ε value(s) used, and justification
  (e.g., ε = paper's reported std across seeds, or a fixed 1% of dynamic
  range). Without this, "value-preserving" is a free parameter.
- **Minimal repair**: State ε explicitly per experiment and justify it.

### B5. "4 independent real-trace papers (R1-B1) but they are all
  pre-registered / constructed deviations, not natural bugs."
- **Severity**: MINOR
- **Existing evidence answering**: R1-B1 is explicitly the *real-trace +
  controlled-decision* tier; R1-C is the *natural* tier. The brief's
  evidence-ladder (Figure 3) already separates them.
- **Missing evidence**: None — but the paper must not conflate "real
  public traces" (R1-B1, deviations are constructed) with "natural
  historical corrections" (R1-C, deviations are real published bugs).
- **Minimal repair**: Precise wording distinguishing the two tiers.

### B6. "CIA=1.0 across all experiments is a red flag for overfitting the
  contract to the answer."
- **Severity**: MAJOR
- **Existing evidence answering**: R2_CONTRACT_AUDIT: 0 FAULT_SPECIFIC,
  0 OVERREACH; 5 EXPLICITLY_SUPPORTED, 3 REASONABLE_GENERAL. CIA=1.0
  reflects that every induced contract is defensible from the paper alone.
- **Missing evidence**: The audit is a human-style classification; the
  paper should note CIA was *audited* (this report) not just computed.
- **Minimal repair**: Cite the contract audit and its 5/3/0/0/0 breakdown.

### B7. "E02 real-world status = TRACE_INSUFFICIENT — so your most
  realistic evaluation could not even run."
- **Severity**: MAJOR (honest limitation)
- **Existing evidence answering**: The R1-C report records
  e02_real_world_status=TRACE_INSUFFICIENT: for some cases the public
  pre-fix runtime trace was not recoverable, so the *runtime* check fell
  back to the documented-protocol (gold) evidence. This is exactly the
  §18 limitation "public runtime traces are scarce."
- **Missing evidence**: A per-case flag: which of the 8 had a true
  recoverable runtime pre-trace vs. which relied on protocol-documentation
  evidence.
- **Minimal repair**: Add a "trace provenance" column to Table 4 marking
  each case's trace basis (live re-execution vs. documented-protocol).

### B8. "No variance / confidence intervals anywhere in the headline
  metrics."
- **Severity**: MAJOR
- **Existing evidence answering**: None currently reported.
- **Missing evidence**: CIs on NVR, NPCR, paired-correction rate.
- **Minimal repair**: Add Clopper-Pearson / binomial CIs for n=8 in Table 4
  and the abstract discussion.

### B9. "The 6 excluded repos in R1-D2 (dinov2/bert/evaluate/flax/evalplus/
  Barlow) are C3/C4/C6 families — exactly the under-explored ones. Your
  'search-negative' is not negative where it matters."
- **Severity**: MAJOR
- **Existing evidence answering**: R1-D2 explicitly records these as
  ACCESS_BLOCKED (quota), and the brief says R1-D2 is a pure expansion
  round that did *not* lower criteria. The honest statement is: the 476-
  lead search covered 4 repos; the C3/C4/C6 families were *not* fully
  searched.
- **Missing evidence**: A search of the 6 unfetched repos. This is the
  one place where additional work is defensible — BUT per §13 stop-rule,
  new experiments are only allowed if a FATAL reviewer objection requires
  them. This is MAJOR not FATAL, so NO new experiment; instead, state the
  limitation clearly.
- **Minimal repair**: A limitation paragraph: "Naturalistic search covered
  4/10 repos; C3/C4/C6 families remain under-explored; 0 confirmed there
  is *not* claimed."

### B10. "Paired correction rate NPCR=1.0 but pre and post use the same
  code for the 'clean' run — did you re-execute, or reuse a log?"
- **Severity**: MINOR
- **Existing evidence answering**: R1-C paired_corrections=8, all
  FAIL→PASS with the same frozen contract. The protocol is pre-fix trace
  (live or documented) → contract check → post-fix trace → recheck.
- **Missing evidence**: A clear statement of how the "post-fix" trace was
  obtained (re-execution of the fixed code vs. the fix commit's reported
  numbers).
- **Minimal repair**: One line per case in the appendix: post-trace provenance.

**Reviewer B verdict: 1 arguably-FATAL (B1, reframable), 8 MAJOR, 3 MINOR.**
Most are *reporting* fixes (CIs, ε, trace-provenance flags), not new
experiments. B1 and B9 are the two that need careful wording, and both are
answered by R1-D2 + an honest limitations section. No new experiment is
strictly required under the §13 stop-rule because none is FATAL in a way
that cannot be addressed by narrowing the claim.

---

## Reviewer C — Skeptical Reproducibility Reviewer

*Attacks leakage, cherry-picking, and naturalistic gold quality.*

### C1. "How do you know the blind prediction wasn't contaminated by the
  gold?"
- **Severity**: FATAL (if unanswered) → MAJOR with the forensic audit.
- **Existing evidence answering**: R2_R1C_FORENSIC_AUDIT (8/8 Grade A):
  physical isolation (R1C_BLIND/ vs R1C_DISCOVERY_GOLD/), single-manifest
  freeze timestamp, blind files contain no gold fields, pre-predictions
  contain no post-verdict, all 25 SHA256SUMS + 8 manifest hashes verified
  consistent under the correct scheme.
- **Missing evidence**: The audit proves *structural* isolation, not that
  the *human* who induced the contract didn't already know the bug. The
  contract-audit (CAND-05/07/08 = REASONABLE_GENERAL) shows the contracts
  are inducible from the paper alone — this is the answer to human
  contamination.
- **Minimal repair**: Combine the forensic audit (structural) + contract
  audit (content) to close both leakage channels. State both explicitly.

### C2. "The 8 cases are exactly the famous reproducibility papers. Of
  course EpiTrace catches them — they're the canonical examples."
- **Severity**: MAJOR
- **Existing evidence answering**: This is the cherry-picking concern from
  §4. The CONSORT-like flow (discovered → paper-linked → gold-confirmed →
  recoverable pre-fix → execution-evidence → blind-evaluable) plus R1-D2's
  476-lead search (0 additional confirmed) shows the 8 are the *survivors*
  of a filter, not a hand-pick. The famous-reproducibility-paper nature is
  precisely *why* they have independent gold (author errata / merged PR /
  reproducibility paper) — that's the inclusion criterion, not a bias.
- **Missing evidence**: A statement that the 8 were selected by the
  *gold-chain gate* (independent external confirmation), which is
  anti-cherry-picking (you cannot confirm a case without an external
  authority).
- **Minimal repair**: Lead §8 with the selection funnel, not with "we
  picked 8 famous papers."

### C3. "Gold quality: 'author confirmed on GitHub' (CAND-05, CAND-08) is
  weaker than 'merged fix PR' (CAND-07). Are all 8 golds equal?"
- **Severity**: MAJOR
- **Existing evidence answering**: Gold authority types are recorded per
  case: A_author_github_issue (CAND-05, CAND-08), B_explicit_fix_pr
  (CAND-07), E_reproducibility_paper (the rest). The forensic audit treats
  all 8 as Grade A but the *type* differs.
- **Missing evidence**: A tiering of gold strength. The paper should say
  the *strongest* primary evidence rests on the B (merged-PR) and E
  (independent reproducibility paper) cases, and A (author-issue) cases
  are corroborating.
- **Minimal repair**: Rank gold authority (E > B > A) and state which
  cases carry the primary evidential weight.

### C4. "The 'post-fix verdict PASS' — was the post-fix trace actually
  executed, or inferred from the fix commit's description?"
- **Severity**: MAJOR (overlaps B7)
- **Existing evidence answering**: R1-C pairs are all FAIL→PASS with the
  same frozen contract. But trace provenance (live vs documented) is not
  per-case flagged.
- **Missing evidence**: Per-case post-trace provenance.
- **Minimal repair**: Same as B7 — add trace-provenance column.

### C5. "Semantic_match=TRUE and localization_match=TRUE for all 8 — how
  were these judged? Human or automatic? If human, that's a leakage
  channel."
- **Severity**: MAJOR (overlaps A9)
- **Existing evidence answering**: Witness audit CSV records both TRUE.
- **Missing evidence**: The match rubric and who/what performed it.
- **Minimal repair**: Define the rubric; if human-judged, state it was
  done against the *predicted* witness (frozen) and the *gold* violation
  independently, with the judge not knowing the prediction until after.

### C6. "You can't claim 'EpiTrace detects the violation' if the
  violation was defined to match the predicate."
- **Severity**: MINOR
- **Existing evidence answering**: The predicate is induced from the paper
  (contract audit), not from the violation. The violation is what the
  gold evidence describes. The two agreeing (semantic match) is the
  *test*, not the definition.
- **Missing evidence**: None — but the paper must make the
  induction-before-violation-observation order explicit.
- **Minimal repair**: Timeline figure: contract induced from paper (T0) →
  blind prediction (T1) → gold reveal (T2), with T0 < T2 always.

### C7. "R1-D2 used a *compromised* token and a fake-token ad-hoc run that
  drained your rate limit. Does any of that taint the 476-lead result?"
- **Severity**: MINOR (process, not science)
- **Existing evidence answering**: R1-D2 §0 secret audit = SECRET_FOUND NO;
  the pipeline is token-free (env/gh/anonymous only); the 476 leads come
  from §2's clean 8-call anonymous fetch. The token scrubbing and the
  fake-token mock run were verification hygiene, not data sources.
- **Missing evidence**: A one-line statement that the adjudicated corpus is
  from the clean §2 anonymous fetch, not from any token-authenticated run.
- **Minimal repair**: One sentence in §8 / limitations.

### C8. "NVR=NPCR=1.0 with n=8: if one case flips, you're at 7/8. The
  contribution is fragile."
- **Severity**: MAJOR (overlaps B1)
- **Existing evidence answering**: The honest framing is *detectability*,
  not *recall*. R1-D2's 0-additional-confirmed is itself a robustness
  signal (the method doesn't over-fire on the 476 non-cases).
- **Missing evidence**: R1-D2's 476 leads give a *negative-control* set:
  476 adjudicated, 0 confirmed, meaning the method has a low false-positive
  rate on real issues.
- **Minimal repair**: Report R1-D2 as the negative control: EpiTrace did
  NOT confirm any of 476 real GitHub issues as value-preserving
  violations, supporting specificity.

### C9. "The 'localization witness' points to trace fields like
  protocol.selection_target — but those fields are in *your* trace schema.
  You're localizing to your own representation."
- **Severity**: MINOR
- **Existing evidence answering**: The trace schema is a typed execution
  graph G_T; the witness is a node in G_T. Localization accuracy is
  measured against the gold violation's *semantic* locus (which split /
  which aggregation), not against a fixed schema.
- **Missing evidence**: A mapping showing the witness node corresponds to
  the gold's described violation locus.
- **Minimal repair**: In the appendix, map each case's witness → gold
  violation locus.

### C10. "You rely on GitHub issue numbers as gold (Informer #36/#118,
  ALBERT #37/#18, CenterNet #7/#53). Issues can be closed in error."
- **Severity**: MINOR
- **Existing evidence answering**: Each issue reference is paired with an
  independent authority (author, merged PR, or reproducibility paper).
  No case rests on a single issue.
- **Missing evidence**: Explicit dual-authority for each case (already in
  the forensic CSV's gold_authority field).
- **Minimal repair**: Ensure the Table 4 / appendix lists ≥2 gold sources
  per case where available.

**Reviewer C verdict: 1 arguably-FATAL (C1, closed by forensic+contract
audit), 7 MAJOR, 4 MINOR.**

---

## Consolidated Stop-Rule Decision (§13)

A new experiment is permitted ONLY if a FATAL objection satisfies all of:
(1) not answered by existing artifacts, (2) materially affects the main
claim, (3) cannot be fixed by narrowing the claim, (4) testable without
contaminating the frozen evaluation.

- **B1 / C8** (n=8 fragility): Answered by R1-D2 negative control + CI
  reframing → *not* FATAL; fix by narrowing claim. **No new experiment.**
- **C1** (leakage): Answered by forensic + contract audit → *not* FATAL.
  **No new experiment.**
- **B9** (C3/C4/C6 families unsearched): MAJOR, not FATAL; fix by stating
  the limitation. A *new* search of 6 repos is possible but is NOT required
  to defend the main claim, and per the brief's paper-lock discipline it is
  deferred. **No new experiment (documented as limitation).**
- **A5** (automatic vs. protocol-grounded induction): The single most
  consequential *framing* decision. It is **not** an experiment question —
  it is a claim-calibration question. **Resolve in the manuscript, not in
  a new run.**

**FATAL_REVIEWER_OBJECTIONS (unresolvable without new work): 0**
**NEW_EXPERIMENT_REQUIRED: NO**

Every objection is answerable by (a) existing artifacts, (b) honest
reframing / narrowing, or (c) a limitations paragraph. The manuscript can be
locked without contaminating the frozen evaluation.
