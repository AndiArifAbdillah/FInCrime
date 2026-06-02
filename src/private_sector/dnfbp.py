"""DNFBP (Designated Non-Financial Businesses and Professions) screening.

FATF Recommendations 22-23 require DNFBPs to apply customer due diligence
and report suspicious transactions, same as banks. In Indonesia these are
"Pihak Pelapor Profesi" per PP No.43/2015.

Categories covered:
    - NOTARY        Notaris / PPAT (property conveyancing)
    - REAL_ESTATE   Pedagang properti
    - PRECIOUS      Pedagang logam mulia / permata / perhiasan
    - LUXURY_CAR    Pedagang kendaraan bermotor mewah
    - ART_ANTIQUE   Pedagang seni & antik
    - LAWYER        Advokat (kalau handle transaksi finansial klien)
    - ACCOUNTANT    Akuntan / KAP
    - AUCTION       Pejabat Lelang
    - CASINO        Casino (illegal in ID, included for completeness)
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional

from src.common.logger import get_logger

log = get_logger("private.dnfbp")


# ---------- PPATK reporting thresholds (current as of 2024) ----------
# Sources: PMK No.55/2017, Perka PPATK PER-02/1.02/PPATK/02/15
DNFBP_THRESHOLDS_IDR = {
    "NOTARY":      500_000_000,    # transaksi keuangan klien
    "REAL_ESTATE": 1_000_000_000,  # PMK No.55
    "PRECIOUS":    100_000_000,    # logam mulia cash
    "LUXURY_CAR":  500_000_000,    # kendaraan bermotor
    "ART_ANTIQUE": 500_000_000,
    "LAWYER":      500_000_000,
    "ACCOUNTANT":  500_000_000,
    "AUCTION":     500_000_000,
    "CASINO":      100_000_000,    # if it existed
}


class DNFBPCategory(str, Enum):
    NOTARY = "NOTARY"
    REAL_ESTATE = "REAL_ESTATE"
    PRECIOUS = "PRECIOUS"
    LUXURY_CAR = "LUXURY_CAR"
    ART_ANTIQUE = "ART_ANTIQUE"
    LAWYER = "LAWYER"
    ACCOUNTANT = "ACCOUNTANT"
    AUCTION = "AUCTION"
    CASINO = "CASINO"


@dataclass
class DNFBPTransaction:
    tx_id: str
    category: str                       # one of DNFBPCategory values
    reporter_id: str                    # the DNFBP entity (notary, broker, ...)
    reporter_name: str = ""
    customer_id: str = ""               # buyer/seller/client
    customer_name: str = ""
    counterparty_id: str = ""
    counterparty_name: str = ""
    timestamp: datetime = field(default_factory=datetime.utcnow)
    amount_idr: float = 0.0
    asset_description: str = ""        # "Rumah Pondok Indah 500m2" / "Patek Philippe Nautilus" / "BMW M3"
    payment_method: str = "transfer"   # "cash" | "transfer" | "mixed" | "crypto"
    cash_portion_idr: float = 0.0      # how much paid in cash (red flag if high)
    location: str = ""                 # transaction location
    customer_country: str = "ID"


@dataclass
class DNFBPAlert:
    tx_id: str
    category: str
    severity: str                      # low | medium | high | critical
    score: float                       # 0-1
    triggered_rules: list[str]
    message: str
    customer_id: str
    amount_idr: float


# ============================================================
# Rule engine for DNFBP transactions
# ============================================================
def screen_dnfbp_transaction(tx: DNFBPTransaction,
                             customer_risk_score: float = 0.0,
                             customer_on_pep_list: bool = False,
                             customer_on_sanctions: bool = False) -> Optional[DNFBPAlert]:
    """Apply AML rules specific to DNFBP transactions.

    Returns DNFBPAlert if suspicious, None if clean.
    """
    rules: list[str] = []
    severity_levels = {"low": 1, "medium": 2, "high": 3, "critical": 4}
    sev = "low"
    score = 0.0

    # ----- Rule 1: above reporting threshold -----
    threshold = DNFBP_THRESHOLDS_IDR.get(tx.category, 500_000_000)
    if tx.amount_idr >= threshold:
        rules.append(f"above_threshold_{threshold//1_000_000}M")
        sev = "medium"
        score = max(score, 0.4)

    # ----- Rule 2: structuring (just below threshold) -----
    if 0.85 * threshold <= tx.amount_idr < threshold:
        rules.append("structuring_below_threshold")
        sev = "high"
        score = max(score, 0.7)

    # ----- Rule 3: high cash portion (FATF red flag for property/precious) -----
    if tx.amount_idr > 0:
        cash_pct = tx.cash_portion_idr / tx.amount_idr
        if tx.category in ("REAL_ESTATE", "PRECIOUS", "LUXURY_CAR", "ART_ANTIQUE"):
            if cash_pct >= 0.5:
                rules.append(f"high_cash_payment_{int(cash_pct*100)}pct")
                sev = "high"
                score = max(score, 0.75)
            elif cash_pct >= 0.3:
                rules.append(f"moderate_cash_payment_{int(cash_pct*100)}pct")
                if severity_levels.get(sev, 0) < 2: sev = "medium"
                score = max(score, 0.55)

    # ----- Rule 4: crypto payment for DNFBP (new red flag per FATF 2023) -----
    if tx.payment_method == "crypto":
        rules.append("crypto_payment_for_dnfbp")
        sev = "high"
        score = max(score, 0.7)

    # ----- Rule 5: PEP / sanctions hit -----
    if customer_on_sanctions:
        rules.append("customer_on_sanctions")
        sev = "critical"
        score = 1.0
    elif customer_on_pep_list:
        rules.append("customer_is_pep")
        if severity_levels.get(sev, 0) < 3: sev = "high"
        score = max(score, 0.85)

    # ----- Rule 6: high-risk customer (Layer 0 risk score) -----
    if customer_risk_score >= 70:
        rules.append(f"high_customer_risk_{customer_risk_score:.0f}")
        if severity_levels.get(sev, 0) < 3: sev = "high"
        score = max(score, 0.65)

    # ----- Rule 7: foreign customer purchasing high-value asset -----
    if tx.customer_country not in ("ID", "") and tx.amount_idr >= threshold:
        rules.append(f"foreign_buyer_{tx.customer_country}")
        if severity_levels.get(sev, 0) < 2: sev = "medium"
        score = max(score, 0.55)

    if not rules:
        return None

    msg_parts = []
    if tx.category == "REAL_ESTATE":
        msg_parts.append(f"Transaksi properti Rp {tx.amount_idr:,.0f}")
    elif tx.category == "PRECIOUS":
        msg_parts.append(f"Pembelian logam mulia/permata Rp {tx.amount_idr:,.0f}")
    elif tx.category == "LUXURY_CAR":
        msg_parts.append(f"Penjualan kendaraan mewah Rp {tx.amount_idr:,.0f}")
    elif tx.category == "NOTARY":
        msg_parts.append(f"Transaksi notaris Rp {tx.amount_idr:,.0f}")
    else:
        msg_parts.append(f"Transaksi {tx.category} Rp {tx.amount_idr:,.0f}")

    msg = " · ".join(msg_parts) + f" · {len(rules)} red flag"

    return DNFBPAlert(
        tx_id=tx.tx_id, category=tx.category,
        severity=sev, score=round(score, 3),
        triggered_rules=rules, message=msg,
        customer_id=tx.customer_id, amount_idr=tx.amount_idr,
    )


# ============================================================
# Batch screener
# ============================================================
class DNFBPScreener:
    """Orchestrates DNFBP screening with optional integration to Layer 0 risk."""

    def __init__(self):
        try:
            from src.layer0_risk_scoring import RiskScorer
            self.scorer = RiskScorer()
        except Exception as e:
            log.warning("dnfbp.no_risk_scorer", error=str(e))
            self.scorer = None

    def screen_batch(self, transactions: list[DNFBPTransaction]) -> list[DNFBPAlert]:
        alerts: list[DNFBPAlert] = []
        for tx in transactions:
            alert = screen_dnfbp_transaction(tx)
            if alert:
                alerts.append(alert)
        log.info("dnfbp.batch_screened", n=len(transactions), alerts=len(alerts))
        return alerts
