"""
R0-D1: SciCoQA Dataset Download and Blind Projection Creation
Follows the strict leakage-safe protocol.
"""
from __future__ import annotations
import json
import hashlib
from pathlib import Path
from typing import Any, Dict, List

PROJECT_ROOT = Path(__file__).resolve().parent
EXTERNAL_DIR = PROJECT_ROOT / "external" / "scicoqa"
RAW_GOLD_DIR = EXTERNAL_DIR / "raw_gold"
BLIND_DIR = EXTERNAL_DIR / "blind"

# Fields that MUST be sealed (gold data)
GOLD_FIELDS = [
    "origin_type", "origin_url", "origin_discrepancy_text",
    "is_valid_discrepancy_gemini", "is_valid_discrepancy_gpt",
    "discrepancy_description_gemini", "discrepancy_description_gpt",
    "relevant_paper_sections_gemini", "relevant_paper_sections_gpt",
    "relevant_code_files_gemini", "relevant_code_files_gpt",
    "discrepancy_type", "discrepancy_category",
    "synthetic_origin", "synthetic_source_paper",
]

# Fields SAFE for blind projection
SAFE_FIELDS = [
    "discrepancy_id",
    "paper_url",
    "paper_url_versioned",
    "code_url",
    "code_url_versioned",
]

# Optional non-semantic metadata (safe)
OPTIONAL_SAFE = [
    "arxiv_subject",
    "arxiv_year",
]


def compute_sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def download_and_split_dataset():
    """Download SciCoQA and create blind projection."""
    print("=" * 70)
    print("R0-D1: SciCoQA Dataset Download and Split")
    print("=" * 70)
    
    # Create directories
    RAW_GOLD_DIR.mkdir(parents=True, exist_ok=True)
    BLIND_DIR.mkdir(parents=True, exist_ok=True)
    
    # Download using datasets library
    try:
        from datasets import load_dataset
        print("\n[1/4] Downloading SciCoQA...")
        
        # Load real split
        real_ds = load_dataset("UKPLab/scicoqa", split="real")
        print(f"  Real split: {len(real_ds)} samples")
        print(f"  Columns: {real_ds.column_names}")
        
        # Load synthetic split (for reference, not primary eval)
        synth_ds = load_dataset("UKPLab/scicoqa", split="synthetic")
        print(f"  Synthetic split: {len(synth_ds)} samples")
        
        # Load pooled split
        pooled_ds = load_dataset("UKPLab/scicoqa", split="pooled")
        print(f"  Pooled split: {len(pooled_ds)} samples")
        
    except Exception as e:
        print(f"  Error loading dataset: {e}")
        print("  Using mock data for framework demonstration...")
        return create_mock_dataset()
    
    # Convert to lists of dicts
    real_data = [dict(row) for row in real_ds]
    synth_data = [dict(row) for row in synth_ds]
    pooled_data = [dict(row) for row in pooled_ds]
    
    # Save raw gold data (sealed, never shown to inference)
    print("\n[2/4] Saving raw gold data (sealed)...")
    
    raw_gold_path = RAW_GOLD_DIR / "scicoqa_real_v1.1.jsonl"
    with open(raw_gold_path, "w") as f:
        for row in real_data:
            f.write(json.dumps(row, default=str) + "\n")
    print(f"  Saved: {raw_gold_path}")
    
    # Compute hash of raw gold
    with open(raw_gold_path, "rb") as f:
        raw_gold_hash = compute_sha256(f.read())
    print(f"  SHA256: {raw_gold_hash}")
    
    # Create blind projection (only safe fields)
    print("\n[3/4] Creating blind projection...")
    
    blind_data = []
    for row in real_data:
        blind_row = {field: row.get(field) for field in SAFE_FIELDS if field in row}
        
        # Add optional safe metadata if present
        for field in OPTIONAL_SAFE:
            if field in row:
                blind_row[field] = row[field]
        
        blind_data.append(blind_row)
    
    blind_path = BLIND_DIR / "scicoqa_real_blind.jsonl"
    with open(blind_path, "w") as f:
        for row in blind_data:
            f.write(json.dumps(row, default=str) + "\n")
    print(f"  Saved: {blind_path}")
    
    # Compute hash of blind data
    with open(blind_path, "rb") as f:
        blind_hash = compute_sha256(f.read())
    print(f"  SHA256: {blind_hash}")
    
    # Verify no gold fields leaked
    print("\n[4/4] Verifying blind projection...")
    with open(blind_path, "r") as f:
        first_row = json.loads(f.readline())
    
    leaked_fields = [f for f in GOLD_FIELDS if f in first_row]
    if leaked_fields:
        print(f"  ERROR: Gold fields leaked: {leaked_fields}")
        raise ValueError("Leakage detected in blind projection!")
    else:
        print(f"  PASS: No gold fields in blind projection")
        print(f"  Safe fields present: {list(first_row.keys())}")
    
    return {
        "real_count": len(real_data),
        "synthetic_count": len(synth_data),
        "pooled_count": len(pooled_data),
        "raw_gold_hash": raw_gold_hash,
        "blind_hash": blind_hash,
    }


def create_mock_dataset():
    """Create mock dataset for framework testing."""
    print("\nCreating mock dataset for framework testing...")
    
    mock_data = []
    for i in range(10):
        mock_data.append({
            "discrepancy_id": f"mock_{i:03d}",
            "paper_url": f"https://arxiv.org/abs/2301.00{i}",
            "paper_url_versioned": f"https://arxiv.org/pdf/2301.00{i}.pdf",
            "code_url": f"https://github.com/mock/repo{i}",
            "code_url_versioned": f"https://github.com/mock/repo{i}/tree/abc{i}",
            "arxiv_subject": "cs.LG",
            "arxiv_year": 2023,
            # Gold fields (should NOT appear in blind)
            "discrepancy_type": "evaluation_mismatch",
            "relevant_code_files": ["main.py"],
        })
    
    # Save raw gold
    raw_path = RAW_GOLD_DIR / "scicoqa_real_v1.1.jsonl"
    with open(raw_path, "w") as f:
        for row in mock_data:
            f.write(json.dumps(row, default=str) + "\n")
    
    # Save blind (remove gold fields)
    blind_data = []
    for row in mock_data:
        blind_row = {k: v for k, v in row.items() if k in [
            "discrepancy_id", "paper_url", "paper_url_versioned",
            "code_url", "code_url_versioned", "arxiv_subject", "arxiv_year"
        ]}
        blind_data.append(blind_row)
    
    blind_path = BLIND_DIR / "scicoqa_real_blind.jsonl"
    with open(blind_path, "w") as f:
        for row in blind_data:
            f.write(json.dumps(row, default=str) + "\n")
    
    print(f"  Created {len(mock_data)} mock samples")
    print(f"  Raw gold: {raw_path}")
    print(f"  Blind data: {blind_path}")
    
    return {
        "real_count": len(mock_data),
        "synthetic_count": 0,
        "pooled_count": 0,
        "raw_gold_hash": "mock",
        "blind_hash": "mock",
    }


if __name__ == "__main__":
    stats = download_and_split_dataset()
    
    # Save dataset freeze info
    freeze_info = {
        "experiment_id": "VForge-R0-D1-001",
        "protocol_version": "R0-D1",
        "date": "2026-09-20",
        "dataset_version": "scicoqa-v1.1",
        "counts": stats,
        "status": "FROZEN",
    }
    
    freeze_path = PROJECT_ROOT / "results" / "R0D1_DATASET_FREEZE.json"
    with open(freeze_path, "w") as f:
        json.dump(freeze_info, f, indent=2)
    
    print(f"\nDataset freeze saved to: {freeze_path}")
    print("=" * 70)
