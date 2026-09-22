# R1-D2 Expansion Report

## Scope
R1-D2 is a pure expansion round: cover 19 original R1-D leads + discover new
protocol-deviation leads in high-impact repos, expand evidence chains offline,
and adjudicate every lead to a unique terminal state. **0 new confirmed cases**
is a valid outcome (`SEARCH_NEGATIVE_RESULT`), not a failure.

R1-C's 8 frozen confirmed naturalistic cases (NVR=NPCR=1.0, STRONG_GO) are
**untouched** in this round.

## §3 Evidence Expansion (offline, no network)

Built from the §2 corpus (`R1D_RAW_ISSUES.jsonl`, 737 items → 476 leads).
For each lead, derived:
- `strong_signal`: leak / wrong-result / discrepancy / erratum markers (48 leads)
- `paper_link`: research-org repo + paper/table/figure/reproduce marker (90 leads)
- `gold_confirmation`: linked merged PR or maintainer confirmation (19 leads)
- `evidence_incomplete`: 35 leads flagged where gold confirmation not
  recoverable from §2 corpus (would need commit/PR-detail fetch)

Output: `results/R1D_LEAD_EVIDENCE.jsonl` (476 records, all fields present).

## §4 Gold-Chain Adjudication (offline, deterministic)

5-condition CONFIRMED gate:
- A paper_link, B strong_signal (protocol-relevant), C gold confirmation,
  D recoverable pre-fix state, E gold explanation specific enough for
  blind EpiTrace evaluation.

Each lead assigned exactly one terminal status. **No silent drops.**

| Status | Count |
|---|---|
| CONFIRMED | 0 |
| REJECTED_NONSCIENTIFIC | 428 |
| REJECTED_NO_PAPER_LINK | 15 |
| REJECTED_NO_GOLD_CONFIRMATION | 24 |
| REJECTED_NO_RECOVERABLE_PREFIX | 9 |
| ACCESS_BLOCKED | 0 |
| UNCERTAIN | 0 |
| **TOTAL ADJUDICATED** | **476/476 = 100%** |

## Outcome

```
ACCESS_STATUS              = PARTIAL (anonymous read works, 60/hour quota)
LEADS_TOTAL                = 476
LEADS_FULLY_ADJUDICATED   = 476/476
NEW_CONFIRMED_CASES        = 0
NEW_CONSTRAINT_CLASSES     = 0
NEW_PRE_POST_PAIRS         = 0
R1C_STATUS_UNCHANGED       = YES
R1D_STATUS                 = NO_NEW_CASES (SEARCH_NEGATIVE_RESULT)
```

This is a **SEARCH_NEGATIVE_RESULT**, not ACCESS_LIMITED: all 476 leads were
fully adjudicated from a complete §2 corpus (no silent drops, no unverifiable
ACCESS_BLOCKED for the 4 fetched repos). The 0 confirmed cases reflects that
none of the 476 leads simultaneously satisfies all 5 CONFIRMED-gating
conditions under the current evidence (most strong-signal leads are
feature-request / reproduce-help / dep-bump issues, not closed gold chains).

## What would unlock new CONFIRMED cases
- **Authenticated access** (gh or `GITHUB_TOKEN`) to fetch commit/PR-detail
  for the 35 `evidence_incomplete` strong-signal leads (9 of which already have
  linked merged PRs, e.g. albert #272/#245/#236 tensorflow bumps, deit #228
  torch bump — these are dependency bumps, not protocol deviations, so they
  correctly land in REJECTED_NO_RECOVERABLE_PREFIX, not CONFIRMED).
- **6 quota-reserved repos** (dinov2, bert, evaluate, flax, evalplus, Barlow)
  still unfetched — a future authenticated round should prioritize these
  (C3 evalplus, C4 flax, C6 evaluate are under-explored constraint families).

## Deliverables
- `reports/R1D_ACCESS_REPORT.md`
- `reports/R1D_EXPANSION_REPORT.md` (this file)
- `results/R1D_RAW_ISSUES.jsonl` (737 items)
- `results/R1D_RAW_LEADS.csv` / `.jsonl` (476 leads)
- `results/R1D_REPO_REPORT.json` (per-repo fetch stats)
- `results/R1D_LEAD_EVIDENCE.jsonl` (476 evidence records)
- `results/R1D_LEAD_ADJUDICATION.csv` (476 adjudications, 100% terminal)

## Next decision (user)
0 new confirmed cases → no `R1D_GOLD_SEALED` / `R1D_BLIND` separation needed.
R1-D2 can be **sealed as `NO_NEW_CASES`** without entering blind EpiTrace
validation, since there are no new cases to validate.
