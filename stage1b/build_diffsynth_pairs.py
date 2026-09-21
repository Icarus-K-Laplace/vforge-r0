"""
Stage1b: Real-trace counterfactual pairing for DiffSynth (CVPRW 2025).

Uses authentic run-result CSVs from the public GitHub repo.
Only the reporting/selection DECISION differs between T+ and T-.
"""
from __future__ import annotations
import json, csv, hashlib
from pathlib import Path
from statistics import mean, pstdev
from typing import List, Dict

PROJECT_ROOT = Path(__file__).resolve().parent
TRACES_DIR   = PROJECT_ROOT / "traces_real"
TRACES_DIR.mkdir(exist_ok=True)
EXT_DIR      = PROJECT_ROOT / "external"
CONTRACTS_DIR = PROJECT_ROOT / "contracts_freeze"
EPSILON0 = 0.01
TAU = 0.20  # VPS threshold, frozen before evaluation


def _sha(obj) -> str:
    return hashlib.sha256(json.dumps(obj, sort_keys=True, default=str).encode()).hexdigest()


def load_csv_rows(fname: str) -> List[Dict]:
    rows = []
    with open(EXT_DIR / fname) as f:
        reader = csv.DictReader(f)
        for r in reader:
            rows.append({k: (v if v not in (None, "") else None) for k, v in r.items()})
    return rows


def build_diffsynth_pairs() -> List[Dict]:
    """
    E01: Cross-category aggregation.
      Faithful T+ : mean over ALL 3 declared categories (mugs, shoes, T-shirts).
      Invalid T-  : mean over a PROPER SUBSET (2 or 1 categories) that
                    best preserves the scalar (value-preserving selective aggregation).
      Metric: AKD (keypoint average keypoint distance, lower is better).

    E04: Category subgroup selective reporting.
      Faithful T+ : report all 3 categories.
      Invalid T-  : report only the 2 categories where the method "wins".

    E06: Comparator resource asymmetry.
      The paper uses asymmetric dataset sizes (diffusion ~5000, random ~300).
      The T- case is a reporting decision that omits the resource-asymmetry
      disclosure while keeping the same scalar.
    """
    # all_metrics.csv: index, meanAP, AKD, median_KD, seg_map, bbox_map, category, experiment
    am = load_csv_rows("diffsynth_all_metrics.csv")
    # Filter to rows with valid AKD
    valid = [r for r in am if r.get("AKD") and r["category"] in ("mug", "shoe", "tshirt")]

    # Group by experiment (texturing method)
    by_exp: Dict[str, List[Dict]] = {}
    for r in valid:
        by_exp.setdefault(r["experiment"], []).append(r)

    pairs = []

    # ── E01: cross-category selective aggregation ──────────────────
    for exp, rows in sorted(by_exp.items()):
        cats = [r["category"] for r in rows]
        if len(set(cats)) < 3:
            continue  # need all 3 categories for E01
        all_cats = sorted(set(cats))
        akd_by_cat = {}
        for r in rows:
            akd_by_cat[r["category"]] = float(r["AKD"])
        all_vals = [akd_by_cat[c] for c in all_cats]
        y_plus = mean(all_vals)
        sigma_clean = pstdev(all_vals) if len(all_vals) > 1 else EPSILON0

        # T-: find the 2-category subset that best preserves y_plus
        from itertools import combinations
        best_subset = None
        best_diff = float("inf")
        for combo in combinations(all_cats, 2):
            sub = [akd_by_cat[c] for c in combo]
            diff = abs(mean(sub) - y_plus)
            if diff < best_diff:
                best_diff = diff
                best_subset = list(combo)

        y_minus = mean(akd_by_cat[c] for c in best_subset)
        vps = best_diff / max(sigma_clean, EPSILON0)

        group_id = f"DS_E01_{exp.replace('-', '_')}"

        def make_trace(trace_id, cats_used, y, faithful, exp_key):
            trace = {
                "trace_id": trace_id,
                "paper": "diffusing_synth_2411.10164",
                "repository": "tlpss/diffusing-synthetic-data",
                "family": "E01",
                "experiment": exp_key,
                "protocol": {
                    "declared_categories": all_cats,
                    "reported_categories": cats_used,
                    "aggregation_rule": "mean",
                    "metric": "AKD",
                },
                "outputs": {
                    "reported_value": {
                        "value": round(y, 4),
                        "aggregation_rule": "mean",
                        "upstream_categories": cats_used,
                    }
                },
                "is_counterfactual": not faithful,
                "contract_id": "DS_E01_CROSS_CAT_AGG",
            }
            trace["self_hash"] = _sha({k: v for k, v in trace.items() if k != "self_hash"})
            return trace

        t_plus = make_trace(f"{group_id}_Tplus", all_cats, y_plus, True, exp)
        t_minus = make_trace(f"{group_id}_Tminus", best_subset, y_minus, False, exp)
        t_minus["vps"] = round(vps, 4)
        t_minus["value_preserving"] = vps <= TAU
        t_minus["abs_diff"] = round(best_diff, 4)

        pairs.append({
            "pair_id": group_id,
            "paper": "diffusing_synth_2411.10164",
            "family": "E01",
            "experiment": exp,
            "n_cats_all": len(all_cats),
            "n_cats_invalid": len(best_subset),
            "y_plus": round(y_plus, 4),
            "y_minus": round(y_minus, 4),
            "vps": round(vps, 4),
            "value_preserving": vps <= TAU,
            "sigma_clean": round(sigma_clean, 4),
            "metric": "AKD",
        })
        TRACES_DIR.joinpath(f"{group_id}_Tplus.json").write_text(json.dumps(t_plus, indent=2))
        TRACES_DIR.joinpath(f"{group_id}_Tminus.json").write_text(json.dumps(t_minus, indent=2))

    # ── E04: category subgroup selective reporting ──────────────────
    for exp, rows in sorted(by_exp.items()):
        cats = [r["category"] for r in rows]
        if len(set(cats)) < 3:
            continue
        all_cats = sorted(set(cats))
        akd_by_cat = {r["category"]: float(r["AKD"]) for r in rows}
        all_vals = [akd_by_cat[c] for c in all_cats]
        y_plus = mean(all_vals)
        sigma_clean = pstdev(all_vals) if len(all_vals) > 1 else EPSILON0

        # T-: report only the 2 categories with the LOWEST AKD (best performance)
        ranked = sorted(all_cats, key=lambda c: akd_by_cat[c])  # ascending (lower=good)
        subset = ranked[:2]
        y_minus = mean(akd_by_cat[c] for c in subset)
        diff = abs(y_minus - y_plus)
        vps = diff / max(sigma_clean, EPSILON0)

        group_id = f"DS_E04_{exp.replace('-', '_')}"

        def make_trace_e04(trace_id, cats_used, y, faithful, exp_key):
            trace = {
                "trace_id": trace_id,
                "paper": "diffusing_synth_2411.10164",
                "repository": "tlpss/diffusing-synthetic-data",
                "family": "E04",
                "experiment": exp_key,
                "protocol": {
                    "declared_categories": all_cats,
                    "reported_categories": cats_used,
                    "aggregation_rule": "mean",
                    "metric": "AKD",
                },
                "outputs": {
                    "reported_value": {
                        "value": round(y, 4),
                        "aggregation_rule": "mean",
                        "upstream_categories": cats_used,
                    }
                },
                "is_counterfactual": not faithful,
                "contract_id": "DS_E04_CATEGORY_SUBGROUP",
            }
            trace["self_hash"] = _sha({k: v for k, v in trace.items() if k != "self_hash"})
            return trace

        t_plus = make_trace_e04(f"{group_id}_Tplus", all_cats, y_plus, True, exp)
        t_minus = make_trace_e04(f"{group_id}_Tminus", subset, y_minus, False, exp)
        t_minus["vps"] = round(vps, 4)
        t_minus["value_preserving"] = vps <= TAU
        t_minus["abs_diff"] = round(diff, 4)

        pairs.append({
            "pair_id": group_id,
            "paper": "diffusing_synth_2411.10164",
            "family": "E04",
            "experiment": exp,
            "n_cats_all": len(all_cats),
            "n_cats_invalid": len(subset),
            "y_plus": round(y_plus, 4),
            "y_minus": round(y_minus, 4),
            "vps": round(vps, 4),
            "value_preserving": vps <= TAU,
            "sigma_clean": round(sigma_clean, 4),
            "metric": "AKD",
        })
        TRACES_DIR.joinpath(f"{group_id}_Tplus.json").write_text(json.dumps(t_plus, indent=2))
        TRACES_DIR.joinpath(f"{group_id}_Tminus.json").write_text(json.dumps(t_minus, indent=2))

    # ── E06: comparator resource asymmetry ───────────────────────────
    # The paper uses asymmetric dataset sizes:
    #   diffusion texturing: ~5000 images
    #   random texturing: ~300 images
    # The T- case omits the resource-asymmetry disclosure.
    # This is a DOCUMENTATION pair (the scalar is unchanged; the
    # epistemic contract checks whether the asymmetry was declared).
    ds_info = {"diffusion": 5000, "random": 300}
    group_id = "DS_E06_DATASET_ASYM"

    t_plus = {
        "trace_id": f"{group_id}_Tplus",
        "paper": "diffusing_synth_2411.10164",
        "repository": "tlpss/diffusing-synthetic-data",
        "family": "E06",
        "protocol": {
            "declared_budgets": {"diffusion_texturing": 5000, "random_texturing": 300},
            "comparator_budgets": {"diffusion_texturing": 5000, "random_texturing": 300},
            "asymmetry_disclosed": True,
        },
        "outputs": {"reported_value": {"value": "n/a", "note": "E06 is a documentation pair"}},
        "is_counterfactual": False,
        "contract_id": "DS_E06_RESOURCE_ASYM",
    }
    t_plus["self_hash"] = _sha({k: v for k, v in t_plus.items() if k != "self_hash"})

    t_minus = {
        "trace_id": f"{group_id}_Tminus",
        "paper": "diffusing_synth_2411.10164",
        "repository": "tlpss/diffusing-synthetic-data",
        "family": "E06",
        "protocol": {
            "declared_budgets": {"diffusion_texturing": 5000, "random_texturing": 300},
            "comparator_budgets": {"diffusion_texturing": 5000, "random_texturing": 300},
            "asymmetry_disclosed": False,  # T- hides the asymmetry
        },
        "outputs": {"reported_value": {"value": "n/a", "note": "E06 is a documentation pair"}},
        "is_counterfactual": True,
        "contract_id": "DS_E06_RESOURCE_ASYM",
    }
    t_minus["self_hash"] = _sha({k: v for k, v in t_minus.items() if k != "self_hash"})
    t_minus["vps"] = 0.0
    t_minus["value_preserving"] = True

    pairs.append({
        "pair_id": group_id,
        "paper": "diffusing_synth_2411.10164",
        "family": "E06",
        "experiment": "dataset-size-asymmetry",
        "n_cats_all": 2,
        "n_cats_invalid": 2,
        "y_plus": None,
        "y_minus": None,
        "vps": 0.0,
        "value_preserving": True,
        "sigma_clean": None,
        "metric": "documentation",
    })
    TRACES_DIR.joinpath(f"{group_id}_Tplus.json").write_text(json.dumps(t_plus, indent=2))
    TRACES_DIR.joinpath(f"{group_id}_Tminus.json").write_text(json.dumps(t_minus, indent=2))

    return pairs


def save_index(all_pairs: List[Dict]):
    index = {
        "stage": "R1-B1-Stage1b",
        "n_pairs": len(all_pairs),
        "pairs": [
            {"pair_id": p["pair_id"], "family": p["family"], "experiment": p.get("experiment"),
             "value_preserving": p["value_preserving"]}
            for p in all_pairs
        ],
    }
    out = TRACES_DIR / "REAL_PAIR_INDEX.json"
    out.write_text(json.dumps(index, indent=2))
    print(f"Stage1b pairs: {len(all_pairs)} -> {out}")
    by_fam = {}
    for p in all_pairs:
        by_fam.setdefault(p["family"], []).append(p)
    for fam, ps in sorted(by_fam.items()):
        vp = sum(1 for p in ps if p["value_preserving"])
        print(f"  {fam}: {len(ps)} pairs, {vp} value-preserving")


if __name__ == "__main__":
    pairs = build_diffsynth_pairs()
    save_index(pairs)
