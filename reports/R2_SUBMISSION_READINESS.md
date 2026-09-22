# R2 §20: Submission Readiness Verdict

Generated at end of R2 paper-lock phase. All frozen hashes re-verified
(R1-C 25/25 SHA-OK + 8/8 manifest-hash-consistent under the correct
JSON-serialization scheme; Stage1b 17/17; R1-D2 476/476 adjudicated).
No frozen result was modified.

---

## Forensic Audit (§3)
8/8 naturalistic cases = **Grade A** (complete independent chain:
physical isolation, single-freeze-timestamp, blind files free of gold
fields, pre-predictions free of post-verdicts, SHA-consistent, gold
independently sourced). No case downgraded to B/C/INVALID.

**FORENSIC_STATUS = PASS**

## Novelty (§5)
Closest neighbors (P-PLAN, Validity Constraints 2024, RO-Crate) differ on
the epistemic + value-preserving + naturalistic-validation axes that EpiTrace
occupies. No fatal collision. The one calibration decision is the
*automaticity* framing (reviewer A5): claim **protocol-grounded
constraint specification** (fixed P1–P6 template library, induced from the
paper without bug access), not unbounded free-form induction.

**NOVELTY_STATUS = CLEAR_ENOUGH_FOR_SUBMISSION**

## Contract Audit (§11)
5/8 EXPLICITLY_SUPPORTED_BY_PAPER, 3/8 REASONABLE_GENERAL_SCIENTIFIC_
PRINCIPLE, **0 FAULT_SPECIFIC, 0 OVERREACH, 0 AMBIGUOUS**. No contract
excluded from the primary claim. CIA=1.0 is defended, not assumed.

**CONTRACT_AUDIT = PASS**

## Reviewer Attack Simulation (§12)
- **FATAL_REVIEWER_OBJECTIONS (unresolvable without new work) = 0**
- Reviewer A: 0 FATAL / 4 MAJOR / 6 MINOR
- Reviewer B: 1 arguably-FATAL (B1, reframable) / 8 MAJOR / 3 MINOR
- Reviewer C: 1 arguably-FATAL (C1, closed by forensic+contract audit) /
  7 MAJOR / 4 MINOR
- All objections answerable by (a) existing artifacts, (b) honest
  reframing/narrowing, or (c) a limitations paragraph.
- **NEW_EXPERIMENT_REQUIRED = NO** (per §13 stop-rule: no FATAL objection
  that can't be handled by narrowing the claim).

## What to fix before submission (reporting-level, no new experiments)
1. **B1/B8**: Add binomial (Clopper–Pearson) CIs to NVR/NPCR/PSD; reframe
   1.0 as detectability, not population recall.
2. **A5**: Calibrate the induction claim to "protocol-grounded" (done in
   §4.1 of the manuscript).
3. **B4/A7**: State ε concretely per experiment (Appendix G).
4. **B7/C4**: Add per-case trace-basis column (live vs documented) to
   Table 4.
5. **C3**: Add gold-authority tier column (E > B > A) to Table 4.
6. **B9**: State the 6 unsampled C3/C4/C6 repos as a limitation, not a
   negative result.
7. **A3**: Footnote the 2 ABSTAIN cases with reason.

## Manuscript state
V0 complete for all 10 sections + abstract + 5 title candidates + 5 figure
specs + 5 table specs + appendix plan. Numbers trace to frozen artifacts.
Remaining work is **polish**: CI annotations, Table 4 column additions,
references population, figure rendering, and the §4.1 wording pass.

**MANUSCRIPT_STATUS = READY_FOR_POLISH**

---

## TOP_CONFERENCE_RESEARCH_READINESS

Honest, non-inflated score. Weights: forensic integrity (20), novelty
defensibility (25), contract validity (15), empirical coverage (20),
reporting rigor (10), reproducibility (10).

- Forensic integrity: 20/20 (8/8 Grade A, all hashes consistent).
- Novelty defensibility: 21/25 (clear, but the automaticity calibration is
  a real narrowing; −4).
- Contract validity: 14/15 (audited, 0 fault-specific; −1 for small
  template library).
- Empirical coverage: 13/20 (controlled + real-trace + naturalistic +
  search-negative are all present and strong; −7 for small n, wide CIs,
  6 unsampled families).
- Reporting rigor: 6/10 (CIs, ε, trace-basis, gold-tier columns not yet
  in the tables; fixable in polish).
- Reproducibility: 9/10 (all numbers trace to frozen artifacts; −1 for
  undocumented-protocol cases in R1-C).

**TOP_CONFERENCE_RESEARCH_READINESS = 83%**

Interpretation: the *science* is submission-ready; the *paper* is
submission-ready after the reporting-polish items above. The 83% reflects
that no fatal gap exists, but the empirical set is small (n=8 natural,
6 families unsampled) and the tables still lack CIs/ε/trace-basis. It is
deliberately not inflated to 90+ — a reviewer who weights the naturalistic
scale (Reviewer B) would discount more.

## Final verdict block

```
FORENSIC_STATUS              = PASS
NOVELTY_STATUS               = CLEAR_ENOUGH_FOR_SUBMISSION
CONTRACT_AUDIT               = PASS
FATAL_REVIEWER_OBJECTIONS    = 0
NEW_EXPERIMENT_REQUIRED      = NO
MANUSCRIPT_STATUS            = READY_FOR_POLISH
TOP_CONFERENCE_RESEARCH_READINESS = 83%
```

## Do NOT do
- No R1-E / R1-F / R1-G expansion rounds.
- No modification of frozen R1-A / R1-B1 / R1-C / R1-D2 results.
- No new experiments (stop-rule: no qualifying FATAL objection).
- Broad case search stays closed unless a specific FATAL reviewer
  objection later requires it.
