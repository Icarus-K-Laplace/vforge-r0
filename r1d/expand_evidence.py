"""
R1-D2 §3: Evidence-chain expansion for each keyword-matched lead.

For every lead (from R1D_RAW_LEADS.jsonl), fetch and archive:
  - issue body
  - all comments
  - issue events (timeline)
  - linked PRs (if any)
  - candidate fix commits (from event timeline: closed_by / merged refs)

Output: results/R1D_LEAD_EVIDENCE.jsonl
One record per lead with all gold-chain fields populated (or null if not recoverable).

Anonymous REST only. No Search API. 422 stays VALIDATION_OR_ABUSE_LIMIT.
"""
import json, ssl, time, urllib.request, urllib.error
from pathlib import Path

ROOT = Path("E:/VForge-R0")
RESULTS = ROOT / "r1d" / "results"
ctx = ssl.create_default_context(); ctx.check_hostname = False; ctx.verify_mode = ssl.CERT_NONE

def get(url, retries=3):
    req = urllib.request.Request(url, headers={"User-Agent":"VForge-R1D2-evidence","Accept":"application/vnd.github.v3+json"})
    for a in range(retries):
        try:
            r = urllib.request.urlopen(req, timeout=25, context=ctx)
            return json.loads(r.read().decode("utf-8","replace")), r.status
        except urllib.error.HTTPError as e:
            body = e.read().decode("utf-8","replace") if e.fp else ""
            if e.code == 403 and "rate limit" in body.lower():
                # Wait for rate-limit reset if possible
                reset_hdr = e.headers.get("x-ratelimit-reset")
                if reset_hdr:
                    import datetime
                    reset_ts = int(reset_hdr)
                    now = time.time()
                    wait = max(0, reset_ts - now + 5)
                    print(f"  rate-limited; sleeping {wait:.0f}s until reset...")
                    time.sleep(min(wait, 600))
                    continue
                time.sleep(10); continue
            if e.code == 422:
                return {"_error":"VALIDATION_OR_ABUSE_LIMIT","_status":422,"_body":body[:300]}, 422
            if e.code == 404:
                return None, 404
            return {"_error":str(e.code),"_status":e.code,"_body":body[:200]}, e.code
        except Exception as e:
            if "SSL" in str(e) or "handshake" in str(e):
                time.sleep(4*(a+1)); continue
            return None, 0
    return None, 0

def sha_text(s):
    import hashlib
    return hashlib.sha256((s or "").encode()).hexdigest()

def expand_lead(lead):
    """Fetch full evidence chain for one lead (issue or PR)."""
    repo = lead["repo"]
    num = lead["number"]
    kind = lead.get("kind", "ISSUE")
    rec = {
        "repo": repo,
        "issue_pr_number": num,
        "kind": kind,
        "title": lead.get("title"),
        "body": lead.get("body") or "",
        "body_hash": sha_text(lead.get("body") or ""),
        "expected_family": lead.get("expected_family"),
        "keyword_hits": lead.get("keyword_hits"),
        "comments": [],
        "comment_hashes": [],
        "events": [],
        "linked_prs": [],
        "candidate_paper": None,
        "candidate_scientific_claim": None,
        "candidate_violation_type": lead.get("expected_family"),
        "author_or_maintainer_confirmation": None,  # bool | None
        "fix_commit_candidate": None,
        "pre_fix_commit_candidate": None,
        "post_fix_commit_candidate": None,
        "erratum_or_repro_report": None,
        "timestamp": lead.get("created_at"),
    }

    base = f"https://api.github.com/repos/{repo}"

    # If kind is ISSUE, also check if there's a linked PR
    if kind == "ISSUE":
        # Get issue detail (may have more than list gave us)
        issue_data, st = get(f"{base}/issues/{num}")
        if st == 200 and issue_data:
            rec["body"] = issue_data.get("body") or rec["body"]
            rec["state"] = issue_data.get("state")
        # Comments
        comments, cst = get(f"{base}/issues/{num}/comments?per_page=100")
        if cst == 200 and isinstance(comments, list):
            for c in comments:
                cmin = {"user": (c.get("user") or {}).get("login"),
                        "created_at": c.get("created_at"),
                        "body": c.get("body") or ""}
                rec["comments"].append(cmin)
                rec["comment_hashes"].append(sha_text(cmin["body"]))
        # Events (timeline)
        events, est = get(f"{base}/issues/{num}/timeline?per_page=100")
        if est == 200 and isinstance(events, list):
            for ev in events:
                evt = {"event": ev.get("event"),
                       "created_at": ev.get("created_at"),
                       "commit_id": ev.get("commit_id"),
                       "source_type": (ev.get("source") or {}).get("type") if ev.get("source") else None,
                       "source_number": (ev.get("source") or {}).get("number") if ev.get("source") else None}
                rec["events"].append(evt)
                # Detect closing / referencing commit
                if ev.get("event") == "closed" and ev.get("commit_id"):
                    rec.setdefault("closing_commit", ev.get("commit_id"))
                if ev.get("event") == "referenced" and ev.get("commit_id"):
                    rec.setdefault("referenced_commit", ev.get("commit_id"))
                if ev.get("event") == "cross-referenced" and ev.get("source"):
                    src = ev.get("source")
                    if src.get("type") == "pull_request":
                        rec["linked_prs"].append({
                            "number": src.get("number"),
                            "title": (src.get("title")),
                            "state": src.get("state"),
                            "merged_at": (src.get("merged_at") if isinstance(src.get("merged_at"), str) else None),
                        })
        # If linked PR found, fetch its merge commit
        for lpr in rec["linked_prs"]:
            if lpr.get("number"):
                pr_data, pst = get(f"{base}/pulls/{lpr['number']}")
                if pst == 200 and pr_data:
                    lpr["merge_commit_sha"] = pr_data.get("merge_commit_sha")
                    lpr["merged"] = pr_data.get("merged")
                    lpr["state"] = pr_data.get("state")
                    if pr_data.get("merge_commit_sha"):
                        # This is the post-fix commit candidate
                        rec["post_fix_commit_candidate"] = pr_data.get("merge_commit_sha")
                        # Pre-fix: the parent of merge commit (approximate)
                        parent_data, pps = get(f"{base}/commits/{pr_data.get('merge_commit_sha')}")
                        if pps == 200 and parent_data:
                            parents = parent_data.get("parents", [])
                            if parents:
                                rec["pre_fix_commit_candidate"] = parents[0].get("sha")

    # If kind is PR, fetch merge info directly
    if kind == "PR":
        pr_data, pst = get(f"{base}/pulls/{num}")
        if pst == 200 and pr_data:
            rec["merge_commit_sha"] = pr_data.get("merge_commit_sha")
            rec["merged"] = pr_data.get("merged")
            if pr_data.get("merge_commit_sha"):
                rec["post_fix_commit_candidate"] = pr_data.get("merge_commit_sha")
                parent_data, pps = get(f"{base}/commits/{pr_data.get('merge_commit_sha')}")
                if pps == 200 and parent_data:
                    parents = parent_data.get("parents", [])
                    if parents:
                        rec["pre_fix_commit_candidate"] = parents[0].get("sha")
        # PR comments (issue comments API works for PRs too)
        comments, cst = get(f"{base}/issues/{num}/comments?per_page=100")
        if cst == 200 and isinstance(comments, list):
            for c in comments:
                cmin = {"user": (c.get("user") or {}).get("login"),
                        "created_at": c.get("created_at"),
                        "body": c.get("body") or ""}
                rec["comments"].append(cmin)
                rec["comment_hashes"].append(sha_text(cmin["body"]))

    return rec

def main():
    # Load leads
    leads = []
    leads_p = RESULTS / "R1D_RAW_LEADS.jsonl"
    if leads_p.exists():
        for line in open(leads_p, encoding="utf-8"):
            if line.strip():
                leads.append(json.loads(line))
    else:
        print("ERROR: R1D_RAW_LEADS.jsonl not found. Run paginate_issues.py first.")
        return

    # Deduplicate: same repo+number+kind
    seen = set()
    unique_leads = []
    for l in leads:
        key = (l["repo"], l["number"], l.get("kind","ISSUE"))
        if key not in seen:
            seen.add(key)
            unique_leads.append(l)

    print(f"Expanding evidence for {len(unique_leads)} unique leads...")
    records = []
    for i, lead in enumerate(unique_leads):
        print(f"  [{i+1}/{len(unique_leads)}] {lead['repo']}#{lead['number']} ({lead.get('kind','ISSUE')})")
        rec = expand_lead(lead)
        rec["lead_index"] = i
        records.append(rec)
        time.sleep(0.4)

    out = RESULTS / "R1D_LEAD_EVIDENCE.jsonl"
    with open(out, "w", encoding="utf-8") as f:
        for r in records:
            f.write(json.dumps(r, ensure_ascii=False, default=str) + "\n")
    print(f"\n{len(records)} lead evidence records -> {out}")

    # Summary
    n_with_comments = sum(1 for r in records if r["comments"])
    n_with_linked_pr = sum(1 for r in records if r["linked_prs"])
    n_with_post_commit = sum(1 for r in records if r.get("post_fix_commit_candidate"))
    n_with_pre_commit = sum(1 for r in records if r.get("pre_fix_commit_candidate"))
    print(f"  with comments: {n_with_comments}")
    print(f"  with linked PR: {n_with_linked_pr}")
    print(f"  with post-fix commit: {n_with_post_commit}")
    print(f"  with pre-fix commit: {n_with_pre_commit}")

if __name__ == "__main__":
    main()
