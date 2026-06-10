"""Convert real bank-statement CSV exports into the canonical Transaction schema.

Supported formats (auto-detected by column-name heuristic):
    - BCA          KlikBCA export
    - MANDIRI      Livin' export
    - BRI          BRImo export
    - BNI          BNI Direct export
    - GENERIC      A standard schema described in docs/generic_bank.md

Each parser is intentionally lenient — Indonesian banks change column names
fairly often. We auto-detect via fuzzy header match and fall back to GENERIC.
"""
from __future__ import annotations

from datetime import datetime
from src.common.utils import utc_now
from pathlib import Path
from typing import Callable, Optional

import pandas as pd

from src.common.logger import get_logger
from src.common.schemas import Transaction, Channel
from src.common.utils import make_id

log = get_logger("ingestion.csv_bank")


# ============================================================
# Parsers
# ============================================================
def _parse_amount(value) -> float:
    """Convert '1.000.000,50' or '1,000,000.50' or '1000000.5' to float."""
    import math
    if value is None or pd.isna(value):
        return 0.0
    s = str(value).strip().replace(" ", "").replace("Rp", "").replace("IDR", "")
    if not s or s.lower() in {"nan", "none", "null", "-"}:
        return 0.0
    # Indonesian format: '.' = thousands, ',' = decimal
    if "," in s and s.rfind(",") > s.rfind("."):
        s = s.replace(".", "").replace(",", ".")
    else:
        s = s.replace(",", "")
    # Strip trailing CR/DB markers
    s = s.replace("CR", "").replace("DB", "").strip()
    try:
        v = float(s)
        if math.isnan(v) or math.isinf(v):
            return 0.0
        return abs(v)  # amount is always positive; debit/credit handled separately
    except ValueError:
        return 0.0


def _parse_date(value, formats: list[str]) -> datetime:
    if pd.isna(value):
        return utc_now()
    s = str(value).strip()
    for fmt in formats:
        try:
            return datetime.strptime(s, fmt)
        except ValueError:
            continue
    try:
        return pd.to_datetime(s).to_pydatetime()
    except Exception:
        return utc_now()


# ----- BCA KlikBCA -----
def parse_bca(df: pd.DataFrame, account_id: str) -> list[Transaction]:
    """BCA columns (typical):
        Tanggal | Keterangan | Cabang | Mutasi | Saldo
    Mutasi like '1,000,000.00 DB' (debit) or '500,000.00 CR' (credit).
    """
    txs: list[Transaction] = []
    for _, row in df.iterrows():
        raw = str(row.get("Mutasi") or row.get("mutasi") or "")
        amount = _parse_amount(raw)
        if amount == 0:
            continue
        is_debit = "DB" in raw.upper()
        ts = _parse_date(row.get("Tanggal") or row.get("tanggal"),
                         ["%d/%m/%Y", "%d-%m-%Y", "%Y-%m-%d"])
        desc = str(row.get("Keterangan", row.get("keterangan", "")))
        counterparty = _extract_counterparty(desc) or f"UNKNOWN_{hash(desc) & 0xFFFFFFFF:08x}"
        sender = account_id if is_debit else counterparty
        receiver = counterparty if is_debit else account_id
        txs.append(Transaction(
            tx_id=f"BCA_{make_id('tx')[3:]}",
            channel=Channel.BANK,
            timestamp=ts,
            sender_id=sender,
            receiver_id=receiver,
            amount_idr=amount,
            currency="IDR",
            sender_age_days=0, sender_tx_count_7d=0,
        ))
    return txs


# ----- Mandiri Livin -----
def parse_mandiri(df: pd.DataFrame, account_id: str) -> list[Transaction]:
    """Mandiri columns: Tanggal | Deskripsi | Debit | Kredit | Saldo"""
    txs: list[Transaction] = []
    for _, row in df.iterrows():
        debit = _parse_amount(row.get("Debit", 0))
        credit = _parse_amount(row.get("Kredit", row.get("Credit", 0)))
        amount = debit if debit > 0 else credit
        if amount == 0:
            continue
        is_debit = debit > 0
        ts = _parse_date(row.get("Tanggal") or row.get("Tgl"),
                         ["%d/%m/%Y", "%d-%m-%Y", "%Y-%m-%d", "%d %b %Y"])
        desc = str(row.get("Deskripsi", row.get("Keterangan", "")))
        counterparty = _extract_counterparty(desc) or f"MND_{hash(desc) & 0xFFFFFFFF:08x}"
        sender = account_id if is_debit else counterparty
        receiver = counterparty if is_debit else account_id
        txs.append(Transaction(
            tx_id=f"MND_{make_id('tx')[3:]}",
            channel=Channel.BANK,
            timestamp=ts,
            sender_id=sender,
            receiver_id=receiver,
            amount_idr=amount,
            currency="IDR",
            sender_age_days=0, sender_tx_count_7d=0,
        ))
    return txs


# ----- BRI BRImo -----
def parse_bri(df: pd.DataFrame, account_id: str) -> list[Transaction]:
    """BRI columns: Tanggal Transaksi | Keterangan | Debit | Kredit | Saldo"""
    return parse_mandiri(df.rename(columns={
        "Tanggal Transaksi": "Tanggal",
        "Keterangan": "Deskripsi",
    }), account_id)


# ----- BNI -----
def parse_bni(df: pd.DataFrame, account_id: str) -> list[Transaction]:
    """BNI: TGL | KETERANGAN | DEBET | KREDIT | SALDO"""
    return parse_mandiri(df.rename(columns={
        "TGL": "Tanggal", "KETERANGAN": "Deskripsi",
        "DEBET": "Debit", "KREDIT": "Kredit",
    }), account_id)


# ----- Generic (documented format) -----
def parse_generic(df: pd.DataFrame, account_id: str) -> list[Transaction]:
    """Generic format:
        date | description | amount | type (DEBIT/CREDIT) | counterparty
    'counterparty' optional — falls back to description-based hash.
    """
    txs: list[Transaction] = []
    for _, row in df.iterrows():
        amount = _parse_amount(row.get("amount", 0))
        if amount == 0:
            continue
        is_debit = str(row.get("type", "DEBIT")).upper().startswith("D")
        ts = _parse_date(row.get("date"),
                         ["%Y-%m-%d", "%d/%m/%Y", "%Y-%m-%dT%H:%M:%S",
                          "%Y-%m-%d %H:%M:%S"])
        desc = str(row.get("description", ""))
        counterparty = (str(row.get("counterparty", "")).strip()
                        or _extract_counterparty(desc)
                        or f"GEN_{hash(desc) & 0xFFFFFFFF:08x}")
        sender = account_id if is_debit else counterparty
        receiver = counterparty if is_debit else account_id
        txs.append(Transaction(
            tx_id=str(row.get("tx_id") or f"GEN_{make_id('tx')[3:]}"),
            channel=Channel.BANK,
            timestamp=ts,
            sender_id=sender,
            receiver_id=receiver,
            amount_idr=amount,
            currency=row.get("currency", "IDR"),
        ))
    return txs


# ============================================================
# Auto-detect
# ============================================================
PARSERS: dict[str, Callable[[pd.DataFrame, str], list[Transaction]]] = {
    "bca": parse_bca,
    "mandiri": parse_mandiri,
    "bri": parse_bri,
    "bni": parse_bni,
    "generic": parse_generic,
}


def detect_format(df: pd.DataFrame) -> str:
    cols = {c.lower().strip() for c in df.columns}
    if {"mutasi"} <= cols:
        return "bca"
    if {"debet", "kredit"} <= cols or {"debet"} <= cols:
        return "bni"
    if "tanggal transaksi" in cols:
        return "bri"
    if {"debit", "kredit"} <= cols or {"debit", "credit"} <= cols:
        return "mandiri"
    if {"date", "amount", "type"} <= cols:
        return "generic"
    return "generic"


# ============================================================
# Helpers
# ============================================================
def _extract_counterparty(desc: str) -> Optional[str]:
    """Heuristic — pull a rekening number or known prefix from description."""
    import re
    # 10–16 digit number = likely rekening
    m = re.search(r"\b(\d{10,16})\b", desc)
    if m:
        return f"ACCT_{m.group(1)}"
    # Trf TO X or DR X
    m = re.search(r"(?:TRF|TRANSFER|TO|DR|FROM)\s+([A-Z0-9\.\- ]{5,30})",
                  desc.upper())
    if m:
        slug = m.group(1).strip().replace(" ", "_")[:20]
        return f"NAME_{slug}"
    return None


# ============================================================
# Main entry
# ============================================================
def import_csv(csv_path: Path, account_id: str,
               bank: Optional[str] = None,
               encoding: str = "utf-8") -> list[Transaction]:
    """Import a single bank-statement CSV. Auto-detects bank format if unspecified."""
    try:
        df = pd.read_csv(csv_path, encoding=encoding)
    except UnicodeDecodeError:
        df = pd.read_csv(csv_path, encoding="latin-1")

    fmt = (bank or detect_format(df)).lower()
    parser = PARSERS.get(fmt, parse_generic)
    log.info("csv_bank.import", path=str(csv_path), bank=fmt,
             rows=len(df), account=account_id)
    return parser(df, account_id)
