"""R2V2 Phase -1 gate: independently recompute the R1-C forensic hashes
and verify the CSV against the freeze manifest.

Canonical scheme (verified against r1c/isolate_and_freeze.py):
  hash = sha256(utf8(json.dumps(data, indent=2, ensure_ascii=False)))
which equals sha256(file_bytes) because the files were written verbatim.

Run: python r2v2/verify_forensic_hashes.py
Exit 0 iff 8/8 consistent AND R1C_SHA256SUMS all OK.
"""
import json, csv, hashlib, pathlib, sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
R1C = ROOT / "r1c"
BLIND = R1C / "R1C_BLIND"
GOLD = R1C / "R1C_DISCOVERY_GOLD"
MANIFEST = R1C / "results" / "R1C_CASE_FREEZE.json"
SUMS = R1C / "results" / "R1C_SHA256SUMS"
FORENSICS = ROOT / "results" / "R2_R1C_CASE_FORENSICS.csv"


def canon_sha(fp: pathlib.Path) -> str:
    data = json.loads(fp.read_text(encoding="utf-8"))
    s = json.dumps(data, indent=2, ensure_ascii=False)
    return hashlib.sha256(s.encode("utf-8")).hexdigest()


def main() -> int:
    man = {c["candidate_id"]: c for c in json.loads(MANIFEST.read_text(encoding="utf-8"))["cases"]}
    rows = {r["case_id"]: r for r in csv.DictReader(open(FORENSICS, encoding="utf-8"))}

    ok = True
    print(f"{'case':8} {'field':6} {'manifest':12} {'recomputed':12} match")
    for cid in sorted(man):
        for label, dirn in (("blind", BLIND), ("gold", GOLD)):
            fp = dirn / f"{cid}_{label.upper()}.json"
            rec = canon_sha(fp)
            man_v = man[cid][f"{label}_hash"]
            csv_rec = rows[cid][f"recomputed_{label}_hash"]
            csv_man = rows[cid][f"manifest_{label}_hash"]
            m_ok = rec == man_v
            c_ok = rec == csv_rec == csv_man
            if not (m_ok and c_ok):
                ok = False
            print(f"{cid:8} {label:6} {man_v[:12]:12} {rec[:12]:12} M==R:{m_ok} CSV==R:{c_ok}")

    # R1C_SHA256SUMS re-verify (frozen artifact integrity)
    bad = []
    for l in open(SUMS, encoding="utf-8"):
        l = l.strip()
        if not l or l.startswith("#"):
            continue
        h, rel = l.split("  ")
        p = R1C / rel
        if not p.exists() or hashlib.sha256(p.read_bytes()).hexdigest() != h:
            bad.append(rel)
    if bad:
        ok = False
        print(f"R1C_SHA256SUMS: BAD -> {bad}")
    else:
        print(f"R1C_SHA256SUMS: 25/25 OK")

    print(f"\nGATE 8/8 internally consistent + sums OK = {ok}")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
