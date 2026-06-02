"""Extract AML/compliance-related sections from BI CBDC documents."""
from __future__ import annotations
import sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

try:
    from PyPDF2 import PdfReader
except ImportError:
    from pypdf import PdfReader

PDFS = {
    "White Paper CBDC 2022": Path(r"D:\kuliah\BANK INDONESIA\White_Paper_CBDC-2022.pdf"),
    "Konsultasi Publik Garuda": Path(r"D:\kuliah\BANK INDONESIA\Laporan-Konsultasi-Publik-Proyek-Garuda.pdf"),
    "POC Proyek Garuda": Path(r"D:\kuliah\BANK INDONESIA\Laporan_POC_Proyek_Garuda_ID.pdf"),
    "Consultative Paper Rupiah Digital": Path(r"D:\kuliah\BANK INDONESIA\Consultative_Paper_Rupiah_Digital_BI.pdf"),
}

# Keywords yang relate ke AML / FinCrime
KEYWORDS = [
    "AML", "anti-money", "anti money", "money laundering", "pencucian uang",
    "TPPU", "fraud", "LTKM", "LTKT", "PPATK",
    "FATF", "compliance", "kepatuhan", "audit", "risiko",
    "privacy", "privasi", "anonymous", "anonim", "transparansi",
    "wholesale", "retail", "rRupiah", "wRupiah",
    "DLT", "distributed ledger", "smart contract", "programmability",
    "intermediary", "intermediasi", "KYC",
    "illicit", "illegal", "criminal",
    "Travel Rule", "screening",
]


def extract_relevant(name: str, path: Path, max_pages: int = 40):
    if not path.exists():
        print(f"  [!] {path} tidak ditemukan")
        return
    reader = PdfReader(str(path))
    total = len(reader.pages)
    print(f"\n{'='*70}")
    print(f"  {name}  ({total} pages)")
    print(f"{'='*70}")

    hits = []
    for i in range(min(max_pages, total)):
        try:
            text = reader.pages[i].extract_text() or ""
        except Exception:
            continue
        text_lower = text.lower()
        matched = [kw for kw in KEYWORDS if kw.lower() in text_lower]
        if matched:
            hits.append((i + 1, matched, text))

    if not hits:
        print("  (tidak ada AML/compliance keyword di first 40 pages)")
        return

    print(f"\n  Pages with AML/compliance keywords:")
    for page_num, matched, text in hits[:8]:
        print(f"\n  --- PAGE {page_num} ---")
        print(f"  Matched: {', '.join(sorted(set(matched))[:10])}")
        # Print relevant sentences
        sentences = text.replace("\n", " ").split(". ")
        for s in sentences:
            s_lower = s.lower()
            if any(kw.lower() in s_lower for kw in matched):
                snippet = s.strip()[:400]
                if len(snippet) > 60:
                    print(f"    > {snippet}")


for name, path in PDFS.items():
    extract_relevant(name, path)
