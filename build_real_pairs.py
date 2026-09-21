"""
R1-B1 Real-Trace Counterfactual Pairing.

Builds T+ (scientifically faithful) and T- (scientifically invalid) pairs
from AUTHENTIC public W&B runs. The underlying executions are real; only
the reporting/selection DECISION differs between T+ and T-.

T- cases are clearly labeled as experimental counterfactuals. We do NOT
imply the original authors committed these violations.

All T- pairs use real run metric values — no fabricated training outputs.
"""
from __future__ import annotations

import json
import hashlib
from pathlib import Path
from typing import Dict, List, Any, Optional
from statistics import mean, pstdev

PROJECT_ROOT = Path(__file__).resolve().parent
TRACES_DIR    = PROJECT_ROOT / "traces_real"
TRACES_DIR.mkdir(exist_ok=True)
EXT_DIR       = PROJECT_ROOT / "external"
CONTRACTS_DIR = PROJECT_ROOT / "contracts_real"

EPSILON0 = 0.01  # floor for VPS denominator


def _sha(obj: Any) -> str:
    return hashlib.sha256(json.dumps(obj, sort_keys=True, default=str).encode()).hexdigest()


def _load_wandb(fname: str) -> List[Dict]:
    return json.loads((EXT_DIR / fname).read_text())


def _parse_seed(name: str) -> int:
    """Extract seed from a W&B displayName like 'icarl_r4_s1993'."""
    import re
    m = re.search(r"_s?(\d+)$", name)
    return int(m.group(1)) if m else -1


# ──────────────────────────────────────────────────────────────
# ViewBatchModel: E01 selective-aggregation pairs
# ──────────────────────────────────────────────────────────────
def build_viewbatchmodel_pairs() -> List[Dict]:
    """
    Table 6 uses (aug_repeat, flag) groups × 3 seeds (1993, 1996, 1997).
    T+ : mean over all 3 seeds (faithful).
    T- : mean over a PROPER SUBSET (1 or 2 seeds) that preserves the scalar
         within VPS threshold (value-preserving selective aggregation).
    """
    vb = _load_wandb("viewbatchmodel_wandb.json")
    runs = []
    for e in vb:
        n = e["node"]
        name = n["displayName"]
        sm = json.loads(n["summaryMetrics"]) if n.get("summaryMetrics") else {}
        # Parse: model_(rN)_(flag)_s<seed>
        import re
        m = re.match(r"(icarl)_(r(\d+))?(_(hard_aug|ssl))?_s?(\d+)$", name)
        if not m:
            continue
        flag = m.group(5) or "none"
        aug = int(m.group(3)) if m.group(3) else 1
        seed = int(m.group(6))
        runs.append({
            "display_name": name,
            "aug_repeat": aug,
            "flag": flag,
            "seed": seed,
            "state": n["state"],
            "class_mean": sm.get("RESULT_class_mean_accs"),
            "task_mean": sm.get("RESULT_task_mean_accs"),
        })

    # Group by (aug, flag)
    groups: Dict[tuple, List[Dict]] = {}
    for r in runs:
        key = (r["aug_repeat"], r["flag"])
        groups.setdefault(key, []).append(r)

    pairs = []
    for (aug, flag), grp in sorted(groups.items()):
        grp = [r for r in grp if r.get("class_mean") is not None]
        if len(grp) < 2:
            continue
        seed_vals = {r["seed"]: r for r in grp}
        all_seeds = sorted(seed_vals.keys())
        metric = "class_mean"  # use class-mean accuracy as the table scalar

        # T+: faithful = mean over ALL declared seeds
        all_vals = [seed_vals[s][metric] for s in all_seeds]
        y_plus = mean(all_vals)
        sigma_clean = pstdev(all_vals) if len(all_vals) > 1 else EPSILON0

        # T-: proper subset that best preserves the scalar (E01 flagship:
        #      minimize |Aggregate(S') - Aggregate(S)| over proper subsets)
        best_subset = None
        best_diff = float("inf")
        # Try all proper subsets (small N so this is cheap)
        for mask in range(1, (1 << len(all_seeds)) - 1):
            if mask == (1 << len(all_seeds)) - 1:  # skip the full set
                continue
            sub_seeds = [all_seeds[i] for i in range(len(all_seeds)) if mask & (1 << i)]
            sub_vals = [seed_vals[s][metric] for s in sub_seeds]
            y_sub = mean(sub_vals)
            diff = abs(y_sub - y_plus)
            if diff < best_diff:
                best_diff = diff
                best_subset = sub_seeds

        y_minus = mean(seed_vals[s][metric] for s in best_subset)
        vps = best_diff / max(sigma_clean, EPSILON0)
        value_preserving = vps <= 0.20  # τ = 0.20 frozen

        group_id = f"VB_E01_r{aug}_{flag}"

        # Build T+ and T- trace records
        def make_trace(sid: str, seed_set: List[int], agg_rule: str,
                       y: float, faithful: bool) -> Dict:
            trace = {
                "trace_id": sid,
                "paper": "viewbatchmodel_2503.18371",
                "repository": "hankyul2/ViewBatchModel",
                "source_runs": [seed_vals[s]["display_name"] for s in seed_set],
                "protocol": {
                    "declared_seeds": all_seeds,
                    "aggregation_rule": agg_rule,
                    "aggregation_inputs": [f"VB_s{s}" for s in seed_set],
                    "aug_repeat": aug,
                    "flag": flag,
                },
                "outputs": {
                    "reported_value": {
                        "value": round(y, 4),
                        "aggregation_rule": agg_rule,
                        "upstream_runs": [f"VB_s{s}" for s in seed_set],
                    },
                },
                "is_counterfactual": not faithful,
                "family": "E01",
                "contract_id": "VB_C1_TABLE6_SEED_AGGREGATION",
            }
            trace["self_hash"] = _sha({k: v for k, v in trace.items() if k != "self_hash"})
            return trace

        t_plus  = make_trace(f"{group_id}_Tplus", all_seeds, "mean", y_plus, faithful=True)
        t_minus = make_trace(f"{group_id}_Tminus", best_subset, "mean", y_minus, faithful=False)
        t_minus["vps"] = round(vps, 4)
        t_minus["value_preserving"] = value_preserving
        t_minus["abs_diff"] = round(best_diff, 4)

        pair = {
            "pair_id": group_id,
            "paper": "viewbatchmodel_2503.18371",
            "family": "E01",
            "aug_repeat": aug,
            "flag": flag,
            "n_seeds_all": len(all_seeds),
            "n_seeds_used_invalid": len(best_subset),
            "y_plus": round(y_plus, 4),
            "y_minus": round(y_minus, 4),
            "vps": round(vps, 4),
            "value_preserving": value_preserving,
            "sigma_clean": round(sigma_clean, 4),
        }
        pairs.append({"pair": pair, "t_plus": t_plus, "t_minus": t_minus})
    return pairs


# ──────────────────────────────────────────────────────────────
# RevisitDML: E01 seed-completeness pairs (organic)
# ──────────────────────────────────────────────────────────────
def build_revisitdml_pairs() -> List[Dict]:
    """
    RevisitDML: groups are (dataset, method). Some have 5 seeds, some 2.
    E01: T+ = mean over all available seeds; T- = mean over a proper subset.
    For groups with 5 seeds, selecting a best-3 subset that preserves value
    is the selective-aggregation counterfactual.
    """
    rdml = _load_wandb("revisitdml_wandb.json")
    # Pick a stable metric from summary_metrics (e.g. Test: discriminative_e_recall: e_recall@1)
    # First, discover which metric keys are present
    sample = rdml[0]["node"]
    sm = json.loads(sample.get("summaryMetrics", "{}")) if sample.get("summaryMetrics") else {}
    # Find a 'Test:' recall metric
    metric_key = None
    for k in sm:
        if k.startswith("Test: discriminative_e_recall: e_recall@1"):
            metric_key = k
            break
    if not metric_key:
        # fall back to any Test metric
        for k in sm:
            if k.startswith("Test:"):
                metric_key = k
                break

    # Group by (dataset, method)
    groups: Dict[tuple, List[Dict]] = {}
    for e in rdml:
        n = e["node"]
        name = n["displayName"]
        parts = name.split("_")
        if len(parts) < 3 or not (parts[-1].startswith("s") and parts[-1][1:].isdigit()):
            continue
        sm = json.loads(n.get("summaryMetrics", "{}")) if n.get("summaryMetrics") else {}
        val = sm.get(metric_key)
        if val is None:
            continue
        groups.setdefault((parts[0], "_".join(parts[1:-1])), []).append(
            {"display_name": name, "seed": int(parts[-1][1:]), "value": val}
        )

    pairs = []
    # Only take groups with >=3 seeds so a proper subset exists
    for key, grp in sorted(groups.items()):
        if len(grp) < 3:
            continue
        grp = sorted(grp, key=lambda r: r["seed"])
        all_seeds = [r["seed"] for r in grp]
        by_seed = {r["seed"]: r for r in grp}
        all_vals = [by_seed[s]["value"] for s in all_seeds]
        y_plus = mean(all_vals)
        sigma_clean = pstdev(all_vals) if len(all_vals) > 1 else EPSILON0

        # T-: pick the 2 best seeds (highest value) — selective aggregation
        # that preserves the mean approximately.
        ranked = sorted(all_seeds, key=lambda s: by_seed[s]["value"], reverse=True)
        for k in [2, 3, 4]:  # try smallest proper subsets that preserve value
            if k >= len(all_seeds):
                continue
            subset = ranked[:k]
            y_sub = mean(by_seed[s]["value"] for s in subset)
            diff = abs(y_sub - y_plus)
            vps = diff / max(sigma_clean, EPSILON0)
            if vps <= 0.25:
                break

        group_id = f"RDML_E01_{key[0]}_{key[1]}"

        def make_trace(sid: str, seed_set: List[int], y: float, faithful: bool) -> Dict:
            trace = {
                "trace_id": sid,
                "paper": "revisitdml_2002.08473",
                "repository": "Confusezius/Revisiting_Deep_Metric_Learning_PyTorch",
                "source_runs": [f"{key[0]}_{key[1]}_s{s}" for s in seed_set],
                "protocol": {
                    "dataset": key[0],
                    "method": key[1],
                    "declared_seeds": all_seeds,
                    "aggregation_rule": "mean",
                    "aggregation_inputs": [f"{group_id}_s{s}" for s in seed_set],
                },
                "outputs": {
                    "reported_value": {
                        "value": round(y, 4),
                        "aggregation_rule": "mean",
                        "upstream_runs": [f"{group_id}_s{s}" for s in seed_set],
                    },
                },
                "is_counterfactual": not faithful,
                "family": "E01",
                "contract_id": "RDML_C1_SEED_GROUP_AGGREGATION",
            }
            trace["self_hash"] = _sha({k: v for k, v in trace.items() if k != "self_hash"})
            return trace

        t_plus = make_trace(f"{group_id}_Tplus", all_seeds, y_plus, True)
        t_minus = make_trace(f"{group_id}_Tminus", subset, y_sub, False)
        t_minus["vps"] = round(vps, 4)
        t_minus["value_preserving"] = vps <= 0.25
        t_minus["abs_diff"] = round(diff, 4)

        pair = {
            "pair_id": group_id,
            "paper": "revisitdml_2002.08473",
            "family": "E01",
            "dataset": key[0],
            "method": key[1],
            "n_seeds_all": len(all_seeds),
            "n_seeds_used_invalid": len(subset),
            "y_plus": round(y_plus, 4),
            "y_minus": round(y_sub, 4),
            "vps": round(vps, 4),
            "value_preserving": vps <= 0.25,
            "sigma_clean": round(sigma_clean, 4),
            "metric": metric_key,
        }
        pairs.append({"pair": pair, "t_plus": t_plus, "t_minus": t_minus})

    return pairs


# ──────────────────────────────────────────────────────────────
# ViewBatchModel: E04 selective-subgroup (task) reporting
# ──────────────────────────────────────────────────────────────
def build_viewbatchmodel_e04_pairs() -> List[Dict]:
    """
    E04: The paper reports mean over all 5 tasks.
    T+ : report all 5 declared task subgroups.
    T- : report only the 3 highest-value tasks (selected subgroups).
    Same underlying run metrics; only the reporting scope differs.
    """
    vb = _load_wandb("viewbatchmodel_wandb.json")
    import re
    groups: Dict[tuple, List[Dict]] = {}
    for e in vb:
        n = e["node"]
        name = n["displayName"]
        sm = json.loads(n["summaryMetrics"]) if n.get("summaryMetrics") else {}
        m = re.match(r"(icarl)_(r(\d+))?(_(hard_aug|ssl))?_s?(\d+)$", name)
        if not m:
            continue
        flag = m.group(5) or "none"
        aug = int(m.group(3)) if m.group(3) else 1
        seed = int(m.group(6))
        task_accs = {i: sm.get(f"RESULT_class_acc_{i}") for i in range(5)}
        if any(v is None for v in task_accs.values()):
            continue
        groups.setdefault((aug, flag), []).append(
            {"seed": seed, "display_name": name, "task_accs": task_accs})

    pairs = []
    for (aug, flag), grp in sorted(groups.items()):
        task_means = {}
        for t in range(5):
            vals = [g["task_accs"][t] for g in grp]
            task_means[t] = mean(vals)
        all_tasks = sorted(task_means.keys())
        y_plus = mean(task_means.values())

        ranked = sorted(all_tasks, key=lambda t: task_means[t], reverse=True)
        subset = ranked[:3]
        y_minus = mean(task_means[t] for t in subset)
        diff = abs(y_minus - y_plus)
        sigma_clean = pstdev(list(task_means.values())) if len(task_means) > 1 else EPSILON0
        vps = diff / max(sigma_clean, EPSILON0)

        group_id = f"VB_E04_r{aug}_{flag}"

        def make_trace(sid, task_set, y, faithful):
            trace = {
                "trace_id": sid,
                "paper": "viewbatchmodel_2503.18371",
                "repository": "hankyul2/ViewBatchModel",
                "source_runs": [f"VB_{g['display_name']}" for g in grp],
                "protocol": {
                    "declared_subgroups": all_tasks,
                    "reported_subgroups": task_set,
                    "aggregation_rule": "mean_over_tasks",
                    "aug_repeat": aug,
                    "flag": flag,
                },
                "outputs": {
                    "reported_value": {
                        "value": round(y, 4),
                        "aggregation_rule": "mean_over_tasks",
                        "upstream_tasks": [f"task_{t}" for t in task_set],
                    },
                },
                "is_counterfactual": not faithful,
                "family": "E04",
                "contract_id": "VB_C2_TASK_SUBGROUP_SCOPE",
            }
            trace["self_hash"] = _sha({k: v for k, v in trace.items() if k != "self_hash"})
            return trace

        t_plus = make_trace(f"{group_id}_Tplus", all_tasks, y_plus, True)
        t_minus = make_trace(f"{group_id}_Tminus", subset, y_minus, False)
        t_plus["contract_id"] = "VB_C2_TASK_SUBGROUP_SCOPE"
        t_minus["contract_id"] = "VB_C2_TASK_SUBGROUP_SCOPE"
        t_minus["vps"] = round(vps, 4)
        t_minus["value_preserving"] = vps <= 0.25
        t_minus["abs_diff"] = round(diff, 4)

        pair = {
            "pair_id": group_id,
            "paper": "viewbatchmodel_2503.18371",
            "family": "E04",
            "n_subgroups_all": len(all_tasks),
            "n_subgroups_used_invalid": len(subset),
            "y_plus": round(y_plus, 4),
            "y_minus": round(y_minus, 4),
            "vps": round(vps, 4),
            "value_preserving": vps <= 0.25,
            "sigma_clean": round(sigma_clean, 4),
        }
        pairs.append({"pair": pair, "t_plus": t_plus, "t_minus": t_minus})
    return pairs


# ──────────────────────────────────────────────────────────────
# E02 attempt: checkpoint/run-selection provenance
# ──────────────────────────────────────────────────────────────
def build_e02_attempt() -> Dict:
    """
    E02 (evaluation-to-selection leakage) requires observing:
      - checkpoint candidates
      - the selection criterion (which split drove selection)
      - which checkpoint was selected

    Check both real sources for whether this provenance is exposed.
    Returns a documented insufficiency record if not observable.
    """
    vb = _load_wandb("viewbatchmodel_wandb.json")
    rdml = _load_wandb("revisitdml_wandb.json")

    vb_sample = json.loads(vb[0]["node"].get("summaryMetrics", "{}")) if vb else {}
    vb_keys = sorted(vb_sample.keys())
    vb_has_ckpt = any(
        k.lower() in ("checkpoint_selected", "selection_criterion", "selection_split",
                      "best_ckpt", "ckpt_candidates") for k in vb_keys
    )

    rdml_sample = json.loads(rdml[0]["node"].get("summaryMetrics", "{}")) if rdml else {}
    rdml_keys = sorted(rdml_sample.keys())[:15]
    rdml_has_ckpt = any(
        k.lower() in ("checkpoint_selected", "selection_criterion", "selection_split")
        for k in rdml_keys
    )

    observable = vb_has_ckpt or rdml_has_ckpt
    record = {
        "family": "E02",
        "status": "OBSERVABLE" if observable else "TRACE_INSUFFICIENT",
        "viewbatchmodel_exposes_checkpoint_provenance": vb_has_ckpt,
        "revisitdml_exposes_checkpoint_provenance": rdml_has_ckpt,
        "vb_summary_metric_keys_sample": vb_keys[:15],
        "rdml_summary_metric_keys_sample": rdml_keys,
        "reasoning": (
            "W&B summaryMetrics for both public projects expose per-run task/class "
            "accuracy and test discriminative metrics, but do NOT expose "
            "checkpoint-selection provenance (selection criterion split, candidate "
            "checkpoints, selected checkpoint id). E02 therefore cannot be "
            "constructed from these sources without fabricating selection data. "
            "Recorded as TRACE_INSUFFICIENT per protocol (document, don't invent)."
        ),
        "constructed_pairs": 0,
    }
    return record


def save_all():
    vb_pairs = build_viewbatchmodel_pairs()
    rdml_pairs = build_revisitdml_pairs()
    vb_e04 = build_viewbatchmodel_e04_pairs()
    e02_rec = build_e02_attempt()
    all_pairs = vb_pairs + rdml_pairs + vb_e04

    # Write pair index + traces
    index = {
        "n_pairs": len(all_pairs),
        "e02_attempt": e02_rec,
        "pairs": [
            {
                "pair_id": p["pair"]["pair_id"],
                "paper": p["pair"]["paper"],
                "family": p["pair"]["family"],
                "value_preserving": p["pair"]["value_preserving"],
                "vps": p["pair"]["vps"],
            }
            for p in all_pairs
        ],
    }
    # Save traces
    for p in all_pairs:
        for key in ("t_plus", "t_minus"):
            tr = p[key]
            (TRACES_DIR / f"{tr['trace_id']}.json").write_text(
                json.dumps(tr, indent=2), encoding="utf-8"
            )
    # Save index
    idx_path = TRACES_DIR / "REAL_PAIR_INDEX.json"
    idx_path.write_text(json.dumps(index, indent=2), encoding="utf-8")
    # SHA of index
    idx_path_sha = _sha(index)
    index["index_sha256"] = idx_path_sha
    idx_path.write_text(json.dumps(index, indent=2), encoding="utf-8")

    # Save E02 attempt record
    (TRACES_DIR / "E02_TRACE_INSUFFICIENCY_RECORD.json").write_text(
        json.dumps(e02_rec, indent=2), encoding="utf-8")

    print(f"Real-trace pairs: {len(all_pairs)} (VB_E01={len(vb_pairs)}, "
          f"RDML_E01={len(rdml_pairs)}, VB_E04={len(vb_e04)})")
    print(f"E02 attempt: {e02_rec['status']} (constructed={e02_rec['constructed_pairs']})")
    vp = sum(1 for p in all_pairs if p["pair"]["value_preserving"])
    print(f"Value-preserving: {vp}/{len(all_pairs)} = {vp/len(all_pairs):.3f}")
    print(f"Index -> {idx_path}")
    return all_pairs


if __name__ == "__main__":
    save_all()
