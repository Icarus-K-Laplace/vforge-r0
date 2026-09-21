"""Fetch the two Stage1b priority papers from arXiv."""
import urllib.request, urllib.parse, ssl, re
ctx = ssl.create_default_context(); ctx.check_hostname=False; ctx.verify_mode=ssl.CERT_NONE

def arxiv(query, n=6):
    url = "http://export.arxiv.org/api/query?" + urllib.parse.urlencode({
        "search_query": query, "max_results": n})
    req = urllib.request.Request(url, headers={"User-Agent": "VForgeResearch/1.0"})
    xml = urllib.request.urlopen(req, timeout=60).read().decode("utf-8", "ignore")
    out = []
    for aid, title, summ, pub in re.findall(
        r"<id>(.*?)</id>\s*<title>(.*?)</title>\s*<summary>(.*?)</summary>\s*<published>(.*?)</published>",
        xml, re.S):
        t = re.sub(r"\s+", " ", title).strip()
        s = re.sub(r"\s+", " ", summ).strip()[:160]
        out.append((aid.strip(), t, s, pub.strip()))
    return out

for label, q in [
    ("ClinicalBench KDD2026", 'all:"ClinicalBench" AND cat:cs.CL'),
    ("ClinicalBench (loose)", 'all:"ClinicalBench"'),
    ("T2I texturing synthetic data CVPRW", 'all:"texturing" AND all:"synthetic" AND all:"diffusion"'),
    ("T2I texturing synth (loose)", 'all:"Text-to-Image" AND all:"synthetic data"'),
]:
    print(f"\n=== {label} ===")
    try:
        res = arxiv(q)
        if not res:
            print("  (no results)")
        for r in res:
            print(f"  {r[0]}  [{r[3]}]")
            print(f"    {r[1]}")
            print(f"    {r[2]}")
    except Exception as e:
        print(f"  ERR {e}")
