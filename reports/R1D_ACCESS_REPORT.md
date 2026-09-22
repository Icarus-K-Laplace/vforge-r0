# R1-D2 Access Report

## §0 Secret Audit
- **SECRET_FOUND = NO** (`reports/R1D_SECRET_AUDIT.md`, re-run after hex-encoding fix)
- Source file `r1d/discover_leads.py`: clean (reads token from env, no literal)
- Working tree / tracked / git history / reflog-reachable: 0 hits
- Audit script itself uses hex-encoded prefix at runtime (no self-reference false positive)
- **Compromised token from previous round is NOT used anywhere in R1-D2 pipeline**

## §1 Access Diagnostic (anonymous, no token)

Probed `google-research/albert` (known-public) across 7 endpoint types:

| Endpoint | HTTP | Notes |
|---|---|---|
| repository metadata | 200 | OK |
| list issues | 200 | OK (paginates) |
| get one issue | 200 | OK |
| list issue comments | 200 | OK |
| list issue events (timeline) | 200 | OK |
| commit lookup | 200 | OK |
| pull request lookup | 200 | OK |

- **ACCESS_STATUS = PARTIAL** — anonymous read works, but 60 req/hour core quota
- **422 classification**: treated as `VALIDATION_OR_ABUSE_LIMIT` throughout, never auto-mapped to permission denial
- Auth modes: `gh` not logged in, `GITHUB_TOKEN` not set → **anonymous only**

## §2 Per-repo pagination (quota-aware)

8 API calls total (4 repos × 2 kinds × 1 page of 100):

| Repo | Family | Issues | PRs | Keyword-matched |
|---|---|---|---|---|
| google-research/albert | C5 | 100 | 93 | 121 |
| WongKinYiu/yolov7 | C5 | 100 | 100 | 88 |
| facebookresearch/deit | C5 | 100 | 44 | 94 |
| openai/gym | C2 | 100 | 100 | 173 |

**Total: 737 raw items, 476 keyword-matched leads**

6 additional repos (dinov2, bert, evaluate, flax, evalplus, Barlow) marked
`ACCESS_BLOCKED (quota reserved)` — no quota spent. Their leads are not in this
round's corpus; they remain deferred to a future authenticated run.

## §5 Access Fallback (protocol §5)
- Search API not used (422 on previous round; not attempted this round)
- Per-repo issue pagination + local keyword filtering: **completed**
- Public issue endpoint accessible: **yes** (anonymous)
- No `ACCESS_BLOCKED` for the 4 fetched repos; only for the 6 quota-reserved repos

## Quota state at end of run
`core: 60/60 remaining=0 reset_in=44min` — all subsequent work (§3/§4) was done
offline from the §2 corpus, spending 0 additional API calls.
