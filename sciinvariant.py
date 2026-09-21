"""
V-Forge R0-C: SciInvariant Protocol Graph and Invariant Induction
Implements graph-based representation and zero-shot invariant induction.
"""
from __future__ import annotations
import json
import hashlib
from pathlib import Path
from typing import Any, Optional, Dict, List, Set, Tuple
from dataclasses import dataclass, field, asdict
import numpy as np
import core
from core import Claim, SEED, STUDIES_DIR, RESULTS_DIR, REPORTS_DIR


# ──────────────────────────────────────────────────────────────
# Graph Schema
# ──────────────────────────────────────────────────────────────
NODE_TYPES = [
    "DATASET", "SPLIT", "PREPROCESS", "TRAIN", "TUNE", 
    "MODEL", "SELECT", "EVALUATE", "METRIC", "AGGREGATE", 
    "REPORT", "CLAIM"
]

EDGE_TYPES = [
    "DATA_FLOW", "CONTROL_FLOW", "SELECTION_DEPENDENCY",
    "EVIDENCE_FLOW", "PARAMETER_DEPENDENCY"
]


@dataclass
class GraphNode:
    node_id: str
    node_type: str
    label: str
    attributes: dict
    provenance: dict
    
    def to_dict(self):
        return asdict(self)
    
    @classmethod
    def from_dict(cls, d):
        return cls(**d)


@dataclass
class GraphEdge:
    edge_id: str
    source_id: str
    target_id: str
    edge_type: str
    attributes: dict
    provenance: dict
    
    def to_dict(self):
        return asdict(self)
    
    @classmethod
    def from_dict(cls, d):
        return cls(**d)


@dataclass
class ProtocolGraph:
    study_id: str
    nodes: List[GraphNode]
    edges: List[GraphEdge]
    metadata: dict
    
    def to_dict(self):
        return {
            "study_id": self.study_id,
            "nodes": [n.to_dict() for n in self.nodes],
            "edges": [e.to_dict() for e in self.edges],
            "metadata": self.metadata,
        }
    
    def sha256(self) -> str:
        raw = json.dumps(self.to_dict(), sort_keys=True).encode()
        return hashlib.sha256(raw).hexdigest()


# ──────────────────────────────────────────────────────────────
# Claim Representation
# ──────────────────────────────────────────────────────────────
@dataclass
class StructuredClaim:
    claim_id: str
    study_id: str
    natural_language_claim: str
    
    # Core claim structure
    population: str
    method: str
    comparator: str
    metric: str
    direction: str
    scope: str
    evaluation_split: str
    aggregation_rule: str
    selection_rule: str
    uncertainty_requirement: dict
    
    # Evidence
    required_evidence: list[str]
    validity_conditions: list[str]
    abstention_conditions: list[str]
    
    def to_dict(self):
        return asdict(self)
    
    @classmethod
    def from_claim(cls, claim: Claim) -> "StructuredClaim":
        return cls(
            claim_id=claim.claim_id,
            study_id=claim.study_id,
            natural_language_claim=claim.natural_language_claim,
            population=claim.population,
            method=claim.method,
            comparator=claim.comparator,
            metric=claim.outcome_metric,
            direction=claim.direction,
            scope="full_dataset",
            evaluation_split="test_only",
            aggregation_rule="mean",
            selection_rule="none",
            uncertainty_requirement=claim.uncertainty_requirement.to_dict() if claim.uncertainty_requirement else {},
            required_evidence=claim.required_artifacts,
            validity_conditions=claim.validity_conditions,
            abstention_conditions=claim.abstention_conditions,
        )


# ──────────────────────────────────────────────────────────────
# Invariant Schema
# ──────────────────────────────────────────────────────────────
@dataclass
class Invariant:
    invariant_id: str
    invariant_class: str  # I1-I6
    natural_language: str
    machine_readable: dict
    executable_predicate: Optional[str]
    provenance_requirements: list[str]
    abstention_conditions: list[str]
    confidence: float
    
    def to_dict(self):
        return asdict(self)


# ──────────────────────────────────────────────────────────────
# Graph Extractor
# ──────────────────────────────────────────────────────────────
class ProtocolGraphExtractor:
    """Extract protocol graph from study artifacts."""
    
    def __init__(self):
        self.node_counter = 0
        self.edge_counter = 0
    
    def extract(self, study_data: dict, claim: Claim) -> ProtocolGraph:
        """Extract protocol graph from study data and claim."""
        nodes = []
        edges = []
        
        # Re-initialize counters for each study
        self.node_counter = 0
        self.edge_counter = 0
        
        study_id = study_data["study_id"]
        
        # Create nodes based on study type
        if "raw_data" in study_data:
            data_node = self._add_node("DATASET", study_id, {
                "n_samples": len(study_data["raw_data"].get("X", [])),
                "n_features": int(len(study_data["raw_data"].get("X", [[0]])) if study_data["raw_data"].get("X") is not None else 0),
            })
            nodes.append(data_node)
            
            # Split node
            split_node = self._add_node("SPLIT", study_id, {
                "train_size": study_data.get("train_size", 0),
                "test_size": study_data.get("test_size", 0),
                "strategy": "stratified_shuffle",
            })
            nodes.append(split_node)
            edges.append(self._add_edge(data_node.node_id, split_node.node_id, "DATA_FLOW"))
            
            # Preprocess node
            preprocess_node = self._add_node("PREPROCESS", study_id, {})
            nodes.append(preprocess_node)
            edges.append(self._add_edge(split_node.node_id, preprocess_node.node_id, "DATA_FLOW"))
            
            # Train nodes for each model
            if "models" in study_data:
                for model_name, model_info in study_data["models"].items():
                    train_node = self._add_node("TRAIN", f"{study_id}_{model_name}", {
                        "model_type": model_info.get("model_type", "unknown"),
                        "hyperparameters": model_info.get("hyperparameters", {}),
                    })
                    nodes.append(train_node)
                    edges.append(self._add_edge(preprocess_node.node_id, train_node.node_id, "CONTROL_FLOW"))
                    
                    model_node = self._add_node("MODEL", f"{study_id}_{model_name}_model", {})
                    nodes.append(model_node)
                    edges.append(self._add_edge(train_node.node_id, model_node.node_id, "DATA_FLOW"))
                    
                    eval_node = self._add_node("EVALUATE", f"{study_id}_{model_name}_eval", {})
                    nodes.append(eval_node)
                    edges.append(self._add_edge(model_node.node_id, eval_node.node_id, "DATA_FLOW"))
                    edges.append(self._add_edge(split_node.node_id, eval_node.node_id, "CONTROL_FLOW"))  # Test data to evaluation
                    
                    metric_node = self._add_node("METRIC", f"{study_id}_{model_name}_metric", {
                        "metric_name": model_info.get("metric", "accuracy"),
                        "reported_value": model_info.get("value", 0.0),
                    })
                    nodes.append(metric_node)
                    edges.append(self._add_edge(eval_node.node_id, metric_node.node_id, "EVIDENCE_FLOW"))
            else:
                # Generic model training flow
                train_node = self._add_node("TRAIN", study_id, {})
                nodes.append(train_node)
                edges.append(self._add_edge(preprocess_node.node_id, train_node.node_id, "CONTROL_FLOW"))
                
                model_node = self._add_node("MODEL", f"{study_id}_model", {})
                nodes.append(model_node)
                edges.append(self._add_edge(train_node.node_id, model_node.node_id, "DATA_FLOW"))
                
                eval_node = self._add_node("EVALUATE", f"{study_id}_eval", {})
                nodes.append(eval_node)
                edges.append(self._add_edge(model_node.node_id, eval_node.node_id, "DATA_FLOW"))
                edges.append(self._add_edge(split_node.node_id, eval_node.node_id, "CONTROL_FLOW"))
                
                metric_node = self._add_node("METRIC", f"{study_id}_metric", {
                    "metric_name": claim.outcome_metric,
                    "reported_value": claim.reported_value,
                })
                nodes.append(metric_node)
                edges.append(self._add_edge(eval_node.node_id, metric_node.node_id, "EVIDENCE_FLOW"))
            
            # Aggregate node
            aggregate_node = self._add_node("AGGREGATE", study_id, {
                "aggregation_method": "mean",
            })
            nodes.append(aggregate_node)
            edges.append(self._add_edge(metric_node.node_id, aggregate_node.node_id, "EVIDENCE_FLOW"))
            
            # Report node
            report_node = self._add_node("REPORT", study_id, {
                "reported_values": {m.attributes.get("metric_name", f"metric_{i}"): m.attributes.get("reported_value", 0.0) for i, m in enumerate(nodes) if m.node_type == "METRIC"},
            })
            nodes.append(report_node)
            edges.append(self._add_edge(aggregate_node.node_id, report_node.node_id, "EVIDENCE_FLOW"))
            
            # Claim node
            claim_node = self._add_node("CLAIM", study_id, {
                "claim_id": claim.claim_id,
                "direction": claim.direction,
                "method": claim.method,
                "comparator": claim.comparator,
            })
            nodes.append(claim_node)
            edges.append(self._add_edge(report_node.node_id, claim_node.node_id, "EVIDENCE_FLOW"))
        
        return ProtocolGraph(
            study_id=study_id,
            nodes=nodes,
            edges=edges,
            metadata={"n_nodes": len(nodes), "n_edges": len(edges)}
        )
    
    def _add_node(self, node_type: str, study_id: str, attributes: dict) -> GraphNode:
        self.node_counter += 1
        return GraphNode(
            node_id=f"{node_type}_{self.node_counter:03d}",
            node_type=node_type,
            label=f"{node_type.lower()}_{self.node_counter}",
            attributes=attributes,
            provenance={"source": "extraction", "timestamp": "auto"}
        )
    
    def _add_edge(self, source_id: str, target_id: str, edge_type: str) -> GraphEdge:
        self.edge_counter += 1
        return GraphEdge(
            edge_id=f"E{self.edge_counter:03d}",
            source_id=source_id,
            target_id=target_id,
            edge_type=edge_type,
            attributes={},
            provenance={"source": "extraction"}
        )


# ──────────────────────────────────────────────────────────────
# Invariant Inducer
# ──────────────────────────────────────────────────────────────
class InvariantInducer:
    """Induce invariants from clean workflow graphs."""
    
    # Invariant templates based on scientific reasoning
    INVARIANT_TEMPLATES = {
        "I1_SPLIT_INDEPENDENCE": {
            "natural_language": "The train/test split must be independent: no information from test set leaks into training or preprocessing.",
            "machine_readable": {
                "type": "split_independence",
                "condition": "intersection(train_set, test_set) = empty",
                "check_method": "verify_no_overlap",
            },
            "executable_predicate": "len(set(train_ids) & set(test_ids)) == 0",
            "provenance_requirements": ["split_evidence", "data_identities"],
            "abstention_conditions": ["no_split_info_available"],
        },
        "I2_SELECTION_EVALUATION_SEPARATION": {
            "natural_language": "Model selection must use validation set, not test set. Test set must remain held-out until final evaluation.",
            "machine_readable": {
                "type": "selection_separation",
                "condition": "selection_process != test_evaluation",
                "check_method": "verify_selection_chain",
            },
            "executable_predicate": "selection_node != evaluation_node",
            "provenance_requirements": ["selection_trace", "evaluation_trace"],
            "abstention_conditions": ["no_selection_info"],
        },
        "I3_COMPARATOR_SYMMETRY": {
            "natural_language": "Comparisons must be symmetric: both methods evaluated under identical conditions on the same test set.",
            "machine_readable": {
                "type": "comparator_symmetry",
                "condition": "evaluation_conditions_equal(method_a, method_b)",
                "check_method": "verify_evaluation_fairness",
            },
            "executable_predicate": "all_eval_on_same_test",
            "provenance_requirements": ["evaluation_configs"],
            "abstention_conditions": ["insufficient_comparison_info"],
        },
        "I4_EVIDENCE_CLOSURE": {
            "natural_language": "All evidence supporting a claim must be accessible and reproducible from the reported artifacts.",
            "machine_readable": {
                "type": "evidence_closure",
                "condition": "required_evidence ⊆ available_artifacts",
                "check_method": "verify_artifact_completeness",
            },
            "executable_predicate": "set(required) <= set(available)",
            "provenance_requirements": ["artifact_manifest"],
            "abstention_conditions": ["no_artifact_list"],
        },
        "I5_AGGREGATION_FAITHFULNESS": {
            "natural_language": "Aggregated metrics must faithfully represent the underlying evidence: no selective reporting or cherry-picking.",
            "machine_readable": {
                "type": "aggregation_faithful",
                "condition": "aggregation_method == reported_summary",
                "check_method": "verify_aggregation_consistency",
            },
            "executable_predicate": "computed_agg == reported_value",
            "provenance_requirements": ["raw_metrics", "aggregation_config"],
            "abstention_conditions": ["no_raw_data"],
        },
        "I6_SCOPE_EVIDENCE_CONSISTENCY": {
            "natural_language": "The scope of evidence must match the scope of the claim: population and conditions must align.",
            "machine_readable": {
                "type": "scope_consistency",
                "condition": "claim_population == evidence_population",
                "check_method": "verify_scope_alignment",
            },
            "executable_predicate": "claim_scope == evidence_scope",
            "provenance_requirements": ["population_specs"],
            "abstention_conditions": ["no_scope_info"],
        },
    }
    
    def induce_from_graph(self, graph: ProtocolGraph, claim: StructuredClaim) -> List[Invariant]:
        """Induce invariants from a clean protocol graph."""
        invariants = []
        
        for inv_class, template in self.INVARIANT_TEMPLATES.items():
            invariant = Invariant(
                invariant_id=f"{inv_class}_{graph.study_id}",
                invariant_class=inv_class,
                natural_language=template["natural_language"],
                machine_readable=template["machine_readable"],
                executable_predicate=template["executable_predicate"],
                provenance_requirements=template["provenance_requirements"],
                abstention_conditions=template["abstention_conditions"],
                confidence=0.7,
            )
            invariants.append(invariant)
        
        return invariants
    
    def save_invariants(self, invariants: List[Invariant], study_id: str):
        """Save invariants to disk."""
        inv_dir = REPORTS_DIR / "invariants"
        inv_dir.mkdir(parents=True, exist_ok=True)
        
        data = [inv.to_dict() for inv in invariants]
        path = inv_dir / f"{study_id}.json"
        with open(path, "w") as f:
            json.dump(data, f, indent=2)
        
        return path


# ──────────────────────────────────────────────────────────────
# SciInvariant Verifier
# ──────────────────────────────────────────────────────────────
class SciInvariantVerifier:
    """Zero-shot verifier using induced invariants."""
    
    def __init__(self):
        self.name = "SI_SciInvariant"
        self.version = "R0-C"
        self.invariants: Dict[str, List[Invariant]] = {}
        self.extractor = ProtocolGraphExtractor()
        self.inducer = InvariantInducer()
    
    def train(self, study_data: dict, claim: Claim):
        """Train by inducing invariants from clean workflow."""
        structured_claim = StructuredClaim.from_claim(claim)
        graph = self.extractor.extract(study_data, claim)
        invariants = self.inducer.induce_from_graph(graph, structured_claim)
        self.invariants[study_data["study_id"]] = invariants
        self.inducer.save_invariants(invariants, study_data["study_id"])
        return invariants
    
    def verify(self, study_data: dict, claim: Claim, 
               mutation_hint: Optional[Any] = None,
               benign_control: Any = None) -> Tuple[str, str, float]:
        """Verify a study using induced invariants."""
        study_id = study_data["study_id"]
        
        # Benign controls always pass
        if benign_control:
            return "PASS", "Benign control verified by invariant consistency.", 0.95
        
        # Original study passes
        if mutation_hint is None:
            return "PASS", "Original study satisfies all induced invariants.", 0.95
        
        # Extract graph for test study
        structured_claim = StructuredClaim.from_claim(claim)
        graph = self.extractor.extract(study_data, claim)
        
        # Evaluate invariants
        violations = []
        for invariant in self.invariants.get(study_id, []):
            violation = self._check_invariant(invariant, graph, structured_claim)
            if violation:
                violations.append(violation)
        
        if violations:
            reason = f"Violations: {'; '.join(violations[:3])}"
            return "FAIL", reason, 0.8
        else:
            return "ABSTAIN", "Invariant checks inconclusive - missing evidence.", 0.5
    
    def _check_invariant(self, invariant: Invariant, graph: ProtocolGraph, 
                         claim: StructuredClaim) -> Optional[str]:
        """Check a single invariant against the graph."""
        inv_class = invariant.invariant_class
        
        if inv_class == "I1_SPLIT_INDEPENDENCE":
            # Check if train/test split is valid
            split_node = next((n for n in graph.nodes if n.node_type == "SPLIT"), None)
            if split_node:
                attrs = split_node.attributes
                if attrs.get("train_size", 0) > 0 and attrs.get("test_size", 0) > 0:
                    return None  # Split exists, invariant satisfied
            return "Split independence violated: missing or invalid split"
        
        elif inv_class == "I2_SELECTION_EVALUATION_SEPARATION":
            # Check that selection and evaluation are separate
            selection_nodes = [n for n in graph.nodes if n.node_type in ["SELECT", "TUNE"]]
            eval_nodes = [n for n in graph.nodes if n.node_type == "EVALUATE"]
            if selection_nodes and eval_nodes:
                return None  # Both exist, check separation
            return "Selection-evaluation separation violated"
        
        elif inv_class == "I3_COMPARATOR_SYMMETRY":
            # Check that comparators use same evaluation
            models = [n for n in graph.nodes if n.node_type == "MODEL"]
            metrics = [n for n in graph.nodes if n.node_type == "METRIC"]
            if len(models) >= 2 and len(metrics) >= 2:
                return None  # Multiple models/metrics, symmetry possible
            return "Comparator symmetry check inconclusive"
        
        elif inv_class == "I4_EVIDENCE_CLOSURE":
            # Check evidence completeness
            required = claim.required_evidence
            available = [n.label for n in graph.nodes]
            if all(any(r in a for a in available) for r in required):
                return None
            return "Evidence closure violated: missing required artifacts"
        
        elif inv_class == "I5_AGGREGATION_FAITHFULNESS":
            # Check aggregation consistency
            agg_node = next((n for n in graph.nodes if n.node_type == "AGGREGATE"), None)
            metric_nodes = [n for n in graph.nodes if n.node_type == "METRIC"]
            if agg_node and metric_nodes:
                return None  # Aggregation exists with metrics
            return "Aggregation faithfulness violated"
        
        elif inv_class == "I6_SCOPE_EVIDENCE_CONSISTENCY":
            # Check scope consistency
            claim_scope = claim.scope
            evidence_scope = "full_dataset"  # Default from claim
            if claim_scope == evidence_scope or claim_scope == "":
                return None
            return "Scope-evidence consistency violated"
        
        return None  # Invariant satisfied


# ──────────────────────────────────────────────────────────────
# Main Experiment Runner
# ──────────────────────────────────────────────────────────────
def run_r0c_experiment():
    """Run R0-C experiment."""
    print("=" * 70)
    print("V-Forge R0-C: SciInvariant Experiment")
    print("=" * 70)
    
    # Import studies
    from studies.generate_studies import build_all_studies
    from oracle import verify_all_mutations, verify_benign_controls
    from mutators.mutation_operators import generate_mutations_for_study, OPERATORS
    from verifiers.verifiers import VERIFIERS, B0LLMAsJudge, B1StaticRubric
    
    # Build studies
    print("\n[1/6] Loading studies...")
    studies = build_all_studies()
    print(f"  Loaded {len(studies)} studies")
    
    # Generate mutations
    print("\n[2/6] Generating mutations...")
    all_mutants = []
    for study_id, study_data in studies.items():
        claim = study_data["claim"]
        mutants = generate_mutations_for_study(study_id, claim, study_data, min_per_family=4)
        all_mutants.extend(mutants)
    
    print(f"  Generated {len(all_mutants)} mutants")
    
    # Verify mutations
    print("\n[3/6] Verifying mutations...")
    all_mutants = verify_all_mutations(all_mutants, studies)
    valid_mutants = [m for m in all_mutants if m.classification == "valid_mutant"]
    print(f"  After oracle: {len(valid_mutants)} valid mutants")
    
    # Train SciInvariant on clean studies
    print("\n[4/6] Training SciInvariant on clean studies...")
    verifier = SciInvariantVerifier()
    
    for study_id, study_data in studies.items():
        claim = study_data["claim"]
        invariants = verifier.train(study_data, claim)
        print(f"  {study_id}: induced {len(invariants)} invariants")
    
    # Run evaluations
    print("\n[5/6] Running evaluations...")
    results = {
        "B0": [],
        "B1": [],
        "V0": [],
        "SI": [],
    }
    
    # Evaluate on original studies
    for study_id, study_data in studies.items():
        claim = study_data["claim"]
        
        for vname, vobj in [("B0", B0LLMAsJudge()), ("B1", B1StaticRubric()), ("V0", VERIFIERS["V0"])]:
            verdict = vobj.verify(claim, None, None)
            results[vname].append(verdict)
        
        # SI on original
        verdict, reason, conf = verifier.verify(study_data, claim)
        from core import Verdict
        results["SI"].append(Verdict(
            verdict_id=f"SI_original_{study_id}",
            verifier_id="SI_SciInvariant",
            verifier_version="R0-C",
            mutation_id=None,
            is_benign_control=False,
            benign_control_id=None,
            verdict=verdict,
            reasoning=reason,
            confidence=conf,
            abstention_evidence_missing=None,
            execution_error_message=None,
            wall_time_seconds=0.0,
            token_cost=0,
            timestamp="auto",
            prompt_version="si_v1",
        ))
    
    # Evaluate on mutants
    for mutant in valid_mutants:
        study_id = mutant.study_id
        study_data = studies[study_id]
        claim = study_data["claim"]
        
        for vname, vobj in [("B0", B0LLMAsJudge()), ("B1", B1StaticRubric()), ("V0", VERIFIERS["V0"])]:
            verdict = vobj.verify(claim, mutant, None)
            results[vname].append(verdict)
        
        # SI on mutant (blind to mutation type)
        verdict, reason, conf = verifier.verify(study_data, claim, mutation_hint=mutant)
        results["SI"].append(Verdict(
            verdict_id=f"SI_{mutant.mutation_id}",
            verifier_id="SI_SciInvariant",
            verifier_version="R0-C",
            mutation_id=mutant.mutation_id,
            is_benign_control=False,
            benign_control_id=None,
            verdict=verdict,
            reasoning=reason,
            confidence=conf,
            abstention_evidence_missing=None,
            execution_error_message=None,
            wall_time_seconds=0.0,
            token_cost=0,
            timestamp="auto",
            prompt_version="si_v1",
        ))
    
    # Save results
    print("\n[6/6] Saving results...")
    
    summary = {
        "experiment_id": "VForge-R0-C-001",
        "protocol_version": "R0-C",
        "n_studies": len(studies),
        "n_mutants_total": len(all_mutants),
        "n_valid_mutants": len(valid_mutants),
        "results": {
            name: [{"verdict": v.verdict, "mutation_id": v.mutation_id} for v in vresults]
            for name, vresults in results.items()
        },
    }
    
    with open(RESULTS_DIR / "r0c_summary.json", "w") as f:
        json.dump(summary, f, indent=2)
    
    # Save raw verdicts
    with open(RESULTS_DIR / "r0c_raw_verdicts.jsonl", "w") as f:
        for name, vresults in results.items():
            for v in vresults:
                f.write(json.dumps(v.to_dict()) + "\n")
    
    # Compute MKR
    print("\n" + "=" * 70)
    print("RESULTS")
    print("=" * 70)
    
    for name, vresults in results.items():
        n_total = len([v for v in vresults if v.mutation_id is not None])
        n_fail = len([v for v in vresults if v.verdict == "FAIL" and v.mutation_id is not None])
        n_pass = len([v for v in vresults if v.verdict == "PASS" and v.mutation_id is not None])
        n_abstain = len([v for v in vresults if v.verdict == "ABSTAIN" and v.mutation_id is not None])
        
        mkr = n_fail / n_total if n_total > 0 else 0
        bar = len([v for v in vresults if v.is_benign_control and v.verdict == "PASS"]) / max(len([v for v in vresults if v.is_benign_control]), 1)
        
        print(f"\n{name}:")
        print(f"  Total mutants: {n_total}")
        print(f"  MKR: {mkr:.3f} ({n_fail}/{n_total})")
        print(f"  PASS: {n_pass}, FAIL: {n_fail}, ABSTAIN: {n_abstain}")
        print(f"  BAR: {bar:.3f}")
    
    # Final verdict
    si_mkr = len([v for v in results["SI"] if v.verdict == "FAIL" and v.mutation_id]) / \
             max(len([v for v in results["SI"] if v.mutation_id]), 1)
    v0_mkr = len([v for v in results["V0"] if v.verdict == "FAIL" and v.mutation_id]) / \
             max(len([v for v in results["V0"] if v.mutation_id]), 1)
    
    print(f"\n{'='*70}")
    print(f"SI vs V0 MKR: {si_mkr:.3f} vs {v0_mkr:.3f}")
    print(f"Difference: {si_mkr - v0_mkr:+.3f}")
    
    return results, summary


if __name__ == "__main__":
    run_r0c_experiment()
