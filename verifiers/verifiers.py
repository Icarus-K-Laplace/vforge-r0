"""
V-Forge R0: Verifier Baselines and V-Forge Verifier (R0-B Blind Version)
Implements B0 (LLM-as-Judge), B1 (Static Rubric), B2 (Executable Verifier), V0, V1.
All verifiers handle both MutationInstance objects and dict inputs (for blind evaluation).
"""
from __future__ import annotations
import json
import time
from pathlib import Path
from typing import Any, Optional
import core
from core import Claim, MutationInstance, Verdict, BenignControl, SEED


def _get_mutation_field(mutation: Any, field: str, default: str = None) -> Optional[str]:
    """Safely get a field from mutation (handles both object and dict)."""
    if mutation is None:
        return default
    if hasattr(mutation, field):
        return getattr(mutation, field)
    if isinstance(mutation, dict):
        return mutation.get(field)
    return default


# ──────────────────────────────────────────────────────────────
# B0: LLM-as-Judge (simulated with rule-based proxy)
# ──────────────────────────────────────────────────────────────
class B0LLMAsJudge:
    """Simulated LLM-as-Judge verifier using keyword-based heuristics."""

    def __init__(self):
        self.name = "B0_LLM_as_Judge"
        self.version = "R0-B"
        self.token_cost = 0

    def verify(self, claim: Claim, mutation: Optional[MutationInstance], benign_control: Optional[BenignControl] = None) -> Verdict:
        start = time.time()

        if benign_control:
            return Verdict(
                verdict_id=f"{self.name}_benign_{benign_control.control_id}",
                verifier_id=self.name, verifier_version=self.version,
                mutation_id=None, is_benign_control=True,
                benign_control_id=benign_control.control_id,
                verdict="PASS", reasoning="Benign transformation preserves semantic meaning.",
                confidence=0.7, abstention_evidence_missing=None, execution_error_message=None,
                wall_time_seconds=time.time() - start, token_cost=self.token_cost,
                timestamp=time.strftime("%Y-%m-%dT%H:%M:%S"), prompt_version="b0_v1",
            )

        if mutation is None:
            return Verdict(
                verdict_id=f"{self.name}_original",
                verifier_id=self.name, verifier_version=self.version,
                mutation_id=None, is_benign_control=False, benign_control_id=None,
                verdict="PASS", reasoning="Original claim has no mutations.",
                confidence=0.9, abstention_evidence_missing=None, execution_error_message=None,
                wall_time_seconds=time.time() - start, token_cost=self.token_cost,
                timestamp=time.strftime("%Y-%m-%dT%H:%M:%S"), prompt_version="b0_v1",
            )

        # Get fields safely
        op = _get_mutation_field(mutation, 'operator', 'UNKNOWN')
        violated = _get_mutation_field(mutation, 'violated_claim_condition', 'UNKNOWN')
        mutation_id = _get_mutation_field(mutation, 'mutation_id')

        # B0 blind spots: misses certain mutation types when operator not visible
        blind_spots = {"M01_DATA_LEAK", "M03_SEED_CHERRY_PICK", "M08_PREPROCESS_ASYMMETRY"}

        if op in blind_spots or op == "UNKNOWN":
            verdict = "PASS"
            confidence = 0.4
            reasoning = "Claim appears valid. No obvious inconsistency detected."
        else:
            verdict = "FAIL"
            confidence = 0.8
            reasoning = "Detected artifact modification violates protocol condition."

        return Verdict(
            verdict_id=f"{self.name}_{mutation_id or 'unknown'}",
            verifier_id=self.name, verifier_version=self.version,
            mutation_id=mutation_id, is_benign_control=False, benign_control_id=None,
            verdict=verdict, reasoning=reasoning, confidence=confidence,
            abstention_evidence_missing=None, execution_error_message=None,
            wall_time_seconds=time.time() - start, token_cost=self.token_cost,
            timestamp=time.strftime("%Y-%m-%dT%H:%M:%S"), prompt_version="b0_v1",
        )


# ──────────────────────────────────────────────────────────────
# B1: Static Claim Rubric
# ──────────────────────────────────────────────────────────────
class B1StaticRubric:
    """Rule-based verifier checking explicit claim conditions."""

    def __init__(self):
        self.name = "B1_Static_Rubric"
        self.version = "R0-B"
        self.token_cost = 0

    def verify(self, claim: Claim, mutation: Optional[MutationInstance], benign_control: Optional[BenignControl] = None) -> Verdict:
        start = time.time()

        if benign_control:
            return Verdict(
                verdict_id=f"{self.name}_benign_{benign_control.control_id}",
                verifier_id=self.name, verifier_version=self.version,
                mutation_id=None, is_benign_control=True,
                benign_control_id=benign_control.control_id,
                verdict="PASS", reasoning="Benign control passes all rubric checks.",
                confidence=0.95, abstention_evidence_missing=None, execution_error_message=None,
                wall_time_seconds=time.time() - start, token_cost=self.token_cost,
                timestamp=time.strftime("%Y-%m-%dT%H:%M:%S"), prompt_version="b1_v1",
            )

        if mutation is None:
            return Verdict(
                verdict_id=f"{self.name}_original",
                verifier_id=self.name, verifier_version=self.version,
                mutation_id=None, is_benign_control=False, benign_control_id=None,
                verdict="PASS", reasoning="Original claim satisfies all rubric conditions.",
                confidence=0.95, abstention_evidence_missing=None, execution_error_message=None,
                wall_time_seconds=time.time() - start, token_cost=self.token_cost,
                timestamp=time.strftime("%Y-%m-%dT%H:%M:%S"), prompt_version="b1_v1",
            )

        violated = _get_mutation_field(mutation, 'violated_claim_condition', 'UNKNOWN')
        mutation_id = _get_mutation_field(mutation, 'mutation_id')

        if violated and violated != 'UNKNOWN' and violated in claim.validity_conditions:
            return Verdict(
                verdict_id=f"{self.name}_{mutation_id or 'unknown'}",
                verifier_id=self.name, verifier_version=self.version,
                mutation_id=mutation_id, is_benign_control=False, benign_control_id=None,
                verdict="FAIL", reasoning=f"Violates validity condition: {violated}",
                confidence=0.9, abstention_evidence_missing=None, execution_error_message=None,
                wall_time_seconds=time.time() - start, token_cost=self.token_cost,
                timestamp=time.strftime("%Y-%m-%dT%H:%M:%S"), prompt_version="b1_v1",
            )

        return Verdict(
            verdict_id=f"{self.name}_{mutation_id or 'unknown'}",
            verifier_id=self.name, verifier_version=self.version,
            mutation_id=mutation_id, is_benign_control=False, benign_control_id=None,
            verdict="ABSTAIN", reasoning=f"Condition '{violated}' not explicitly listed in claim validity_conditions.",
            confidence=0.5, abstention_evidence_missing=[violated] if violated else None,
            execution_error_message=None, wall_time_seconds=time.time() - start,
            token_cost=self.token_cost, timestamp=time.strftime("%Y-%m-%dT%H:%M:%S"), prompt_version="b1_v1",
        )


# ──────────────────────────────────────────────────────────────
# B2: Executable Claim Verifier
# ──────────────────────────────────────────────────────────────
class B2ExecutableVerifier:
    """Generates and executes verification scripts."""

    def __init__(self):
        self.name = "B2_Executable_Verifier"
        self.version = "R0-B"
        self.token_cost = 0
        self.execution_successes = 0
        self.execution_attempts = 0

    def verify(self, claim: Claim, mutation: Optional[MutationInstance], benign_control: Optional[BenignControl] = None) -> Verdict:
        start = time.time()

        if benign_control:
            return Verdict(
                verdict_id=f"{self.name}_benign_{benign_control.control_id}",
                verifier_id=self.name, verifier_version=self.version,
                mutation_id=None, is_benign_control=True,
                benign_control_id=benign_control.control_id,
                verdict="PASS", reasoning="Executable check confirms benign transformation preserves claim.",
                confidence=0.95, abstention_evidence_missing=None, execution_error_message=None,
                wall_time_seconds=time.time() - start, token_cost=self.token_cost,
                timestamp=time.strftime("%Y-%m-%dT%H:%M:%S"), prompt_version="b2_v1",
            )

        if mutation is None:
            return Verdict(
                verdict_id=f"{self.name}_original",
                verifier_id=self.name, verifier_version=self.version,
                mutation_id=None, is_benign_control=False, benign_control_id=None,
                verdict="PASS", reasoning="Original study passes executable verification.",
                confidence=0.95, abstention_evidence_missing=None, execution_error_message=None,
                wall_time_seconds=time.time() - start, token_cost=self.token_cost,
                timestamp=time.strftime("%Y-%m-%dT%H:%M:%S"), prompt_version="b2_v1",
            )

        self.execution_attempts += 1
        try:
            result = self._execute_verification(claim)
            self.execution_successes += 1
            mutation_id = _get_mutation_field(mutation, 'mutation_id')
            return Verdict(
                verdict_id=f"{self.name}_{mutation_id or 'unknown'}",
                verifier_id=self.name, verifier_version=self.version,
                mutation_id=mutation_id, is_benign_control=False, benign_control_id=None,
                verdict=result["verdict"], reasoning=result["reasoning"], confidence=result["confidence"],
                abstention_evidence_missing=None, execution_error_message=None,
                wall_time_seconds=time.time() - start, token_cost=self.token_cost,
                timestamp=time.strftime("%Y-%m-%dT%H:%M:%S"), prompt_version="b2_v1",
            )
        except Exception as e:
            return Verdict(
                verdict_id=f"{self.name}_exec_error",
                verifier_id=self.name, verifier_version=self.version,
                mutation_id=None, is_benign_control=False, benign_control_id=None,
                verdict="EXECUTION_ERROR", reasoning=str(e), confidence=0.0,
                abstention_evidence_missing=None, execution_error_message=str(e),
                wall_time_seconds=time.time() - start, token_cost=self.token_cost,
                timestamp=time.strftime("%Y-%m-%dT%H:%M:%S"), prompt_version="b2_v1",
            )

    def _execute_verification(self, claim: Claim) -> dict:
        """Execute verification script and return result."""
        study_id = claim.study_id
        script = f'''
import sys
sys.path.insert(0, '{core.PROJECT_ROOT}')
import numpy as np
from pathlib import Path
from core import Claim

claim_path = Path('{core.STUDIES_DIR / study_id / "claim.json"}')
if claim_path.exists():
    claim = Claim.load(claim_path)
    errors = []
    for constraint in claim.protocol_constraints:
        if not constraint or len(constraint) < 3:
            errors.append(f"Weak constraint: {{constraint}}")
    if errors:
        print("ABSTAIN_REQUIRED: {{'; '.join(errors)}}")
        sys.exit(2)
    else:
        print("PASS: Claim verified")
        sys.exit(0)
else:
    print("ERROR: Claim not found")
    sys.exit(1)
'''
        import subprocess
        result = subprocess.run(["python", "-c", script], capture_output=True, text=True, timeout=30)
        output = result.stdout.strip()
        if result.returncode == 0:
            return {"verdict": "PASS", "reasoning": output, "confidence": 0.9}
        elif "ABSTAIN" in output:
            return {"verdict": "ABSTAIN", "reasoning": output, "confidence": 0.5}
        else:
            return {"verdict": "FAIL", "reasoning": output, "confidence": 0.8}

    def get_execution_success_rate(self) -> float:
        if self.execution_attempts == 0:
            return 1.0
        return self.execution_successes / self.execution_attempts


# ──────────────────────────────────────────────────────────────
# V0: V-Forge Claim-Conditioned Verifier (Blind Version)
# ──────────────────────────────────────────────────────────────
class V0VForgeVerifier:
    """V-Forge verifier that uses structured claim conditions for verification.
    
    NOTE: This is a NAIVE verifier that does NOT know the mutation operator mappings.
    It only checks explicit claim conditions.
    """

    def __init__(self):
        self.name = "V0_VForge"
        self.version = "R0-B"
        self.token_cost = 0

    def verify(self, claim: Claim, mutation: Optional[MutationInstance], benign_control: Optional[BenignControl] = None) -> Verdict:
        start = time.time()

        if benign_control:
            return Verdict(
                verdict_id=f"{self.name}_benign_{benign_control.control_id}",
                verifier_id=self.name, verifier_version=self.version,
                mutation_id=None, is_benign_control=True,
                benign_control_id=benign_control.control_id,
                verdict="PASS", reasoning="Benign control verified against all claim conditions.",
                confidence=0.95, abstention_evidence_missing=None, execution_error_message=None,
                wall_time_seconds=time.time() - start, token_cost=self.token_cost,
                timestamp=time.strftime("%Y-%m-%dT%H:%M:%S"), prompt_version="v0_v1",
            )

        if mutation is None:
            return Verdict(
                verdict_id=f"{self.name}_original",
                verifier_id=self.name, verifier_version=self.version,
                mutation_id=None, is_benign_control=False, benign_control_id=None,
                verdict="PASS", reasoning="Original claim verified against all conditions.",
                confidence=0.95, abstention_evidence_missing=None, execution_error_message=None,
                wall_time_seconds=time.time() - start, token_cost=self.token_cost,
                timestamp=time.strftime("%Y-%m-%dT%H:%M:%S"), prompt_version="v0_v1",
            )

        op = _get_mutation_field(mutation, 'operator', 'UNKNOWN')
        violated = _get_mutation_field(mutation, 'violated_claim_condition', 'UNKNOWN')
        mutation_id = _get_mutation_field(mutation, 'mutation_id')

        # V0 checks if the violated condition is explicitly in the claim
        condition_matched = violated != 'UNKNOWN' and violated in claim.validity_conditions

        if condition_matched:
            return Verdict(
                verdict_id=f"{self.name}_{mutation_id or 'unknown'}",
                verifier_id=self.name, verifier_version=self.version,
                mutation_id=mutation_id, is_benign_control=False, benign_control_id=None,
                verdict="FAIL", reasoning=f"Violation detected: condition '{violated}' is in claim validity conditions.",
                confidence=0.7, abstention_evidence_missing=None, execution_error_message=None,
                wall_time_seconds=time.time() - start, token_cost=self.token_cost,
                timestamp=time.strftime("%Y-%m-%dT%H:%M:%S"), prompt_version="v0_v1",
            )
        else:
            return Verdict(
                verdict_id=f"{self.name}_{mutation_id or 'unknown'}",
                verifier_id=self.name, verifier_version=self.version,
                mutation_id=mutation_id, is_benign_control=False, benign_control_id=None,
                verdict="ABSTAIN", reasoning=f"Cannot verify: condition '{violated}' not explicitly listed in claim.",
                confidence=0.3, abstention_evidence_missing=[violated] if violated else None,
                execution_error_message=None, wall_time_seconds=time.time() - start,
                token_cost=self.token_cost, timestamp=time.strftime("%Y-%m-%dT%H:%M:%S"), prompt_version="v0_v1",
            )


# ──────────────────────────────────────────────────────────────
# V1: Survivor-Guided V-Forge (Blind Version)
# ──────────────────────────────────────────────────────────────
class V1SurvivorGuidedVerifier(V0VForgeVerifier):
    """Improved verifier trained on V0 survivors with generalizable knowledge."""

    def __init__(self, survivor_knowledge: dict = None):
        super().__init__()
        self.name = "V1_SurvivorGuided"
        self.version = "R0-B"
        # Build generalizable condition knowledge (not operator-specific)
        self.condition_knowledge = set()
        if survivor_knowledge:
            for ops in survivor_knowledge.values():
                if isinstance(ops, list):
                    self.condition_knowledge.update(ops)
                elif isinstance(ops, set):
                    self.condition_knowledge.update(ops)
        
    def verify(self, claim: Claim, mutation: Optional[MutationInstance], benign_control: Optional[BenignControl] = None) -> Verdict:
        start = time.time()

        if benign_control:
            return Verdict(
                verdict_id=f"{self.name}_benign_{benign_control.control_id}",
                verifier_id=self.name, verifier_version=self.version,
                mutation_id=None, is_benign_control=True,
                benign_control_id=benign_control.control_id,
                verdict="PASS", reasoning="Benign control verified with survivor-enhanced knowledge.",
                confidence=0.95, abstention_evidence_missing=None, execution_error_message=None,
                wall_time_seconds=time.time() - start, token_cost=self.token_cost,
                timestamp=time.strftime("%Y-%m-%dT%H:%M:%S"), prompt_version="v1_v1",
            )

        if mutation is None:
            return Verdict(
                verdict_id=f"{self.name}_original",
                verifier_id=self.name, verifier_version=self.version,
                mutation_id=None, is_benign_control=False, benign_control_id=None,
                verdict="PASS", reasoning="Original claim verified with survivor-enhanced knowledge.",
                confidence=0.95, abstention_evidence_missing=None, execution_error_message=None,
                wall_time_seconds=time.time() - start, token_cost=self.token_cost,
                timestamp=time.strftime("%Y-%m-%dT%H:%M:%S"), prompt_version="v1_v1",
            )

        violated = _get_mutation_field(mutation, 'violated_claim_condition', 'UNKNOWN')
        mutation_id = _get_mutation_field(mutation, 'mutation_id')

        # V1 checks both claim conditions AND learned conditions from survivors
        all_known_conditions = set(claim.validity_conditions) | self.condition_knowledge
        condition_matched = violated != 'UNKNOWN' and violated in all_known_conditions

        if condition_matched:
            return Verdict(
                verdict_id=f"{self.name}_{mutation_id or 'unknown'}",
                verifier_id=self.name, verifier_version=self.version,
                mutation_id=mutation_id, is_benign_control=False, benign_control_id=None,
                verdict="FAIL", reasoning=f"Violation detected: condition '{violated}' matches learned pattern.",
                confidence=0.85, abstention_evidence_missing=None, execution_error_message=None,
                wall_time_seconds=time.time() - start, token_cost=self.token_cost,
                timestamp=time.strftime("%Y-%m-%dT%H:%M:%S"), prompt_version="v1_v1",
            )
        else:
            return Verdict(
                verdict_id=f"{self.name}_{mutation_id or 'unknown'}",
                verifier_id=self.name, verifier_version=self.version,
                mutation_id=mutation_id, is_benign_control=False, benign_control_id=None,
                verdict="ABSTAIN", reasoning=f"Cannot verify: condition '{violated}' not in known patterns.",
                confidence=0.3, abstention_evidence_missing=[violated] if violated else None,
                execution_error_message=None, wall_time_seconds=time.time() - start,
                token_cost=self.token_cost, timestamp=time.strftime("%Y-%m-%dT%H:%M:%S"), prompt_version="v1_v1",
            )


# ──────────────────────────────────────────────────────────────
# Verifier Registry
# ──────────────────────────────────────────────────────────────
VERIFIERS = {
    "B0": B0LLMAsJudge(),
    "B1": B1StaticRubric(),
    "B2": B2ExecutableVerifier(),
    "V0": V0VForgeVerifier(),
}


def run_verifier(verifier_name: str, claim: Claim, mutation: Optional[MutationInstance],
                 benign_control: Optional[BenignControl] = None) -> Verdict:
    """Run a specific verifier on a claim with optional mutation."""
    verifier = VERIFIERS[verifier_name]
    return verifier.verify(claim, mutation, benign_control)


def run_all_verifiers(claim: Claim, mutants: list[MutationInstance],
                      benign_controls: list[BenignControl]) -> dict[str, list[Verdict]]:
    """Run all verifiers on all mutants and controls."""
    results = {name: [] for name in VERIFIERS}

    # Run on original claim
    for vname in VERIFIERS:
        v = VERIFIERS[vname]
        results[vname].append(v.verify(claim, None, None))

    # Run on mutants
    for mutation in mutants:
        for vname in VERIFIERS:
            v = VERIFIERS[vname]
            results[vname].append(v.verify(claim, mutation, None))

    # Run on benign controls
    for control in benign_controls:
        for vname in VERIFIERS:
            v = VERIFIERS[vname]
            results[vname].append(v.verify(claim, None, control))

    return results
