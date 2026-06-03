"""Locate the proposal-rules pages in the guidebook (sections, word limits, format)."""
from __future__ import annotations
import sys
from pathlib import Path
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
try:
    from PyPDF2 import PdfReader
except ImportError:
    from pypdf import PdfReader

PDF = Path(r"D:\kuliah\BANK INDONESIA\BUKU PANDUAN 2ND SUBMISSION PROPOSAL_20260511.pdf")

KEYWORDS = [
    "executive summary", "team composition", "problem statement",
    "problem validation", "impact measurement", "originality",
    "business model", "market fit", "adoption", "progress since",
    "word", "kata", "maksimal", "max ", "character", "karakter",
    "attachment", "lampiran", "format", "pdf", " mb", "file size",
    "submission", "deadline", "page limit", "halaman",
]

reader = PdfReader(str(PDF))
total = len(reader.pages)
print(f"=== Total pages: {total} ===")
page_text = []
for i in range(total):
    t = reader.pages[i].extract_text() or ""
    page_text.append(t)

# Map: which pages mention proposal-structure keywords
print("\n=== Pages mentioning proposal sections / limits / format ===")
for i, t in enumerate(page_text):
    low = t.lower()
    hits = [k for k in KEYWORDS if k in low]
    # Only flag pages with several structural hits (signal, not noise)
    strong = [k for k in ("executive summary", "team composition", "problem validation",
                          "impact measurement", "originality", "business model",
                          "attachment", "word", "kata", "maksimal", "format") if k in low]
    if len(strong) >= 2:
        print(f"\n--- PAGE {i+1}  (hits: {', '.join(hits[:10])}) ---")
        for line in t.splitlines():
            ll = line.lower().strip()
            if any(k in ll for k in KEYWORDS) and len(ll) > 3:
                print("   | " + line.strip()[:170])
