# V-Forge R0 Test Suite

import pytest
import json
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from core import Claim, MutationInstance, Verdict, BenignControl
from studies.generate_studies import build_all_studies
from mutators.mutation_operators import OPERATORS, generate_all_mutations
from verifiers.verifiers import run_all_verifiers, VERIFIERS
from oracle import verify_all_mutations
from evaluate import compute_mkr, compute_bar, compute_va


class TestStudyGeneration:
    """Test that all studies generate correctly."""

    def test_all_studies_generated(self):
        studies = build_all_studies()
        assert len(studies) == 5
        for sid in ["study_01", "study_02", "study_03", "study_04", "study_05"]:
            assert sid in studies
            assert "claim" in studies[sid]
            assert studies[sid]["claim"] is not None

    def test_study_claims_have_required_fields(self):
        studies = build_all_studies()
        for sid, study in studies.items():
            claim = study["claim"]
            assert hasattr(claim, 'claim_id')
            assert hasattr(claim, 'natural_language_claim')
            assert hasattr(claim, 'claim_type')
            assert hasattr(claim, 'validity_conditions')
            assert hasattr(claim, 'oracle_definition')


class TestMutationOperators:
    """Test mutation operators work correctly."""

    def test_all_operators_registered(self):
        assert len(OPERATORS) == 8
        expected_ids = {"M01_DATA_LEAK", "M02_BASELINE_HANDICAP", "M03_SEED_CHERRY_PICK",
                       "M04_SUBGROUP_DROP", "M05_METRIC_SWAP", "M06_AGGREGATION_FAULT",
                       "M07_TEST_SET_SELECTION", "M08_PREPROCESS_ASYMMETRY"}
        assert set(OPERATORS.keys()) == expected_ids

    def test_mutation_application(self):
        studies = build_all_studies()
        study = studies["study_01"]
        claim = study["claim"]

        for op_id, op in OPERATORS.items():
            if op.precondition(study):
                mutated = op.apply(study, seed=42)
                assert mutated is not None
                violated = op.violated_condition(claim, mutated)
                assert violated is not None
                assert isinstance(violated, str)


class TestVerifiers:
    """Test verifier implementations."""

    def test_verifier_registry(self):
        assert "B0" in VERIFIERS
        assert "B1" in VERIFIERS
        assert "B2" in VERIFIERS
        assert "V0" in VERIFIERS

    def test_verifiers_handle_original_claim(self):
        studies = build_all_studies()
        study = studies["study_01"]
        claim = study["claim"]

        for vname, verifier in VERIFIERS.items():
            verdict = verifier.verify(claim, None, None)
            assert verdict.verdict == "PASS"
            assert verdict.confidence > 0.5

    def test_verifiers_handle_benign_control(self):
        studies = build_all_studies()
        study = studies["study_01"]
        claim = study["claim"]
        control = BenignControl(
            control_id="test_benign",
            study_id="study_01",
            claim_id=claim.claim_id,
            transformation_type="input_permutation",
            description="Test benign control",
            parameters={},
            oracle_verified=True,
            oracle_verification_hash="abc123",
            sha256_original="orig",
            sha256_transformed="trans",
        )

        for vname, verifier in VERIFIERS.items():
            verdict = verifier.verify(claim, None, control)
            assert verdict.verdict == "PASS"
            assert verdict.is_benign_control


class TestEvaluation:
    """Test evaluation metrics."""

    def test_compute_mkr(self):
        # Create mock verdicts and mutants
        mutants = [
            MutationInstance(
                mutation_id="M01_test_000", operator="M01_DATA_LEAK", study_id="study_01",
                claim_id="c1", precondition="True", modification_description="test",
                artifacts_modified=[], diff_sha256="abc", violated_claim_condition="cond1",
                independent_oracle_result=True, magnitude=0.5, deterministic_replay_hash="r1",
                classification="valid_mutant", notes=""
            ),
            MutationInstance(
                mutation_id="M02_test_000", operator="M02_BASELINE_HANDICAP", study_id="study_01",
                claim_id="c1", precondition="True", modification_description="test",
                artifacts_modified=[], diff_sha256="def", violated_claim_condition="cond2",
                independent_oracle_result=True, magnitude=0.3, deterministic_replay_hash="r2",
                classification="valid_mutant", notes=""
            ),
        ]
        verdicts = [
            Verdict(
                verdict_id="v1", verifier_id="V0", verifier_version="R0",
                mutation_id="M01_test_000", is_benign_control=False, benign_control_id=None,
                verdict="FAIL", reasoning="test", confidence=0.9, abstention_evidence_missing=None,
                execution_error_message=None, wall_time_seconds=0.1, token_cost=0,
                timestamp="2026-09-20", prompt_version="v1"
            ),
            Verdict(
                verdict_id="v2", verifier_id="V0", verifier_version="R0",
                mutation_id="M02_test_000", is_benign_control=False, benign_control_id=None,
                verdict="PASS", reasoning="test", confidence=0.5, abstention_evidence_missing=None,
                execution_error_message=None, wall_time_seconds=0.1, token_cost=0,
                timestamp="2026-09-20", prompt_version="v1"
            ),
        ]
        controls = []

        mkr = compute_mkr(verdicts, mutants)
        assert mkr == 0.5  # 1 out of 2 killed

    def test_compute_bar(self):
        verdicts = [
            Verdict(
                verdict_id="v1", verifier_id="V0", verifier_version="R0",
                mutation_id=None, is_benign_control=True, benign_control_id="bc1",
                verdict="PASS", reasoning="test", confidence=0.95, abstention_evidence_missing=None,
                execution_error_message=None, wall_time_seconds=0.1, token_cost=0,
                timestamp="2026-09-20", prompt_version="v1"
            ),
        ]
        controls = [
            BenignControl(
                control_id="bc1", study_id="study_01", claim_id="c1",
                transformation_type="input_permutation", description="test",
                parameters={}, oracle_verified=True, oracle_verification_hash="h1",
                sha256_original="o", sha256_transformed="t"
            ),
        ]

        bar = compute_bar(verdicts, controls)
        assert bar == 1.0

    def test_compute_va(self):
        assert compute_va(0.5, 0.8) == 0.3
        assert compute_va(1.0, 1.0) == 1.0
        assert compute_va(0.0, 0.0) == -1.0


class TestIntegration:
    """Integration tests for full pipeline."""

    def test_full_pipeline_runs(self):
        """Test that the full experiment pipeline runs without errors."""
        studies = build_all_studies()
        mutants, benign_controls = generate_all_mutations(studies, min_per_family=3)
        mutants = verify_all_mutations(mutants, studies)

        valid_mutants = [m for m in mutants if m.classification == "valid_mutant"]
        assert len(valid_mutants) > 0
        assert len(benign_controls) > 0

        # Run verifiers on first study
        study = studies["study_01"]
        study_mutants = [m for m in mutants if m.study_id == "study_01"]
        study_benign = [b for b in benign_controls if b.study_id == "study_01"]

        verdicts = run_all_verifiers(study["claim"], study_mutants, study_benign)
        assert len(verdicts) == len(VERIFIERS)

    def test_results_are_deterministic(self):
        """Test that running the same experiment produces same results."""
        studies1 = build_all_studies()
        studies2 = build_all_studies()

        for sid in studies1:
            assert studies1[sid]["claim"].sha256() == studies2[sid]["claim"].sha256()
