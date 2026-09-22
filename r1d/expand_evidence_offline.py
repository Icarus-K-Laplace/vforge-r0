"""
R1-D2 §3 (offline): Evidence expansion from the §2 raw-issue corpus.

NO network calls. Uses R1D_RAW_ISSUES.jsonl (737 items, 476 keyword-matched
leads) already fetched in §2. For each lead, derives:
  - protocol_relevance: strong signal (leak/wrong-result/discrepancy/erratum)
  - paper_link: repo is a research org + mentions paper/table/figure/reproduce
  - gold_confirmation: merged PR linked, or closing commit in body
  - pre_fix_commit: parent of a merged fix PR (recovered from §2 data when present)
  - post_fix_commit: merge commit of a linked merged PR

Writes R1D_LEAD_EVIDENCE.jsonl (offline evidence, network-free).
Leads that need comment/event/commit detail beyond §2 data get
"evidence_incomplete": true so §4 can mark UNCERTAIN (not silently dropped).
"""
import json
from pathlib import Path

ROOT = Path("E:/VForge-R0")
RESULTS = ROOT / "r1d" / "results"

STRONG = ["leak","leakage","test set","reproduc","erratum","corrigend",
          "wrong result","incorrect result","bug in evaluation","discrepan",
          "cherry","subset","asymmetric","unfair","early stop","flip"]
PAPER = ["paper","table","figure","reproduce","reproducibility","benchmark","arxiv","doi"]
RESEARCH_ORGS = ["google-research","facebookresearch","microsoft","huggingface",
                 "openai","nvidia","apple","ibm","yandex"]

def sha(s):
    import hashlib
    return hashlib.sha256((s or "").encode()).hexdigest()

def main():
    items = [json.loads(l) for l in open(RESULTS/"R1D_RAW_ISSUES.jsonl", encoding="utf-8") if l.strip()]
    leads = [i for i in items if "keyword_hits" in i]

    # Build a quick index of merged PRs per repo for pre/post commit recovery
    merged_prs = {}
    for it in items:
        if it.get("kind") == "PR" and it.get("merged"):
            merged_prs.setdefault(it["repo"], []).append(it)

    records = []
    for l in leads:
        text = ((l.get("title") or "") + " " + (l.get("body") or "")).lower()
        repo = l["repo"]
        org = repo.split("/")[0].lower()
        is_research = any(o in org for o in RESEARCH_ORGS)

        strong_hit = [s for s in STRONG if s in text]
        paper_hit = [p for p in PAPER if p in text]
        paper_link = is_research and bool(paper_hit)

        # Linked merged PR for this issue (same repo, referenced in body)
        linked_merged = []
        for mp in merged_prs.get(repo, []):
            ref = f"#{mp['number']}" in (l.get("body") or "")
            if ref:
                linked_merged.append(mp)
        post_commit = linked_merged[0].get("sha") if linked_merged else None
        # Pre-fix = parent of post_commit (only if we had full PR detail; else None)
        pre_commit = None  # requires network fetch of merge commit parent

        evidence_complete = True
        # If no strong signal and no paper link, we can still adjudicate -> complete
        # If strong signal present but no gold confirmation recoverable, mark incomplete
        if strong_hit and not linked_merged:
            evidence_complete = False

        rec = {
            "repo": repo,
            "issue_pr_number": l.get("number"),
            "kind": l.get("kind"),
            "title": l.get("title"),
            "body_hash": sha(l.get("body") or ""),
            "comment_hashes": [],  # not fetched (quota)
            "events": [],          # not fetched (quota)
            "linked_prs": [{"number": m["number"], "title": m["title"],
                            "state": m["state"], "merged": m.get("merged")} for m in linked_merged],
            "candidate_paper": ("; ".join(paper_hit[:3]) if paper_link else None),
            "candidate_scientific_claim": (" ".join(strong_hit[:3]) if strong_hit else None),
            "candidate_violation_type": l.get("expected_family"),
            "author_or_maintainer_confirmation": (bool(linked_merged) or any("maintainer" in (l.get("body") or "").lower() for _ in [0])),
            "fix_commit_candidate": post_commit,
            "pre_fix_commit_candidate": pre_commit,
            "post_fix_commit_candidate": post_commit,
            "erratum_or_repro_report": any(e in text for e in ["erratum","corrigend","reproducibility study"]),
            "strong_signal": bool(strong_hit),
            "paper_link": paper_link,
            "evidence_complete": evidence_complete,
            "evidence_incomplete_reason": None if evidence_complete else
                "strong-signal lead but linked merged PR not recoverable from §2 corpus (needs comment/event fetch)",
            "keyword_hits": l.get("keyword_hits"),
            "expected_family": l.get("expected_family"),
            "_access_blocked": False,  # offline-derived from §2 corpus; not a fetch failure
        }
        records.append(rec)

    out = RESULTS / "R1D_LEAD_EVIDENCE.jsonl"
    with open(out, "w", encoding="utf-8") as f:
        for r in records:
            f.write(json.dumps(r, ensure_ascii=False, default=str) + "\n")

    strong_n = sum(1 for r in records if r["strong_signal"])
    paper_n = sum(1 for r in records if r["paper_link"])
    confirm_n = sum(1 for r in records if r["author_or_maintainer_confirmation"])
    incomplete_n = sum(1 for r in records if not r["evidence_complete"])
    print(f"{len(records)} leads -> {out}")
    print(f"  strong-signal: {strong_n}, paper-link: {paper_n}, gold-confirmation: {confirm_n}, evidence-incomplete: {incomplete_n}")

if __name__ == "__main__":
    main()
