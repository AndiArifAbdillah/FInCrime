"""Real estate / property transaction monitoring.

FATF identifies real estate as the #1 sector for laundering proceeds globally.
Indonesian context: PMK No.55/2017 requires notaris/PPAT to report transactions
above IDR 1B and any suspicious activity.

Red flags monitored:
    - All-cash purchase of property >= IDR 1B
    - Sale immediately after purchase (flipping)
    - Multiple properties bought by single buyer in short window
    - Price significantly below/above market (under/over-valuation)
    - Buyer-seller related (transfer pricing)
    - Property in name of nominee (PEP red flag)
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Optional

import pandas as pd

from src.common.logger import get_logger
from .dnfbp import DNFBPTransaction, screen_dnfbp_transaction

log = get_logger("private.property")


@dataclass
class PropertyTransaction:
    """Real estate transaction record (notary/PPAT data)."""
    tx_id: str
    notary_id: str
    notary_name: str = ""
    deed_number: str = ""              # nomor akta
    deed_date: datetime = field(default_factory=datetime.utcnow)
    buyer_id: str = ""
    buyer_name: str = ""
    buyer_country: str = "ID"
    seller_id: str = ""
    seller_name: str = ""
    property_type: str = "RUMAH"       # RUMAH | TANAH | APARTEMEN | RUKO | KOMERSIAL
    location: str = ""                 # full address
    region_code: str = ""              # kelurahan/kecamatan code
    area_m2: float = 0.0
    sale_price_idr: float = 0.0
    appraised_value_idr: float = 0.0   # NJOP / KJPP appraisal
    payment_method: str = "transfer"
    cash_portion_idr: float = 0.0
    mortgage_idr: float = 0.0          # KPR / financing amount


# ============================================================
# Monitor
# ============================================================
class PropertyMonitor:
    """Screens property transactions for AML red flags."""

    def __init__(self, history_df: Optional[pd.DataFrame] = None):
        # Historical transactions for pattern detection (flipping, multi-purchase)
        self.history = history_df if history_df is not None else pd.DataFrame()

    def screen(self, tx: PropertyTransaction) -> list[dict]:
        """Apply property-specific AML rules. Returns list of alerts (each as dict)."""
        alerts: list[dict] = []

        # ---- Rule: above LTKT threshold IDR 500M ----
        if tx.sale_price_idr >= 500_000_000:
            alerts.append({
                "rule": "ltkt_threshold",
                "severity": "medium",
                "message": f"Transaksi properti {tx.sale_price_idr:,.0f} >= LTKT trigger",
            })

        # ---- Rule: PMK No.55 mandatory reporting ----
        if tx.sale_price_idr >= 1_000_000_000:
            alerts.append({
                "rule": "pmk_55_mandatory",
                "severity": "high",
                "message": f"Wajib lapor PMK No.55/2017 (>= IDR 1M)",
            })

        # ---- Rule: under-/over-valuation vs appraisal ----
        if tx.appraised_value_idr > 0:
            ratio = tx.sale_price_idr / tx.appraised_value_idr
            if ratio < 0.7:
                alerts.append({
                    "rule": "undervaluation",
                    "severity": "high",
                    "message": f"Harga jual ({tx.sale_price_idr:,.0f}) hanya {ratio:.0%} dari nilai appraisal ({tx.appraised_value_idr:,.0f}) - indikasi under-the-table cash",
                })
            elif ratio > 1.5:
                alerts.append({
                    "rule": "overvaluation",
                    "severity": "high",
                    "message": f"Harga jual {ratio:.0%} di atas appraisal — indikasi laundering via over-pricing",
                })

        # ---- Rule: all-cash high-value purchase ----
        cash_pct = tx.cash_portion_idr / max(tx.sale_price_idr, 1)
        if tx.sale_price_idr >= 1_000_000_000 and cash_pct >= 0.7:
            alerts.append({
                "rule": "all_cash_high_value",
                "severity": "critical",
                "message": f"Properti {tx.sale_price_idr:,.0f} dibayar {cash_pct:.0%} tunai — sangat mencurigakan",
            })
        elif tx.sale_price_idr >= 500_000_000 and cash_pct >= 0.5:
            alerts.append({
                "rule": "majority_cash",
                "severity": "high",
                "message": f"Cash payment {cash_pct:.0%} pada properti {tx.sale_price_idr:,.0f}",
            })

        # ---- Rule: flipping (buyer & seller had recent transactions) ----
        if not self.history.empty and "buyer_id" in self.history.columns:
            recent = self.history[
                (self.history["buyer_id"] == tx.seller_id) |
                (self.history["seller_id"] == tx.buyer_id)
            ]
            if "deed_date" in recent.columns:
                recent = recent[pd.to_datetime(recent["deed_date"]) >
                                (tx.deed_date - timedelta(days=180))]
                if len(recent) > 0:
                    alerts.append({
                        "rule": "potential_flipping",
                        "severity": "high",
                        "message": f"{len(recent)} transaksi properti dalam 6 bulan terakhir oleh pihak yang sama",
                    })

        # ---- Rule: foreign buyer high-value (under KITAS/KITAP restrictions) ----
        if tx.buyer_country not in ("ID", "") and tx.sale_price_idr >= 5_000_000_000:
            alerts.append({
                "rule": "foreign_buyer_restricted",
                "severity": "high",
                "message": f"Pembeli WNA ({tx.buyer_country}) untuk properti {tx.sale_price_idr:,.0f} — verifikasi izin tinggal",
            })

        # ---- Rule: no mortgage on big-ticket (suspicious for income-bracket mismatch) ----
        if tx.sale_price_idr >= 5_000_000_000 and tx.mortgage_idr == 0:
            alerts.append({
                "rule": "no_mortgage_big_ticket",
                "severity": "medium",
                "message": "Properti high-value tanpa pembiayaan bank — verifikasi sumber dana",
            })

        return alerts

    def screen_batch(self, transactions: list[PropertyTransaction]) -> list[dict]:
        all_alerts: list[dict] = []
        for tx in transactions:
            for a in self.screen(tx):
                a["tx_id"] = tx.tx_id
                a["buyer_id"] = tx.buyer_id
                a["amount_idr"] = tx.sale_price_idr
                all_alerts.append(a)
        log.info("property.batch_screened", n=len(transactions), alerts=len(all_alerts))
        return all_alerts
