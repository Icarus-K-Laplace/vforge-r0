"""Extract Delta Attention paper text + check for public trace source."""
import pdfplumber, re, urllib.request, ssl, json, time

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

# 1. Extract text
t = ""
pdf = pdfplumber.open("stage1b/papers/DELTA_ATTENTION_2605.18855.pdf")
for p in pdf.pages:
    t += (p.extract_text() or "") + "\n"
open("stage1b/papers/DELTA_ATTENTION.txt", "w").write(t)
print(f"Delta Attention text: {len(t)} chars")

# 2. Show abstract
abs_m = re.search(r"Abstract\s*[:.]?\s*(.{200,700})", t, re.S)
print("\n=== Abstract ===")
print(re.sub(r"\s+", " ", abs_m.group(1))[:600] if abs_m else "not found")

# 3. Protocol mentions
low = t.lower()
print("\n=== Protocol keywords ===")
for kw in ["seed", "mean", "std", "aggregat", "run", "dataset", "backbone", "model size", "epoch", "table"]:
    matches = list(re.finditer(re.escape(kw), low))
    if matches:
        print(f"\n[{kw}] ({len(matches)} matches):")
        for m in matches[:3]:
            s = max(0, m.start()-120)
            e = min(len(t), m.end()+120)
            print(f"  ...{re.sub(chr(10), ' ', t[s:e])}...")

# 4. Check for a repo / trace source
print("\n=== Repo / trace source ===")
for m in re.finditer(r"(github\.com/[A-Za-z0-9_./-]+|wandb\.ai/[A-Za-z0-9_/-]+|huggingface\.co/[A-Za-z0-9_/-]+)", t):
    print(" ", m.group(1))
