"""
R0-D1: Paper Claim Miner
Extracts implementation-relevant scientific claims from paper text ONLY.
"""
from __future__ import annotations
import json
import hashlib
import re
from pathlib import Path
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field, asdict


@dataclass
class MinedClaim:
    """A claim extracted from paper text."""
    claim_id: str
    claim_text: str
    claim_type: str  # MODEL_ARCHITECTURE, ALGORITHM, LOSS, DATA_USAGE, etc.
    paper_section: str
    paper_span: str
    normative_requirement: str
    expected_implementation_observable: str
    confidence: float
    
    def to_dict(self):
        return asdict(self)
    
    def sha256(self) -> str:
        raw = json.dumps(self.to_dict(), sort_keys=True).encode()
        return hashlib.sha256(raw).hexdigest()


class PaperClaimMiner:
    """Mine implementation-relevant claims from paper text."""
    
    # Claim type patterns
    CLAIM_PATTERNS = {
        "MODEL_ARCHITECTURE": [
            r"(?:proposes?|introduces?|presents?)\s+(?:a\s+)?(?:new\s+)?([^,.]+(?:network|architecture|model|framework))",
            r"the\s+(?:proposed|new|our)\s+(?:method|model|approach)\s+(?:consists|comprises|is\s+composed)\s+of\s+([^,.]+)",
        ],
        "ALGORITHM": [
            r"we\s+(propose|introduce|present)\s+([^,.]+(?:algorithm|method|approach|technique))",
            r"the\s+(?:proposed|new)\s+(?:algorithm|method)\s+works\s+by\s+([^,.]+)",
        ],
        "LOSS": [
            r"(?:loss|objective)\s+(?:function\s+)?(?:is|defined\s+as|given\s+by)\s+([^,.]+)",
            r"we\s+optimize\s+([^,.]+)",
        ],
        "DATA_USAGE": [
            r"(?:train|evaluate|test)\s+(?:on|using|with)\s+([^,.]+(?:dataset|data))",
            r"the\s+dataset\s+(?:consists|contains|comprises)\s+([^,.]+)",
            r"we\s+use\s+([^,.]+)\s+(?:for|to)",
        ],
        "PREPROCESSING": [
            r"(?:preprocess|normalize|augment)\s+([^,.]+)",
            r"data\s+(?:preprocessing|augmentation)\s+(?:involves|includes)\s+([^,.]+)",
        ],
        "TRAINING": [
            r"we\s+(train|optimize)\s+(?:the\s+)?model\s+([^,.]+)",
            r"(?:training|optimization)\s+(?:is\s+)?([^,.]+)",
        ],
        "OPTIMIZATION": [
            r"(?:optimizer|optimization)\s+(?:is|uses)\s+([^,.]+)",
            r"we\s+use\s+([^,.]+)\s+(?:optimizer|algorithm)",
        ],
        "HYPERPARAMETER_PROTOCOL": [
            r"(?:learning\s+rate|lr|batch\s+size|epochs?|dropout)\s+(?:is|of|:)\s*(\d+\.?\d*)",
            r"hyperparameters\s+(?:include|are)\s+([^,.]+)",
        ],
        "SELECTION": [
            r"(?:select|choose|pick)\s+(?:the\s+)?([^,.]+)\s+(?:based\s+on|using|from)",
            r"(?:validation|selection)\s+(?:set|data)\s+([^,.]+)",
        ],
        "EVALUATION": [
            r"we\s+(evaluate|assess|test)\s+(?:on|using|with)\s+([^,.]+)",
            r"(?:evaluation|experimental)\s+(?:setup|protocol)\s+([^,.]+)",
        ],
        "METRIC": [
            r"(?:metric|measure)\s+(?:is|includes|uses)\s+([^,.]+)",
            r"we\s+report\s+(?:the\s+)?([^,.]+)",
            r"(accuracy|precision|recall|F1|AUC|RMSE|MSE)\s+(?:of|:)\s*(\d+\.?\d*)",
        ],
        "AGGREGATION": [
            r"(?:aggregate|average|mean)\s+([^,.]+)",
            r"results\s+(?:are|were)\s+(?:aggregated|averaged)\s+([^,.]+)",
        ],
        "STATISTICS": [
            r"(?:statistical\s+)?(?:test|significance)\s+(?:is|was)\s+([^,.]+)",
            r"(?:p-value|confidence|interval)\s+([^,.]+)",
        ],
    }
    
    def __init__(self):
        self.claim_counter = 0
        self.mined_claims: List[MinedClaim] = []
    
    def mine(self, paper_text: str, paper_id: str) -> List[MinedClaim]:
        """Mine claims from paper text."""
        self.claim_counter = 0
        self.mined_claims = []
        
        # Split into sentences
        sentences = [s.strip() for s in paper_text.split('.') if len(s.strip()) > 20]
        
        for sentence in sentences:
            for claim_type, patterns in self.CLAIM_PATTERNS.items():
                for pattern in patterns:
                    match = re.search(pattern, sentence, re.IGNORECASE)
                    if match:
                        self.claim_counter += 1
                        claim_text = match.group(0) if match.lastindex is None else match.group(1)
                        
                        # Determine normative requirement
                        normative = self._derive_normative_requirement(claim_type, claim_text)
                        
                        # Determine expected observable
                        observable = self._derive_expected_observable(claim_type)
                        
                        claim = MinedClaim(
                            claim_id=f"{paper_id}_CLAIM_{self.claim_counter:03d}",
                            claim_text=claim_text[:200],
                            claim_type=claim_type,
                            paper_section=self._detect_section(sentence),
                            paper_span=sentence[:100],
                            normative_requirement=normative,
                            expected_implementation_observable=observable,
                            confidence=self._estimate_confidence(claim_type, claim_text),
                        )
                        
                        self.mined_claims.append(claim)
                        break  # Only first match per pattern
        
        return self.mined_claims
    
    def _derive_normative_requirement(self, claim_type: str, claim_text: str) -> str:
        """Derive normative requirement from claim type."""
        requirements = {
            "MODEL_ARCHITECTURE": "Implementation must match described architecture",
            "ALGORITHM": "Implementation must follow described algorithm",
            "LOSS": "Implementation must use specified loss function",
            "DATA_USAGE": "Implementation must use specified data",
            "PREPROCESSING": "Implementation must apply described preprocessing",
            "TRAINING": "Implementation must follow training protocol",
            "OPTIMIZATION": "Implementation must use specified optimizer",
            "HYPERPARAMETER_PROTOCOL": "Implementation must use specified hyperparameters",
            "SELECTION": "Selection must use held-out data, not test data",
            "EVALUATION": "Evaluation must follow described protocol",
            "METRIC": "Reported metrics must match computed values",
            "AGGREGATION": "Aggregation must be faithful to raw computations",
            "STATISTICS": "Statistical claims must have supporting evidence",
        }
        return requirements.get(claim_type, "Implementation must be consistent with claim")
    
    def _derive_expected_observable(self, claim_type: str) -> str:
        """Derive what to look for in code."""
        observables = {
            "MODEL_ARCHITECTURE": "model class definition, layer specifications",
            "ALGORITHM": "algorithm implementation, key functions",
            "LOSS": "loss function definition, loss computation",
            "DATA_USAGE": "data loading, dataset specification",
            "PREPROCESSING": "preprocessing pipeline, normalization code",
            "TRAINING": "training loop, training configuration",
            "OPTIMIZATION": "optimizer initialization, optimization settings",
            "HYPERPARAMETER_PROTOCOL": "hyperparameter values in config/scripts",
            "SELECTION": "validation split usage, selection procedure",
            "EVALUATION": "evaluation code, metric computation",
            "METRIC": "metric computation, reported values",
            "AGGREGATION": "aggregation code, summary statistics",
            "STATISTICS": "statistical tests, p-values, confidence intervals",
        }
        return observables.get(claim_type, "corresponding code implementation")
    
    def _detect_section(self, sentence: str) -> str:
        """Detect which section the claim likely comes from."""
        sentence_lower = sentence.lower()
        if any(kw in sentence_lower for kw in ["method", "approach", "model", "network"]):
            return "Method"
        elif any(kw in sentence_lower for kw in ["dataset", "data", "benchmark"]):
            return "Data"
        elif any(kw in sentence_lower for kw in ["experiment", "result", "performance"]):
            return "Experiment"
        elif any(kw in sentence_lower for kw in ["train", "optimiz", "hyperparameter"]):
            return "Training"
        elif any(kw in sentence_lower for kw in ["implement", "code", "algorithm"]):
            return "Implementation"
        return "General"
    
    def _estimate_confidence(self, claim_type: str, claim_text: str) -> float:
        """Estimate confidence in the extracted claim."""
        # Higher confidence for clearer, more specific claims
        if any(kw in claim_text.lower() for kw in ["achieves", "outperforms", "state-of-the-art"]):
            return 0.9
        elif len(claim_text) > 50:
            return 0.8
        elif any(kw in claim_text.lower() for kw in ["proposed", "new", "novel"]):
            return 0.75
        return 0.6
    
    def freeze_and_hash(self) -> str:
        """Freeze mined claims and compute hash."""
        if not self.mined_claims:
            return ""
        
        claims_data = [c.to_dict() for c in self.mined_claims]
        raw = json.dumps(claims_data, sort_keys=True).encode()
        return hashlib.sha256(raw).hexdigest()
    
    def save(self, output_path: Path):
        """Save mined claims to file."""
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w") as f:
            for claim in self.mined_claims:
                f.write(json.dumps(claim.to_dict()) + "\n")


# Test the claim miner
if __name__ == "__main__":
    miner = PaperClaimMiner()
    
    sample_paper = """
    We propose a novel deep learning architecture for image classification.
    Our model achieves 95.2% accuracy on CIFAR-10, outperforming ResNet-18.
    We train on the training split and evaluate on the held-out test set.
    The loss function is cross-entropy. We use Adam optimizer with learning rate 0.001.
    Models were selected using validation performance.
    """
    
    claims = miner.mine(sample_paper, "test_paper")
    print(f"Mined {len(claims)} claims:")
    for c in claims:
        print(f"  [{c.claim_type}] {c.claim_text[:60]}...")
    
    hash_val = miner.freeze_and_hash()
    print(f"\nFrozen claims hash: {hash_val}")
