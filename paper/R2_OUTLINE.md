# EpiTrace: From Scientific Claims to Epistemic Execution Constraints
## Manuscript V0 Outline

Target venue: ICML (methodology / trustworthy ML track), with secondary
positioning at ICLR / NeurIPS. The manuscript stands alone without venue-
specific claims.

---

## Abstract (§15)
Problem: ML experiments increasingly produce correct numbers through
questionable processes.
Gap: Existing provenance and reproducibility tools answer "what happened?"
but not "was what happened scientifically admissible for the claim being
made?"
Method: EpiTrace compiles a paper's protocol statements into epistemic
execution constraints and checks them against runtime provenance.
Controlled result: Same-paper/same-code paired discrimination (R1-A: 30
pairs, PSD = 0.900 (27/30), 0% for all 4 baselines).
Real-trace result: 48 claim-level pairs from 2 public repositories, 36
strict value-preserving, EpiTrace PSD = 48/48 (R1-B1).
Naturalistic result: 8 real historical corrections, NVR=NPCR=1.0,
blind pre-prediction, 0 leakage.
Main implication: Numerical agreement does not imply evidential validity.

## 1. Introduction
- Scientific AI is automating hypothesis → code → experiment → analysis →
  paper.
- Two executions can produce the same reported result while only one
  constitutes valid evidence for the claimed protocol.
  (Example: "mean over all seeds" vs. "outcome-conditioned subset, same
  final scalar.")
- Existing verification checks code consistency, reproducibility, and
  reported-vs-observed values. It does not check *evidential validity*.
- EpiTrace formulates **value-preserving epistemic violations** and checks
  them automatically.
- Six contributions (≤6, per §7):
  1. Formulate scientific execution conformance and value-preserving
     epistemic violations.
  2. Protocol-grounded constraint specification (paper protocol statements
     matched to a fixed principle-template library — see A5 framing
     decision; do NOT claim unbounded free-form automatic induction).
  3. Runtime provenance verifier with localized scientific witnesses.
  4. Controlled identifiability evaluation (R1-A).
  5. Real-public-trace cross-paper evaluation (R1-B1).
  6. Blind naturalistic historical-correction validation (R1-C) +
     search-negative control (R1-D2).

## 2. Problem Formulation (§6)
- P = paper/protocol, C = claim, Φ_C = induced epistemic contract,
  T = execution trace, G_T = typed execution graph.
- Contract induction: F(P,C) → Φ_C.
- Verification: V(Φ_C, G_T) ∈ {PASS, FAIL, ABSTAIN}; G_T ⊨ Φ_C.
- Value-preserving violation: T+, T− with |y(T+)−y(T−)| ≤ ε but
  G_T+ ⊨ Φ_C and G_T− ⊭ Φ_C.
- Define: VPVD, Paired Scientific Discrimination, Witness Accuracy,
  Contract Induction Accuracy, Naturalistic Violation Recall,
  Naturalistic Paired Correction Rate.
- Key conceptual distinction: output equivalence vs. evidence-process
  validity.
- Guarantees: verifier is sound w.r.t. the induced contract, bounded by
  contract observability (state explicitly; do not overclaim).

## 3. Related Work
- Explicit exclusions (from §2): provenance, runtime traces, prospective vs.
  retrospective, plan-vs-execution, workflow validity constraints, workflow
  conformance, NL workflow generation, paper-code checking, reproducibility
  infrastructure, claim extraction, execution attestation, reported-vs-
  observed matching.
- Cite and distinguish: P-PLAN/PROV, Workflow Run RO-Crate, Validity
  Constraints for Data Analysis Workflows (2024), MLflow2PROV, CiteArk/CAP,
  AI-assisted spec-to-execution, execution-evidence/claim-boundary work.
- Position EpiTrace on the epistemic / value-preserving axis for which,
  in our survey, we did not find a published system occupying the full
  composition (specification + runtime checking + localization +
  naturalistic validation).
- Include Table 1 (prior-art capability matrix, from R2_PRIOR_ART_MATRIX).

## 4. EpiTrace (method)
- 4.1 Epistemic contract induction (F): paper protocol statements → typed
  constraint predicates (principle templates P1–P6); match rule;
  observability requirement.
- 4.2 Runtime provenance typing (G_T): trace fields, typed execution graph.
- 4.3 Conformance verification (V): predicate evaluation, PASS/FAIL/ABSTAIN,
  coverage vs. outcome-determinacy (resolve A8).
- 4.4 Localized witness: trace-entity pointer + semantic locus mapping.
- 4.5 Value-preserving detection: ε threshold, VPS metric.
- State the automatic-vs-protocol-grounded induction decision (A5) here,
  precisely and honestly.

## 5. Experimental Design
- Evidence ladder (Figure 3): R1-A (controlled) → R1-B1 (real public traces
  + controlled deviations) → R1-C (natural historical corrections) → R1-D2
  (search-negative control).
- Distinguish mechanistic (R1-A/B1) from inferential (R1-C) roles (B3).
- Distinguish real-trace-with-constructed-deviation (R1-B1) from natural
  bug (R1-C) (B5).
- Selection funnel (CONSORT-like, §4): discovered → paper-linked →
  gold-confirmed → recoverable pre-fix → execution-evidence → blind-
  evaluable. R1-D2 476-lead adjudication as negative control (B9/C2/C8).

## 6. Controlled Identifiability Results (R1-A)
- Table 2: 30 paired executions, EpiTrace 100% pair-correct, B0–B4 0%.
- Ablation ladder A1–A5; key: A3 (provenance w/o contract) vs. A5
  (EpiTrace) isolates the constraint as the active ingredient (B2).
- ABSTAIN cases (E03-03, E06-05): report with reason (A3 reviewer).

## 7. Real-Trace Evaluation (R1-B1)
- Table 3: 48 value-preserving pairs, 4 independent papers/repos.
- VPS values, ε justification (B4).
- Same-repo paired discrimination; static baseline B2 = 0.

## 8. Naturalistic External Validation (R1-C)
- Table 4: 8 cases, NVR=NPCR=1.0, witness accuracy 1.0, CIA=1.0 (audited).
- Per-case trace-provenance column (B7/C4): live re-execution vs.
  documented-protocol.
- Gold authority tiering: E_reproducibility_paper > B_explicit_fix_pr >
  A_author_github_issue (C3).
- Blind protocol: physical isolation, single freeze timestamp, SHA-verified
  (forensic audit, 8/8 Grade A).
- Binomial CIs on n=8 (B1/B8): reframe NVR as detectability lower bound.
- R1-D2 search-negative: 476/476 adjudicated, 0 additional confirmed
  (B9/C8).

## 9. Limitations and Discussion (§18)
- Naturalistic set is small (n=8); CIs are wide.
- Public runtime traces are scarce (E02 = TRACE_INSUFFICIENT for some
  cases).
- E02 selection provenance often unavailable.
- Evidence concentrated in computational ML.
- Contracts depend on observability (coverage).
- EpiTrace does not determine scientific truth — it checks whether
  execution evidence conforms to claim-relevant protocol constraints.
- 4 of 10 target repos (C3/C4/C6 families) were quota-blocked in R1-D2;
  0-confirmed there is NOT claimed (B9).
- Scarcity of high-quality recoverable execution histories motivates
  better provenance infrastructure (framing, not a limitation to hide).

## 10. Conclusion
- Numerical agreement ≠ evidential validity.
- EpiTrace closes the gap: paper → epistemic contract → provenance check →
  conformance verdict → localized witness.
- Future: broader constraint-template library, more automatic paper-to-
  protocol matching (beyond the current template-based specification),
  runtime provenance infrastructure.

## Appendices
- A: All 8 naturalistic forensic chains (one page each).
- B: All contracts (8) + principle templates (P1–P6).
- C: All witness outputs (witness audit).
- D: R1-D2 search-negative (476-lead adjudication summary).
- E: Prior-art matrix (full).
- F: Witness semantic-match rubric + localization-mapping (A9/C9).
- G: ε definition and per-experiment values (B4).
- H: Gold authority tiering and per-case sources (C3/C10).
