"""Analyze the two W&B run datasets for R1-B1 trace-source audit."""
import json
from collections import defaultdict
from pathlib import Path
from statistics import mean, pstdev

PROJECT_ROOT = Path(__file__).resolve().parent

# ─── ViewBatchModel ──────────────────────────────────────────────
vb = json.loads((PROJECT_ROOT / "external/viewbatchmodel_wandb.json").read_text())
print(f"=== ViewBatchModel: {len(vb)} runs ===")

# Parse displayName: icarl_r1_s1993, icarl_r4_1997, icarl_r4_ssl_s1993, etc.
# Pattern: model = icarl, r<N> = aug_repeat, optional flag (hard_aug/ssl), s<seed>
import re
vb_runs = []
for e in vb:
    n = e["node"]
    name = n["displayName"]
    sm = json.loads(n["summaryMetrics"]) if n.get("summaryMetrics") else {}
    m = re.match(r"(icarl)_(r(\d+))(_(hard_aug|ssl|1))?_s?(\d+)$", name)
    if m:
        vb_runs.append({
            "display_name": name,
            "aug_repeat": int(m.group(3)) if m.group(3) else 1,
            "flag": m.group(5) or "none",
            "seed": int(m.group(6)),
            "state": n["state"],
            "class_mean": sm.get("RESULT_class_mean_accs"),
            "task_mean": sm.get("RESULT_task_mean_accs"),
            "class_accs": {k: v for k, v in sm.items() if "class_acc" in k},
            "task_accs": {k: v for k, v in sm.items() if "task_acc" in k},
        })
    else:
        vb_runs.append({"display_name": name, "state": n["state"], "parse_failed": True,
                        "class_mean": sm.get("RESULT_class_mean_accs"),
                        "task_mean": sm.get("RESULT_task_mean_accs")})

parsed = [r for r in vb_runs if not r.get("parse_failed")]
print(f"Parsed: {len(parsed)}/{len(vb_runs)}")

# Group by (aug_repeat, flag) - this is the Table 6 grouping
groups = defaultdict(list)
for r in parsed:
    key = (r["aug_repeat"], r["flag"])
    groups[key].append(r)

print("\nGroups (aug_repeat, flag) -> seeds:")
for key, items in sorted(groups.items()):
    seeds = sorted(r["seed"] for r in items)
    cmeans = [r["class_mean"] for r in items if r.get("class_mean") is not None]
    tmeans = [r["task_mean"] for r in items if r.get("task_mean") is not None]
    c_std = pstdev(cmeans) if len(cmeans) > 1 else 0
    t_std = pstdev(tmeans) if len(tmeans) > 1 else 0
    print(f"  r{key[0]} {key[1]}: seeds={seeds}  "
          f"class_mean={mean(cmeans):.2f}±{c_std:.2f}  task_mean={mean(tmeans):.2f}±{t_std:.2f}")

# E01: full seed set vs. selective seed
# The paper reports 3 seeds (1993, 1996, 1997).
# E01 invalid = use only 1 seed (e.g. the best).
print("\n--- E01 candidates (aug_repeat=4, flag=none) ---")
e01_runs = groups.get((4, "none"), [])
if e01_runs:
    all_seeds = [r for r in e01_runs]
    # faithful = mean of all 3 seeds
    cm = [r["class_mean"] for r in all_seeds]
    tm = [r["task_mean"] for r in all_seeds]
    faithful_class = mean(cm)
    faithful_task = mean(tm)
    print(f"  Faithful (all {len(all_seeds)} seeds): class={faithful_class:.4f} task={faithful_task:.4f}")
    # invalid = best seed only
    for r in all_seeds:
        print(f"  Seed {r['seed']}: class={r['class_mean']:.4f} task={r['task_mean']:.4f}")

# ─── RevisitDML ──────────────────────────────────────────────────
rdml = json.loads((PROJECT_ROOT / "external/revisitdml_wandb.json").read_text())
print(f"\n=== RevisitDML: {len(rdml)} runs ===")

names = [e["node"]["displayName"] for e in rdml]
print(f"Sample names: {names[:15]}")

# Parse: e.g. "CARS_NPair_s3" -> dataset=CARS, method=NPair, seed=3
rdml_runs = []
for e in rdml:
    n = e["node"]
    name = n["displayName"]
    sm = json.loads(n["summaryMetrics"]) if n.get("summaryMetrics") else {}
    # Parse dataset/method/seed
    parts = name.split("_")
    if len(parts) >= 3 and parts[-1].startswith("s") and parts[-1][1:].isdigit():
        rdml_runs.append({
            "display_name": name,
            "dataset": parts[0],
            "method": "_".join(parts[1:-1]),
            "seed": int(parts[-1][1:]),
            "state": n["state"],
            "summary_metrics": sm,
        })

parsed2 = rdml_runs
print(f"Parsed: {len(parsed2)}/{len(rdml)}")

# Group by (dataset, method)
groups2 = defaultdict(list)
for r in parsed2:
    groups2[(r["dataset"], r["method"])].append(r)

print(f"\nGroups (dataset, method): {len(groups2)}")
print("Seeds per group (top 10):")
for key, items in sorted(groups2.items())[:10]:
    seeds = sorted(r["seed"] for r in items)
    print(f"  {key}: {len(items)} runs, seeds={seeds[:10]}")
