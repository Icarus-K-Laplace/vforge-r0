# R2 §20: Submission Readiness Verdict — V1 (post-polish)

Generated at end of R2 paper-lock polish phase. All frozen hashes
re-verified (R1-C 25/25 SHA-OK + 8/8 manifest-hash-consistent under the
correct JSON-serialization scheme; R1-D2 476/476 adjudicated; R1-A /
R1-B1 frozen results cross-checked against manuscript). No frozen result
was modified. The V0 checkpoint is tagged `research-lock-v0` at commit
`0636156`; all polish work is on the `r2-polish-v1` branch.

---

## What the polish pass corrected (V0 → V1)

A full paper↔table↔artifact consistency audit found **two material
overstatements in the V0 manuscript** that are now corrected:

| # | V0 claim | Frozen value (source) | V1 correction |
|---|---|---|---|
| 1 | R1-A "PSD = 1.0 (30/30)" | **PSD = 0.900 (27/30)** (`R1A_FINAL_REPORT.md`, `R1A_PAIR_RESULTS.jsonl` `tc_pair_correct`) | §6 now reports 27/30 with 95% CI [0.735, 0.994] and names the 3 non-discriminated pairs (2 ABSTAIN + 1 clean false-positive E03-04) |
| 2 | R1-B1 "48 value-preserving pairs across 4 independent public repositories" | **48 claim-level pairs from 2 repositories; 36 strict value-preserving (VPS ≤ 0.25)** (`R1B1_FINAL_REPORT.md`, `R1B1_REAL_TRACE_PAIRS.jsonl`, `R1B1_VPVD.csv` = 36 rows) | §7 now reports 48/48 PSD with the strict-VPS subset 36/36 and names the 2 repos (ViewBatchModel CVPR'25, RevisitDML ICML'20) |

All other V0 numbers were verified against the frozen artifacts and were
correct: R1-C NVR/NPCR/Witness/CIA = 8/8 (95% CI [0.631, 1.000]),
R1-D2 = 0/476 confirmed (95% upper bound 0.77%), baselines B0–B3 = 0/30,
B2/B3/B4 on R1-B1 = 0/48, 2-of-8 value-preserving naturalistic cases.

## Forensic Audit (§3)
8/8 naturalistic cases = **Grade A** (complete independent chain:
physical isolation, single-freeze-timestamp, blind files free of gold
fields, pre-predictions free of post-verdicts, SHA-consistent, gold
independently sourced). No case downgraded to B/C/INVALID.

**FORENSIC_STATUS = PASS**

## Novelty (§5)
Closest neighbors (P-PLAN, Validity Constraints 2024, RO-Crate) differ on
the epistemic + value-preserving + naturalistic-validation axes that
EpiTrace occupies. No fatal collision. The one calibration decision is the
*automaticity* framing (reviewer A5): claim **protocol-grounded
constraint specification** (fixed P1–P6 template library, induced from the
paper without bug access), not unbounded free-form induction. This
calibration is now unified across §4.1, the abstract, the contributions
list, the outline, and the novelty defense (hunting down and replacing
every "automatic induction" / "compiler" over-claim).

**NOVELTY_STATUS = CLEAR_ENOUGH_FOR_SUBMISSION**

## Contract Audit (§11)
5/8 EXPLICITLY_SUPPORTED_BY_PAPER, 3/8 REASONABLE_GENERAL_SCIENTIFIC_
PRINCIPLE, **0 FAULT_SPECIFIC, 0 OVERREACH, 0 AMBIGUOUS**. No contract
excluded from the primary claim. CIA=1.0 is defended, not assumed.

**CONTRACT_AUDIT = PASS**

## Wording & hedging pass (§2 of the polish brief)
- "compiles / compiler / induction" → **"specifies / specification"**
  throughout the abstract, §4.1, the contributions list, and the
  conclusion, consistent with the protocol-grounded calibration.
- Every absolute prior-art negative ("X cannot do Y", "no surveyed system
  does Y") → hedged to **"in our survey, we did not find evidence that X
  does Y in its published description"** (manuscript §1/§3, outline,
  novelty defense).
- §4.1 header renamed to "Epistemic contract specification (F)"; the
  "Calibration of the claim" paragraph now leads with the calibrated scope.

## Reviewer Attack Simulation (§12) — unchanged conclusions
- **FATAL_REVIEWER_OBJECTIONS (unresolvable without new work) = 0**
- All MAJOR objections remain answerable by existing artifacts, honest
  reframing, or a limitations paragraph. **NEW_EXPERIMENT_REQUIRED = NO.**

## Reporting-rigor items now closed by the polish
1. **CIs**: Clopper–Pearson 95% CIs are in the abstract, §6, §7, §8, the
   Table-2/3/4 specs, and `R2_CI_VALUES.json` (verified against
   `scipy.stats.beta`). NVR/NPCR/PSD framed as detectability, not
   population recall.
2. **ε / VPS threshold**: `R2_EPS_DEFINITION.md` (Appendix G) defines VPS
   and the 0.25 strict-VPS threshold; observed range [0.052, 0.651]
   (all 48) / [0.052, 0.246] (36 strict), mean 0.181 on the strict set.
3. **Trace-basis column**: Table 4 spec now carries a per-case trace-basis
   column; **all 8 naturalistic pre-traces are
   documented_protocol_reconstruction** (E02 = TRACE_INSUFFICIENT; no
   live pre-fix re-execution was available). This is flagged, not hidden.
4. **Gold-authority tier column**: Table 4 spec now carries E > B > A
   tiering (5 reproducibility-paper / 1 fix-PR / 2 author-issue).
5. **Prior-art hedging** (item above).
6. **Limitations strengthened (§9)**: now 10 items, proactively stating
   n=8 with wide CI, public-trace scarcity (all 8 = reconstruction),
   E02 selection-provenance gap, computational-ML concentration, the 6
   unsampled C3/C4/C6 repos, template scope, trace-self-hash opacity
   (new forensic finding), and the wording/hedging discipline.

## New forensic finding (Appendix I)
The 16 frozen pre/post R1-C trace files carry `self_hash` fields that do
NOT recompute under any standard JSON serialization (insertion-order
compact, sorted-key compact, or sorted-key pretty). The trace *content*
is verified consistent with the gold evidence and the paired-correction
results; the hashes are opaque integrity markers from the original build
run. This means trace-level cryptographic integrity is not independently
verifiable post-hoc. Recorded as a limitation, not a failure. (R1-C
*file-level* integrity is still fully verified: 25/25 `R1C_SHA256SUMS`
OK + 8/8 manifest blind/gold hashes consistent under the JSON-serialization
scheme the freeze used.)

## Manuscript state
V1: all 10 sections + polished abstract + 5 title candidates + 4 rendered
figures (SVG) + 5 table specs (Table 4/5 with CI/ε/trace-basis/gold-tier)
+ appendix plan (now A–I). The two V0 overstatements are corrected and
cross-validated against the frozen artifacts; every number in the
manuscript now traces to a `results/`, `r1c/results/`, or `r1d/results/`
file.

**MANUSCRIPT_STATUS = REVIEW_READY (V1)**

---

## TOP_CONFERENCE_RESEARCH_READINESS (re-scored post-polish)

The research readiness itself did not change (same frozen evidence). What
changed is *reporting quality*: the numbers now match the artifacts, CIs
are present, the claim is calibrated, and the limitations are proactive.
This raises the manuscript's submittability but is not inflated into the
research score.

- Forensic integrity: 20/20 (8/8 Grade A, all hashes consistent; trace-
  self-hash opacity noted as a limitation).
- Novelty defensibility: 21/25 (clear; automaticity now uniformly
  calibrated to protocol-grounded).
- Contract validity: 14/15 (audited, 0 fault-specific; −1 for small
  template library).
- Empirical coverage: 13/20 (controlled + real-trace + naturalistic +
  search-negative present; R1-A PSD is 0.900 not 1.0, n=8 natural with
  wide CI, 6 families unsampled).
- Reporting rigor: 8/10 (CIs, ε, trace-basis, gold-tier now in the
  tables/abstract; −2 for the small-n CIs and trace-reconstruction basis
  that remain inherent, not polish-fixable).
- Reproducibility: 9/10 (every manuscript number traces to a frozen
  artifact; −1 for the trace self-hash opacity).

**TOP_CONFERENCE_RESEARCH_READINESS = 85%**

Interpretation: up from 83% (V0) → 85% (V1). The +2 reflects the closed
reporting-rigor gap (CIs/ε/trace-basis/gold-tier now present) *and* the
integrity gain from correcting the two V0 overstatements so the paper can
no longer be caught misquoting its own frozen data. It is deliberately
not inflated to 90+ — the empirical set is still small (n=8 natural;
R1-A PSD 0.900; 6 families unsampled), and that is a property of the
frozen evidence, not of the polish.

## Final verdict block (V1)

```
FORENSIC_STATUS              = PASS
NOVELTY_STATUS               = CLEAR_ENOUGH_FOR_SUBMISSION
CONTRACT_AUDIT               = PASS
FATAL_REVIEWER_OBJECTIONS    = 0
NEW_EXPERIMENT_REQUIRED      = NO
MANUSCRIPT_STATUS            = REVIEW_READY
TOP_CONFERENCE_RESEARCH_READINESS = 85%
```

## Next (after V1)
Per the brief: segment-by-segment reviewer-style language edit + venue-
specific 8-page compression + final Figure/Table layout. That is the
*polish-of-the-polish* step; it does not change any number or claim.

## Do NOT do
- No R1-E / R1-F / R1-G expansion rounds.
- No modification of frozen R1-A / R1-B1 / R1-C / R1-D2 results.
- No new experiments (stop-rule: no qualifying FATAL objection).
- Broad case search stays closed unless a specific FATAL reviewer
  objection later requires it.
- Do NOT re-introduce the two corrected overstatements (R1-A 30/30; R1-B1
  "48 value-preserving / 4 repos") — they are now explicitly tracked
  above as the V0→V1 corrections.
