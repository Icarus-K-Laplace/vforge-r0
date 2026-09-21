"""
R0-D1-v2: Corrected SCIINVARIANT production verifier.

Fixes from R0-D1 invalid run:
  - No mutation_hint / benign_control parameters
  - No DEFAULT_PASS shortcut
  - Missing paper → ABSTAIN (not PASS)
  - Missing graph → ABSTAIN (not PASS)
  - Empty/insufficient contract → ABSTAIN (not PASS)
  - Real contract–graph requirement checking

Two-layer contract model:
  - Universal principles (P1-P8): pre-registered, frozen, abstract
  - Paper-induced invariants: derived from actual paper text, with source span
"""
from __future__ import annotations

import json
import hashlib
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass, field, asdict


# ──────────────────────────────────────────────────────────────
# Directories
# ──────────────────────────────────────────────────────────────
PROJECT_ROOT = Path(__file__).resolve().parent
PAPERS_DIR   = PROJECT_ROOT / "papers"
CONTRACTS_DIR = PROJECT_ROOT / "contracts"
GRAPHS_DIR   = PROJECT_ROOT / "graphs"

# ──────────────────────────────────────────────────────────────
# Verdict codes
# ──────────────────────────────────────────────────────────────
PASS                = "PASS"
FAIL                = "FAIL"
ABSTAIN             = "ABSTAIN"
PAPER_UNAVAILABLE   = "PAPER_UNAVAILABLE"
PAPER_PARSE_FAILURE = "PAPER_PARSE_FAILURE"
CONTRACT_INSUFFICIENT = "CONTRACT_INSUFFICIENT"
REPOSITORY_UNAVAILABLE = "REPOSITORY_UNAVAILABLE"
GRAPH_EXTRACTION_FAILURE = "GRAPH_EXTRACTION_FAILURE"
GRAPH_INSUFFICIENT   = "GRAPH_INSUFFICIENT"

# Pre-registered coverage threshold for PASS
PASS_COVERAGE_THRESHOLD = 0.70


@dataclass
class RequirementResult:
    requirement_id: str
    principle: str
    state: str          # SATISFIED | VIOLATED | UNOBSERVABLE
    evidence: str       # graph witness description
    confidence: float


@dataclass
class VerdictRecord:
    sample_id: str
    verdict: str
    n_requirements: int
    n_satisfied: int
    n_violated: int
    n_unobservable: int
    coverage: float    # (satisfied + violated) / total
    reason: str
    graph_witnesses: List[Dict] = field(default_factory=list)

    def to_dict(self) -> Dict:
        return asdict(self)


class R0D1v2Verifier:
    """
    Production R0-D1-v2 verifier.

    Verifies paper-derived normative contracts against observed
    repository protocol graphs. No mutation-era concepts.
    No permissive PASS fallbacks.
    """

    # ────────────────────────────────────────────────────────
    # Paper / contract loading
    # ────────────────────────────────────────────────────────
    def load_paper(self, paper_id: str) -> Optional[str]:
        """Return extracted paper text, or None if unavailable.

        A non-empty file is considered available. Content quality
        (enough text to derive claims) is checked at contract-construction
        time, not here.
        """
        path = PAPERS_DIR / f"{paper_id}.txt"
        if path.exists():
            try:
                text = path.read_text(encoding="utf-8")
                if len(text) > 0:
                    return text
            except Exception:
                pass
        return None

    def load_contract(self, paper_id: str) -> Optional[Dict]:
        """Return paper-derived contract dict, or None."""
        path = CONTRACTS_DIR / f"{paper_id}.json"
        if path.exists():
            try:
                return json.loads(path.read_text(encoding="utf-8"))
            except Exception:
                pass
        return None

    def load_graph(self, paper_id: str) -> Optional[Dict]:
        """Return observed protocol graph dict.

        Returns None when the graph file does not exist at all.
        Returns a dict with the special key _graph_insufficient=True when
        the file exists but is structurally too small to be meaningful.
        """
        path = GRAPHS_DIR / f"{paper_id}.json"
        if not path.exists():
            return None
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            nodes = data.get("nodes", [])
            if len(nodes) < 3:
                data["_graph_insufficient"] = True
                return data
            return data
        except Exception:
            return None

    # ────────────────────────────────────────────────────────
    # Requirement extraction from contract
    # ────────────────────────────────────────────────────────
    def extract_requirements(self, contract: Dict, paper_id: str) -> List[Dict]:
        """
        Extract testable normative requirements from a contract.

        Only requirements with a paper-specific source span are included
        as material requirements. Universal-only requirements are counted
        separately for coverage purposes.
        """
        invariants = contract.get("invariants", [])
        requirements = []
        paper_derived = [inv for inv in invariants if inv.get("source_paper_span") not in ("", "global", None)]
        universal    = [inv for inv in invariants if inv.get("source_paper_span") in ("", "global", None)]

        for inv in paper_derived:
            requirements.append({
                "req_id": inv.get("invariant_id", "REQ"),
                "principle": inv.get("source_principle", "P_UNKNOWN"),
                "type": inv.get("machine_readable", {}).get("type", ""),
                "check": inv.get("machine_readable", {}).get("check", ""),
                "required_evidence": inv.get("required_evidence", []),
                "failure_condition": inv.get("failure_condition", ""),
                "paper_span": inv.get("source_paper_span", ""),
                "source": "paper_derived",
            })
        for inv in universal:
            requirements.append({
                "req_id": inv.get("invariant_id", "REQ_U"),
                "principle": inv.get("source_principle", "P_UNIVERSAL"),
                "type": inv.get("machine_readable", {}).get("type", ""),
                "check": inv.get("machine_readable", {}).get("check", ""),
                "required_evidence": inv.get("required_evidence", []),
                "failure_condition": inv.get("failure_condition", ""),
                "paper_span": inv.get("source_paper_span", "global"),
                "source": "universal",
            })

        return requirements

    # ────────────────────────────────────────────────────────
    # Graph querying
    # ────────────────────────────────────────────────────────
    def query_graph(self, graph: Dict, evidence_types: List[str]) -> Tuple[bool, List[str]]:
        """
        Query the observed graph for required evidence types.

        Returns (evidence_found, observed_node_ids)
        """
        nodes = graph.get("nodes", [])
        found = []
        for node in nodes:
            node_type = node.get("node_type", "").upper()
            attrs = node.get("attributes", {})
            # Match evidence type against node type or attribute keys
            for ev in evidence_types:
                if ev.upper() in node_type or ev.upper() in str(attrs).upper():
                    found.append(node.get("node_id", "unknown"))
                    break
        return (len(found) > 0, found)

    # ────────────────────────────────────────────────────────
    # Per-requirement evaluation
    # ────────────────────────────────────────────────────────
    def evaluate_requirement(
        self, req: Dict, graph: Dict, paper_text: Optional[str]
    ) -> RequirementResult:
        """Evaluate a single normative requirement against the graph."""
        req_id = req.get("req_id", "REQ")
        principle = req.get("principle", "P")
        evidence_types = req.get("required_evidence", [])
        graph_found, observed_nodes = self.query_graph(graph, evidence_types)

        # No graph available → UNOBSERVABLE
        if graph is None or "error" in graph:
            return RequirementResult(req_id, principle, "UNOBSERVABLE", "No protocol graph available", 0.0)

        # Check principle-specific logic
        if principle == "P1_INDEPENDENCE":
            has_split = any(n.get("node_type", "").upper() == "SPLIT" for n in graph.get("nodes", []))
            if has_split:
                return RequirementResult(req_id, principle, "SATISFIED", "Split node present in graph", 0.8)
            elif graph_found:
                return RequirementResult(req_id, principle, "UNOBSERVABLE", "Evidence present but no explicit split node", 0.4)
            else:
                return RequirementResult(req_id, principle, "UNOBSERVABLE", "No split evidence in graph", 0.2)

        elif principle == "P4_SELECTION_SEPARATION":
            has_select  = any(n.get("node_type", "").upper() == "SELECT" for n in graph.get("nodes", []))
            has_evaluate = any(n.get("node_type", "").upper() == "EVALUATE" for n in graph.get("nodes", []))
            # Check attribute values: selection source must not be test set
            sel_source = None
            for n in graph.get("nodes", []):
                attrs = n.get("attributes", {})
                if "selection_metric_source" in attrs or "checkpoint_selection" in attrs:
                    sel_source = str(attrs.get("selection_metric_source", attrs.get("checkpoint_selection", ""))).lower()
                    break
            if sel_source in ("test", "test_set", "test data", "testset", "testaccuracy", "test_accuracy"):
                return RequirementResult(req_id, principle, "VIOLATED",
                                         f"Selection source is test data (observed: {sel_source}); test set must be held out", 0.9)
            elif has_select and has_evaluate:
                return RequirementResult(req_id, principle, "SATISFIED", "Separate SELECT and EVALUATE nodes, no test-set selection observed", 0.85)
            elif has_select or has_evaluate:
                return RequirementResult(req_id, principle, "UNOBSERVABLE", "Only one of SELECT/EVALUATE present", 0.4)
            else:
                return RequirementResult(req_id, principle, "UNOBSERVABLE", "No selection or evaluation nodes", 0.2)

        elif principle == "P3_SYMMETRY":
            model_count = sum(1 for n in graph.get("nodes", []) if n.get("node_type", "").upper() == "MODEL")
            if model_count >= 2:
                return RequirementResult(req_id, principle, "UNOBSERVABLE",
                                         f"{model_count} models present; symmetry check requires config inspection", 0.5)
            else:
                return RequirementResult(req_id, principle, "UNOBSERVABLE",
                                         "Single model; symmetry not observable", 0.3)

        elif principle in ("P6_AGGREGATION_FIDELITY", "P7_EVIDENCE_CLOSURE"):
            # P6: check if aggregation rule is observable in graph attributes
            if principle == "P6_AGGREGATION_FIDELITY":
                # Look for aggregation_rule attribute
                agg_rule = None
                for n in graph.get("nodes", []):
                    attrs = n.get("attributes", {})
                    if "aggregation_rule" in attrs:
                        agg_rule = str(attrs["aggregation_rule"]).lower()
                        break
                check = req.get("check", "")
                if agg_rule is not None:
                    # Check if the required aggregation matches what was observed
                    # Extract expected rule from the check string, e.g. "aggregation_rule == mean"
                    import re
                    expected_rule = None
                    m = re.search(r'aggregation_rule\s*==\s*(\w+)', check)
                    if m:
                        expected_rule = m.group(1)
                    if expected_rule and agg_rule != expected_rule:
                        return RequirementResult(req_id, principle, "VIOLATED",
                                                 f"Aggregation rule observed={agg_rule}, required={expected_rule}", 0.9)
                    elif expected_rule:
                        return RequirementResult(req_id, principle, "SATISFIED",
                                                 f"Aggregation rule {agg_rule} matches required {expected_rule}", 0.85)
                    else:
                        return RequirementResult(req_id, principle, "UNOBSERVABLE",
                                                 f"Aggregation rule observed={agg_rule} but expected value not specified in check", 0.4)
                if graph_found:
                    return RequirementResult(req_id, principle, "UNOBSERVABLE",
                                             "Evidence nodes present but aggregation rule not in attributes", 0.4)
                return RequirementResult(req_id, principle, "UNOBSERVABLE",
                                         "No aggregation evidence in graph", 0.2)
            # P7: evidence closure
            if graph_found:
                return RequirementResult(req_id, principle, "UNOBSERVABLE",
                                         "Evidence nodes present but closure check requires full metric audit", 0.4)
            return RequirementResult(req_id, principle, "UNOBSERVABLE",
                                     "No evidence nodes for closure check", 0.2)

        elif principle == "P8_STATISTICAL_SUFFICIENCY":
            has_metric = any(n.get("node_type", "").upper() == "METRIC" for n in graph.get("nodes", []))
            if has_metric:
                return RequirementResult(req_id, principle, "UNOBSERVABLE",
                                         "Metric nodes present; significance not directly observable", 0.4)
            else:
                return RequirementResult(req_id, principle, "UNOBSERVABLE",
                                         "No metric nodes", 0.2)

        # Fallback: graph found → partial satisfaction
        if graph_found:
            return RequirementResult(req_id, principle, "UNOBSERVABLE",
                                     f"Evidence nodes found: {observed_nodes[:3]}; requirement not directly verifiable", 0.4)
        return RequirementResult(req_id, principle, "UNOBSERVABLE",
                                 "No relevant evidence in graph", 0.1)

    # ────────────────────────────────────────────────────────
    # Full verification
    # ────────────────────────────────────────────────────────
    def verify(self, paper_id: str) -> VerdictRecord:
        """
        Full R0-D1-v2 verification for one sample.

        No shortcut PASS. ABSTAIN is the safe default when evidence is
        insufficient. FAIL only when a material requirement is confirmed
        violated.
        """
        graph = self.load_graph(paper_id)
        paper_text = self.load_paper(paper_id)
        contract = self.load_contract(paper_id)

        # 1. Paper unavailable → ABSTAIN (PAPER_UNAVAILABLE)
        if paper_text is None:
            return VerdictRecord(
                sample_id=paper_id,
                verdict=PAPER_UNAVAILABLE,
                n_requirements=0, n_satisfied=0, n_violated=0, n_unobservable=0,
                coverage=0.0,
                reason="Paper text not available; cannot derive normative contract from paper.",
            )

        # 2. Contract missing or insufficient → ABSTAIN
        if contract is None:
            return VerdictRecord(
                sample_id=paper_id,
                verdict=CONTRACT_INSUFFICIENT,
                n_requirements=0, n_satisfied=0, n_violated=0, n_unobservable=0,
                coverage=0.0,
                reason="No normative contract found for this paper.",
            )

        # 3. Check contract has paper-derived content (not just universal)
        requirements = self.extract_requirements(contract, paper_id)
        paper_derived = [r for r in requirements if r["source"] == "paper_derived"]

        if not paper_derived and not requirements:
            return VerdictRecord(
                sample_id=paper_id,
                verdict=CONTRACT_INSUFFICIENT,
                n_requirements=0, n_satisfied=0, n_violated=0, n_unobservable=0,
                coverage=0.0,
                reason="Contract has no testable requirements.",
            )

        # 4. Graph unavailable or insufficient → ABSTAIN
        if graph is None:
            graph_file_exists = (GRAPHS_DIR / f"{paper_id}.json").exists()
            if graph_file_exists:
                return VerdictRecord(
                    sample_id=paper_id,
                    verdict=ABSTAIN,
                    n_requirements=len(requirements),
                    n_satisfied=0, n_violated=0, n_unobservable=len(requirements),
                    coverage=0.0,
                    reason="Graph file exists but is insufficient (empty, corrupt, or too small).",
                )
            else:
                return VerdictRecord(
                    sample_id=paper_id,
                    verdict=REPOSITORY_UNAVAILABLE,
                    n_requirements=len(requirements),
                    n_satisfied=0, n_violated=0, n_unobservable=len(requirements),
                    coverage=0.0,
                    reason="Repository graph not available; cannot verify contract against observed protocol.",
                )
        if graph.get("_graph_insufficient"):
            return VerdictRecord(
                sample_id=paper_id,
                verdict=ABSTAIN,
                n_requirements=len(requirements),
                n_satisfied=0, n_violated=0, n_unobservable=len(requirements),
                coverage=0.0,
                reason=f"Graph is structurally insufficient (n_nodes={len(graph.get('nodes', []))}); insufficient observable evidence to verify.",
            )

        # 5. Evaluate all requirements
        results: List[RequirementResult] = []
        for req in requirements:
            res = self.evaluate_requirement(req, graph, paper_text)
            results.append(res)

        n_sat  = sum(1 for r in results if r.state == "SATISFIED")
        n_viol = sum(1 for r in results if r.state == "VIOLATED")
        n_unob = sum(1 for r in results if r.state == "UNOBSERVABLE")
        total  = len(results)

        # Coverage = fraction of requirements that were checkable (SAT or VIOL)
        coverage = (n_sat + n_viol) / total if total > 0 else 0.0

        witnesses = [
            {"req": r.requirement_id, "state": r.state, "evidence": r.evidence, "conf": r.confidence}
            for r in results if r.state in ("SATISFIED", "VIOLATED")
        ]

        # 6. Verdict logic (no permissive PASS)
        if n_viol > 0:
            return VerdictRecord(
                sample_id=paper_id,
                verdict=FAIL,
                n_requirements=total, n_satisfied=n_sat, n_violated=n_viol, n_unobservable=n_unob,
                coverage=coverage,
                reason=f"{n_viol} requirement(s) violated. First: {results[[r.state for r in results].index('VIOLATED')].evidence[:80]}",
                graph_witnesses=witnesses,
            )

        # No confirmed violation; check coverage for PASS eligibility
        # A sample with only universal requirements (no paper-derived) cannot PASS
        has_paper_derived_sat = any(
            r.state == "SATISFIED" and
            next((req for req in requirements if req["req_id"] == r.requirement_id), {}).get("source") == "paper_derived"
            for r in results
        )

        if coverage >= PASS_COVERAGE_THRESHOLD and has_paper_derived_sat:
            return VerdictRecord(
                sample_id=paper_id,
                verdict=PASS,
                n_requirements=total, n_satisfied=n_sat, n_violated=n_viol, n_unobservable=n_unob,
                coverage=coverage,
                reason=f"All {n_sat} checkable requirements satisfied (coverage={coverage:.2f}).",
                graph_witnesses=witnesses,
            )

        return VerdictRecord(
            sample_id=paper_id,
            verdict=ABSTAIN,
            n_requirements=total, n_satisfied=n_sat, n_violated=n_viol, n_unobservable=n_unob,
            coverage=coverage,
            reason=f"No confirmed violation; coverage={coverage:.2f} < threshold={PASS_COVERAGE_THRESHOLD} or no paper-derived SATISFIED.",
            graph_witnesses=witnesses,
        )

    # ────────────────────────────────────────────────────────
    # Batch run
    # ────────────────────────────────────────────────────────
    def run_batch(self, sample_ids: List[str]) -> List[VerdictRecord]:
        """Run verification on a list of sample IDs."""
        print(f"\nRunning R0-D1-v2 verifier on {len(sample_ids)} samples...")
        records = []
        for sid in sample_ids:
            rec = self.verify(sid)
            records.append(rec)
        return records

    @staticmethod
    def summarize(records: List[VerdictRecord]) -> Dict:
        from collections import Counter
        vc = Counter(r.verdict for r in records)
        n = len(records)
        return {
            "total": n,
            "verdicts": dict(vc),
            "pass_rate": vc.get("PASS", 0) / n if n else 0,
            "fail_rate": vc.get("FAIL", 0) / n if n else 0,
            "abstain_rate": sum(
                vc.get(v, 0) for v in [
                    ABSTAIN, PAPER_UNAVAILABLE, PAPER_PARSE_FAILURE,
                    CONTRACT_INSUFFICIENT, REPOSITORY_UNAVAILABLE,
                    GRAPH_EXTRACTION_FAILURE, GRAPH_INSUFFICIENT
                ]
            ) / n if n else 0,
        }


if __name__ == "__main__":
    # Quick smoke test with a few known IDs
    verifier = R0D1v2Verifier()

    # Check a paper with extracted text
    paper_ids = [p.stem for p in PAPERS_DIR.glob("*.txt")]
    print(f"Available papers: {len(paper_ids)}")

    # Verify first 5
    if paper_ids:
        records = verifier.run_batch(paper_ids[:5])
        for r in records:
            print(f"  {r.sample_id}: {r.verdict} (coverage={r.coverage:.2f}) — {r.reason[:60]}")
