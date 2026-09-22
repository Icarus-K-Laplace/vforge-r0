# R2 §5: Novelty Defense

## Claim
EpiTrace introduces a new verification class: **automatic compilation of scientific
protocol statements into epistemic execution constraints, followed by machine
checking over runtime provenance to detect execution histories whose outputs
may numerically agree with the paper while their evidential process does not
support the scientific claim.**

This is the candidate novelty. Everything else — provenance capture, workflow
recording, static code checking, paper-code consistency, value matching — is
explicitly excluded from the novelty claim and cited as prior art.

## Explicit Novelty Exclusions (What EpiTrace Does NOT Claim)
1. **Not** novel provenance capture (MLflow2PROV, PROV, RO-Crate all capture execution traces).
2. **Not** novel workflow representation (P-PLAN, RO-Crate, Airflow DAGs).
3. **Not** novel constraint checking per se (Validity Constraints 2024, workflow conformance monitors).
4. **Not** novel paper-code consistency (ReproZip, Paper2Code, RePro).
5. **Not** novel natural-language workflow generation (LLM-Workflow, AutoPipeline).
6. **Not** novel execution attestation or attested computation (CiteArk, AI attestation systems).
7. **Not** novel reported-value vs observed-value matching (any reproducibility harness).

## What Is Novel
The specific composition for which, in our survey, we did not find evidence
in any single published system:
- **A: Protocol-grounded constraint specification (calibrated claim).**
  Given a paper P and a claim C, a procedure F(P,C) → Φ_C produces a set of
  epistemic constraints by *matching the paper's protocol statements*
  (seed declaration, split description, aggregation procedure, evaluation
  tool version, checkpoint-selection rule) to a fixed library of principle
  templates (P1–P6), without access to the eventual bug. We claim
  *protocol-grounded* specification — not unbounded free-form induction.
  The template library is fixed and small; a new constraint *class* would
  require a new template. This calibration (reviewer A5) is the single most
  important framing decision in the paper.
- **B: Epistemic character.** The constraints are properties of the *evidential
  process* ("did this execution produce admissible evidence for this claim?"),
  not operational properties ("did step X run?"). This is the axis on which
  P-PLAN and Validity Constraints 2024 differ.
- **C: Value-preserving discrimination.** The system detects the case where
  two executions of the same code produce (nearly) the same reported scalar
  but only one constitutes valid evidence. In our survey, we did not find
  evidence that any published system targets this failure mode.
- **D: Naturalistic external validation.** Blind pre-prediction against 8 real,
  publicly-documented historical corrections (author errata, merged fix PRs,
  reproducibility papers), with physical isolation of gold evidence from blind
  inputs. In our survey, we did not find evidence that any published system
  carries a naturalistic external-validation protocol of this kind.

## Nearest Neighbors and How They Differ

### P-PLAN (ICWS 2024 / preprint)
- **What it does**: Provenance-based planning and execution for scientific
  workflows. Captures execution provenance, represents the intended workflow,
  and supports constraints.
- **How EpiTrace differs**: P-PLAN's constraints are *operational* and
  *hand-specified* ("step 3 must complete before step 4", "output file X must
  exist"). EpiTrace's constraints are *epistemic* and *auto-induced from the
  paper* ("the reported metric must be the mean over all declared seeds").
  P-PLAN does not detect value-preserving violations and has no naturalistic
  validation protocol.

### Workflow Run RO-Crate (W3C)
- **What it does**: Records a workflow execution as a RO-Crate artifact
  (software package + manifest + annotations).
- **How EpiTrace differs**: RO-Crate is a recording standard — it answers
  "what happened?" not "was what happened scientifically admissible?" It
  imposes no constraints, does not check actual execution against a scientific
  protocol, and has no discrimination capability.

### Validity Constraints for Data Analysis Workflows (2024)
- **What it does**: Formal validity constraints over data-lineage graphs
  (e.g., "the training set must not be derived from the test set").
- **How EpiTrace differs**: These constraints are *declarative* and
  *operational* (data-flow properties). EpiTrace's constraints are
  *epistemic* (properties of the evidence-generation process relative to a
  scientific claim) and are *induced automatically* from the paper's protocol,
  not written by a domain expert.

### MLflow2PROV / PROV-O
- **What it does**: Maps MLflow experiment-tracking entities (runs, metrics,
  params, artifacts) to PROV-O annotations.
- **How EpiTrace differs**: Post-hoc recording only. No constraint checking,
  no paper-protocol induction, no discrimination.

### CiteArk CAP
- **What it does**: Citation provenance API — links software/code to the
  citations that justify its use.
- **How EpiTrace differs**: Citation graph, not execution provenance. No
  runtime checking, no epistemic constraints.

### ReproZip / Paper2Code / RePro
- **What they do**: Check whether a paper's code reproduces its reported
  values. ReproZip packages the execution environment; Paper2Code generates
  code from a paper; RePro measures reproducibility.
- **How EpiTrace differs**: These check *value agreement* (does the code
  produce the paper's numbers?). EpiTrace targets the case where the values
  *do* agree but the *process* is scientifically inadmissible — the
  value-preserving violation. A paper that reports "mean over all seeds"
  but whose code silently drops two failing seeds will pass ReproZip's
  value check (if the remaining seeds' mean happens to be close) but fail
  EpiTrace's epistemic check.

## Residual Collision Risk
The one axis where a collision could be argued: **automatic constraint
induction from papers.** If a future system does "paper → formal constraint
set → check against execution" with *operational* (not epistemic)
constraints, it would overlap with EpiTrace on axis A but not on B/C/D.
The defense: the epistemic character of the constraints (B) and the
value-preserving discrimination target (C) are what distinguish EpiTrace.
A system that auto-induces operational constraints and checks them is a
workflow conformance monitor, not a scientific-evidence validator.

**Status: CLEAR_ENOUGH_FOR_SUBMISSION.** No fatal collision. The manuscript
must cite all of the above and position EpiTrace on the epistemic/value-
preserving axis for which, in our survey, we did not find evidence that any
published system provides a complete solution.
