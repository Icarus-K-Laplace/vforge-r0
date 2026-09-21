"""
Stage1b: Freeze epistemic contracts from paper text ONLY.
Reads paper body/method/appendix, generates + hashes epistemic
contracts. No run/metric data is consulted during this step.
"""
from __future__ import annotations
import json, hashlib
from pathlib import Path
from datetime import datetime

PROJECT_ROOT = Path(__file__).resolve().parent
PAPERS_DIR   = PROJECT_ROOT / "papers"
CONTRACTS_DIR = PROJECT_ROOT / "contracts_freeze"
CONTRACTS_DIR.mkdir(exist_ok=True)

def _sha(obj) -> str:
    return hashlib.sha256(json.dumps(obj, sort_keys=True, default=str).encode()).hexdigest()

def load_paper(stem: str) -> str:
    p = PAPERS_DIR / f"{stem}.txt"
    if not p.exists():
        # Try alternate naming (KDD26 LLM-vs-ML paper)
        alt = PAPERS_DIR / f"{stem}.txt"
        if alt.exists():
            return alt.read_text(encoding="utf-8")
        return ""
    return p.read_text(encoding="utf-8")

def build_diffsynth_contracts() -> list:
    """DIFFUSING_SYNTH (CVPRW 2025). Paper protocol, no run data."""
    paper = load_paper("DIFFUSING_SYNTH")
    phash = _sha(paper)
    contracts = [
        {
            "contract_id": "DS_E01_CROSS_CAT_AGG",
            "source_paper": "diffusing_synth_2411.10164",
            "family": "E01",
            "claim_text": ("Per-category results in Table II are single-run "
                "evaluations on (method, category) pairs; any cross-category "
                "'mean' reported in the paper must use ALL declared categories. "
                "Selecting only the category where the method outperforms the "
                "baseline is a selective-aggregation violation."),
            "paper_text_hash": phash,
            "predicates": [{
                "predicate_id": "E01_ALL_CATEGORIES",
                "principle": "P6_AGGREGATION_FIDELITY",
                "natural_language": ("When the paper reports a cross-category mean "
                    "or comparison, ALL declared categories (mugs, shoes, T-shirts) "
                    "must contribute equally; no category may be selectively omitted."),
                "trace_fields": ["protocol.declared_categories","protocol.reported_categories","outputs.category_values"],
                "condition": "set(protocol.reported_categories) == set(protocol.declared_categories)",
                "source_span": "Table II",
                "confidence": 0.85,
            }],
            "universal_principles": ["P6_AGGREGATION_FIDELITY"],
            "coverage_threshold": 0.70,
            "self_hash": "",
        },
        {
            "contract_id": "DS_E04_CATEGORY_SUBGROUP",
            "source_paper": "diffusing_synth_2411.10164",
            "family": "E04",
            "claim_text": ("Tables II/III report metrics for all three object "
                "categories (mugs, shoes, T-shirts). The claim that diffusion "
                "texturing outperforms the real baseline must hold across ALL "
                "declared categories, not just a selected subset."),
            "paper_text_hash": phash,
            "predicates": [{
                "predicate_id": "E04_CATEGORY_SCOPE",
                "principle": "P7_EVIDENCE_CLOSURE",
                "natural_language": ("The reported category set must equal the "
                    "declared category set; no category may be selectively omitted."),
                "trace_fields": ["protocol.declared_categories","protocol.reported_categories"],
                "condition": "set(protocol.reported_categories) == set(protocol.declared_categories)",
                "source_span": "Table II",
                "confidence": 0.85,
            }],
            "universal_principles": ["P7_EVIDENCE_CLOSURE"],
            "coverage_threshold": 0.70,
            "self_hash": "",
        },
        {
            "contract_id": "DS_E06_RESOURCE_ASYM",
            "source_paper": "diffusing_synth_2411.10164",
            "family": "E06",
            "claim_text": ("The paper compares texturing methods using asymmetric "
                "dataset sizes (diffusion ~5000, random ~300). Any "
                "method-comparison claim requires a fairness justification or a "
                "symmetric control. Without it, the superiority claim is not "
                "supported."),
            "paper_text_hash": phash,
            "predicates": [{
                "predicate_id": "E06_BUDGET_SYMMETRY",
                "principle": "P8_COMPARATOR_FAIRNESS",
                "natural_language": ("When comparing method A vs B, both must have "
                    "the same resource budget (dataset size, epochs, model "
                    "capacity) OR the asymmetry must be explicitly declared "
                    "and controlled for."),
                "trace_fields": ["protocol.declared_budgets","comparator_budgets"],
                "condition": "comparator_budgets_symmetric OR asymmetry_declared",
                "source_span": "Section IV-B",
                "confidence": 0.80,
            }],
            "universal_principles": ["P8_COMPARATOR_FAIRNESS"],
            "coverage_threshold": 0.70,
            "self_hash": "",
        },
    ]
    for c in contracts:
        payload = {k: v for k, v in c.items() if k != "self_hash"}
        c["self_hash"] = _sha(payload)
        (CONTRACTS_DIR / f"{c['contract_id']}.json").write_text(json.dumps(c, indent=2), encoding="utf-8")
    return contracts

def save_clinicalbench_contracts():
    """CLINICALBENCH (KDD 2026)."""
    paper = load_paper("CLINICALBENCH")
    phash = _sha(paper)
    contracts = [
        {
            "contract_id": "CB_E04_CATEGORY_INTERACTION",
            "source_paper": "clinicalbench_2605.11143",
            "family": "E04",
            "claim_text": ("ClinicalBench evaluates by category x condition "
                "interaction, not aggregate score. All 9 assertion-sensitive "
                "categories must be reported; selecting only categories where "
                "retrieval wins is a selective-subgroup violation."),
            "paper_text_hash": phash,
            "predicates": [{
                "predicate_id": "E04_CATEGORY_INTERACTION",
                "principle": "P7_EVIDENCE_CLOSURE",
                "natural_language": ("The reported category set must equal the full "
                    "declared set of 9 assertion-sensitive categories; no category "
                    "may be selectively omitted."),
                "trace_fields": ["protocol.declared_categories","protocol.reported_categories"],
                "condition": "len(protocol.reported_categories) == len(protocol.declared_categories)",
                "source_span": "Section 4.2",
                "confidence": 0.90,
            }],
            "universal_principles": ["P7_EVIDENCE_CLOSURE"],
            "coverage_threshold": 0.70,
            "self_hash": "",
        },
        {
            "contract_id": "CB_E06_CROSS_MODEL_ASYM",
            "source_paper": "clinicalbench_2605.11143",
            "family": "E06",
            "claim_text": ("Cross-model comparison uses 6 LLMs of very different "
                "sizes (4B to 431B). The gain-slope analysis acknowledges "
                "regression-to-mean. A fair comparator claim requires "
                "model-size asymmetry to be controlled for or declared."),
            "paper_text_hash": phash,
            "predicates": [{
                "predicate_id": "E06_MODEL_SIZE_CONTROL",
                "principle": "P8_COMPARATOR_FAIRNESS",
                "natural_language": ("Cross-model claims must either control for "
                    "model-size asymmetry (size-matched) or explicitly declare it "
                    "as a limitation. Selectively reporting only the model pair "
                    "with the largest gains is a resource-asymmetry violation."),
                "trace_fields": ["protocol.model_sizes","comparator_budgets"],
                "condition": "size_asymmetry_controlled OR size_asymmetry_justified",
                "source_span": "Section 4.7",
                "confidence": 0.80,
            }],
            "universal_principles": ["P8_COMPARATOR_FAIRNESS"],
            "coverage_threshold": 0.70,
            "self_hash": "",
        },
        {
            "contract_id": "CB_E01_BOOTSTRAP_AGG",
            "source_paper": "clinicalbench_2605.11143",
            "family": "E01",
            "claim_text": ("ClinicalBench uses BCa bootstrap 95% CIs, n=2000 "
                "resamples, seed 42, with patient-level cluster bootstrap over "
                "43 patients. Any reported CI must use the full declared "
                "resample set; a bootstrap resample subset is a "
                "selective-aggregation violation."),
            "paper_text_hash": phash,
            "predicates": [{
                "predicate_id": "E01_BOOTSTRAP_FIDELITY",
                "principle": "P6_AGGREGATION_FIDELITY",
                "natural_language": ("The bootstrap CI must use all declared "
                    "resamples (n=2000, seed 42); no resample subset may be "
                    "selectively used."),
                "trace_fields": ["protocol.bootstrap_n","protocol.bootstrap_seed","protocol.resample_used"],
                "condition": "protocol.resample_used == protocol.bootstrap_n",
                "source_span": "Methods: Bootstrap",
                "confidence": 0.90,
            }],
            "universal_principles": ["P6_AGGREGATION_FIDELITY"],
            "coverage_threshold": 0.70,
            "self_hash": "",
        },
    ]
    for c in contracts:
        payload = {k: v for k, v in c.items() if k != "self_hash"}
        c["self_hash"] = _sha(payload)
        (CONTRACTS_DIR / f"{c['contract_id']}.json").write_text(json.dumps(c, indent=2), encoding="utf-8")
    return contracts

def build_delta_attention_contracts() -> list:
    """DELTA_ATTENTION (arXiv 2605.18855). Paper protocol, no run data."""
    paper = load_paper("DELTA_ATTENTION")
    phash = _sha(paper)
    contracts = [
        {
            "contract_id": "DA_E06_BUDGET_SYMMETRY",
            "source_paper": "delta_attention_2605.18855",
            "family": "E06",
            "claim_text": ("The paper compares Baseline, AttnRes, Full AttnRes, "
                "Delta Block, and Delta AttnRes under IDENTICAL architecture, "
                "data, and hyperparameters per model scale. Any method "
                "comparison requires symmetric resource budgets; a "
                "method receiving a different step count, dataset, or "
                "learning rate while its PPL is still reported in the "
                "same comparison table is a resource-asymmetry "
                "violation."),
            "paper_text_hash": phash,
            "predicates": [{
                "predicate_id": "E06_BUDGET_SYMMETRY",
                "principle": "P8_COMPARATOR_FAIRNESS",
                "natural_language": ("All methods in a comparison table must "
                    "share the same resource budget (training steps, "
                    "dataset, learning rate, architecture). Selectively "
                    "giving one method a different budget while reporting "
                    "it in the same table is a comparator-resource "
                    "asymmetry violation."),
                "trace_fields": ["protocol.comparator_methods",
                                  "protocol.comparator_budgets",
                                  "protocol.budgets_symmetric"],
                "condition": "protocol.budgets_symmetric == True",
                "source_span": "Table 1",
                "confidence": 0.90,
            }],
            "universal_principles": ["P8_COMPARATOR_FAIRNESS"],
            "coverage_threshold": 0.70,
            "self_hash": "",
        },
        {
            "contract_id": "DA_E01_CROSS_METHOD_AGG",
            "source_paper": "delta_attention_2605.18855",
            "family": "E01",
            "claim_text": ("Per-scale results report a Val PPL for each "
                "method independently. Any cross-method 'mean PPL' "
                "aggregation at a scale must use ALL declared methods; "
                "selecting a subset is a selective-aggregation violation."),
            "paper_text_hash": phash,
            "predicates": [{
                "predicate_id": "E01_ALL_METHODS",
                "principle": "P6_AGGREGATION_FIDELITY",
                "natural_language": ("A cross-method mean PPL at a model "
                    "scale must be computed over ALL declared methods; "
                    "no method may be selectively omitted."),
                "trace_fields": ["protocol.declared_methods",
                                  "protocol.reported_methods",
                                  "outputs.reported_value"],
                "condition": "set(protocol.reported_methods) == set(protocol.declared_methods)",
                "source_span": "Table 1",
                "confidence": 0.85,
            }],
            "universal_principles": ["P6_AGGREGATION_FIDELITY"],
            "coverage_threshold": 0.70,
            "self_hash": "",
        },
    ]
    for c in contracts:
        payload = {k: v for k, v in c.items() if k != "self_hash"}
        c["self_hash"] = _sha(payload)
        (CONTRACTS_DIR / f"{c['contract_id']}.json").write_text(json.dumps(c, indent=2), encoding="utf-8")
    return contracts


def freeze_contracts() -> dict:
    ds = build_diffsynth_contracts()
    cb = save_clinicalbench_contracts()
    da = build_delta_attention_contracts()
    all_contracts = ds + cb + da
    freeze = {
        "stage": "R1-B1-Stage1b",
        "frozen_time": datetime.now().isoformat(),
        "contracts": [
            {"contract_id": c["contract_id"], "source_paper": c["source_paper"],
             "family": c["family"], "self_hash": c["self_hash"],
             "n_predicates": len(c["predicates"])}
            for c in all_contracts
        ],
    }
    freeze["freeze_sha256"] = _sha(freeze)
    (CONTRACTS_DIR / "STAGE1B_FREEZE_MANIFEST.json").write_text(json.dumps(freeze, indent=2), encoding="utf-8")
    return freeze

if __name__ == "__main__":
    f = freeze_contracts()
    print(f"Stage1b contracts frozen: {len(f['contracts'])}")
    for c in f["contracts"]:
        print(f"  {c['contract_id']}  [{c['family']}]  hash={c['self_hash'][:16]}...")
    print(f"Freeze SHA256: {f['freeze_sha256'][:32]}...")
