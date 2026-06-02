"""Pull REAL Ethereum transactions from Etherscan for known-bad wallets.

This replaces the synthetic crypto_edges.csv with real on-chain data around
publicly-documented sanctioned/criminal wallets (Tornado Cash, Lazarus Group,
hack proceeds, etc.).

Usage:
    1. Get a free API key: https://etherscan.io/myapikey
    2. Add to .env:   ETHERSCAN_API_KEY=YOUR_KEY_HERE
    3. Run:           python scripts/fetch_real_blockchain.py
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
from src.ingestion.blockchain_connector import BlockchainConnector
from src.ingestion.sanctions_loader import KNOWN_BAD_WALLETS, get_seed_bad_wallets

log = get_logger("fetch_real_blockchain")


def main(seed_wallets: list[str], limit_per_wallet: int, hops: int,
         out_dir: Path):
    if not settings.etherscan_api_key:
        print("\n" + "=" * 60)
        print("  [!] ETHERSCAN_API_KEY missing")
        print("=" * 60)
        print("  Get a free key (3 steps, ~2 minutes):")
        print()
        print("    1. Open: https://etherscan.io/register")
        print("    2. Login -> https://etherscan.io/myapikey -> 'Add'")
        print("    3. Edit .env:")
        print("         ETHERSCAN_API_KEY=YourKeyHere")
        print()
        print("  Free tier: 5 calls/sec, 100k calls/day — more than enough.")
        print("=" * 60)
        sys.exit(1)

    out_dir.mkdir(parents=True, exist_ok=True)
    conn = BlockchainConnector()

    print("\n" + "=" * 60)
    print("  REAL ETHEREUM DATA FETCH")
    print("=" * 60)
    rate = conn.get_eth_to_idr()
    print(f"  ETH -> IDR rate (live):  Rp {rate:,.0f} / ETH")
    print(f"  Seed wallets:            {len(seed_wallets)}")
    print(f"  Tx limit / wallet:       {limit_per_wallet}")
    print(f"  Tracing hops:            {hops}")
    print()

    all_tx: list[dict] = []
    discovered_wallets: set[str] = set()
    # Start with seed wallets at hop 0
    current_layer: set[str] = set(addr.lower() for addr in seed_wallets)
    visited: set[str] = set()

    for hop in range(hops + 1):
        print(f"  [Hop {hop}]  {len(current_layer)} wallet(s) to scan ...")
        next_layer: set[str] = set()
        for addr in current_layer:
            if addr in visited:
                continue
            visited.add(addr)
            discovered_wallets.add(addr)
            try:
                txs = conn.fetch_address_transfers(addr, limit=limit_per_wallet)
            except Exception as e:
                print(f"    [!] {addr[:10]}... failed: {e}")
                continue
            for tx in txs:
                all_tx.append(tx.model_dump())
                # Build next hop
                for w in (tx.sender_id.replace("WALLET_", ""),
                          tx.receiver_id.replace("WALLET_", "")):
                    if w not in visited:
                        next_layer.add(w)
        current_layer = next_layer
        if not current_layer:
            break

    print(f"\n  Pulled {len(all_tx):,} REAL transactions touching "
          f"{len(discovered_wallets):,} wallets")

    if not all_tx:
        print("  No transactions pulled — check API key + network.")
        return

    # ---------- Write real transactions ----------
    df = pd.DataFrame(all_tx)
    real_tx_path = out_dir / "real_transactions.csv"
    df.to_csv(real_tx_path, index=False)
    print(f"  -> {real_tx_path}")

    # ---------- Derive wallet→wallet edges (aggregated) ----------
    edge_agg = (df.groupby(["sender_id", "receiver_id"])
                  .agg(weight=("amount_idr", "sum"),
                       tx_count=("tx_id", "count"))
                  .reset_index()
                  .rename(columns={"sender_id": "src", "receiver_id": "dst"}))
    seed_set = {f"WALLET_{a.lower()}" for a in seed_wallets}
    edge_agg["is_layering"] = (
        edge_agg["src"].isin(seed_set) | edge_agg["dst"].isin(seed_set)
    ).astype(int)
    edges_path = out_dir / "real_crypto_edges.csv"
    edge_agg.to_csv(edges_path, index=False)
    print(f"  -> {edges_path}  ({len(edge_agg):,} edges)")

    # ---------- Derive wallet entity records ----------
    bad_set = {f"WALLET_{a.lower()}" for a in get_seed_bad_wallets().keys()}
    wallets = pd.DataFrame({"entity_id": sorted(
        set(df["sender_id"]) | set(df["receiver_id"])
    )})
    wallets["entity_type"] = "wallet"
    wallets["country"] = "XX"
    wallets["age_days"] = 365  # placeholder; could fetch first-tx block
    wallets["kyc_level"] = 0
    counts = pd.concat([df["sender_id"], df["receiver_id"]]).value_counts()
    wallets["txn_count_30d"] = wallets["entity_id"].map(counts).fillna(0).astype(int)
    volumes = (df.groupby("sender_id")["amount_idr"].sum().add(
               df.groupby("receiver_id")["amount_idr"].sum(), fill_value=0))
    wallets["total_volume_30d"] = wallets["entity_id"].map(volumes).fillna(0.0)
    wallets["avg_tx_amount"] = (wallets["total_volume_30d"] /
                                wallets["txn_count_30d"].clip(lower=1)).round(2)
    wallets["distinct_counterparties_30d"] = wallets["txn_count_30d"]  # rough
    wallets["pep_flag"] = False
    wallets["sanction_flag"] = wallets["entity_id"].isin(bad_set)
    wallets["has_crypto_activity"] = True
    wallets["is_fraud"] = wallets["sanction_flag"].astype(int)
    wallets_path = out_dir / "real_wallets.csv"
    wallets.to_csv(wallets_path, index=False)
    print(f"  -> {wallets_path}  ({len(wallets):,} wallets, "
          f"{int(wallets.sanction_flag.sum())} sanctioned)")

    print("\n[OK] Real blockchain data fetched.")
    print("\n  Next step:")
    print("    python scripts\\train_all_models.py "
          "--entities data\\real\\real_wallets.csv "
          "--transactions data\\real\\real_transactions.csv")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--wallets", type=str, nargs="*", default=None,
                        help="Seed wallets (default: hardcoded list of OFAC sanctioned)")
    parser.add_argument("--limit", type=int, default=50,
                        help="Tx per wallet (default 50)")
    parser.add_argument("--hops", type=int, default=1,
                        help="Tracing hops outward (default 1)")
    parser.add_argument("--out", type=Path,
                        default=settings.app_data_dir / "real")
    args = parser.parse_args()

    seeds = args.wallets or list(KNOWN_BAD_WALLETS.keys())
    main(seeds, args.limit, args.hops, args.out)
