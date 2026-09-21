"""
Systematic Search for Candidate Cases for R1-C Naturalistic Validation.
Queries arXiv and Semantic Scholar for:
1. Documented protocol mismatches
2. Reproducibility challenge reports
3. Test leakage / evaluation discrepancies
4. Benchmark corrections and errata
"""
import urllib.request
import urllib.parse
import json
import ssl
import time
import re
from pathlib import Path

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

OUT_DIR = Path("r1c/results")
OUT_DIR.mkdir(parents=True, exist_ok=True)

def search_arxiv(query, max_results=10):
    url = f"http://export.arxiv.org/api/query?search_query={urllib.parse.quote(query)}&max_results={max_results}"
    req = urllib.request.Request(url, headers={'User-Agent': 'VForge-R1C-Discovery/1.0'})
    try:
        resp = urllib.request.urlopen(req, timeout=30, context=ctx)
        xml = resp.read().decode('utf-8', 'ignore')
        entries = []
        for m in re.finditer(r'<entry>(.*?)</entry>', xml, re.DOTALL):
            entry_xml = m.group(1)
            title = re.search(r'<title>(.*?)</title>', entry_xml, re.DOTALL)
            summary = re.search(r'<summary>(.*?)</summary>', entry_xml, re.DOTALL)
            id_m = re.search(r'<id>(.*?)</id>', entry_xml, re.DOTALL)
            published = re.search(r'<published>(.*?)</published>', entry_xml, re.DOTALL)
            t_text = re.sub(r'\s+', ' ', title.group(1)).strip() if title else ""
            s_text = re.sub(r'\s+', ' ', summary.group(1)).strip() if summary else ""
            i_text = id_m.group(1).strip() if id_m else ""
            p_text = published.group(1).strip() if published else ""
            entries.append({
                "source": "arxiv",
                "id": i_text,
                "published": p_text,
                "title": t_text,
                "summary": s_text
            })
        return entries
    except Exception as e:
        print(f"arXiv search error for '{query}': {e}")
        return []

def search_semantic_scholar(query, limit=10):
    url = f"https://api.semanticscholar.org/graph/v1/paper/search?query={urllib.parse.quote(query)}&limit={limit}&fields=title,authors,year,abstract,venue,citationCount,openAccessPdf"
    req = urllib.request.Request(url, headers={'User-Agent': 'VForge-R1C-Discovery/1.0'})
    try:
        resp = urllib.request.urlopen(req, timeout=30, context=ctx)
        data = json.loads(resp.read().decode('utf-8', 'ignore'))
        papers = []
        for p in data.get('data', []):
            papers.append({
                "source": "semantic_scholar",
                "id": p.get('paperId', ''),
                "title": p.get('title', ''),
                "year": p.get('year', ''),
                "venue": p.get('venue', ''),
                "abstract": (p.get('abstract') or '')[:500],
                "citationCount": p.get('citationCount', 0),
                "openAccessPdf": (p.get('openAccessPdf') or {}).get('url', '')
            })
        return papers
    except Exception as e:
        print(f"Semantic Scholar error for '{query}': {e}")
        return []

if __name__ == "__main__":
    queries = [
        "ML Reproducibility Challenge report",
        "data leakage evaluation benchmark machine learning",
        "pitfalls evaluation graph neural networks",
        "metric learning reality check evaluation",
        "deep reinforcement learning that matters reproducibility",
        "reproducibility report cherry picking seeds",
        "discrepancy published paper results evaluation bug",
        "test set leakage machine learning paper",
        "are transformers effective for time series",
        "reproducibility study evaluation protocol"
    ]
    
    all_candidates = []
    for q in queries:
        print(f"Searching: {q}")
        res_s2 = search_semantic_scholar(q, limit=5)
        for r in res_s2:
            r['search_query'] = q
            all_candidates.append(r)
        time.sleep(1)
        res_ax = search_arxiv(q, max_results=5)
        for r in res_ax:
            r['search_query'] = q
            all_candidates.append(r)
        time.sleep(1)

    print(f"Total retrieved raw candidates: {len(all_candidates)}")
    with open(OUT_DIR / "raw_candidates.json", "w", encoding="utf-8") as f:
        json.dump(all_candidates, f, indent=2, ensure_ascii=False)
