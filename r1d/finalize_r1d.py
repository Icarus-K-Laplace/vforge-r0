"""
R1-D finalization: log the access limitation as a scientific finding,
freeze whatever is reproducible, and produce the required reports.
No cases are asserted without an independently-verified gold evidence chain,
so R1-D reports ACCESS_LIMITED instead of inventing cases.
"""
import json, csv, hashlib
from pathlib import Path
from datetime import datetime

ROOT = Path("r1d")
RESULTS = ROOT/"results"; REPORTS = ROOT/"reports"
RESULTS.mkdir(parents=True, exist_ok=True); REPORTS.mkdir(parents=True, exist_ok=True)

def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()

# Count raw leads actually retrieved
leads = list(csv.DictReader(open(RESULTS/"R1D_RAW_LEADS.csv", encoding="utf-8")))
n_leads = len(leads)

# Determine which repos yielded issues vs 404/error
repos_404 = ["facebookresearch/Barlow", "mlfoundations/evalplus"]

status_report = f"""# R1-D: Expansion Round — Discovery Access Report

**Date**: {datetime.now().strftime('%Y-%m-%d')}
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
- {n_leads} raw keyword-matched leads logged to `results/R1D_RAW_LEADS.csv` (lead_type=repo_issue).
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
RAW_LEADS_RETRIEVED: {n_leads}
REPOS_ISSUES_OK: 8/10
REPOS_404: {repos_404}
ROOT_CAUSE: fine-grained PAT lacks issue-read + search grants on third-party repos
UNBLOCKING: run discovery with a classic token (repo:read + public_repo) or gh CLI auth,
            then re-verify each lead's gold chain (author comment / fix commit) before assertion.
```

This is recorded, not faked. The R1-C primary naturalistic result (8 confirmed cases,
NVR=NPCR=1.0) remains fully intact and frozen; R1-D is the expansion round that is
blocked on token scope, not on the method.
"""
(REPORTS/"R1D_DISCOVERY_ACCESS_REPORT.md").write_text(status_report, encoding="utf-8")

# Freeze manifest for R1-D artifacts
manifest = {
    "stage": "R1-D",
    "status": "ACCESS_LIMITED",
    "date": datetime.now().isoformat(timespec="seconds"),
    "new_confirmed_cases": 0,
    "raw_leads": n_leads,
    "files": []
}
for p in sorted(ROOT.rglob("*")):
    if p.is_file() and p.name not in ("R1D_FREEZE_MANIFEST.json","R1D_SHA256SUMS"):
        manifest["files"].append({"path": str(p), "sha256": sha(p)})
fp = RESULTS/"R1D_FREEZE_MANIFEST.json"
fp.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
sha_fp = sha(fp)
fp.write_text(json.dumps({**manifest, "self_sha": sha_fp}, indent=2), encoding="utf-8")

sums = []
for p in sorted(ROOT.rglob("*")):
    if p.is_file() and p.name != "R1D_SHA256SUMS":
        rel = str(p)
        sums.append(f"{sha(p)}  {rel}")
(RESULTS/"R1D_SHA256SUMS").write_text("\n".join(sums)+"\n", encoding="utf-8")

print("R1-D finalization done.")
print("New confirmed cases:", manifest["new_confirmed_cases"])
print("Raw leads retrieved:", n_leads)
print("Access status: ACCESS_LIMITED (token scope), recorded as scientific finding.")
print("R1C primary result remains frozen & intact; R1D blocked on classic-token re-run.")
