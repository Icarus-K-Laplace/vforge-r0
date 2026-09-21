"""
R1-D Discovery (fallback): GitHub search API is blocked by the fine-grained PAT (422).
Use direct REST issue listing on specific high-impact repos instead — no search API.
Fetch open issues, filter client-side for protocol-deviation keywords.
"""
import urllib.request, urllib.parse, json, ssl, time, csv
from pathlib import Path

OUT = Path("r1d/results"); OUT.mkdir(parents=True, exist_ok=True)
ctx = ssl.create_default_context(); ctx.check_hostname = False; ctx.verify_mode = ssl.CERT_NONE
import os
TOKEN = os.environ.get("GITHUB_TOKEN", "")

# (repo, expected_family, keywords to filter issue titles/body)
TARGETS = [
    ("google-research/albert", "C5", ["stride", "squad", "dropout", "eval", "discrepan", "mismatch"]),
    ("facebookresearch/Barlow", "C5", ["linear", "probe", "subset", "augment", "mismatch", "evaluation"]),
    ("facebookresearch/dinov2", "C5", ["probe", "linear", "subset", "augment"]),
    ("google-research/bert", "C5", ["glue", "evaluation", "discrepan"]),
    ("huggingface/evaluate", "C6", ["aggregation", "subset", "macro", "mean"]),
    ("mlfoundations/evalplus", "C3", ["subset", "reported", "task"]),
    ("openai/gym", "C2", ["seed", "aggregation", "average", "top"]),
    ("google/flax", "C4", ["budget", "asymmetric", "baseline", "tuning"]),
    ("WongKinYiu/yolov7", "C5", ["conf", "nms", "threshold", "coco", "ap"]),
    ("facebookresearch/deit", "C5", ["crop", "ratio", "evaluation", "accuracy"]),
]

def fetch_issues(repo, per_page=30):
    url = f"https://api.github.com/repos/{repo}/issues?state=all&per_page={per_page}&sort=updated&direction=desc"
    req = urllib.request.Request(url, headers={"User-Agent":"VForge-R1D","Accept":"application/vnd.github.v3+json","Authorization":"token "+TOKEN})
    for a in range(3):
        try:
            data = json.loads(urllib.request.urlopen(req, timeout=20, context=ctx).read())
            return [
                {"title": it.get("title"), "state": it.get("state"), "url": it.get("html_url"),
                 "is_issue": "pull_request" not in it, "body": (it.get("body") or "")[:400]}
                for it in data if "pull_request" not in it
            ]
        except Exception as e:
            if "SSL" in str(e): time.sleep(4*(a+1)); continue
            print(f"  fetch error {repo}: {e}"); return []
    return []

def run():
    pool = []
    for repo, fam, kws in TARGETS:
        issues = fetch_issues(repo)
        matched = [i for i in issues if any(k.lower() in ((i.get("title") or "") + " " + (i.get("body") or "")).lower() for k in kws)]
        print(f"{repo} [{fam}]: {len(issues)} issues, {len(matched)} keyword-matched")
        for m in matched:
            pool.append({"repo": repo, "family": fam, "title": m["title"], "state": m["state"], "url": m["url"], "body_snippet": m.get("body_snippet",""), "lead_type": "repo_issue"})
        time.sleep(2)

    fields = ["lead_type","repo","family","title","state","url","body_snippet"]
    with open(OUT/"R1D_RAW_LEADS.csv","w",newline="",encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields); w.writeheader()
        for p in pool: w.writerow({k:p.get(k,"") for k in fields})
    print(f"\n{len(pool)} leads logged to R1D_RAW_LEADS.csv")

if __name__ == "__main__":
    run()
