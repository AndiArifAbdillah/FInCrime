"""High-value assets monitoring — luxury cars, jewelry, precious metals, art.

These are FATF Rec 22-listed sectors. In Indonesia:
    - Logam mulia / permata threshold: IDR 100M (cash transactions)
    - Kendaraan mewah threshold: IDR 500M
    - Seni & antik threshold: IDR 500M
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional

from src.common.logger import get_logger

log = get_logger("private.hva")


class AssetClass(str, Enum):
    GOLD_BAR = "GOLD_BAR"              # logam mulia Antam, UBS, dll
    JEWELRY = "JEWELRY"                # perhiasan
    DIAMOND = "DIAMOND"                # berlian/permata
    LUXURY_CAR = "LUXURY_CAR"          # > IDR 1B mobil
    LUXURY_WATCH = "LUXURY_WATCH"      # > IDR 100M jam tangan
    ART = "ART"                        # lukisan, patung
    ANTIQUE = "ANTIQUE"                # keramik, dll
    YACHT = "YACHT"
    PRIVATE_JET = "PRIVATE_JET"


@dataclass
class HighValueAsset:
    """A high-value asset transaction record."""
    tx_id: str
    asset_class: str                   # one of AssetClass values
    asset_description: str
    dealer_id: str
    dealer_name: str = ""
    buyer_id: str = ""
    buyer_name: str = ""
    timestamp: datetime = field(default_factory=datetime.utcnow)
    amount_idr: float = 0.0
    payment_method: str = "transfer"   # transfer | cash | crypto | mixed
    cash_portion_idr: float = 0.0
    serial_number: str = ""            # IMEI/VIN/certificate ID
    is_resale: bool = False            # second-hand
    delivery_location: str = ""


# ============================================================
# HVA-specific rules
# ============================================================
HVA_THRESHOLDS_IDR = {
    "GOLD_BAR": 100_000_000,
    "JEWELRY": 100_000_000,
    "DIAMOND": 100_000_000,
    "LUXURY_CAR": 500_000_000,
    "LUXURY_WATCH": 100_000_000,
    "ART": 500_000_000,
    "ANTIQUE": 500_000_000,
    "YACHT": 1_000_000_000,
    "PRIVATE_JET": 5_000_000_000,
}


class HVAMonitor:
    """Screen high-value asset transactions for AML red flags."""

    def screen(self, tx: HighValueAsset,
               buyer_risk_score: float = 0.0,
               buyer_on_pep_list: bool = False) -> list[dict]:
        alerts: list[dict] = []
        threshold = HVA_THRESHOLDS_IDR.get(tx.asset_class, 500_000_000)

        # ---- Threshold breach ----
        if tx.amount_idr >= threshold:
            alerts.append({
                "rule": f"threshold_{threshold//1_000_000}M",
                "severity": "medium",
                "message": f"{tx.asset_class}: {tx.amount_idr:,.0f} >= threshold {threshold:,.0f}",
            })

        # ---- Structuring ----
        if 0.85 * threshold <= tx.amount_idr < threshold:
            alerts.append({
                "rule": "structuring",
                "severity": "high",
                "message": f"Transaksi {tx.amount_idr:,.0f} tepat di bawah threshold {threshold:,.0f}",
            })

        # ---- Cash percentage ----
        cash_pct = tx.cash_portion_idr / max(tx.amount_idr, 1)
        if cash_pct >= 0.7 and tx.amount_idr >= threshold:
            alerts.append({
                "rule": "high_cash_purchase",
                "severity": "critical",
                "message": f"{cash_pct:.0%} dibayar tunai — sangat tidak biasa untuk {tx.asset_class}",
            })
        elif cash_pct >= 0.3 and tx.amount_idr >= threshold / 2:
            alerts.append({
                "rule": "moderate_cash",
                "severity": "high",
                "message": f"Cash payment {cash_pct:.0%}",
            })

        # ---- Crypto for HVA (FATF 2023 red flag) ----
        if tx.payment_method == "crypto":
            alerts.append({
                "rule": "crypto_payment_hva",
                "severity": "high",
                "message": "Pembayaran via kripto untuk barang fisik - red flag layering",
            })

        # ---- PEP / high-risk customer ----
        if buyer_on_pep_list:
            alerts.append({
                "rule": "pep_buyer",
                "severity": "high",
                "message": "Pembeli adalah PEP (Politically Exposed Person)",
            })
        if buyer_risk_score >= 70:
            alerts.append({
                "rule": "high_risk_buyer",
                "severity": "high",
                "message": f"Risk score pembeli {buyer_risk_score:.0f}/100",
            })

        # ---- Anonymous/no-serial high-value (red flag for art especially) ----
        if (tx.asset_class in ("ART", "ANTIQUE", "DIAMOND") and
            tx.amount_idr >= 500_000_000 and not tx.serial_number):
            alerts.append({
                "rule": "no_provenance_doc",
                "severity": "high",
                "message": "Tidak ada serial/sertifikat untuk barang seni/permata high-value",
            })

        # ---- Resale flip (just-bought high-value being resold) ----
        if tx.is_resale and tx.amount_idr >= threshold:
            alerts.append({
                "rule": "high_value_resale",
                "severity": "medium",
                "message": "Resale high-value asset — verifikasi histori kepemilikan",
            })

        return alerts

    def screen_batch(self, transactions: list[HighValueAsset]) -> list[dict]:
        all_alerts: list[dict] = []
        for tx in transactions:
            for a in self.screen(tx):
                a["tx_id"] = tx.tx_id
                a["buyer_id"] = tx.buyer_id
                a["asset_class"] = tx.asset_class
                a["amount_idr"] = tx.amount_idr
                all_alerts.append(a)
        log.info("hva.batch_screened", n=len(transactions), alerts=len(all_alerts))
        return all_alerts
