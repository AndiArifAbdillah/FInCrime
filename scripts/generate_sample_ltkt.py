"""Generate a sample LTKT report for the demo (cash transactions >= IDR 500M).

Usage: python scripts/generate_sample_ltkt.py
Outputs: data/reports/LTKT-YYYYMMDD-Xxxxxxxx.html + .json
"""
from __future__ import annotations
import sys
from pathlib import Path as _Path
sys.path.insert(0, str(_Path(__file__).resolve().parent.parent))
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from datetime import timedelta
from src.common.utils import utc_now
from src.common.config import settings
from src.layer3_regtech.report_generator import (
    build_ltkt_from_transactions, ReportGenerator,
)


def main() -> None:
    # Demo customer with 4 cash transactions same business day, total ~ IDR 1.4 M
    today = utc_now().replace(hour=9, minute=0, second=0, microsecond=0)
    transactions = [
        {
            "tx_id": "BCA_LTKT_001",
            "channel": "bank",
            "timestamp": (today + timedelta(hours=0)).isoformat(),
            "sender_id": "CORP_NOMINEE_XYZ",
            "receiver_id": "ACME_8675309",
            "amount_idr": 480_000_000,
            "currency": "IDR",
            "note": "Setoran tunai cabang Sudirman",
        },
        {
            "tx_id": "BCA_LTKT_002",
            "channel": "bank",
            "timestamp": (today + timedelta(hours=1, minutes=20)).isoformat(),
            "sender_id": "CORP_NOMINEE_XYZ",
            "receiver_id": "ACME_8675309",
            "amount_idr": 495_000_000,
            "currency": "IDR",
            "note": "Setoran tunai cabang Kemang",
        },
        {
            "tx_id": "BCA_LTKT_003",
            "channel": "bank",
            "timestamp": (today + timedelta(hours=2, minutes=45)).isoformat(),
            "sender_id": "CORP_NOMINEE_XYZ",
            "receiver_id": "ACME_8675309",
            "amount_idr": 250_000_000,
            "currency": "IDR",
            "note": "Setoran tunai cabang Bintaro",
        },
        {
            "tx_id": "BCA_LTKT_004",
            "channel": "bank",
            "timestamp": (today + timedelta(hours=4, minutes=10)).isoformat(),
            "sender_id": "CORP_NOMINEE_XYZ",
            "receiver_id": "ACME_8675309",
            "amount_idr": 200_000_000,
            "currency": "IDR",
            "note": "Setoran tunai cabang Pondok Indah",
        },
    ]

    payload = build_ltkt_from_transactions(
        customer_id="CUST_000123",
        customer_name="PT Maju Bersama Investasi",
        customer_type="corporate",
        transactions=transactions,
    )
    if payload is None:
        print("[!] Total below threshold — payload not generated")
        return

    gen = ReportGenerator()
    out_dir = settings.app_data_dir / "reports"
    out_dir.mkdir(parents=True, exist_ok=True)
    paths = gen.write(payload, out_dir)

    print("\n" + "=" * 70)
    print("  SAMPLE LTKT GENERATED")
    print("=" * 70)
    print(f"  Report ID:        {payload.report_id}")
    print(f"  Customer:         {payload.customer_name} ({payload.customer_id})")
    print(f"  Transactions:     {payload.transaction_count}")
    print(f"  Total amount:     Rp {payload.total_amount:,.0f}")
    print(f"  Triggers LTKT:    {'YES' if payload.total_amount >= 500_000_000 else 'no'}")
    print()
    for k, v in paths.items():
        print(f"  {k.upper():4}: {v}")
    print()


if __name__ == "__main__":
    main()
