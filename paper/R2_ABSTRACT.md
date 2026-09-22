# EpiTrace: Abstract (V0)

## Draft

Automatic machine-learning pipelines now produce increasingly accurate
results through an opaque chain of data processing, model selection, and
aggregation. A central question for trustworthy scientific computing is
whether a *correct reported number* is also *valid evidence* for the
scientific claim under which it was made. We study this question by
introducing **EpiTrace**, a verification system that (i) compiles a
paper's protocol statements into epistemic execution constraints, (ii)
checks these constraints against runtime provenance, and (iii) localizes
the evidential failure to a specific execution step when the check fails.

The key phenomenon we target is the **value-preserving epistemic
violation**: two executions of the same code on the same data produce
(nearly) the same reported scalar, yet only one execution constitutes
admissible evidence for the paper's claim. Numerical agreement therefore
does not imply evidential validity. Existing provenance systems and
reproducibility harnesses answer *what happened*; EpiTrace answers
*whether what happened was scientifically admissible for the claim being
made*.

We evaluate EpiTrace along an evidence ladder. In controlled same-
paper/same-code paired executions, EpiTrace discriminates valid from
invalid runs with 100% accuracy on 30 pairs, where four baselines
(paper-only, paper+repo, static auditor, random) score 0%. On 48
value-preserving pairs drawn from four independent public
repositories, EpiTrace detects the evidential violation in every case.
Blind validation against 8 real, independently-confirmed historical
corrections (author errata, merged fix pull requests, and
reproducibility papers) yields naturalistic violation recall and
paired-correction rate of 1.0, with contract-induction accuracy
independently audited as paper-supported (no fault-specific contracts).
A 476-lead search-negative control across 10 high-impact repositories
yields 0 additional confirmed cases, supporting specificity.

These results establish that the *process* by which a number was
produced carries scientific information that the number itself does not,
and that this information can be captured, checked, and localized
without re-running the experiment.

---

## Author notes (not part of the abstract)
- "100%" and "1.0" are the *frozen* R1-A/R1-C results. In the final
  manuscript, add binomial confidence intervals (n=30, n=8 are small)
  and frame as detectability, not population recall (reviewer B1/B8).
- "Blind validation" = blind inputs physically isolated from gold
  evidence before prediction (R1-C protocol); make explicit in the
  supporting clause.
- Tie "value-preserving" to a concrete ε in the final version
  (reviewer B4).
