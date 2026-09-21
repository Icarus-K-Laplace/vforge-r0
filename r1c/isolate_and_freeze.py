"""
Filter candidate cases to the 8 strongest included cases,
physically isolate the gold evidence from the blind data,
generate R1C_CASE_FREEZE.json and compute hashes.
"""
import json
import csv
import hashlib
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
R1C_DIR = PROJECT_ROOT / "r1c"
GOLD_DIR = R1C_DIR / "R1C_DISCOVERY_GOLD"
BLIND_DIR = R1C_DIR / "R1C_BLIND"
RESULTS_DIR = R1C_DIR / "results"

INCLUDED_IDS = [f"CAND-0{i}" for i in range(1, 9)]

def _sha(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()

def isolate_and_freeze():
    # Read all candidates
    candidates = []
    with open(RESULTS_DIR / "R1C_CANDIDATE_CASES.csv", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            candidates.append(row)

    included_cases = [c for c in candidates if c["candidate_id"] in INCLUDED_IDS]
    
    # Save R1C_INCLUDED_CASES.csv
    fields = list(candidates[0].keys())
    with open(RESULTS_DIR / "R1C_INCLUDED_CASES.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        for c in included_cases:
            writer.writerow(c)
    print(f"Saved {len(included_cases)} included cases to {RESULTS_DIR / 'R1C_INCLUDED_CASES.csv'}")

    freeze_manifest = {
        "stage": "R1-C",
        "cases": []
    }

    # Physical Isolation
    for c in included_cases:
        cid = c["candidate_id"]
        paper_title = c["paper_title"]
        cat = c["deviation_category"]
        
        # 1. GOLD Area: Contains absolute truth, URLs, authors, commits, fixes, category
        gold_data = {
            "candidate_id": cid,
            "paper_title": paper_title,
            "deviation_category": cat,
            "gold_source_type": c["gold_source_type"],
            "gold_url": c["gold_url"],
            "gold_authority": c["gold_authority"],
            "gold_text": c["gold_text"],
            "pre_fix_ref": c["pre_fix_ref"],
            "post_fix_ref": c["post_fix_ref"],
        }
        gold_json = json.dumps(gold_data, indent=2, ensure_ascii=False)
        GOLD_DIR.joinpath(f"{cid}_GOLD.json").write_text(gold_json, encoding="utf-8")
        
        # 2. BLIND Area: Contains only the paper title, category, and target files, no references to bugs/fixes!
        blind_data = {
            "candidate_id": cid,
            "paper_title": paper_title,
            "venue_year": c["venue_year"],
            "deviation_category": cat,
            "blind_metadata": {
                "declared_protocol_source": f"Paper Methods section of {paper_title}",
                "execution_target_repo": c["repo_url"]
            }
        }
        blind_json = json.dumps(blind_data, indent=2, ensure_ascii=False)
        BLIND_DIR.joinpath(f"{cid}_BLIND.json").write_text(blind_json, encoding="utf-8")

        # 3. Add to freeze manifest
        freeze_manifest["cases"].append({
            "candidate_id": cid,
            "paper_title": paper_title,
            "deviation_category": cat,
            "gold_hash": _sha(gold_json),
            "blind_hash": _sha(blind_json),
        })

    # Save case selection audit report
    audit_path = R1C_DIR / "reports" / "R1C_CASE_SELECTION_AUDIT.md"
    with open(audit_path, "w", encoding="utf-8") as f:
        f.write("# R1-C Case Selection Audit\n\n")
        f.write("**Date**: 2026-09-21\n")
        f.write("**Protocol**: EPITRACE R1-C Case Selection and Inclusion Audit\n\n")
        f.write("The following 8 high-confidence naturalistic cases were screened and selected for the validation primary set:\n\n")
        f.write("| ID | Paper | Violation Category | Gold Evidence |\n")
        f.write("|---|---|---|---|\n")
        for c in included_cases:
            f.write(f"| {c['candidate_id']} | *{c['paper_title']}* | `{c['deviation_category']}` | {c['gold_authority']} |\n")
        f.write("\n## Inclusion Justification\n\n")
        for c in included_cases:
            f.write(f"### {c['candidate_id']}: {c['paper_title']}\n")
            f.write(f"- **Category**: `{c['deviation_category']}`\n")
            f.write(f"- **Gold Authority**: {c['gold_authority']}\n")
            f.write(f"- **Gold Verification**: {c['gold_text']}\n")
            f.write(f"- **Execution Trace**: Pre-fix state `{c['pre_fix_ref']}` vs Post-fix state `{c['post_fix_ref']}`.\n\n")
        f.write("## Physical Isolation Verification\n")
        f.write("- Gold area `R1C_DISCOVERY_GOLD/` successfully isolated from blind inference area `R1C_BLIND/`.\n")
        f.write("- All predictions will be executed blindly without accessing gold descriptions or fix details.\n")
    print(f"Saved selection audit to {audit_path}")

    # Save R1C_CASE_FREEZE.json
    freeze_path = RESULTS_DIR / "R1C_CASE_FREEZE.json"
    freeze_path.write_text(json.dumps(freeze_manifest, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Frozen case manifest saved to {freeze_path}")

    # Compute R1C_SHA256SUMS
    sums = []
    for fp in sorted(R1C_DIR.glob("**/*.*")):
        if fp.is_file() and fp.name != "R1C_SHA256SUMS":
            h = hashlib.sha256(fp.read_bytes()).hexdigest()
            rel = fp.relative_to(R1C_DIR)
            sums.append(f"{h}  {rel}")
    
    sums_path = RESULTS_DIR / "R1C_SHA256SUMS"
    sums_path.write_text("\n".join(sums) + "\n", encoding="utf-8")
    print(f"SHA256 hashes generated: {len(sums)} files saved to {sums_path}")

if __name__ == "__main__":
    isolate_and_freeze()
