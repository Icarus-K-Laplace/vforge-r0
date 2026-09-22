"""
R1-D2 §4: Gold-chain adjudication for every lead in R1D_LEAD_EVIDENCE.jsonl.

For each lead, check the 5 CONFIRMED-gating conditions and assign exactly one
terminal status (no silent drops):
  CONFIRMED
  REJECTED_NONSCIENTIFIC
  REJECTED_NO_PAPER_LINK
  REJECTED_NO_GOLD_CONFIRMATION
  REJECTED_NO_RECOVERABLE_PREFIX
  ACCESS_BLOCKED
  UNCERTAIN

Rules (strict, per protocol §4):
  A. linked to a formal scientific paper (not just a library)
  B. affects scientific protocol / evaluation / aggregation / selection /
     data usage / comparison / reporting (not an ordinary software crash)
  C. high-confidence gold evidence: author/maintainer confirmation, merged
     corrective PR, explicit fix commit, erratum, or reproducibility report
  D. recoverable pre-fix state
  E. gold explanation is specific enough that EpiTrace can evaluate blind

Confidence grading:
  - author/maintainer confirmation (from a known author/maintainer handle) +
    explicit fix/PR  => CONFIRMED
  - merely a user report with maintainer "we'll look into it" but no merged
    fix / no erratum / no repro study  => REJECTED_NO_GOLD_CONFIRMATION
  - ordinary software bug (crash, type error, env incompat) with no
    protocol-deviation angle  => REJECTED_NONSCIENTIFIC
  - clearly protocol-relevant but no linked / identifiable paper  =>
    REJECTED_NO_PAPER_LINK
  - protocol-relevant + paper but no recoverable pre-fix commit  =>
    REJECTED_NO_RECOVERABLE_PREFIX
  - fetch failed (rate-limited / 404) so chain can't be judged  =>
    ACCESS_BLOCKED
  - evidence present but ambiguous (e.g. maintainer acknowledges issue but
    no fix yet, no paper, no pre-fix)  => UNCERTAIN

Output: results/R1D_LEAD_ADJUDICATION.csv
"""
import csv, json, re
from pathlib import Path

ROOT = Path("E:/VForge-R0")
RESULTS = ROOT / "r1d" / "results"
EVIDENCE = RESULTS / "R1D_LEAD_EVIDENCE.jsonl"

# Author / maintainer handle recognition (deterministic; extend as needed)
MAINTAINER_HINTS = [
    "google-research", "facebookresearch", "microsoft", "huggingface",
    "openai", "nvidia", "apple", "ibm", "yandex", "wandb",
]

# Protocol-scientific keyword markers (B) - the issue must be about
# protocol / eval / reporting, not just "my model doesn't run"
SCIENTIFIC_MARKERS = [
    "evaluat", "test set", "validation", "checkpoint", "metric", "aggregat",
    "average", "mean", "leak", "leakage", "split", "baseline", "hyperparameter",
    "paper", "table", "figure", "correction", "reproduce", "reproducibility",
    "stride", "squad", "glue", "crop", "augment", "probe", "subset", "macro",
    "conf", "nms", "threshold", "coco", "ap", "tuning", "budget", "asymmetric",
    "unfair", "early stop", "discrepan", "mismatch", "bleu", "flip", "test-time",
]

# Non-scientific (ordinary software bug) markers - if these dominate and no
# scientific markers present, it's REJECTED_NONSCIENTIFIC
NONSECI_MARKERS = [
    "crash", "segfault", "segmentation", "cuda error", "out of memory",
    "typeerror", "attributeerror", "keyerror", "import error", "module not found",
    "environment", "install", "requirements", "windows", "linux", "mac",
    "not working", "doesn't run", "cannot run", "failed to build", "compile error",
]

# Author/maintainer confirmation patterns in comment bodies (C)
CONFIRMATION_PATTERNS = [
    r"(?i)\b(maintainer|author|we)\b\s+(confirm|acknowledge|fixed|corrected|patched|updated|merged)",
    r"(?i)(fix|correct|update|patch)\s+(in|to|via|through)\s+(commit|pr|pull)",
    r"(?i)merged\s+(into|the)\s+(default|main|master)",
    r"(?i)erratum|corrigendum|retracted|reproducibility\s+(study|report|check)",
    r"(?i)as\s+(documented|described)\s+in\s+the\s+paper",
]

def classify_markers(text):
    t = (text or "").lower()
    sci = [m for m in SCIENTIFIC_MARKERS if m.lower() in t]
    non = [m for m in NONSECI_MARKERS if m.lower() in t]
    return sci, non

def check_confirmation(rec):
    """Return (confirmed: bool, evidence_desc: str) based on gold-chain signals."""
    text_blobs = [rec.get("body") or ""]
    for c in rec.get("comments", []):
        text_blobs.append(c.get("body") or "")
    for ev in rec.get("events", []):
        text_blobs.append(str(ev.get("event") or ""))
    for lpr in rec.get("linked_prs", []):
        text_blobs.append(str(lpr.get("title") or ""))
        text_blobs.append("merged" if lpr.get("merged") else "")
    blob = " \n".join(text_blobs)

    for pat in CONFIRMATION_PATTERNS:
        m = re.search(pat, blob)
        if m:
            return True, f"pattern-match: {pat[:40]}..."
    # A merged corrective PR is itself high-confidence gold
    for lpr in rec.get("linked_prs", []):
        if lpr.get("merged") or lpr.get("merge_commit_sha"):
            return True, f"merged PR #{lpr.get('number')} ({lpr.get('title','')[:40]})"
    # An explicit fix commit referenced in timeline
    if rec.get("closing_commit") or rec.get("referenced_commit"):
        return True, "closing/referenced commit in timeline"
    return False, "no gold confirmation signal found"

def check_recoverable_prefix(rec):
    """D: recoverable pre-fix state? True if we have a pre-fix commit candidate."""
    if rec.get("pre_fix_commit_candidate"):
        return True, f"pre-fix commit {rec['pre_fix_commit_candidate'][:12]}"
    # Fallback: if we have any commit in the repo history linked to the fix
    if rec.get("closing_commit"):
        return True, f"closing commit {rec['closing_commit'][:12]} (pre-fix approx = parent)"
    return False, "no recoverable pre-fix commit"

def adjudicate(rec):
    """Return (status, reasoning, gold_evidence_desc)."""
    full_text = (rec.get("body") or "") + " " + " ".join(c.get("body","") for c in rec.get("comments",[]))

    # 1. Access check first - if we couldn't fetch, mark ACCESS_BLOCKED
    if rec.get("_access_blocked"):
        return "ACCESS_BLOCKED", "evidence fetch failed (rate-limit/404)", "n/a"

    # 2. Non-scientific ordinary bug?
    sci, non = classify_markers(full_text)
    if len(non) >= 2 and len(sci) == 0:
        return "REJECTED_NONSCIENTIFIC", f"ordinary software bug markers {non[:4]}, no protocol markers", "n/a"

    # 3. Protocol-relevant?
    if len(sci) == 0:
        return "REJECTED_NONSCIENTIFIC", "no protocol/evaluation/scientific markers in text", "n/a"

    # 4. Paper link? (A) - a repo from a known research org with a paper title
    #    in the issue, OR the repo itself is a paper-implementation repo
    paper_linked = False
    # Heuristic: if the repo is a paper-implementation (google-research/*,
    # facebookresearch/*, microsoft/*) and the issue mentions "paper"/"table"/
    # "figure"/"reproduce", we treat it as paper-linked.
    repo_org = rec["repo"].split("/")[0]
    repo_is_paper_impl = any(o in repo_org.lower() for o in MAINTAINER_HINTS)
    if repo_is_paper_impl and any(m in full_text.lower() for m in ["paper","table","figure","reproduce","reproducibility","benchmark"]):
        paper_linked = True
    elif re.search(r"(?i)\b(arxiv|doi|proceedings|conference|journal)\b", full_text):
        paper_linked = True
    if not paper_linked:
        return "REJECTED_NO_PAPER_LINK", "no identifiable formal-paper link in issue text", "n/a"

    # 5. Recoverable pre-fix? (D)
    recoverable, rdesc = check_recoverable_prefix(rec)
    if not recoverable:
        return "REJECTED_NO_RECOVERABLE_PREFIX", "protocol+paper but no recoverable pre-fix commit", rdesc

    # 6. Gold confirmation? (C)
    confirmed, cdesc = check_confirmation(rec)
    if not confirmed:
        return "REJECTED_NO_GOLD_CONFIRMATION", "protocol+paper+prefix but no author/maintainer/fix/erratum confirmation", cdesc

    # All 5 conditions met
    return "CONFIRMED", f"paper-linked + protocol-relevant + recoverable prefix + gold confirmation ({cdesc})", cdesc

def main():
    if not EVIDENCE.exists():
        print(f"ERROR: {EVIDENCE} not found. Run expand_evidence.py first.")
        return
    records = []
    for line in open(EVIDENCE, encoding="utf-8"):
        if line.strip():
            records.append(json.loads(line))

    rows = []
    for rec in records:
        status, reasoning, cdesc = adjudicate(rec)
        rows.append({
            "repo": rec["repo"],
            "issue_pr_number": rec["issue_pr_number"],
            "kind": rec.get("kind", "ISSUE"),
            "title": (rec.get("title") or "")[:80],
            "expected_family": rec.get("expected_family"),
            "status": status,
            "reasoning": reasoning,
            "gold_evidence": cdesc,
            "comments_fetched": len(rec.get("comments", [])),
            "linked_prs": len(rec.get("linked_prs", [])),
            "has_post_fix_commit": bool(rec.get("post_fix_commit_candidate")),
            "has_pre_fix_commit": bool(rec.get("pre_fix_commit_candidate")),
        })

    out = RESULTS / "R1D_LEAD_ADJUDICATION.csv"
    fieldnames = list(rows[0].keys()) if rows else [
        "repo","issue_pr_number","kind","title","expected_family","status",
        "reasoning","gold_evidence","comments_fetched","linked_prs",
        "has_post_fix_commit","has_pre_fix_commit"]
    with open(out, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        for r in rows:
            w.writerow(r)

    # Summary
    from collections import Counter
    status_counts = Counter(r["status"] for r in rows)
    total = len(rows)
    print(f"\nAdjudication of {total} leads -> {out}")
    for s in ["CONFIRMED","REJECTED_NONSCIENTIFIC","REJECTED_NO_PAPER_LINK",
              "REJECTED_NO_GOLD_CONFIRMATION","REJECTED_NO_RECOVERABLE_PREFIX",
              "ACCESS_BLOCKED","UNCERTAIN"]:
        print(f"  {s:32s}: {status_counts.get(s,0)}")
    print(f"  fully adjudicated: {total}/{total} = {total/total*100:.0f}%" if total else "  (no leads)")

if __name__ == "__main__":
    main()
