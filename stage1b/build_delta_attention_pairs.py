"""
Delta Attention Residuals Stage1b trace pair builder.

W&B entity wdlctc_abr, project 'residual' (public).
Paper: Table 1 — main results across scales (220M/533M/1044M).
5 methods per scale: baseline, block (AttnRes), full, delta_block, delta.

E06: The paper's central claim is "all methods share identical
architecture, data, and hyperparameters per scale." The
resource-asymmetry contract checks that for any (method, scale)
comparison pair the declared budgets are symmetric.
E01: cross-method aggregation within a scale — the paper reports
per-method Val PPL; a cross-method "mean" would be an aggregation
over methods (not standard, but E01 is sanity-check per protocol).
"""
from __future__ import annotations

import json
import csv
import urllib.request
import ssl
import time
import hashlib
from pathlib import Path
from statistics import mean, pstdev
from typing import List, Dict
from itertools import combinations

PROJECT_ROOT = Path(__file__).resolve().parent.parent
TRACES_DIR   = PROJECT_ROOT / "stage1b" / "traces_real"
TRACES_DIR.mkdir(exist_ok=True)
EXT_DIR      = PROJECT_ROOT / "stage1b" / "external"
CONTRACTS_DIR = PROJECT_ROOT / "stage1b" / "contracts_freeze"
EPSILON0 = 0.01
TAU = 0.20

WANDB_ENTITY = "wdlctc_abr"
WANDB_PROJECT = "residual"


def _sha(obj) -> str:
    return hashlib.sha256(json.dumps(obj, sort_keys=True, default=str).encode()).hexdigest()


def fetch_wandb_runs() -> List[Dict]:
    """Fetch W&B run data for the Delta Attention project (public)."""
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE

    out = EXT_DIR / "delta_attention_wandb.json"
    if out.exists():
        return json.loads(out.read_text())

    node_fields = "name displayName state summaryMetrics"
    q = ('{ entity(name: "' + WANDB_ENTITY + '") { project(name: "'
         + WANDB_PROJECT + '") { runs(first: 300) { edges { node { '
         + node_fields + ' } } } } } }')
    payload = json.dumps({"query": q}).encode()
    req = urllib.request.Request(
        "https://api.wandb.ai/graphql",
        data=payload,
        headers={"Content-Type": "application/json", "User-Agent": "Mozilla/5.0"},
    )
    for a in range(5):
        try:
            r = urllib.request.urlopen(req, timeout=45, context=ctx)
            data = json.loads(r.read().decode("utf-8", "ignore"))
            if data.get("data") and data["data"].get("entity"):
                edges = data["data"]["entity"]["project"]["runs"]["edges"]
                out.write_text(json.dumps(edges))
                print(f"  Fetched {len(edges)} W&B runs")
                return edges
            else:
                print("  No data returned")
                return []
        except Exception as e:
            if "SSL" in str(e):
                time.sleep(8 * (a + 1))
            else:
                print(f"  ERR: {type(e).__name__}: {str(e)[:100]}")
                return []
    return []


def parse_scale_method(display_name: str) -> Dict:
    """Parse a W&B displayName like 'baseline-d768-L12-10k' or 'delta-d1024-L24-10k-final'."""
    import re
    m = re.match(r"(\w[\w_-]*?)-(?:d(\d+)-L(\d+)-10k|d(\d+)-L(\d+)-lr6e4|d(\d+)-L(\d+)-lr6e4-v3)(-fixed|-final)?$", display_name)
    if m:
        method = m.group(1)
        d = m.group(2) or m.group(5) or m.group(8)
        L = m.group(3) or m.group(6) or m.group(9)
        scale = f"d{d}_L{L}" if d and L else "unknown"
        return {"method": method, "scale": scale, "raw": display_name}
    # Fallback: try a looser pattern
    m2 = re.match(r"(\w[\w_-]*?)-d(\d+)-L(\d+)(.*)$", display_name)
    if m2:
        return {"method": m2.group(1), "scale": f"d{m2.group(2)}_L{m2.group(3)}",
                "raw": display_name}
    return {"method": display_name, "scale": "unknown", "raw": display_name}


def build_delta_pairs() -> List[Dict]:
    """
    E06 (primary): For each scale, the paper compares 5 methods under
    identical resource budgets (same data, same hyperparameters, same
    training steps). The contract checks comparator-budget symmetry.
    T+ : all 5 methods at the same scale share identical budgets (symmetric).
    T- : one method receives a different budget (asymmetric) while the
         reported PPL scalar is preserved.

    E01 (sanity): cross-method aggregation at a scale — the mean Val PPL
    over methods. T+ uses all 5; T- uses a subset that preserves the mean.
    """
    runs = fetch_wandb_runs()
    if not runs:
        print("WARNING: no W&B runs fetched; using WANDB_RUNS.md as fallback")
        return _build_from_markdown()

    # Parse scale/method for each run
    parsed = []
    for e in runs:
        node = e.get("node", {})
        name = node.get("displayName", "")
        sm = json.loads(node.get("summaryMetrics", "{}")) if node.get("summaryMetrics") else {}
        # Find Val PPL in summary
        ppl = None
        for k, v in sm.items():
            if "val" in k.lower() and "ppl" in k.lower():
                ppl = v
                break
        if ppl is None:
            for k, v in sm.items():
                if "ppl" in k.lower():
                    ppl = v
                    break
        if ppl is None:
            continue
        info = parse_scale_method(name)
        parsed.append({
            "display_name": name,
            "method": info["method"],
            "scale": info["scale"],
            "ppl": float(ppl),
        })

    print(f"Parsed {len(parsed)} runs with PPL from W&B")
    scales = sorted(set(r["scale"] for r in parsed))
    methods_per_scale: Dict[str, List[Dict]] = {}
    for s in scales:
        methods_per_scale[s] = [r for r in parsed if r["scale"] == s]
        print(f"  {s}: {len(methods_per_scale[s])} methods")

    pairs = []

    # ── E06: resource asymmetry (primary) ──────────────────────────
    for s, runs_s in methods_per_scale.items():
        if len(runs_s) < 3:
            continue
        all_methods = [r["method"] for r in runs_s]
        ppls = {r["method"]: r["ppl"] for r in runs_s}
        y_plus = mean(list(ppls.values()))

        group_id = f"DA_E06_{s.replace('_','')}"
        # T+: symmetric — all methods share identical budget
        t_plus = {
            "trace_id": f"{group_id}_Tplus",
            "paper": "delta_attention_2605.18855",
            "repository": "wdlctc/delta-attention-residuals-code",
            "family": "E06",
            "scale": s,
            "protocol": {
                "declared_methods": all_methods,
                "comparator_methods": all_methods,
                "comparator_budgets": {
                    m: {"dataset": "FineWeb-Edu", "steps": 10000, "lr": "6e-4"}
                    for m in all_methods
                },
                "budgets_symmetric": True,
            },
            "outputs": {
                "reported_value": {
                    "value": round(y_plus, 4),
                    "metric": "val_ppl",
                    "per_method_ppl": ppls,
                }
            },
            "is_counterfactual": False,
            "contract_id": "DA_E06_BUDGET_SYMMETRY",
        }
        t_plus["self_hash"] = _sha({k: v for k, v in t_plus.items() if k != "self_hash"})

        # T-: one method gets a DIFFERENT step budget (e.g. half steps),
        # but the PPL scalar is kept the same (value-preserving)
        t_minus = {
            "trace_id": f"{group_id}_Tminus",
            "paper": "delta_attention_2605.18855",
            "repository": "wdlctc/delta-attention-residuals-code",
            "family": "E06",
            "scale": s,
            "protocol": {
                "declared_methods": all_methods,
                "comparator_methods": all_methods,
                "comparator_budgets": {
                    m: {"dataset": "FineWeb-Edu", "steps": 5000 if m == all_methods[0] else 10000,
                        "lr": "6e-4"}
                    for m in all_methods
                },
                "budgets_symmetric": False,
            },
            "outputs": {
                "reported_value": {
                    "value": round(y_plus, 4),  # preserved
                    "metric": "val_ppl",
                    "per_method_ppl": ppls,
                }
            },
            "is_counterfactual": True,
            "contract_id": "DA_E06_BUDGET_SYMMETRY",
        }
        t_minus["self_hash"] = _sha({k: v for k, v in t_minus.items() if k != "self_hash"})
        t_minus["vps"] = 0.0
        t_minus["value_preserving"] = True
        t_minus["abs_diff"] = 0.0

        pair = {
            "pair_id": group_id,
            "paper": "delta_attention_2605.18855",
            "family": "E06",
            "scale": s,
            "n_methods_all": len(all_methods),
            "n_methods_invalid": len(all_methods),
            "y_plus": round(y_plus, 4),
            "y_minus": round(y_plus, 4),
            "vps": 0.0,
            "value_preserving": True,
            "sigma_clean": round(pstdev(list(ppls.values())), 4) if len(ppls) > 1 else None,
            "metric": "val_ppl",
        }
        pairs.append(pair)
        TRACES_DIR.joinpath(f"{group_id}_Tplus.json").write_text(json.dumps(t_plus, indent=2))
        TRACES_DIR.joinpath(f"{group_id}_Tminus.json").write_text(json.dumps(t_minus, indent=2))

    # ── E01 (sanity): cross-method aggregation at a scale ─────────
    for s, runs_s in methods_per_scale.items():
        if len(runs_s) < 3:
            continue
        all_methods = [r["method"] for r in runs_s]
        ppls = {r["method"]: r["ppl"] for r in runs_s}
        all_vals = list(ppls.values())
        y_plus = mean(all_vals)
        sigma_clean = pstdev(all_vals) if len(all_vals) > 1 else EPSILON0

        # T-: proper subset that best preserves the mean
        best_subset = None
        best_diff = float("inf")
        for size in [2, 3, 4]:
            if size >= len(all_methods):
                continue
            for combo in combinations(all_methods, size):
                diff = abs(mean(ppls[m] for m in combo) - y_plus)
                if diff < best_diff:
                    best_diff = diff
                    best_subset = list(combo)

        y_minus = mean(ppls[m] for m in best_subset)
        vps = best_diff / max(sigma_clean, EPSILON0)

        group_id = f"DA_E01_{s.replace('_','')}"
        t_plus = {
            "trace_id": f"{group_id}_Tplus",
            "paper": "delta_attention_2605.18855",
            "repository": "wdlctc/delta-attention-residuals-code",
            "family": "E01",
            "scale": s,
            "protocol": {
                "declared_methods": all_methods,
                "reported_methods": all_methods,
                "aggregation_rule": "mean",
                "metric": "val_ppl",
            },
            "outputs": {
                "reported_value": {
                    "value": round(y_plus, 4),
                    "aggregation_rule": "mean",
                    "upstream_methods": all_methods,
                }
            },
            "is_counterfactual": False,
            "contract_id": "DA_E01_CROSS_METHOD_AGG",
        }
        t_plus["self_hash"] = _sha({k: v for k, v in t_plus.items() if k != "self_hash"})

        t_minus = {
            "trace_id": f"{group_id}_Tminus",
            "paper": "delta_attention_2605.18855",
            "repository": "wdlctc/delta-attention-residuals-code",
            "family": "E01",
            "scale": s,
            "protocol": {
                "declared_methods": all_methods,
                "reported_methods": best_subset,
                "aggregation_rule": "mean",
                "metric": "val_ppl",
            },
            "outputs": {
                "reported_value": {
                    "value": round(y_minus, 4),
                    "aggregation_rule": "mean",
                    "upstream_methods": best_subset,
                }
            },
            "is_counterfactual": True,
            "contract_id": "DA_E01_CROSS_METHOD_AGG",
        }
        t_minus["self_hash"] = _sha({k: v for k, v in t_minus.items() if k != "self_hash"})
        t_minus["vps"] = round(vps, 4)
        t_minus["value_preserving"] = vps <= TAU
        t_minus["abs_diff"] = round(best_diff, 4)

        pairs.append({
            "pair_id": group_id,
            "paper": "delta_attention_2605.18855",
            "family": "E01",
            "scale": s,
            "n_methods_all": len(all_methods),
            "n_methods_invalid": len(best_subset),
            "y_plus": round(y_plus, 4),
            "y_minus": round(y_minus, 4),
            "vps": round(vps, 4),
            "value_preserving": vps <= TAU,
            "sigma_clean": round(sigma_clean, 4),
            "metric": "val_ppl",
        })
        TRACES_DIR.joinpath(f"{group_id}_Tplus.json").write_text(json.dumps(t_plus, indent=2))
        TRACES_DIR.joinpath(f"{group_id}_Tminus.json").write_text(json.dumps(t_minus, indent=2))

    return pairs


def _build_from_markdown() -> List[Dict]:
    """Fallback: build E06 pairs from WANDB_RUNS.md (no PPL values needed)."""
    # Fix markdown fallback regex to handle the actual format
    md = (EXT_DIR / "delta_attention_wandb.md").read_text()
    import re
    # Match "### 220M ($d{=}768$, $L{=}12$)" followed by a table
    sections = re.findall(
        r"### (\S+)\s*\(.*?\)\s*\n\s*\n((?:\|.*\n?)+)", md
    )
    pairs = []
    for scale_label, table in sections:
        # Extract method names from the first column of the table
        lines = [l for l in table.split("\n") if l.strip().startswith("|")]
        # Skip header and separator rows
        methods = []
        for l in lines:
            cells = [c.strip() for c in l.split("|")]
            if len(cells) > 1 and cells[1] and cells[1] not in ("Method", "---", "Method (val PPL)") and not set(cells[1]) == set("-"):
                m = re.match(r"(\w+)", cells[1])
                if m:
                    methods.append(m.group(1))
        if len(methods) < 3:
            continue
        group_id = f"DA_E06_{scale_label.replace('_','')}"
        for side, symmetric in [("Tplus", True), ("Tminus", False)]:
            t = {
                "trace_id": f"{group_id}_{side}",
                "paper": "delta_attention_2605.18855",
                "repository": "wdlctc/delta-attention-residuals-code",
                "family": "E06",
                "scale": scale_label,
                "protocol": {
                    "declared_methods": methods,
                    "comparator_methods": methods,
                    "comparator_budgets": {m: {"steps": 10000} for m in methods},
                    "budgets_symmetric": symmetric,
                },
                "outputs": {"reported_value": {"value": "n/a", "metric": "val_ppl"}},
                "is_counterfactual": not symmetric,
                "contract_id": "DA_E06_BUDGET_SYMMETRY",
            }
            if side == "Tminus":
                t["vps"] = 0.0
                t["value_preserving"] = True
                t["abs_diff"] = 0.0
            t["self_hash"] = _sha({k: v for k, v in t.items() if k != "self_hash"})
            TRACES_DIR.joinpath(f"{t['trace_id']}.json").write_text(json.dumps(t, indent=2))
        pairs.append({
            "pair_id": group_id,
            "paper": "delta_attention_2605.18855",
            "family": "E06",
            "scale": scale_label,
            "n_methods_all": len(methods),
            "n_methods_invalid": len(methods),
            "y_plus": None, "y_minus": None,
            "vps": 0.0, "value_preserving": True,
            "sigma_clean": None, "metric": "val_ppl",
        })
    print(f"Markdown fallback built {len(pairs)} E06 pairs")
    return pairs


if __name__ == "__main__":
    pairs = build_delta_pairs()
    save = []
    for p in pairs:
        save.append({
            "pair_id": p["pair_id"],
            "paper": p["paper"],
            "family": p["family"],
            "experiment": p.get("scale"),
            "value_preserving": p["value_preserving"],
        })
    index = {"stage": "R1-B1-Stage1b", "source": "delta_attention", "n_pairs": len(pairs),
             "pairs": save}
    out = TRACES_DIR / "DELTA_ATTENTION_PAIR_INDEX.json"
    out.write_text(json.dumps(index, indent=2))
    print(f"\nDelta Attention pairs: {len(pairs)}")
    from collections import Counter
    fams = Counter(p["family"] for p in pairs)
    print(f"  By family: {dict(fams)}")
    vp = Counter(p["family"] for p in pairs if p["value_preserving"])
    print(f"  Value-preserving: {dict(vp)}")
