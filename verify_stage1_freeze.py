"""
Stage1b freeze integrity checker.

Verifies that all R1-B1 Stage1 frozen files still match the
freeze manifest. If any file has been modified, the Stage1b
evaluation must be re-run.
"""
from __future__ import annotations

import json
import hashlib
from pathlib import Path
from datetime import datetime

PROJECT_ROOT = Path(__file__).resolve().parent
MANIFEST = PROJECT_ROOT / "reports/R1B1_STAGE1_FREEZE_MANIFEST.json"


def verify_freeze() -> bool:
    manifest = json.loads(MANIFEST.read_text())
    all_ok = True
    for rel_path, info in manifest["files"].items():
        p = PROJECT_ROOT / rel_path
        if not p.exists():
            print(f"  MISSING: {rel_path}")
            all_ok = False
            continue
        content = p.read_bytes()
        actual_sha = hashlib.sha256(content).hexdigest()
        if actual_sha != info["sha256"]:
            print(f"  MODIFIED: {rel_path}")
            print(f"    expected: {info['sha256'][:24]}...")
            print(f"    actual:   {actual_sha[:24]}...")
            all_ok = False
        else:
            print(f"  OK: {rel_path}  ({info['size']} bytes)")
    return all_ok


if __name__ == "__main__":
    print("Stage1 freeze verification:")
    ok = verify_freeze()
    print(f"\n{'ALL OK - Stage1 intact' if ok else 'INTEGRITY VIOLATION - Stage1 modified'}")
    if ok:
        print(f"Verified: {datetime.now().isoformat()}")
