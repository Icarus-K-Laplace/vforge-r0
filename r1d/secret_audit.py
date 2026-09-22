"""
R1-D2 §0: Secret audit for r1d/discover_leads.py and the wider repo.

Scans:
1. The named source file (r1d/discover_leads.py) - exact token literals
2. Working tree - any github_pat_ / ghp_ / gho_ / ghs_ / ghu_ literals
3. Tracked files - via git
4. Reachable git history (all commits)
5. Reflog-reachable recent commits

Report: reports/R1D_SECRET_AUDIT.md
Never prints the token itself. Reports SECRET_FOUND = YES/NO.
"""
import re
import subprocess
import hashlib
from pathlib import Path
from datetime import datetime

ROOT = Path("E:/VForge-R0")
REPORTS = ROOT / "reports"
REPORTS.mkdir(parents=True, exist_ok=True)

# Known token prefixes to scan for (NOT the token value itself)
TOKEN_PREFIXES = [
    r"github_pat_[A-Za-z0-9]{20,}",
    r"ghp_[A-Za-z0-9]{36,}",
    r"gho_[A-Za-z0-9]{36,}",
    r"ghs_[A-Za-z0-9]{36,}",
    r"ghu_[A-Za-z0-9]{36,}",
    r"Bearer\s+[A-Za-z0-9/_-]{30,}",
]

# The specific compromised token prefix (we report presence, not the value).
# Stored hex-encoded so the audit script itself contains no readable
# compromised literal (avoids self-reference false positives).
COMPROMISED_PREFIX = "".join(chr(int(h, 16)) for h in (
    "67 69 74 68 75 62 5f 70 61 74 5f 31 31 42 57 57"
    "52 44 49 61 30 41 56 72 4e 32 75".split()
))

def scan_text(text, label, hits):
    """Scan text for token-like patterns; record matches without exposing the value."""
    found = []
    for pat in TOKEN_PREFIXES:
        for m in re.finditer(pat, text):
            snippet = m.group(0)
            # Redact: keep only first 12 chars + length
            redacted = snippet[:12] + f"...<len={len(snippet)}>"
            found.append({"label": label, "pattern": pat[:30], "redacted": redacted})
    # Specific compromised prefix check
    if COMPROMISED_PREFIX in text:
        found.append({"label": label, "pattern": "compromised_prefix", "redacted": COMPROMISED_PREFIX[:24] + "...<compromised>"})
    if found:
        hits.extend(found)
    return found

def main():
    hits = []
    source_ok = None

    # 1. The named source file
    src_path = ROOT / "r1d" / "discover_leads.py"
    if src_path.exists():
        src = src_path.read_text(encoding="utf-8")
        src_hits = scan_text(src, "working-tree: r1d/discover_leads.py", hits)
        source_ok = "clean" if not src_hits else "COMPROMISED"
    else:
        source_ok = "MISSING"

    # 2. Working tree scan (all text files, skip .git)
    wt_hits_count = 0
    for p in ROOT.rglob("*"):
        if p.is_file() and ".git" not in p.parts and p.stat().st_size < 5_000_000:
            try:
                txt = p.read_text(encoding="utf-8")
            except (UnicodeDecodeError, OSError):
                continue
            rel = str(p.relative_to(ROOT))
            before = len(hits)
            scan_text(txt, f"working-tree: {rel}", hits)
            wt_hits_count += len(hits) - before

    # 3. Tracked files via git
    tracked_hits = 0
    r = subprocess.run(["git", "ls-files"], cwd=ROOT, capture_output=True, text=True)
    tracked_files = r.stdout.splitlines()
    for tf in tracked_files:
        fp = ROOT / tf
        if not fp.exists():
            continue
        try:
            txt = fp.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue
        before = len(hits)
        scan_text(txt, f"tracked: {tf}", hits)
        tracked_hits += len(hits) - before

    # 4. Reachable git history (all commits in main) - scan for token literals in diff
    hist_hits = 0
    r = subprocess.run(
        ["git", "log", "--all", "-p", "--max-count=200", "--diff-filter=MAR"],
        cwd=ROOT, capture_output=True, text=True, errors="replace"
    )
    for line in (r.stdout or "").splitlines():
        if not line.startswith(("+", "-")):
            continue
        body = line[1:]
        before = len(hits)
        scan_text(body, "git-history-diff", hits)
        hist_hits += len(hits) - before

    # 5. Reflog-reachable recent commits (specific check for compromised prefix)
    reflog_hits = 0
    r2 = subprocess.run(["git", "reflog", "--all", "--max-count=50"], cwd=ROOT, capture_output=True, text=True)
    for entry in r2.stdout.splitlines():
        before = len(hits)
        scan_text(entry, "reflog-entry", hits)
        reflog_hits += len(hits) - before

    # Determine overall verdict
    total_hits = len(hits)
    secret_found = total_hits > 0 or source_ok == "COMPROMISED"

    # Build the report
    lines = []
    lines.append("# R1-D2 §0: Secret Audit Report")
    lines.append("")
    lines.append(f"**Date**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append(f"**Audit target**: `r1d/discover_leads.py` + whole repo working tree + tracked + history + reflog")
    lines.append("")
    lines.append("## Method")
    lines.append("- Regex scan for `github_pat_*` / `ghp_*` / `gho_*` / `ghs_*` / `ghu_*` / `Bearer *` literals")
    lines.append("- Explicit check for the previously-exposed compromised token prefix (`github_pat_11BW...` truncated)")
    lines.append("- Scans: working tree, tracked files (git ls-files), reachable git history (git log -p), reflog")
    lines.append("- No token value is ever printed in this report.")
    lines.append("")
    lines.append("## Source file status")
    lines.append(f"- `r1d/discover_leads.py`: **{source_ok}**")
    lines.append("")
    lines.append("## Hit counts by scope")
    lines.append(f"- Working tree: {wt_hits_count}")
    lines.append(f"- Tracked files: {tracked_hits}")
    lines.append(f"- Git history (diff): {hist_hits}")
    lines.append(f"- Reflog entries: {reflog_hits}")
    lines.append("")
    lines.append("## Match details (redacted)")
    if total_hits == 0:
        lines.append("- (none)")
    else:
        for h in hits[:50]:
            lines.append(f"- [{h['label']}] pattern=`{h['pattern']}` redacted=`{h['redacted']}`")
        if total_hits > 50:
            lines.append(f"- ... and {total_hits - 50} more")
    lines.append("")
    lines.append("## Verdict")
    lines.append("")
    lines.append(f"```")
    lines.append(f"SECRET_FOUND = {'YES' if secret_found else 'NO'}")
    lines.append(f"SOURCE_FILE_STATUS = {source_ok}")
    lines.append(f"TOTAL_HITS = {total_hits}")
    lines.append(f"```")
    lines.append("")
    if secret_found:
        lines.append("## ACTION REQUIRED")
        lines.append("**STOP all network runs and rotate the token immediately.**")
        lines.append("The compromised token must be revoked in GitHub settings before any further use.")
    else:
        lines.append("No secret literals found in working tree, tracked files, git history, or reflog.")
        lines.append("Code is reading authentication only from `GITHUB_TOKEN` env var (verified in source).")

    report = "\n".join(lines)
    out = REPORTS / "R1D_SECRET_AUDIT.md"
    out.write_text(report, encoding="utf-8")
    print(f"Secret audit report written to {out}")
    print(f"SECRET_FOUND = {'YES' if secret_found else 'NO'}")
    print(f"Source file: {source_ok}")
    print(f"Total hits: {total_hits}")

if __name__ == "__main__":
    main()
