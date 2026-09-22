# R2V2 Final Readiness

Generated at end of the R2-V2 pre-submission edit phase. All frozen
results unchanged (R1-C 25/25 SHA-OK + 8/8 manifest-consistent under the
canonical JSON-serialization scheme, re-verified after the Phase -1
hash-metadata correction; R1-D2 476/476 adjudicated; R1-A / R1-B1
cross-checked against the V2 manuscript). Work is on branch
`r2-pre-submission-v2`, descendant of `research-lock-v0` (`0636156`).

## Phase -1: hash metadata
`reports/R2V2_HASH_CORRECTION_AUDIT.md` + corrected
`results/R2_R1C_CASE_FORENSICS.csv`. Determination: no manifest value
was ever wrong; the `recomputed_*` columns had been populated by copy,
not recomputation. Canonical scheme = sha256(utf8(json.dumps(indent=2,
ensure_ascii=False))) = sha256(file_bytes), verified for all 16
blind/gold files. Root cause = clerical metadata (16 entries), NOT a
forensic-chain failure; no artifact identity or chronology changed.
Corrected CSV re-run: 8/8 internally consistent; R1C_SHA256SUMS 25/25.

```
HASH_METADATA_STATUS = PASS (after correction)
FORENSIC_STATUS      = PASS
```

## Phase 1: claim lock
`paper/R2V2_CLAIM_LOCK.md` freezes the three levels (primary / method /
empirical) with explicit forbidden characterizations (no unrestricted
rule discovery, no free-form induction, no prevalence generalization).
Every V2 paragraph is compatible.

```
CLAIM_LOCK = PASS
```

## Phases 2–10: manuscript V2
`paper/R2_MANUSCRIPT_V2.md` (ICML-style compact body, ~2.3k words) +
`paper/R2_ABSTRACT_V2.md` (7-part structure; leads with the VPVD
concept, not 8/8). `paper/R2_FIGURE_LAYOUT_V2.md` +
`paper/R2_TABLE_LAYOUT_V2.md` (2 main tables; 4 figures). Line edit
applied: one conceptual claim per paragraph, marketing removed, "specify"
used throughout (not "induce"/"compile"), prior-art hedged, naturalistic
language bounded ("across the eight frozen cases … observed recall in
this selected set"), R1-D2 framed as in-scope negative not absence,
limitation 10 retained + trace-self-hash opacity.

## Phase 7/11: numeric consistency
`reports/R2V2_MANUSCRIPT_CONSISTENCY.md` (audited output of
`r2v2/consistency_audit.py`). All numeric claims traced to frozen
artifacts. The two V0 overstatements remain corrected:

- R1-A: **27/30 PSD = 0.900** (95% CI [0.735, 0.994]); **30/30 is the
  pair-construction (identifiability) property**, not a discrimination
  score. The 3 non-discriminated pairs named (2 ABSTAIN + 1 false-pos
  E03-04).
- R1-B1: **48 claim-level pairs from 2 repositories**; **36 strict
  value-preserving (VPS ≤ 0.25)**; 48/48 PSD (CI [0.926, 1.000]), 36/36
  strict-VPS (CI [0.903, 1.000]); B4 = 0/48. The "across 4" phrasing is
  retained ONLY for the R1-D2 search scope (ALBERT/YOLOv7/DeiT/Gym),
  which is the correct 4-repo *searched* count.

All Clopper–Pearson CIs recomputed with scipy and cross-checked against
`R2_CI_VALUES.json`.

```
NUMERIC_CONSISTENCY = PASS
```

## Phase 12: mock review
`reports/R2V2_MOCK_REVIEWS.md` — three fresh reviewers (ML methodology,
formal/provenance, reproducibility-rigor). All six requested clarifying
edits applied to the V2 manuscript as clarification-only (bug-blind
mapping sentence, ε-freeness sentence, "no ABSTAIN in R1-B1" sentence,
recon-qualified 8/8, NVR-vs-value-preserving distinction, 5 gold-chain
conditions named). Re-ran the consistency audit after the edits: still
PASS.

```
MOCK_REVIEW_FATALS = 0
```

## Final verdict block

```
HASH_METADATA_STATUS            = PASS
FORENSIC_STATUS                 = PASS
CLAIM_LOCK                      = PASS
NUMERIC_CONSISTENCY            = PASS
MOCK_REVIEW_FATALS             = 0
BODY_LENGTH                    = ~8 pages ICML two-column (≈2,300 words
                                  body; figures 1/2/4 + Tables 1-3;
                                  appendix A-I carries chains)
MANUSCRIPT_STATUS              = SUBMISSION_CANDIDATE
TOP_CONFERENCE_RESEARCH_READINESS = 85% (unchanged from V1 — prose
                                  improvement does not move the research
                                  score; the two V0 numeric corrections
                                  were the only integrity gain, already
                                  counted in V1's 85%)
TOP_CONFERENCE_MANUSCRIPT_READINESS = 90%
NEW_EXPERIMENT_REQUIRED        = NO
```

### Why MANUSCRIPT_READINESS = 90%, not 100%
The remaining 10% is *inherent to the frozen evidence*, not a prose gap:
n = 8 naturalistic cases with wide CI; all 8 naturalistic pre-traces are
reconstructions (no live pre-fix re-execution was recoverable for any);
6 families unsampled in R1-D2; R1-A PSD = 0.900 with 2 ABSTAIN; trace
self-hash opacity (Appendix I). None is closable without new experiments,
which the stop-rule forbids. The manuscript now *states* all of these;
the 90% reflects that the paper is internally consistent, claim-calibrated,
and number-accurate, but its empirical floor is genuinely thin.

### SUBMISSION_CANDIDATE meaning
Ready for the *next* (post-polish) step only — venue-specific 8-page
compression with the real two-column typesetter, reference population,
and final figure rendering. It is **not** a claim that a specific venue
will accept it; it is a claim that no internal inconsistency, over-
statement, or un-traced number remains, and no mock-reviewer fatal
objection stands that cannot be met by clarification/narrowing.

## Do NOT do
- No R1-E / R1-F / R1-G expansion rounds.
- No modification of frozen R1-A / R1-B1 / R1-C / R1-D2 results.
- No new experiments (stop-rule: no qualifying FATAL objection).
- No threshold / ε tuning (ε is frozen at case selection; V2 says so).
- Do not re-introduce the corrected V0 overstatements (R1-A 30/30 as
  PSD; R1-B1 "48 value-preserving / 4 repos").
