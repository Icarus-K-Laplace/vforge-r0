# R2V2 Phase 1: Claim Lock

This file freezes the three claim levels for the R2-V2 manuscript. Every
paragraph of `R2_MANUSCRIPT_V2.md` must be compatible with exactly these
claims. Anything stronger is a claim-expansion violation.

---

## PRIMARY CLAIM (frozen)

> **Numerical agreement alone is insufficient to establish the
> evidential validity of a machine-learning experiment.**

Equivalently, the value-preserving epistemic violation (VPVD) exists:
two executions of the same code on the same data can produce (nearly)
the same reported scalar while only one execution constitutes admissible
evidence for the paper's claim. `Result correctness ≠ Evidence validity.`

This is the conceptual thesis. It is a statement about what a number
does and does not encode; it is not a statement about how common such
violations are in science.

## METHOD CLAIM (frozen, bounded)

> **EpiTrace performs protocol-grounded constraint specification from
> scientific text, and evaluates those constraints against runtime
> provenance.**

The method, precisely:

1. A fixed library of epistemic principle templates (P1–P6) is the
   template space.
2. Specification matches the paper's protocol statements to these
   templates and instantiates typed predicates over a typed execution
   trace. This step has **no access to the eventual bug**.
3. The verifier checks the trace against the induced contract, returns
   PASS / FAIL / ABSTAIN, and localizes a witness on FAIL.

**Forbidden method characterizations.** The manuscript MUST NOT
describe EpiTrace as:
- unrestricted automatic scientific rule discovery;
- free-form invariant induction;
- general scientific validity inference;
- a system that determines scientific truth.

The honest scope is *template-based, protocol-grounded* specification:
strong within the P1–P6 space; a new constraint *class* requires a new
template. That scope is stated in §4.1 and Limitations, not hidden.

## EMPIRICAL CLAIM (frozen, bounded by the R1-C set)

> **The existing frozen experiments show that EpiTrace can distinguish
> epistemically valid from invalid executions, including value-
> preserving cases, and detects the studied naturalistic historical
> corrections in the available R1-C set.**

Boundaries of this claim:
- Controlled identifiability (R1-A): PSD = 0.900 (27/30), baselines
  0/30; 30/30 is the pair-*construction* (identifiability) property,
  not a discrimination score.
- Real-trace (R1-B1): 48 claim-level pairs from 2 public repositories
  (ViewBatchModel CVPR'25, RevisitDML ICML'20); 36 strict value-
  preserving pairs under the frozen VPS ≤ 0.25 criterion; EpiTrace
  PSD = 48/48, strict-VPS 36/36; result-matching baseline 0/48.
- Naturalistic (R1-C): 8 frozen cases satisfying the strict gold-chain
  criteria; NVR = NPCR = Witness = CIA = 8/8 (95% Clopper–Pearson CI
  [0.631, 1.000]).
- Search-negative (R1-D2): 476 fully adjudicated discovery leads, 0
  additional cases meeting the strict gold-chain inclusion criteria;
  6 repositories (C3/C4/C6 families) were quota-blocked and are not
  claimed searched.

**Forbidden empirical generalizations.** The manuscript MUST NOT:
- read "8/8" as population-level recall or as "EpiTrace detects real
  scientific errors with 100% accuracy";
- infer the *prevalence* of value-preserving violations in science from
  the R1-C set (n = 8, wide CI);
- interpret R1-D2's 0-confirmed as an absence of real-world violations
  (it is a negative result *within the searched 4-repository scope*);
- claim the 8 naturalistic cases were hand-picked to fit the method.

## Compatibility rule

For every manuscript paragraph, ask:

1. Which of the three frozen levels does this paragraph assert?
2. Does it stay within the stated boundary (template scope; R1-C set;
   search scope)?
3. Would a reviewer flag any stronger reading?

If a paragraph admits a stronger reading, narrow it now. The three
levels are the *ceiling* of the paper's claims; the evidence-ladder
results are the *floor* of what is asserted.

```
CLAIM_LOCK = PASS (frozen as above; verified against V2 manuscript in
             Phase 11 consistency audit)
```
