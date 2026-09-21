"""
V-Forge R0-B: Blind Artifact Packaging System
Ensures verifiers receive only study artifacts without mutation metadata.
"""
from __future__ import annotations
import json
import numpy as np
from pathlib import Path
from typing import Any, Optional
import copy
import core
from core import Claim, MutationInstance, BenignControl, SEED


class BlindArtifactPackager:
    """Packages study artifacts for blind verifier evaluation.
    
    Removes all mutation metadata, renames files, and ensures
    verifiers cannot infer mutation type from artifacts.
    """
    
    # Patterns to remove from artifact keys
    LEAKAGE_PATTERNS = [
        "leak_info", "corrupted_labels", "evaluation_labels",
        "original_seed", "selected_seed", "dropped_subgroup",
        "swapped_from", "swapped_to", "aggregation_method",
        "selection_criteria", "n_kept", "n_removed",
        "preprocess_statistic", "original_preprocess",
        "reported_metric", "magnitude"
    ]
    
    # Mutation-related strings to replace
    MUTATION_STRINGS = {
        "data_leak": "artifact_modification_a",
        "baseline_handicap": "artifact_modification_b",
        "seed_cherry_pick": "artifact_modification_c",
        "subgroup_drop": "artifact_modification_d",
        "metric_swap": "artifact_modification_e",
        "aggregation_fault": "artifact_modification_f",
        "test_set_selection": "artifact_modification_g",
        "preprocess_asymmetry": "artifact_modification_h",
        "M01_DATA_LEAK": "mutation_variant_alpha",
        "M02_BASELINE_HANDICAP": "mutation_variant_beta",
        "M03_SEED_CHERRY_PICK": "mutation_variant_gamma",
        "M04_SUBGROUP_DROP": "mutation_variant_delta",
        "M05_METRIC_SWAP": "mutation_variant_epsilon",
        "M06_AGGREGATION_FAULT": "mutation_variant_zeta",
        "M07_TEST_SET_SELECTION": "mutation_variant_eta",
        "M08_PREPROCESS_ASYMMETRY": "mutation_variant_theta",
    }
    
    def __init__(self):
        self.rename_map = {}
        
    def package_study(self, study_id: str, study_data: dict, claim: Claim) -> dict:
        """Package study data for blind evaluation.
        
        Returns a dictionary with only the artifacts verifiers should see:
        - claim (sanitized)
        - dataset (sanitized)
        - models (if applicable)
        - results (sanitized)
        
        All mutation metadata is removed.
        """
        # Deep copy to avoid modifying original
        packaged = copy.deepcopy(study_data)
        
        # Remove all leakage patterns
        packaged = self._remove_leakage_patterns(packaged)
        
        # Replace mutation strings in descriptions
        packaged = self._sanitize_strings(packaged)
        
        # Rename internal keys to neutral names
        packaged = self._rename_keys(packaged)
        
        # Create clean claim (without mutation hints)
        claim_dict = claim.to_dict()
        claim_dict["natural_language_claim"] = self._sanitize_claim(claim_dict["natural_language_claim"])
        
        return {
            "study_id": study_id,
            "claim": claim_dict,
            "data": packaged.get("raw_data", packaged),
            "artifacts": {
                k: v for k, v in packaged.items() 
                if k not in ["raw_data", "claim", "X_train", "X_test", "y_train", "y_test", "subgroup"]
            }
        }
    
    def _remove_leakage_patterns(self, data: Any) -> Any:
        """Recursively remove keys that leak mutation information."""
        if isinstance(data, dict):
            result = {}
            for k, v in data.items():
                # Skip leakage-pattern keys
                if any(pattern in k.lower() for pattern in self.LEAKAGE_PATTERNS):
                    continue
                result[k] = self._remove_leakage_patterns(v)
            return result
        elif isinstance(data, list):
            return [self._remove_leakage_patterns(item) for item in data]
        return data
    
    def _sanitize_strings(self, data: Any) -> Any:
        """Replace mutation-related strings with neutral alternatives."""
        if isinstance(data, str):
            for old, new in self.MUTATION_STRINGS.items():
                data = data.replace(old, new)
            return data
        elif isinstance(data, dict):
            return {k: self._sanitize_strings(v) for k, v in data.items()}
        elif isinstance(data, list):
            return [self._sanitize_strings(item) for item in data]
        return data
    
    def _rename_keys(self, data: Any, prefix: str = "") -> Any:
        """Rename keys to neutral names."""
        if isinstance(data, dict):
            result = {}
            for k, v in data.items():
                # Sanitize key names
                clean_key = self._sanitize_strings(k)
                result[clean_key] = self._rename_keys(v, prefix + "_" + clean_key)
            return result
        elif isinstance(data, list):
            return [self._rename_keys(item, prefix) for item in data]
        return data
    
    def _sanitize_claim(self, claim_text: str) -> str:
        """Remove mutation hints from claim text."""
        sanitized = claim_text
        for old, new in self.MUTATION_STRINGS.items():
            sanitized = sanitized.replace(old, new)
        return sanitized
    
    def package_mutant(self, mutant: MutationInstance, packaged_study: dict) -> dict:
        """Package a single mutant for blind evaluation.
        
        Returns only what the verifier should see:
        - The modified artifacts (without mutation metadata)
        - The original claim
        """
        # Get the mutated study data
        mutated_data = mutant.to_dict()
        
        # Remove all mutation metadata
        sanitized = self._remove_leakage_patterns(mutated_data)
        sanitized = self._sanitize_strings(sanitized)
        
        # Return only the artifact differences (not the mutation type)
        return {
            "study_id": mutant.study_id,
            "packaged_study": packaged_study,
            "modified_artifacts": sanitized,
            "artifact_diff_hash": mutant.diff_sha256,  # Only hash, not content
        }
    
    def verify_blindness(self, packaged: dict) -> bool:
        """Verify that packaged data doesn't contain leakage."""
        serialized = json.dumps(packaged, sort_keys=True).lower()
        
        for pattern in self.LEAKAGE_PATTERNS:
            if pattern.lower() in serialized:
                return False
        
        for old in self.MUTATION_STRINGS.keys():
            if old.lower() in serialized:
                return False
        
        return True


def create_blind_evaluation_dataset(studies: dict) -> tuple[list[dict], list[dict]]:
    """Create blind evaluation datasets for verifiers.
    
    Returns:
        - Original studies (packaged)
        - Mutant evaluations (packaged, without mutation metadata)
    """
    packager = BlindArtifactPackager()
    
    original_studies = []
    mutant_evaluations = []
    
    for study_id, study_data in studies.items():
        claim = study_data["claim"]
        
        # Package original study
        packaged_original = packager.package_study(study_id, study_data, claim)
        original_studies.append(packaged_original)
        
        # Verify blindness
        assert packager.verify_blindness(packaged_original), \
            f"Packaging failed blindness check for {study_id}"
    
    return original_studies, mutant_evaluations
