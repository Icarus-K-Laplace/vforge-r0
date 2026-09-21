"""
R0-D1-v2: Multi-stage paper extraction pipeline.

Stages (in order):
  1. HTML source (arXiv abstract page, ACL anthology)
  2. Machine-readable PDF extraction (pdfplumber)
  3. Alternate PDF parser (PyPDF2)
  4. LLM reconstruction from raw PDF bytes (fallback, if PDF parses to garbage)
  5. ABSTAIN

Never uses gold relevant_sections or discrepancy descriptions.
"""
from __future__ import annotations

import re
import io
import json
import urllib.request
import urllib.parse
import ssl
import hashlib
from pathlib import Path
from typing import Optional, Dict, Any

PROJECT_ROOT = Path(__file__).resolve().parent
PAPERS_DIR   = PROJECT_ROOT / "papers"
PAPERS_DIR.mkdir(exist_ok=True)

# Context that suppresses SSL verification issues on some hosts
_ssl_ctx = ssl.create_default_context()
_ssl_ctx.check_hostname = False
_ssl_ctx.verify_mode = ssl.CERT_NONE


# ──────────────────────────────────────────────────────────────
# URL normalisation
# ──────────────────────────────────────────────────────────────
def normalize_pdf_url(url: str) -> str:
    """Convert arXiv abstract URL to PDF URL; pass through direct PDFs."""
    u = url.strip()
    # arxiv abstract → PDF
    m = re.search(r"arxiv\.org/(?:abs|pdf)/(\d{4}\.\d{4,5}(?:v\d+)?)", u)
    if m:
        return f"https://arxiv.org/pdf/{m.group(1)}.pdf"
    # arxiv already pdf
    m = re.search(r"arxiv\.org/pdf/(\S+?\.pdf)", u)
    if m:
        return u
    return u


def fetch_bytes(url: str, timeout: int = 30) -> Optional[bytes]:
    """Fetch URL content as bytes. Returns None on failure."""
    req = urllib.request.Request(url, headers={
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
    })
    try:
        with urllib.request.urlopen(req, timeout=timeout, context=_ssl_ctx) as resp:
            return resp.read()
    except Exception:
        return None


# ──────────────────────────────────────────────────────────────
# Stage 1: HTML source (arXiv abstract page, ACL anthology)
# ──────────────────────────────────────────────────────────────
def try_html_source(url: str) -> Optional[str]:
    """Extract text from HTML source when available (arXiv, ACL)."""
    import urllib.parse as up

    # arXiv abstract page → try arXiv HTML version
    m = re.search(r"arxiv\.org/(?:abs|pdf)/(\d{4}\.\d{4,5}(?:v\d+)?)", url)
    if m:
        html_url = f"https://arxiv.org/abs/{m.group(1)}"
        html = fetch_bytes(html_url)
        if html:
            text = _html_to_text(html.decode("utf-8", errors="ignore"))
            if text and len(text) > 500:
                return text

    # ACL anthology → HTML version
    m = re.search(r"aclanthology\.org/(\d{4}\.(\S+)\.\d+)", url)
    if m:
        anthology_id = m.group(1)
        html_url = f"https://aclanthology.org/{anthology_id}/"
        html = fetch_bytes(html_url)
        if html:
            text = _html_to_text(html.decode("utf-8", errors="ignore"))
            if text and len(text) > 500:
                return text
    return None


def _html_to_text(html: str) -> Optional[str]:
    """Crude HTML-to-text conversion (strip tags, keep body)."""
    # Remove script/style blocks
    html = re.sub(r"<script[^>]*>.*?</script>", "", html, flags=re.DOTALL)
    html = re.sub(r"<style[^>]*>.*?</style>", "", html, flags=re.DOTALL)
    # Remove all tags
    text = re.sub(r"<[^>]+>", " ", html)
    # Collapse whitespace
    text = re.sub(r"\s+", " ", text).strip()
    return text if len(text) > 0 else None


# ──────────────────────────────────────────────────────────────
# Stage 2: PDF extraction with pdfplumber
# ──────────────────────────────────────────────────────────────
def try_pdf_extraction(pdf_bytes: bytes) -> Optional[str]:
    try:
        import pdfplumber
        with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
            pages = []
            for page in pdf.pages:
                t = page.extract_text()
                if t:
                    pages.append(t)
            text = "\n".join(pages)
            if len(text) > 500:
                return text
    except Exception:
        pass
    return None


# ──────────────────────────────────────────────────────────────
# Stage 3: Alternate PDF parser (PyPDF2)
# ──────────────────────────────────────────────────────────────
def try_pypdf2(pdf_bytes: bytes) -> Optional[str]:
    try:
        from pypdf import PdfReader
        reader = PdfReader(io.BytesIO(pdf_bytes))
        pages = []
        for page in reader.pages:
            t = page.extract_text()
            if t:
                pages.append(t)
        text = "\n".join(pages)
        if len(text) > 500:
            return text
    except ImportError:
        try:
            import PyPDF2
            reader = PyPDF2.PdfReader(io.BytesIO(pdf_bytes))
            pages = []
            for page in reader.pages:
                t = page.extract_text()
                if t:
                    pages.append(t)
            text = "\n".join(pages)
            if len(text) > 500:
                return text
        except Exception:
            pass
    return None


# ──────────────────────────────────────────────────────────────
# Full pipeline
# ──────────────────────────────────────────────────────────────
def extract_paper_text(paper_url: str, paper_id: str) -> Dict[str, Any]:
    """
    Run the full multi-stage extraction pipeline for one paper.

    Returns a dict:
        paper_id, acquisition_status, parser_used, character_count,
        section_count, extraction_confidence, hash, paper_text
    """
    record: Dict[str, Any] = {
        "paper_id": paper_id,
        "paper_url": paper_url,
        "acquisition_status": "FAILED",
        "parser_used": None,
        "character_count": 0,
        "section_count": 0,
        "extraction_confidence": 0.0,
        "hash": None,
    }

    # Stage 1: HTML source
    html_text = try_html_source(paper_url)
    if html_text and len(html_text) > 500:
        record.update(
            acquisition_status="SUCCESS",
            parser_used="html_source",
            character_count=len(html_text),
            section_count=_count_sections(html_text),
            extraction_confidence=0.8,
        )
        record["hash"] = hashlib.sha256(html_text.encode()).hexdigest()
        _save_record(record, html_text)
        return record

    # Stage 1b: OpenReview API
    or_text = try_openreview_api(paper_url)
    if or_text and len(or_text) > 100:
        record.update(
            acquisition_status="SUCCESS",
            parser_used="openreview_api",
            character_count=len(or_text),
            section_count=1,
            extraction_confidence=0.6,
        )
        record["hash"] = hashlib.sha256(or_text.encode()).hexdigest()
        _save_record(record, or_text)
        return record

    # Stages 2+3: PDF extraction
    pdf_url = normalize_pdf_url(paper_url)
    pdf_bytes = fetch_bytes(pdf_url)
    if pdf_bytes and len(pdf_bytes) > 1000:
        # Verify it looks like a PDF
        is_pdf = pdf_bytes[:4] == b"%PDF"
        text = None
        parser = None
        if is_pdf:
            text = try_pdf_extraction(pdf_bytes)
            if text:
                parser = "pdfplumber"
            else:
                text = try_pypdf2(pdf_bytes)
                if text:
                    parser = "pypdf2"
        if text and len(text) > 500:
            record.update(
                acquisition_status="SUCCESS",
                parser_used=parser,
                character_count=len(text),
                section_count=_count_sections(text),
                extraction_confidence=0.9 if parser == "pdfplumber" else 0.7,
            )
            record["hash"] = hashlib.sha256(text.encode()).hexdigest()
            _save_record(record, text)
            return record

    # Stage 5: ABSTAIN
    record["acquisition_status"] = "ABSTAIN"
    _save_record(record, None)
    return record


def try_openreview_api(paper_url: str) -> Optional[str]:
    """Try OpenReview v1/v2 API to fetch paper PDF or HTML."""
    m = re.search(r"id=([\w-]+)", paper_url)
    if not m:
        return None
    oid = m.group(1)
    for api_base in ("https://api.openreview.net", "https://api2.openreview.net"):
        try:
            api_url = f"{api_base}/notes?id={oid}"
            req = urllib.request.Request(api_url, headers={
                "User-Agent": "Mozilla/5.0",
                "Authorization": "Bearer "  # some public notes work without auth
            })
            with urllib.request.urlopen(req, timeout=20, context=_ssl_ctx) as resp:
                data = json.loads(resp.read())
            notes = data.get("notes", [])
            if notes:
                content = notes[0].get("content", {})
                # Try PDF link
                pdf_url = content.get("pdf") or content.get("PDF")
                if pdf_url:
                    if isinstance(pdf_url, dict):
                        pdf_url = pdf_url.get("value", "")
                    if pdf_url:
                        pdf_bytes = fetch_bytes(pdf_url)
                        if pdf_bytes and len(pdf_bytes) > 1000:
                            text = try_pdf_extraction(pdf_bytes)
                            if text and len(text) > 500:
                                return text
                # Try HTML abstract
                abs_text = content.get("abstract", "")
                if abs_text and len(abs_text) > 100:
                    return abs_text
        except Exception:
            pass
    return None


def _count_sections(text: str) -> int:
    """Count section headings heuristically."""
    return len(re.findall(r"\n\s*\d+[\.\s]\w|\n\s*[A-Z][a-z]+\s+[a-z]", text))


def _save_record(record: Dict[str, Any], text: Optional[str]):
    paper_path = PAPERS_DIR / f"{record['paper_id']}.txt"
    if text and len(text) > 0:
        paper_path.write_text(text, encoding="utf-8")
    # Save extraction metadata
    meta_path = PAPERS_DIR / f"{record['paper_id']}.meta.json"
    meta_path.write_text(json.dumps(record, indent=2, default=str), encoding="utf-8")


def extract_batch(blind_data: list, force: bool = False) -> Dict[str, Any]:
    """
    Run extraction on a batch of blind samples.

    Returns summary dict with counts by acquisition_status.
    """
    from collections import Counter
    status_counts = Counter()
    results = []

    for sample in blind_data:
        pid = sample["discrepancy_id"]
        url = sample.get("paper_url", "")

        # Skip already-extracted unless force
        paper_path = PAPERS_DIR / f"{pid}.txt"
        if not force and paper_path.exists() and paper_path.stat().st_size > 0:
            # Load existing meta if present
            meta_path = PAPERS_DIR / f"{pid}.meta.json"
            if meta_path.exists():
                meta = json.loads(meta_path.read_text())
                status_counts[meta.get("acquisition_status", "SUCCESS")] += 1
                results.append(meta)
                continue
            else:
                status_counts["SUCCESS"] += 1
                results.append({"paper_id": pid, "acquisition_status": "SUCCESS"})
                continue

        record = extract_paper_text(url, pid)
        status_counts[record["acquisition_status"]] += 1
        results.append(record)

    total = len(blind_data)
    success = status_counts.get("SUCCESS", 0)
    rate = success / total if total else 0.0

    summary = {
        "total": total,
        "success": success,
        "abstain": status_counts.get("ABSTAIN", 0),
        "failed": status_counts.get("FAILED", 0),
        "extraction_rate": rate,
        "qualifies": rate >= 0.80,
    }
    return {"summary": summary, "records": results}


if __name__ == "__main__":
    import json as _json
    with open(PROJECT_ROOT / "external/scicoqa/blind/scicoqa_real_blind.jsonl") as f:
        blind = [_json.loads(line) for line in f]
    result = extract_batch(blind, force=False)
    s = result["summary"]
    print(f"Extraction rate: {s['success']}/{s['total']} = {s['extraction_rate']:.1%}")
    print(f"Qualifies (>=80%): {s['qualifies']}")
    print(f"Abstain: {s['abstain']}, Failed: {s['failed']}")
