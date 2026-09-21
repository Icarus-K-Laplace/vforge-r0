# R0-D1-v2 Adversarial Unit Tests T1-T8
#
# Protocol-mandated mock adversarial tests that must pass before any
# external qualification run.
#
# Run: python tests_r0d1v2.py
#
# T1: Paper says mean over 5 seeds, code reports best seed.        Expected FAIL
# T2: Paper says mean over 5 seeds, code computes mean over 5.    Expected PASS
# T3: Paper says test set only for final eval, code selects via   Expected FAIL
#     test accuracy.
# T4: Same paper, code selects via validation set.                 Expected PASS
# T5: No paper text.                                               Expected PAPER_UNAVAILABLE
# T6: No repository graph.                                         Expected REPOSITORY_UNAVAILABLE
# T7: Contract exists, graph lacks observable evidence.            Expected ABSTAIN
# T8: Empty contract.                                              Expected CONTRACT_INSUFFICIENT

from __future__ import annotations

import sys
import json
import tempfile
import shutil
from pathlib import Path
from typing import Dict, Any

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from verifier_r0d1v2 import (
    R0D1v2Verifier,
    PASS, FAIL, ABSTAIN,
    PAPER_UNAVAILABLE, CONTRACT_INSUFFICIENT,
    REPOSITORY_UNAVAILABLE, GRAPH_EXTRACTION_FAILURE,
)

PROJECT_ROOT = Path(__file__).resolve().parent.parent


class TestFixtures:
    """Create temp paper/contract/graph files for testing."""

    def __init__(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.papers = self.tmp / "papers"
        self.contracts = self.tmp / "contracts"
        self.graphs = self.tmp / "graphs"
        self.papers.mkdir()
        self.contracts.mkdir()
        self.graphs.mkdir()

    def make_paper(self, paper_id: str, text: str):
        (self.papers / f"{paper_id}.txt").write_text(text, encoding="utf-8")

    def make_contract(self, paper_id: str, contract: Dict):
        (self.contracts / f"{paper_id}.json").write_text(json.dumps(contract), encoding="utf-8")

    def make_graph(self, paper_id: str, node_types: list, attrs: dict = None):
        nodes = []
        for i, nt in enumerate(node_types, 1):
            node = {
                "node_id": f"N{i:03d}",
                "node_type": nt,
                "attributes": attrs or {},
            }
            nodes.append(node)
        graph = {"nodes": nodes, "edges": [], "metadata": {"n_nodes": len(nodes)}}
        (self.graphs / f"{paper_id}.json").write_text(json.dumps(graph), encoding="utf-8")

    def paper_verifier(self) -> R0D1v2Verifier:
        """Return a verifier pointed at our temp dirs."""
        # Monkey-patch the module-level directories
        import verifier_r0d1v2
        orig_papers, orig_contracts, orig_graphs = (
            verifier_r0d1v2.PAPERS_DIR,
            verifier_r0d1v2.CONTRACTS_DIR,
            verifier_r0d1v2.GRAPHS_DIR,
        )
        verifier_r0d1v2.PAPERS_DIR   = self.papers
        verifier_r0d1v2.CONTRACTS_DIR = self.contracts
        verifier_r0d1v2.GRAPHS_DIR  = self.graphs
        v = R0D1v2Verifier()
        # Restore (verifier uses module-level dirs at call time)
        verifier_r0d1v2.PAPERS_DIR   = orig_papers
        verifier_r0d1v2.CONTRACTS_DIR = orig_contracts
        verifier_r0d1v2.GRAPHS_DIR  = orig_graphs
        return v

    def cleanup(self):
        shutil.rmtree(self.tmp, ignore_errors=True)


def make_paper_derived_contract(
    principles: Dict[str, str],
    seed_info: Dict[str, Any] = None,
) -> Dict:
    """
    Build a paper-derived contract with actual source spans.
    principles: {"P4_SELECTION_SEPARATION": "Paper span text...", ...}
    """
    invariants = []
    for i, (principle, span) in enumerate(principles.items(), 1):
        invariants.append({
            "invariant_id": f"INV_{i:03d}",
            "source_principle": principle,
            "natural_language": f"{principle} constraint derived from paper",
            "machine_readable": {"type": principle.lower().split("_")[-1], "check": "check"},
            "source_paper_span": span,   # NOT "global" = paper-derived
            "required_evidence": ["select", "evaluate"] if "P4" in principle else ["train_ids", "test_ids"],
            "failure_condition": "Requirement violated",
            "abstention_condition": "Evidence missing",
            "confidence": 0.8,
        })
    return {
        "contract_id": "TEST_CONTRACT",
        "source_paper": "TEST",
        "invariants": invariants,
        "metadata": {"n_invariants": len(invariants)},
    }


def make_graph(node_types: list, attrs: dict = None) -> Dict:
    nodes = []
    for i, nt in enumerate(node_types, 1):
        nodes.append({
            "node_id": f"N{i:03d}",
            "node_type": nt,
            "attributes": attrs or {},
        })
    return {"nodes": nodes, "edges": [], "metadata": {"n_nodes": len(nodes)}}


def run_test(label: str, fn, expected: str, fixtures: TestFixtures, paper_id: str = "T") -> bool:
    """Run a single test, restore module dirs, check verdict."""
    import verifier_r0d1v2
    orig = (verifier_r0d1v2.PAPERS_DIR, verifier_r0d1v2.CONTRACTS_DIR, verifier_r0d1v2.GRAPHS_DIR)

    # Set up temp dirs for this test
    verifier_r0d1v2.PAPERS_DIR   = fixtures.papers
    verifier_r0d1v2.CONTRACTS_DIR = fixtures.contracts
    verifier_r0d1v2.GRAPHS_DIR  = fixtures.graphs

    # Create fixtures
    fn(fixtures)
    v = R0D1v2Verifier()
    rec = v.verify(paper_id)

    # Restore
    (verifier_r0d1v2.PAPERS_DIR, verifier_r0d1v2.CONTRACTS_DIR, verifier_r0d1v2.GRAPHS_DIR) = orig

    ok = rec.verdict == expected
    mark = "✅" if ok else "❌"
    print(f"  {mark} {label}: got={rec.verdict} expected={expected}  ({rec.reason[:60]})")
    return ok


def T1(fx: TestFixtures):
    """Paper: mean over 5 seeds. Code: reports best seed. Expected: FAIL."""
    fx.make_paper("T1", "We report the mean accuracy across five random seeds. Each seed is run on independent splits.")
    fx.make_contract("T1", {
        "contract_id": "C_T1",
        "invariants": [
            {
                "invariant_id": "INV_T1_1",
                "source_principle": "P6_AGGREGATION_FIDELITY",
                "natural_language": "Reported value must equal mean over declared seed count",
                "machine_readable": {"type": "aggregation", "check": "aggregation_rule == mean && seed_count == 5"},
                "source_paper_span": "We report the mean accuracy across five random seeds",
                "required_evidence": ["aggregate", "metric"],
                "failure_condition": "Code uses best seed instead of mean",
                "abstention_condition": "No aggregation evidence",
                "confidence": 0.9,
            },
            {
                "invariant_id": "INV_T1_2",
                "source_principle": "P1_INDEPENDENCE",
                "natural_language": "Each seed uses independent data splits",
                "machine_readable": {"type": "independence", "check": "seed_splits_disjoint"},
                "source_paper_span": "Each seed is run on independent splits",
                "required_evidence": ["split"],
                "failure_condition": "Split overlap between seeds",
                "abstention_condition": "No split information",
                "confidence": 0.8,
            },
        ],
        "metadata": {"n_invariants": 2},
    })
    # Graph: best-seed selection node present, no mean aggregation
    fx.make_graph("T1", [
        "SELECT", "METRIC", "MODEL",
    ], attrs={"aggregation_rule": "best", "declared_seeds": 5, "reported_seed": 3})


def T2(fx: TestFixtures):
    """Paper: mean over 5 seeds. Code: mean over 5 seeds. Expected: PASS."""
    fx.make_paper("T2", "We report the mean accuracy across five random seeds. Each seed is run on independent splits.")
    fx.make_contract("T2", {
        "contract_id": "C_T2",
        "invariants": [
            {
                "invariant_id": "INV_T2_1",
                "source_principle": "P6_AGGREGATION_FIDELITY",
                "natural_language": "Reported value must equal mean over declared seed count",
                "machine_readable": {"type": "aggregation", "check": "aggregation_rule == mean && seed_count == 5"},
                "source_paper_span": "We report the mean accuracy across five random seeds",
                "required_evidence": ["aggregate", "metric"],
                "failure_condition": "Code uses best seed instead of mean",
                "abstention_condition": "No aggregation evidence",
                "confidence": 0.9,
            },
            {
                "invariant_id": "INV_T2_2",
                "source_principle": "P1_INDEPENDENCE",
                "natural_language": "Each seed uses independent data splits",
                "machine_readable": {"type": "independence", "check": "seed_splits_disjoint"},
                "source_paper_span": "Each seed is run on independent splits",
                "required_evidence": ["split"],
                "failure_condition": "Split overlap between seeds",
                "abstention_condition": "No split information",
                "confidence": 0.8,
            },
        ],
        "metadata": {"n_invariants": 2},
    })
    fx.make_graph("T2", [
        "SELECT", "AGGREGATE", "METRIC", "SPLIT", "MODEL",
    ], attrs={"aggregation_rule": "mean", "declared_seeds": 5})


def T3(fx: TestFixtures):
    """Paper: test set only for final eval. Code: checkpoint selection via test acc. Expected: FAIL."""
    fx.make_paper("T3", "The test set is used exclusively for final evaluation. Model selection is performed on a held-out validation set.")
    fx.make_contract("T3", {
        "contract_id": "C_T3",
        "invariants": [
            {
                "invariant_id": "INV_T3_1",
                "source_principle": "P4_SELECTION_SEPARATION",
                "natural_language": "Model selection must not use the test set",
                "machine_readable": {"type": "selection_separation", "check": "selection_data != test_data"},
                "source_paper_span": "The test set is used exclusively for final evaluation",
                "required_evidence": ["select", "evaluate"],
                "failure_condition": "Checkpoint selected using test accuracy",
                "abstention_condition": "No selection procedure in code",
                "confidence": 0.9,
            },
        ],
        "metadata": {"n_invariants": 1},
    })
    # Code uses test acc for selection — SELECT node points to test data
    fx.make_graph("T3", [
        "SELECT", "EVALUATE", "METRIC", "MODEL",
    ], attrs={"selection_metric_source": "test_set", "checkpoint_selection": "test_accuracy"})


def T4(fx: TestFixtures):
    """Same paper, code selects using validation set. Expected: PASS."""
    fx.make_paper("T4", "The test set is used exclusively for final evaluation. Model selection is performed on a held-out validation set.")
    fx.make_contract("T4", {
        "contract_id": "C_T4",
        "invariants": [
            {
                "invariant_id": "INV_T4_1",
                "source_principle": "P4_SELECTION_SEPARATION",
                "natural_language": "Model selection must use validation set, not test set",
                "machine_readable": {"type": "selection_separation", "check": "selection_data == validation_data"},
                "source_paper_span": "Model selection is performed on a held-out validation set",
                "required_evidence": ["select", "evaluate"],
                "failure_condition": "Test data used for selection",
                "abstention_condition": "No selection procedure",
                "confidence": 0.9,
            },
            {
                "invariant_id": "INV_T4_2",
                "source_principle": "P1_INDEPENDENCE",
                "natural_language": "Validation and test sets must be disjoint",
                "machine_readable": {"type": "independence", "check": "val_set ∩ test_set = ∅"},
                "source_paper_span": "held-out validation set",
                "required_evidence": ["split"],
                "failure_condition": "Overlap between val and test",
                "abstention_condition": "No split info",
                "confidence": 0.85,
            },
        ],
        "metadata": {"n_invariants": 2},
    })
    fx.make_graph("T4", [
        "SELECT", "EVALUATE", "SPLIT", "MODEL", "METRIC",
    ], attrs={"selection_metric_source": "validation_set", "checkpoint_selection": "validation_accuracy"})


def T5(fx: TestFixtures):
    """No paper text. Expected: PAPER_UNAVAILABLE."""
    # No paper created
    fx.make_contract("T5", {"contract_id": "C_T5", "invariants": []})
    fx.make_graph("T5", ["MODEL"])


def T6(fx: TestFixtures):
    """No repository graph. Expected: REPOSITORY_UNAVAILABLE."""
    fx.make_paper("T6", "We train a model and evaluate on a held-out test set. Results are averaged over three seeds.")
    fx.make_contract("T6", {
        "contract_id": "C_T6",
        "invariants": [
            {
                "invariant_id": "INV_T6_1",
                "source_principle": "P1_INDEPENDENCE",
                "natural_language": "Train and test sets are disjoint",
                "machine_readable": {"type": "independence", "check": "train ∩ test = ∅"},
                "source_paper_span": "evaluate on a held-out test set",
                "required_evidence": ["split"],
                "failure_condition": "Overlap",
                "abstention_condition": "No split info",
                "confidence": 0.8,
            },
        ],
        "metadata": {"n_invariants": 1},
    })
    # No graph created


def T7(fx: TestFixtures):
    """Contract exists, graph lacks evidence. Expected: ABSTAIN (not PASS)."""
    fx.make_paper("T7", "We evaluate our method against three baselines using accuracy on the test set.")
    fx.make_contract("T7", {
        "contract_id": "C_T7",
        "invariants": [
            {
                "invariant_id": "INV_T7_1",
                "source_principle": "P3_SYMMETRY",
                "natural_language": "All baselines evaluated under identical conditions",
                "machine_readable": {"type": "symmetry", "check": "configs(method_a)==configs(method_b)"},
                "source_paper_span": "evaluated against three baselines using accuracy",
                "required_evidence": ["model", "config"],
                "failure_condition": "Config mismatch detected",
                "abstention_condition": "Config not observable",
                "confidence": 0.75,
            },
            {
                "invariant_id": "INV_T7_2",
                "source_principle": "P7_EVIDENCE_CLOSURE",
                "natural_language": "All reported metrics have underlying raw data",
                "machine_readable": {"type": "closure", "check": "required ⊆ available"},
                "source_paper_span": "accuracy on the test set",
                "required_evidence": ["metric", "data"],
                "failure_condition": "Missing raw metrics",
                "abstention_condition": "No metric nodes",
                "confidence": 0.7,
            },
        ],
        "metadata": {"n_invariants": 2},
    })
    # Graph exists but has no config or metric nodes
    fx.make_graph("T7", ["MODEL"])


def T8(fx: TestFixtures):
    """Empty contract. Expected: CONTRACT_INSUFFICIENT (not PASS)."""
    fx.make_paper("T8", "We present a new method for classification.")
    fx.make_contract("T8", {"contract_id": "C_T8", "invariants": []})
    fx.make_graph("T8", ["MODEL", "METRIC"])


# ──────────────────────────────────────────────────────────────
# Run all tests
# ──────────────────────────────────────────────────────────────
def run_all():
    print("=" * 60)
    print("R0-D1-v2 Adversarial Unit Tests T1–T8")
    print("=" * 60)

    tests = [
        ("T1", T1, FAIL,                    "Best seed in code, paper says mean. Expected FAIL"),
        ("T2", T2, PASS,                     "Mean in code, paper says mean. Expected PASS"),
        ("T3", T3, FAIL,                     "Test-set selection in code. Expected FAIL"),
        ("T4", T4, PASS,                     "Validation-set selection in code. Expected PASS"),
        ("T5", T5, PAPER_UNAVAILABLE,        "No paper text. Expected PAPER_UNAVAILABLE"),
        ("T6", T6, REPOSITORY_UNAVAILABLE,   "No graph. Expected REPOSITORY_UNAVAILABLE"),
        ("T7", T7, ABSTAIN,                  "Graph lacks evidence. Expected ABSTAIN"),
        ("T8", T8, CONTRACT_INSUFFICIENT,    "Empty contract. Expected CONTRACT_INSUFFICIENT"),
    ]

    fx = TestFixtures()
    all_passed = True

    for label, setup_fn, expected, desc in tests:
        # Use a fresh paper_id per test to avoid file collisions
        paper_id = label
        # Clean up any existing test files
        for d in [fx.papers, fx.contracts, fx.graphs]:
            for f in d.glob(f"{label}.*"):
                f.unlink()

        ok = run_test(
            label=f"T{label[1]}",
            fn=setup_fn,
            expected=expected,
            fixtures=fx,
            paper_id=paper_id,
        )
        all_passed = all_passed and ok

    fx.cleanup()

    print("=" * 60)
    if all_passed:
        print("RESULT: ALL 8 TESTS PASSED ✅")
    else:
        print("RESULT: SOME TESTS FAILED ❌")
    print("=" * 60)
    return all_passed


if __name__ == "__main__":
    success = run_all()
    sys.exit(0 if success else 1)
