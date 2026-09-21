"""Regenerate all protocol graphs using the fixed extractor."""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from sciinvariant_r0d import RepoGraphExtractor

PROJECT_ROOT = Path(__file__).resolve().parent
REPOS_DIR = PROJECT_ROOT / "repositories"
GRAPHS_DIR = PROJECT_ROOT / "graphs"

with open(PROJECT_ROOT / "external/scicoqa/blind/scicoqa_real_blind.jsonl") as f:
    blind = [json.loads(line) for line in f]

extractor = RepoGraphExtractor()
GRAPHS_DIR.mkdir(exist_ok=True)

ok = 0; insufficient = 0; no_repo = 0
for sample in blind:
    pid = sample["discrepancy_id"]
    repo = REPOS_DIR / pid
    if not repo.exists() or not repo.is_dir():
        graph = {"study_id": pid, "nodes": [], "edges": [],
                 "metadata": {"error": "repo unavailable", "n_nodes": 0}}
        (GRAPHS_DIR / f"{pid}.json").write_text(json.dumps(graph, indent=2))
        no_repo += 1
        continue

    graph = extractor.extract(repo, pid)
    (GRAPHS_DIR / f"{pid}.json").write_text(json.dumps(graph, indent=2))

    n = len(graph.get("nodes", []))
    if n >= 3:
        ok += 1
    else:
        insufficient += 1

total = len(blind)
print(f"Total samples: {total}")
print(f"Usable graphs (>=3 nodes): {ok} ({ok/total*100:.1f}%)")
print(f"Insufficient graphs: {insufficient}")
print(f"No repo: {no_repo}")
print(f"Qualifies (>=75%): {ok >= 0.75*total}")
