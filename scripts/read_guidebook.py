"""Read PIDI guidebook PDF and extract structured text per page range."""
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

if len(sys.argv) > 1:
    rng = sys.argv[1]
    start, end = [int(x) for x in rng.split("-")] if "-" in rng else (int(rng), int(rng))
else:
    start, end = 1, 10

reader = PdfReader(str(PDF))
total = len(reader.pages)
print(f"=== Total pages: {total} ===\n")

for i in range(start - 1, min(end, total)):
    page = reader.pages[i]
    text = page.extract_text() or ""
    text = text.strip()
    if not text:
        text = "(no extractable text — possibly image/scan)"
    print(f"\n{'='*70}")
    print(f"=== PAGE {i+1} ===")
    print('='*70)
    print(text[:3500])
