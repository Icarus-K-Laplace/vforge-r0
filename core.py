"""
V-Forge R0: Mutation-Based Adequacy Testing for Scientific Verifiers
Core data model for claims, studies, and mutations.
"""
from __future__ import annotations
import json
import hashlib
import time
from pathlib import Path
from typing import Any, Optional
from dataclasses import dataclass, field, asdict
import numpy as np

# ──────────────────────────────────────────────────────────────
# Constants
# ──────────────────────────────────────────────────────────────
PROJECT_ROOT = Path(__file__).resolve().parent
SCHEMAS_DIR = PROJECT_ROOT / "schemas"
STUDIES_DIR = PROJECT_ROOT / "studies"
MUTATORS_DIR = PROJECT_ROOT / "mutators"
RESULTS_DIR = PROJECT_ROOT / "results"
REPORTS_DIR = PROJECT_ROOT / "reports"
TESTS_DIR = PROJECT_ROOT / "tests"
MODELS_DIR = PROJECT_ROOT / "models"
DATA_DIR = PROJECT_ROOT / "data"

for d in [STUDIES_DIR, MUTATORS_DIR, RESULTS_DIR, REPORTS_DIR, TESTS_DIR, MODELS_DIR, DATA_DIR]:
    d.mkdir(parents=True, exist_ok=True)

SEED = 42

# ──────────────────────────────────────────────────────────────
# Claim Schema
# ──────────────────────────────────────────────────────────────
@dataclass
class UncertaintyRequirement:
    type: str  # confidence_interval, standard_error, p_value, none
    value: Optional[float]
    level: float

    def to_dict(self):
        return {"type": self.type, "value": self.value, "level": self.level}

    @classmethod
    def from_dict(cls, d):
        return cls(type=d["type"], value=d.get("value"), level=d.get("level", 0.95))

@dataclass
class OracleDefinition:
    description: str
    input_artifacts: list[str]
    output_format: str  # boolean, numerical, categorical

    def to_dict(self):
        return asdict(self)

    @classmethod
    def from_dict(cls, d):
        return cls(**d)

@dataclass
class Claim:
    claim_id: str
    study_id: str
    natural_language_claim: str
    claim_type: str  # comparative_superiority, ood_generalization, calibration, subgroup_robustness, statistical_evidence
    population: str
    method: str
    comparator: str
    outcome_metric: str
    direction: str  # improves, degrades, no_change
    reported_value: float
    uncertainty_requirement: UncertaintyRequirement
    protocol_constraints: list[str]
    required_artifacts: list[str]
    evidence_targets: list[str]
    validity_conditions: list[str]
    abstention_conditions: list[str]
    oracle_definition: OracleDefinition

    def to_dict(self):
        return {
            "claim_id": self.claim_id,
            "study_id": self.study_id,
            "natural_language_claim": self.natural_language_claim,
            "claim_type": self.claim_type,
            "population": self.population,
            "method": self.method,
            "comparator": self.comparator,
            "outcome_metric": self.outcome_metric,
            "direction": self.direction,
            "reported_value": self.reported_value,
            "uncertainty_requirement": self.uncertainty_requirement.to_dict(),
            "protocol_constraints": self.protocol_constraints,
            "required_artifacts": self.required_artifacts,
            "evidence_targets": self.evidence_targets,
            "validity_conditions": self.validity_conditions,
            "abstention_conditions": self.abstention_conditions,
            "oracle_definition": self.oracle_definition.to_dict(),
        }

    def sha256(self) -> str:
        raw = json.dumps(self.to_dict(), sort_keys=True).encode()
        return hashlib.sha256(raw).hexdigest()

    def save(self, path: Path):
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w") as f:
            json.dump(self.to_dict(), f, indent=2)

    @classmethod
    def load(cls, path: Path) -> "Claim":
        with open(path) as f:
            d = json.load(f)
        d["uncertainty_requirement"] = UncertaintyRequirement.from_dict(d["uncertainty_requirement"])
        d["oracle_definition"] = OracleDefinition.from_dict(d["oracle_definition"])
        return cls(**d)


# ──────────────────────────────────────────────────────────────
# Mutation Schema
# ──────────────────────────────────────────────────────────────
class MutationOperator:
    """Base class for all mutation operators."""
    ID: str = "M00_UNKNOWN"
    NAME: str = "Unknown"

    def precondition(self, study_data: dict) -> bool:
        """Return True if mutation can be applied."""
        raise NotImplementedError

    def apply(self, study_data: dict, seed: int = SEED) -> dict:
        """Return mutated study data dict."""
        raise NotImplementedError

    def violated_condition(self, original_claim: Claim, mutated_data: dict) -> str:
        """Return which validity condition is violated, or None."""
        raise NotImplementedError


@dataclass
class MutationInstance:
    mutation_id: str
    operator: str
    study_id: str
    claim_id: str
    precondition: str
    modification_description: str
    artifacts_modified: list[str]
    diff_sha256: str
    violated_claim_condition: str
    independent_oracle_result: bool
    magnitude: float
    deterministic_replay_hash: str
    classification: str  # valid_mutant, trivial_mutant, skipped
    notes: str

    def to_dict(self):
        return asdict(self)

    def sha256(self) -> str:
        raw = json.dumps(self.to_dict(), sort_keys=True).encode()
        return hashlib.sha256(raw).hexdigest()


# ──────────────────────────────────────────────────────────────
# Benign Control Schema
# ──────────────────────────────────────────────────────────────
@dataclass
class BenignControl:
    control_id: str
    study_id: str
    claim_id: str
    transformation_type: str
    description: str
    parameters: dict
    oracle_verified: bool
    oracle_verification_hash: str
    sha256_original: str
    sha256_transformed: str

    def to_dict(self):
        return asdict(self)

    def sha256(self) -> str:
        raw = json.dumps(self.to_dict(), sort_keys=True).encode()
        return hashlib.sha256(raw).hexdigest()


# ──────────────────────────────────────────────────────────────
# Verdict Schema
# ──────────────────────────────────────────────────────────────
@dataclass
class Verdict:
    verdict_id: str
    verifier_id: str
    verifier_version: str
    mutation_id: Optional[str]
    is_benign_control: bool
    benign_control_id: Optional[str]
    verdict: str  # PASS, FAIL, ABSTAIN, EXECUTION_ERROR, TIMEOUT
    reasoning: str
    confidence: float
    abstention_evidence_missing: Optional[list[str]]
    execution_error_message: Optional[str]
    wall_time_seconds: float
    token_cost: Optional[float]
    timestamp: str
    prompt_version: str

    def to_dict(self):
        return asdict(self)


# ──────────────────────────────────────────────────────────────
# Utility
# ──────────────────────────────────────────────────────────────
def compute_sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def compute_diff_sha256(original: dict, mutated: dict) -> str:
    """Compute SHA256 of the diff between two dicts."""
    import difflib
    # Convert numpy arrays and special objects to lists for serialization
    def _convert(obj):
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        elif isinstance(obj, (np.integer, np.int64, np.int32)):
            return int(obj)
        elif isinstance(obj, (np.floating, np.float64, np.float32)):
            return float(obj)
        elif isinstance(obj, np.bool_):
            return bool(obj)
        elif isinstance(obj, dict):
            return {k: _convert(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [_convert(item) for item in obj]
        elif hasattr(obj, 'to_dict'):
            return _convert(obj.to_dict())
        return obj
    orig_serializable = _convert(original)
    mut_serializable = _convert(mutated)
    orig_lines = json.dumps(orig_serializable, sort_keys=True, indent=2).splitlines(keepends=True)
    mut_lines = json.dumps(mut_serializable, sort_keys=True, indent=2).splitlines(keepends=True)
    diff = list(difflib.unified_diff(orig_lines, mut_lines))
    return compute_sha256("".join(diff).encode())


def replay_hash(study_id: str, operator: str, seed: int) -> str:
    """Deterministic hash for reproducible replay."""
    raw = f"{study_id}:{operator}:{seed}".encode()
    return compute_sha256(raw)
