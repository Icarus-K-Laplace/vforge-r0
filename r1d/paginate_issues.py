"""
R1-D2 §2: Per-repository issue+PR pagination (anonymous REST, no Search API).

Fetches ALL issues and ALL PRs for each target repo (paginated per_page=100),
saves raw public metadata to results/R1D_RAW_ISSUES.jsonl, and re-derives the
keyword-matched lead pool locally. No token is used (anonymous public resources).
"""
import json, ssl, time, urllib.request, urllib.error
from pathlib import Path

ROOT = Path("E:/VForge-R0")
RESULTS = ROOT / "r1d" / "results"
RESULTS.mkdir(parents=True, exist_ok=True)
ctx = ssl.create_default_context(); ctx.check_hostname = False; ctx.verify_mode = ssl.CERT_NONE

# 10 target repos (family = expected deviation class, for triage only)
TARGETS = [
    ("google-research/albert", "C5"),
    ("facebookresearch/dinov2", "C5"),
    ("google-research/bert", "C5"),
    ("huggingface/evaluate", "C6"),
    ("openai/gym", "C2"),
    ("google/flax", "C4"),
    ("WongKinYiu/yolov7", "C5"),
    ("facebookresearch/deit", "C5"),
    ("mlfoundations/evalplus", "C3"),
    ("facebookresearch/Barlow", "C5"),
]

# Keyword set (title OR body) per protocol §2
KEYWORDS = [
    "seed","evaluation","test set","validation","checkpoint","metric","aggregation",
    "average","mean","report","wrong result","incorrect result","reproduce","reproducibility",
    "leak","leakage","split","baseline","config","hyperparameter","paper","table","figure",
    "fix","correction","bug in evaluation","stride","squad","dropout","glue","crop","ratio",
    "augment","probe","subset","macro","conf","nms","threshold","coco","ap","tuning","budget",
    "asymmetric","unfair","early stop","discrepan","mismatch","token","detok","bleu","flip","test-time",
]

def get(url, retries=3):
    req = urllib.request.Request(url, headers={"User-Agent":"VForge-R1D2-pager","Accept":"application/vnd.github.v3+json"})
    for a in range(retries):
        try:
            r = urllib.request.urlopen(req, timeout=25, context=ctx)
            return json.loads(r.read().decode("utf-8","replace")), r.status
        except urllib.error.HTTPError as e:
            if e.code == 422:
                return {"_error":"VALIDATION_OR_ABUSE_LIMIT","_status":422}, 422
            if e.code in (404,):
                return {"_error":"NOT_FOUND","_status":404}, 404
            if e.code == 403 and "rate limit" in (e.read().decode("utf-8","replace") if e.fp else "").lower():
                time.sleep(5); continue
            return {"_error":str(e.code),"_status":e.code}, e.code
        except Exception as e:
            if "SSL" in str(e) or "handshake" in str(e):
                time.sleep(4*(a+1)); continue
            return {"_error":str(e),"_status":0}, 0
    return {"_error":"retries_exhausted","_status":0}, 0

def paginate(kind, repo, cap=2000):
    """Fetch a kind ('issues' or 'pulls') fully, paginated."""
    base = f"https://api.github.com/repos/{repo}/{kind}"
    out = []
    page = 1
    while len(out) < cap:
        url = f"{base}?state=all&per_page=100&page={page}"
        data, status = get(url)
        if status != 200:
            return out, status, data.get("_error","")
        if not isinstance(data, list):
            break
        out.extend(data)
        if len(data) < 100:
            break
        page += 1
        time.sleep(0.6)
    return out, status, ""

def main():
    raw = []
    repo_report = []
    for repo, fam in TARGETS:
        issues, ist, ierr = paginate("issues", repo)
        pulls, pst, perr = paginate("pulls", repo)
        all_items = []
        for it in issues:
            is_pr = "pull_request" in it
            it = {
                "repo": repo,
                "kind": "PR" if is_pr else "ISSUE",
                "number": it.get("number"),
                "title": it.get("title"),
                "state": it.get("state"),
                "html_url": it.get("html_url"),
                "created_at": it.get("created_at"),
                "updated_at": it.get("updated_at"),
                "comments": it.get("comments"),
                "user": (it.get("user") or {}).get("login"),
                "body": it.get("body") or "",
                "linked_pr": None,  # filled in §3
            }
            if "pull_request" in it and "PR" in it.get("kind",""):
                it["kind"] = "PR"
            all_items.append(it)
        for it in pulls:
            it = {
                "repo": repo, "kind": "PR", "number": it.get("number"),
                "title": it.get("title"), "state": it.get("state"),
                "html_url": it.get("html_url"), "created_at": it.get("created_at"),
                "updated_at": it.get("updated_at"), "comments": it.get("comments"),
                "user": (it.get("user") or {}).get("login"), "body": it.get("body") or "",
                "merged": (it.get("merged_at") is not None),
                "linked_pr": it.get("html_url"),
            }
            all_items.append(it)

        # Local keyword match on title+body
        matched = []
        for it in all_items:
            hay = ((it.get("title") or "") + " " + (it.get("body") or "")).lower()
            hits = [k for k in KEYWORDS if k.lower() in hay]
            if hits:
                it["keyword_hits"] = sorted(set(hits))
                it["expected_family"] = fam
                matched.append(it)

        raw.extend(all_items)
        repo_report.append({
            "repo": repo, "expected_family": fam,
            "issues_fetched": len(issues), "pulls_fetched": len(pulls),
            "issues_http": ist, "pulls_http": pst,
            "issues_err": ierr, "pulls_err": perr,
            "keyword_matched": len(matched),
            "matched_numbers": [m["number"] for m in matched],
        })
        time.sleep(0.5)

    # Save raw issues (one JSON object per line)
    with open(RESULTS / "R1D_RAW_ISSUES.jsonl", "w", encoding="utf-8") as f:
        for item in raw:
            f.write(json.dumps(item, ensure_ascii=False) + "\n")
    # Save the keyword-matched pool as leads (R1D_RAW_LEADS.jsonl + csv for the 19-lead coverage)
    all_matched = [i for i in raw if "keyword_hits" in i]
    with open(RESULTS / "R1D_RAW_LEADS.jsonl", "w", encoding="utf-8") as f:
        for m in all_matched:
            f.write(json.dumps(m, ensure_ascii=False) + "\n")
    import csv
    with open(RESULTS / "R1D_RAW_LEADS.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["repo","expected_family","kind","number","title","state","html_url","keyword_hits"])
        w.writeheader()
        for m in all_matched:
            w.writerow({k: m.get(k,"") for k in w.fieldnames})

    print("Per-repo report:")
    for rr in repo_report:
        print(f"  {rr['repo']:28s} [{rr['expected_family']}] issues={rr['issues_fetched']} pulls={rr['pulls_fetched']} matched={rr['keyword_matched']}  http={rr['issues_http']}/{rr['pulls_http']}")
    print(f"\nTotal raw items: {len(raw)}, total keyword-matched leads: {len(all_matched)}")

if __name__ == "__main__":
    main()
