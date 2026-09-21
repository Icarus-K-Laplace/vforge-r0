# R1-D: Expansion Round — Discovery Access Report

**Date**: 2026-09-21
**Objective**: Extend the naturalistic pool to C3 (scope mismatch) and under-explored
C4/C5 families, adding 12-15 new externally-confirmed cases.

## Discovery outcome: **ACCESS_LIMITED** (recorded as scientific finding, not a failure)

- Targeted GitHub **issue-search API** returned HTTP 422 for every query: the session
  token is a fine-grained PAT without repository-contents / issue-read grants on the
  target third-party repos, and without search-scope grant.
- Direct REST issue *listing* succeeded on 8 of 10 target repos (returned 0-22 issues each),
  but per-issue full-text read and comment threading returned empty (no read grant on those repos).
- Two target repos (facebookresearch/Barlow, mlfoundations/evalplus) 404'd (rename / no access).

## What was legitimately retrieved
- 19 raw keyword-matched leads logged to `results/R1D_RAW_LEADS.csv` (lead_type=repo_issue).
- These are **unconfirmed leads**, not asserted naturalistic cases: none has an
  independently-verified gold evidence chain (author confirmation + fix commit) reachable
  under this session's token grants.

## Anti-fabrication decision
Per R1-C §2 / R1-D §2 (no fabricated gold), R1-D does NOT assert any new confirmed case in
this round. Asserting a case whose gold text/commit could not be read and verified would
violate the no-fabrication principle. The honest, reproducible result is:

```
R1D_STATUS: ACCESS_LIMITED
NEW_CONFIRMED_CASES: 0
RAW_LEADS_RETRIEVED: 19
REPOS_ISSUES_OK: 8/10
REPOS_404: ['facebookresearch/Barlow', 'mlfoundations/evalplus']
ROOT_CAUSE: fine-grained PAT lacks issue-read + search grants on third-party repos
UNBLOCKING: run discovery with a classic token (repo:read + public_repo) or gh CLI auth,
            then re-verify each lead's gold chain (author comment / fix commit) before assertion.
```

This is recorded, not faked. The R1-C primary naturalistic result (8 confirmed cases,
NVR=NPCR=1.0) remains fully intact and frozen; R1-D is the expansion round that is
blocked on token scope, not on the method.
