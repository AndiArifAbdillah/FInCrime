"""Import one or more bank-statement CSV files into the canonical schema.

Usage:
    python scripts/import_bank_csv.py path/to/statement.csv --account 1234567890
    python scripts/import_bank_csv.py path/to/*.csv --bank mandiri --account ACME01

Output: data/real/imported_transactions.csv  (canonical Transaction schema)
"""
from __future__ import annotations

import sys
from pathlib import Path as _Path
sys.path.insert(0, str(_Path(__file__).resolve().parent.parent))

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

import argparse
import glob
from pathlib import Path

import pandas as pd

from src.common.config import settings
from src.common.logger import get_logger
from src.ingestion.csv_bank_importer import import_csv, PARSERS

log = get_logger("import_bank_csv")


def main(files: list[str], bank: str | None, account_id: str, out_dir: Path):
    out_dir.mkdir(parents=True, exist_ok=True)

    expanded: list[Path] = []
    for f in files:
        if any(c in f for c in "*?["):
            expanded.extend(Path(p) for p in glob.glob(f))
        else:
            expanded.append(Path(f))

    if not expanded:
        print(f"[!] No files matched: {files}")
        return

    print("\n" + "=" * 60)
    print("  BANK CSV IMPORT")
    print("=" * 60)
    print(f"  Files:    {len(expanded)}")
    print(f"  Account:  {account_id}")
    print(f"  Bank:     {bank or 'auto-detect'}")
    print()

    all_tx = []
    for path in expanded:
        if not path.exists():
            print(f"  [!] missing: {path}")
            continue
        try:
            txs = import_csv(path, account_id=account_id, bank=bank)
            print(f"  [OK]  {path.name:<40} -> {len(txs):>5} transactions")
            all_tx.extend(t.model_dump() for t in txs)
        except Exception as e:
            print(f"  [!]   {path.name:<40} failed: {e}")

    if not all_tx:
        print("\n[!] No transactions imported.")
        return

    df = pd.DataFrame(all_tx)
    df["timestamp"] = pd.to_datetime(df["timestamp"]).astype(str)
    out_path = out_dir / "imported_transactions.csv"
    df.to_csv(out_path, index=False)
    print(f"\n  -> {out_path}  ({len(df):,} rows)")

    # Quick sanity stats
    print("\n  Summary:")
    print(f"    Total volume:     Rp {df['amount_idr'].sum():,.0f}")
    print(f"    Largest tx:       Rp {df['amount_idr'].max():,.0f}")
    print(f"    Date range:       {df['timestamp'].min()} -> {df['timestamp'].max()}")
    print(f"    Unique senders:   {df['sender_id'].nunique():,}")
    print(f"    Unique receivers: {df['receiver_id'].nunique():,}")
    above_ltkt = (df["amount_idr"] >= 500_000_000).sum()
    near_smurf = ((df["amount_idr"] >= 40_000_000) &
                  (df["amount_idr"] <= 49_999_999)).sum()
    print(f"    Tx >= IDR 500M (LTKT trigger):       {above_ltkt}")
    print(f"    Tx in smurfing band 40M-49.9M:       {near_smurf}")
    print("\n[OK] Import complete.")
    print("\n  Next step (score for fraud):")
    print("    python scripts\\score_real_data.py")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("files", nargs="+",
                        help="CSV file path(s) or glob(s)")
    parser.add_argument("--account", required=True,
                        help="Your account number/ID (used as sender/receiver)")
    parser.add_argument("--bank", choices=list(PARSERS.keys()), default=None,
                        help="Bank format (default: auto-detect)")
    parser.add_argument("--out", type=Path,
                        default=settings.app_data_dir / "real")
    args = parser.parse_args()
    main(args.files, args.bank, args.account, args.out)
