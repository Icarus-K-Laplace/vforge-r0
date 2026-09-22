# EpiTrace: Abstract — V2 (finalized)

Structure per brief: 1 Problem, 2 Gap, 3 EpiTrace, 4 Controlled
identifiability result, 5 Real-trace result, 6 Naturalistic validation,
7 Implication. Conceptual center: "Two executions can yield the same
reported result while differing in whether their execution process
provides valid evidence for the scientific claim." Does NOT lead with
8/8; sample size stated; no population-level recall claim.

---

## Abstract (V2, ~230 words)

**1. Problem.** Two executions of the same code on the same data can
yield the same reported result yet differ in whether the execution
process provides valid evidence for the scientific claim. A paper that
reports "the mean over five declared seeds" is supported by an
execution that averages all five, and — to measurement precision — also
by one that averages the three best; a reported-value check cannot tell
the two apart.

**2. Gap.** Existing provenance, reproducibility, and workflow-conformance
systems record *what happened* and check operational or value
consistency. In our survey we did not find evidence that any of them
derives claim-relevant *epistemic* constraints from the paper's protocol
and checks a live execution trace against them.

**3. EpiTrace.** We introduce EpiTrace, which specifies protocol-grounded
epistemic constraints from a paper's protocol statements (without access
to the eventual bug) and evaluates a typed execution trace against
them, returning PASS / FAIL / ABSTAIN and a localized witness on
failure.

**4. Controlled identifiability.** On 30 same-paper/same-code pairs
across 6 deviation families, EpiTrace separates valid from invalid
executions with PSD = 0.900 (27/30; 95% CI [0.735, 0.994]), where four
baselines score 0/30.

**5. Real-trace.** On 48 claim-level pairs from two public repositories,
36 of them strict value-preserving (VPS ≤ 0.25), EpiTrace separates
48/48 (36/36 strict), while the result-matching baseline separates 0/48.

**6. Naturalistic validation.** Blind validation on 8 frozen,
independently confirmed historical corrections — author errata, merged
fix pull requests, and a reproducibility paper — yields NVR = NPCR =
witness accuracy = 8/8 (95% CI [0.631, 1.000]), with contracts audited
paper-supported (0 fault-specific) and a 476-lead search-negative
control adding 0 confirmed cases (95% upper bound on false-confirm 0.77%).

**7. Implication.** A reported number's correctness is not its
evidential validity; the process that produced a value carries scientific
information the value itself does not, and it can be checked and
localized without re-running the experiment.
