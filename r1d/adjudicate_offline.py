"""
R1-D2 §4 (offline): Gold-chain adjudication of every lead in R1D_LEAD_EVIDENCE.jsonl.

Deterministic, network-free. Each lead gets EXACTLY ONE terminal status:
  CONFIRMED / REJECTED_NONSCIENTIFIC / REJECTED_NO_PAPER_LINK /
  REJECTED_NO_GOLD_CONFIRMATION / REJECTED_NO_RECOVERABLE_PREFIX /
  ACCESS_BLOCKED / UNCERTAIN

No silent drops. A lead is CONFIRMED only if ALL 5 hold:
  A paper_link, B strong_signal (protocol-relevant, not an ordinary crash),
  C gold confirmation (merged linked PR or erratum/repro report),
  D recoverable pre-fix state (pre_fix_commit_candidate OR a linked merged PR to step back from),
  E gold explanation specific enough for blind EpiTrace evaluation.

Leads that are protocol-relevant but lack a recoverable pre-fix commit or whose
evidence is incomplete are NOT silently dropped -> they land in a concrete
REJECTED_* / UNCERTAIN bucket with the exact missing condition recorded.
"""
import csv, json
from collections import Counter
from pathlib import Path

ROOT = Path("E:/VForge-R0")
RESULTS = ROOT / "r1d" / "results"
EVIDENCE = RESULTS / "R1D_LEAD_EVIDENCE.jsonl"

def adjudicate(rec):
    """Return (status, reasoning, missing_condition)."""
    # Access-blocked placeholder (would be set if §2 fetch for this lead failed)
    if rec.get("_access_blocked"):
        return "ACCESS_BLOCKED", "evidence fetch failed (quota/404)", "fetch"

    A = rec.get("paper_link")
    B = rec.get("strong_signal")
    C = rec.get("author_or_maintainer_confirmation")
    D = rec.get("evidence_complete") and (rec.get("pre_fix_commit_candidate") or rec.get("post_fix_commit_candidate"))
    E = rec.get("candidate_scientific_claim") is not None

    # Priority: fail on the most fundamental missing condition first.
    if not B:
        return ("REJECTED_NONSCIENTIFIC",
                "no strong protocol/evaluation signal (ordinary software issue or feature request)",
                "B")
    if not A:
        return ("REJECTED_NO_PAPER_LINK",
                "protocol-relevant but no formal-paper link in a research-impl repo",
                "A")
    if not C:
        return ("REJECTED_NO_GOLD_CONFIRMATION",
                "protocol + paper, but no merged corrective PR / erratum / author confirmation recoverable",
                "C")
    if not D:
        return ("REJECTED_NO_RECOVERABLE_PREFIX",
                "gold confirmation present but pre-fix state not recoverable from §2 corpus (needs commit fetch)",
                "D")
    if not E:
        return ("UNCERTAIN",
                "conditions A-D hold but gold explanation not specific enough for blind EpiTrace evaluation",
                "E")
    return ("CONFIRMED",
            f"A+D+paper={rec.get('candidate_paper')} claim={rec.get('candidate_scientific_claim')} "
            f"post_commit={rec.get('post_fix_commit_candidate')}",
            None)

def main():
    records = []
    for line in open(EVIDENCE, encoding="utf-8"):
        if line.strip():
            records.append(json.loads(line))

    rows = []
    for rec in records:
        status, reasoning, missing = adjudicate(rec)
        rows.append({
            "repo": rec["repo"],
            "issue_pr_number": rec["issue_pr_number"],
            "kind": rec.get("kind", "ISSUE"),
            "title": (rec.get("title") or "")[:70],
            "expected_family": rec.get("expected_family"),
            "status": status,
            "missing_condition": missing or "",
            "reasoning": reasoning,
            "strong_signal": rec.get("strong_signal"),
            "paper_link": rec.get("paper_link"),
            "gold_confirmation": rec.get("author_or_maintainer_confirmation"),
            "post_fix_commit": rec.get("post_fix_commit_candidate"),
            "pre_fix_commit": rec.get("pre_fix_commit_candidate"),
            "candidate_paper": rec.get("candidate_paper"),
            "candidate_claim": rec.get("candidate_scientific_claim"),
        })

    out = RESULTS / "R1D_LEAD_ADJUDICATION.csv"
    fieldnames = list(rows[0].keys()) if rows else [
        "repo","issue_pr_number","kind","title","expected_family","status",
        "missing_condition","reasoning","strong_signal","paper_link",
        "gold_confirmation","post_fix_commit","pre_fix_commit",
        "candidate_paper","candidate_claim"]
    with open(out, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        for r in rows:
            w.writerow(r)

    dist = Counter(r["status"] for r in rows)
    total = len(rows)
    print(f"\n=== Adjudication of {total} leads -> {out} ===")
    for s in ["CONFIRMED","REJECTED_NONSCIENTIFIC","REJECTED_NO_PAPER_LINK",
              "REJECTED_NO_GOLD_CONFIRMATION","REJECTED_NO_RECOVERABLE_PREFIX",
              "ACCESS_BLOCKED","UNCERTAIN"]:
        print(f"  {s:30s}: {dist.get(s,0)}")
    print(f"  FULLY ADJUDICATED: {total}/{total} = {total/total*100:.0f}%" if total else "  (no leads)")

    # CONFIRMED details
    confirmed = [r for r in rows if r["status"] == "CONFIRMED"]
    print(f"\n=== CONFIRMED leads ({len(confirmed)}) ===")
    for c in confirmed:
        print(f"  {c['repo']}#{c['issue_pr_number']} [{c['expected_family']}] {c['title']}")
        print(f"     paper={c['candidate_paper']} claim={c['candidate_claim']} post={c['post_fix_commit']}")

    # New constraint classes among CONFIRMED
    if confirmed:
        classes = sorted(set(c["expected_family"] for c in confirmed if c["expected_family"]))
        print(f"\nNew/confirmed constraint classes: {classes}")
    else:
        print("\nNo confirmed constraint classes this round -> "
              + ("SEARCH_NEGATIVE_RESULT" if total > 0 else "NO_LEADS"))

if __name__ == "__main__":
    main()
