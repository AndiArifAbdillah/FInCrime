"""Download OFAC sanctions list and apply to entities.csv.

Usage:
    python scripts/fetch_sanctions.py
    python scripts/fetch_sanctions.py --force-refresh
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
from src.common.logger import get_logger
from src.ingestion.sanctions_loader import (
    download_ofac_sdn, parse_ofac_sdn,
    load_sanctioned_crypto_addresses, get_seed_bad_wallets,
    flag_entities_against_sanctions,
)

log = get_logger("fetch_sanctions")


def main(force: bool, entities_csv: Path):
    print("\n" + "=" * 60)
    print("  OFAC SANCTIONS DOWNLOAD")
    print("=" * 60)
    sdn_csv = download_ofac_sdn(force=force)
    entities = parse_ofac_sdn(sdn_csv)
    print(f"  Downloaded {sdn_csv}")
    print(f"  Total sanctioned entries: {len(entities):,}")
    by_program: dict[str, int] = {}
    for e in entities:
        by_program[e.program] = by_program.get(e.program, 0) + 1
    print(f"\n  Top 10 programs:")
    for prog, n in sorted(by_program.items(), key=lambda x: -x[1])[:10]:
        print(f"    {prog:<30} {n:>6,}")

    print("\n" + "=" * 60)
    print("  CRYPTO ADDRESSES ON OFAC LIST")
    print("=" * 60)
    addrs = load_sanctioned_crypto_addresses()
    print(f"  Distinct addresses: {len(addrs):,}")
    print(f"  Sample (first 5):")
    for a in list(addrs)[:5]:
        print(f"    {a}")

    print("\n" + "=" * 60)
    print("  COMBINED KNOWN-BAD WALLET SEED LIST")
    print("=" * 60)
    seed = get_seed_bad_wallets()
    print(f"  Total seed addresses: {len(seed):,}")

    if entities_csv.exists():
        print("\n" + "=" * 60)
        print(f"  APPLYING TO {entities_csv}")
        print("=" * 60)
        df = pd.read_csv(entities_csv)
        flagged, stats = flag_entities_against_sanctions(df)
        # Backup original
        backup = entities_csv.with_suffix(".pre_sanctions.csv")
        df.to_csv(backup, index=False)
        flagged.to_csv(entities_csv, index=False)
        print(f"  Original backup: {backup}")
        print(f"  Updated:         {entities_csv}")
        print(f"  Matched names:   {stats['matched_names']}")
        print(f"  Matched wallets: {stats['matched_wallets']}")
    else:
        print(f"\n  [!] {entities_csv} not found — run generate_sample_data.py first")

    print("\n[OK] Sanctions fetch complete.\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--force-refresh", action="store_true",
                        help="Bypass 24h cache and re-download")
    parser.add_argument("--entities", type=Path,
                        default=settings.app_data_dir / "sample" / "entities.csv")
    args = parser.parse_args()
    main(args.force_refresh, args.entities)
