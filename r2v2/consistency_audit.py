"""R2V2 Phase 11: programmatic manuscript<->frozen-artifact consistency audit.
Exit 0 iff NUMERIC_CONSISTENCY = PASS (all checks pass, no overstatements).
Re-run after any manuscript edit.
"""
import json, csv, pathlib, re, sys
from collections import Counter

ROOT = pathlib.Path(__file__).resolve().parent.parent
MAN = ROOT / "paper/R2_MANUSCRIPT_V2.md"
ABS = ROOT / "paper/R2_ABSTRACT_V2.md"

def load_gt():
    pairsA = [json.loads(l) for l in open(ROOT/"results/R1A_PAIR_RESULTS.jsonl", encoding="utf-8") if l.strip()]
    pairsB = [json.loads(l) for l in open(ROOT/"results/R1B1_REAL_TRACE_PAIRS.jsonl", encoding="utf-8") if l.strip()]
    vpvd = list(csv.DictReader(open(ROOT/"results/R1B1_VPVD.csv", encoding="utf-8")))
    nm = json.loads((ROOT/"r1c/results/R1C_NATURALISTIC_METRICS.json").read_text(encoding="utf-8"))
    r1d = list(csv.DictReader(open(ROOT/"r1d/results/R1D_LEAD_ADJUDICATION.csv", encoding="utf-8")))
    A_correct = sum(1 for p in pairsA if p.get("tc_pair_correct") in (True,"True",1,"1"))
    B_correct = sum(1 for p in pairsB if p.get("sec_pair_correct") in (True,"True",1,"1"))
    B_vps = sum(1 for p in pairsB if p.get("value_preserving") in (True,"True",1,"1"))
    B4 = sum(1 for p in pairsB if p.get("b4_result_matching_separates") in (True,"True",1,"1"))
    repos = set(p.get("paper") for p in pairsB)
    D_conf = sum(1 for r in r1d if r.get("status")=="CONFIRMED")
    D_status = dict(Counter(r.get("status") for r in r1d))
    return dict(
        A_n=len(pairsA), A_correct=A_correct, B_n=len(pairsB), B_correct=B_correct,
        B_vps=B_vps, B4=B4, n_repos=len(repos), repos=repos,
        NVR=nm.get("naturalistic_violation_recall"), NPCR=nm.get("npcr"),
        CIA=nm.get("cia"), witness=nm.get("witness_accuracy"),
        D_n=len(r1d), D_conf=D_conf, D_status=D_status,
    )

def main():
    gt = load_gt()
    text = MAN.read_text(encoding="utf-8") + "\n" + ABS.read_text(encoding="utf-8")
    checks = []
    def chk(d, c): checks.append((d, bool(c)))

    chk("R1-A 27/30 present", "27/30" in text)
    chk("R1-A PSD 0.900 present", "0.900" in text)
    chk("R1-A 30/30 labeled pair-construction", ("pair-construction" in text or "construction property" in text))
    chk("R1-A CI 0.735/0.994", "0.735" in text and "0.994" in text)
    chk("R1-B1 48 present", "48" in text)
    chk("R1-B1 48/48 present", "48/48" in text)
    chk("R1-B1 36 strict present", "36" in text and "strict" in text.lower())
    chk("R1-B1 2 repos present", "2 public" in text or "two public repositories" in text or "2 repositories" in text)
    chk("R1-B1 B4 0/48", "0/48" in text)
    chk("R1-B1 VPS strict mean 0.181", "0.181" in text)
    chk("R1-B1 VPS all mean 0.250", "0.250" in text)
    chk("R1-B1 VPS max 0.651", "0.651" in text)
    chk("R1-C 8/8 present", "8/8" in text)
    chk("R1-C CI 0.631", "0.631" in text)
    chk("R1-C 5 EXPLICIT / 3 PRINCIPLE", "5 EXPLICIT" in text and "3 PRINCIPLE" in text)
    chk("R1-D2 476 present", "476" in text)
    chk("R1-D2 0 confirmed/adding 0", "0 confirmed" in text or "0 additional" in text or "adding 0" in text)
    chk("R1-D2 upper bound 0.77", "0.77" in text)
    chk("R1-D2 breakdown 428/24/15/9", all(x in text for x in ["428","24","15","9"]))
    chk("6 quota-blocked repos named", all(x in text for x in ["dinov2","bert","evaluate","flax","evalplus","Barlow"]))
    # value-correctness
    chk("A_correct==27", gt["A_correct"]==27)
    chk("A_n==30", gt["A_n"]==30)
    chk("B_correct==48", gt["B_correct"]==48)
    chk("B_vps==36", gt["B_vps"]==36)
    chk("n_repos==2", gt["n_repos"]==2)
    chk("B4==0", gt["B4"]==0)
    chk("NVR==1.0", gt["NVR"]==1.0)
    chk("D_conf==0", gt["D_conf"]==0)
    chk("D_n==476", gt["D_n"]==476)
    # overstatement scan
    over = []
    for bad in ["100% accuracy","detects real scientific errors with 100",
                "PSD = 1.0","30/30 pairs separated","30/30 = 1.0",
                "48 value-preserving pairs across 4","four independent public repositories",
                "guarantees scientific validity","automatically determines truth",
                "revolutionary","unprecedented","fundamentally transforms",
                "100% pair-correct","determines scientific truth"]:
        if bad in text: over.append(bad)
    # '4 repositories'/'across 4' allowed ONLY in R1-D2 search-scope context
    for m in re.finditer(r"(4 repositories|across 4)", text):
        ctx = text[max(0,m.start()-40):m.end()+40]
        if not ("ALBERT" in ctx or "YOLOv7" in ctx or "476" in ctx or "4-repo" in text[max(0,m.start()-40):m.end()+40]):
            over.append(f"stale '4 repo' outside R1-D2 scope: {ctx[:40]!r}")

    fails = [d for d,c in checks if not c]
    print(f"checks {sum(1 for c in [x[1] for x in checks] if c)}/{len(checks)} passed")
    if fails: print("FAILED:", fails)
    if over: print("OVERSTATEMENTS:", over)
    print(f"NUMERIC_CONSISTENCY = {'PASS' if (not fails and not over) else 'FAIL'}")
    return 0 if (not fails and not over) else 1

if __name__ == "__main__":
    sys.exit(main())
