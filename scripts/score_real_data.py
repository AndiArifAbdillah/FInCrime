"""Run Layer 1 fraud detection over imported real bank transactions.

Usage:
    python scripts/score_real_data.py
    python scripts/score_real_data.py --input data/real/imported_transactions.csv
"""
from __future__ import annotations

import sys
from pathlib import Path as _Path
sys.path.insert(0, str(_Path(__file__).resolve().parent.parent))

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

import argparse
from pathlib import Path

import pandas as pd

from src.common.config import settings
from src.common.schemas import Transaction


def main(input_csv: Path, out_csv: Path, top_n: int):
    if not input_csv.exists():
        print(f"[!] Input file not found: {input_csv}")
        print("    Run `python scripts/import_bank_csv.py ...` first.")
        sys.exit(1)

    from src.layer1_fraud_detection import FraudDetector
    print(f"\n  Loading Layer 1 detector ...")
    det = FraudDetector()

    print(f"  Reading {input_csv} ...")
    df = pd.read_csv(input_csv)
    print(f"  {len(df):,} transactions to score")

    from src.common.utils import rows_to_transactions
    txs = rows_to_transactions(r for _, r in df.iterrows())
    skipped = len(df) - len(txs)
    if skipped > 0:
        print(f"  [!] {skipped} row(s) failed validation")
    preds = det.predict_batch(txs)
    print(f"  Scored {len(preds):,} transactions")
    if not preds:
        print("\n[!] Nothing to score. Check the input file format.")
        return

    result = pd.DataFrame([{
        "tx_id": p.tx_id,
        "anomaly_score": p.anomaly_score,
        "is_anomaly": p.is_anomaly,
        "rules": ",".join(str(r) for r in p.triggered_rules),
    } for p in preds])
    merged = df.merge(result, on="tx_id", how="left")
    merged.to_csv(out_csv, index=False)

    n_anom = int(merged["is_anomaly"].sum())
    print(f"\n  ANOMALIES DETECTED: {n_anom:,} / {len(merged):,}  ({n_anom/max(len(merged),1):.1%})")
    print(f"  -> Full results: {out_csv}")

    if n_anom > 0:
        top = merged[merged["is_anomaly"]].nlargest(top_n, "anomaly_score")
        print(f"\n  Top {min(top_n, len(top))} flagged transactions:")
        print("-" * 100)
        for _, r in top.iterrows():
            print(f"  {r['tx_id']:<25} {r['amount_idr']:>15,.0f}  "
                  f"score={r['anomaly_score']:.3f}  {r['rules']}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path,
                        default=settings.app_data_dir / "real" / "imported_transactions.csv")
    parser.add_argument("--output", type=Path,
                        default=settings.app_data_dir / "real" / "scored_transactions.csv")
    parser.add_argument("--top", type=int, default=10)
    args = parser.parse_args()
    main(args.input, args.output, args.top)
