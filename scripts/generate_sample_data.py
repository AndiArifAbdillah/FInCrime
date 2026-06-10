"""
Generate synthetic transaction & entity datasets for FinCrime training/demo.

Outputs:
  data/sample/entities.csv          — customer/wallet metadata + labels (fraudulent)
  data/sample/transactions.csv      — labeled transactions (bank/ewallet/crypto)
  data/sample/crypto_edges.csv      — wallet->wallet edges for GNN
  data/sample/known_bad_wallets.csv — ground-truth labels for Layer 2

Designed so the models trained on these have realistic AUC > 0.85.
"""
from __future__ import annotations

# --- make `src` importable when run as `python scripts/generate_sample_data.py` ---
import sys
from pathlib import Path as _Path
sys.path.insert(0, str(_Path(__file__).resolve().parent.parent))

# Windows: force UTF-8 stdout so emoji/Unicode in print() doesn't crash on cp1252
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

import argparse
import random
from datetime import timedelta
from src.common.utils import utc_now
from pathlib import Path

import numpy as np
import pandas as pd

RANDOM_SEED = 42
random.seed(RANDOM_SEED)
np.random.seed(RANDOM_SEED)


HIGH_RISK_COUNTRIES = {"KP", "IR", "MM", "AF", "SY", "VE"}  # FATF-flavored
INDONESIAN_BANKS = ["BCA", "BRI", "BNI", "MANDIRI", "CIMB", "PERMATA", "BTN"]
EWALLETS = ["GOPAY", "OVO", "DANA", "SHOPEEPAY", "LINKAJA"]
CHAINS = ["eth", "btc", "bsc", "polygon"]


def _gen_entities(n_individuals: int, n_corp: int, n_wallets: int,
                  fraud_rate: float = 0.05) -> pd.DataFrame:
    rows = []

    # Individuals
    for i in range(n_individuals):
        is_fraud = random.random() < fraud_rate
        age_days = random.randint(30, 3650)
        kyc = np.random.choice([0, 1, 2], p=[0.05, 0.55, 0.40])
        txn_count = int(np.random.gamma(2.0, 15.0))
        if is_fraud:
            txn_count = int(txn_count * random.uniform(1.5, 5))
        volume = txn_count * np.random.lognormal(13, 1.2)
        rows.append({
            "entity_id": f"IND_{i:06d}",
            "entity_type": "individual",
            "country": random.choices(
                ["ID"] + list(HIGH_RISK_COUNTRIES),
                weights=[0.93] + [0.07 / len(HIGH_RISK_COUNTRIES)] * len(HIGH_RISK_COUNTRIES),
            )[0],
            "age_days": age_days,
            "kyc_level": int(kyc),
            "txn_count_30d": txn_count,
            "total_volume_30d": float(volume),
            "avg_tx_amount": float(volume / max(txn_count, 1)),
            "distinct_counterparties_30d": min(txn_count, random.randint(1, 50)),
            "pep_flag": random.random() < (0.10 if is_fraud else 0.005),
            "sanction_flag": random.random() < (0.20 if is_fraud else 0.001),
            "has_crypto_activity": random.random() < (0.55 if is_fraud else 0.10),
            "is_fraud": int(is_fraud),
        })

    # Corporates (slightly different distributions)
    for i in range(n_corp):
        is_fraud = random.random() < fraud_rate * 1.5  # corp more often shell
        rows.append({
            "entity_id": f"CORP_{i:05d}",
            "entity_type": "corporate",
            "country": random.choices(
                ["ID"] + list(HIGH_RISK_COUNTRIES),
                weights=[0.85] + [0.15 / len(HIGH_RISK_COUNTRIES)] * len(HIGH_RISK_COUNTRIES),
            )[0],
            "age_days": random.randint(180, 7300),
            "kyc_level": np.random.choice([1, 2], p=[0.35, 0.65]),
            "txn_count_30d": int(np.random.gamma(3.0, 80.0)),
            "total_volume_30d": float(np.random.lognormal(18, 1.5)),
            "avg_tx_amount": 0.0,
            "distinct_counterparties_30d": random.randint(5, 300),
            "pep_flag": random.random() < (0.05 if is_fraud else 0.002),
            "sanction_flag": random.random() < (0.30 if is_fraud else 0.001),
            "has_crypto_activity": random.random() < (0.45 if is_fraud else 0.05),
            "is_fraud": int(is_fraud),
        })

    # Crypto wallets (will be used in Layer 2)
    for i in range(n_wallets):
        is_fraud = random.random() < fraud_rate * 2.5  # higher base rate in crypto
        rows.append({
            "entity_id": f"WALLET_0x{i:012x}",
            "entity_type": "wallet",
            "country": "XX",  # wallets are pseudonymous
            "age_days": random.randint(1, 1825),
            "kyc_level": 0,
            "txn_count_30d": int(np.random.gamma(2.5, 25.0)),
            "total_volume_30d": float(np.random.lognormal(15, 2.0)),
            "avg_tx_amount": 0.0,
            "distinct_counterparties_30d": random.randint(1, 200),
            "pep_flag": False,
            "sanction_flag": random.random() < (0.15 if is_fraud else 0.001),
            "has_crypto_activity": True,
            "is_fraud": int(is_fraud),
        })

    df = pd.DataFrame(rows)
    df["avg_tx_amount"] = (df["total_volume_30d"] / df["txn_count_30d"].clip(lower=1)).round(2)
    return df


def _gen_transactions(entities: pd.DataFrame, n_tx: int) -> pd.DataFrame:
    """Generate transactions with deliberate fraud patterns (smurfing, layering, spikes)."""
    bank_corp = entities[entities.entity_type.isin(["individual", "corporate"])]
    wallets = entities[entities.entity_type == "wallet"]
    fraud_ids = set(entities[entities.is_fraud == 1].entity_id)

    rows = []
    base_time = utc_now() - timedelta(days=30)

    for i in range(n_tx):
        # Sample sender — fraud entities oversampled to create signal
        if random.random() < 0.25:
            sender = random.choice(entities[entities.is_fraud == 1].entity_id.tolist()
                                   or [entities.entity_id.iloc[0]])
        else:
            sender = random.choice(entities.entity_id.tolist())

        sender_row = entities[entities.entity_id == sender].iloc[0]

        # Channel routing
        if sender_row.entity_type == "wallet":
            channel = "crypto"
            receiver = random.choice(wallets.entity_id.tolist())
        else:
            channel = random.choices(["bank", "ewallet"], weights=[0.65, 0.35])[0]
            if random.random() < 0.10:
                # cross-channel: bank -> wallet  (the dangerous on/off-ramp)
                channel = "crypto"
                receiver = random.choice(wallets.entity_id.tolist())
            else:
                receiver = random.choice(bank_corp.entity_id.tolist())

        ts = base_time + timedelta(seconds=random.randint(0, 30 * 24 * 3600))

        # Amount — fraudsters tend to either smurf (sub-threshold) or burst
        is_fraud_sender = sender in fraud_ids
        if is_fraud_sender:
            r = random.random()
            if r < 0.5:
                # Smurfing: just below the 50M IDR PPATK trigger
                amount = random.uniform(40_000_000, 49_900_000)
            elif r < 0.8:
                # Burst transfers
                amount = random.uniform(100_000_000, 5_000_000_000)
            else:
                amount = float(np.random.lognormal(14, 1.5))
        else:
            amount = float(np.random.lognormal(12.5, 1.2))

        rows.append({
            "tx_id": f"TX_{i:09d}",
            "channel": channel,
            "timestamp": ts.isoformat(),
            "sender_id": sender,
            "receiver_id": receiver,
            "amount_idr": round(amount, 2),
            "currency": "IDR",
            "country_from": sender_row.country if sender_row.country != "XX" else "ID",
            "country_to": "ID" if random.random() < 0.92 else random.choice(list(HIGH_RISK_COUNTRIES)),
            "chain": random.choice(CHAINS) if channel == "crypto" else None,
            "tx_hash": f"0x{random.randint(0, 16**64):064x}" if channel == "crypto" else None,
            "sender_age_days": int(sender_row.age_days),
            "sender_tx_count_7d": int(sender_row.txn_count_30d / 4),
            "is_high_risk_jurisdiction": sender_row.country in HIGH_RISK_COUNTRIES,
            "is_fraud": int(is_fraud_sender and amount > 30_000_000),
        })

    return pd.DataFrame(rows)


def _gen_crypto_graph(entities: pd.DataFrame, density: float = 4.0) -> pd.DataFrame:
    """Generate wallet->wallet edges for the GNN. Inject layering chains around fraud wallets."""
    wallets = entities[entities.entity_type == "wallet"].entity_id.tolist()
    fraud_wallets = entities[(entities.entity_type == "wallet") &
                             (entities.is_fraud == 1)].entity_id.tolist()
    n_edges = int(len(wallets) * density)
    edges = []

    # Random base edges
    for _ in range(n_edges):
        a, b = random.sample(wallets, 2)
        edges.append({
            "src": a, "dst": b,
            "weight": float(np.random.lognormal(13, 1.5)),
            "tx_count": random.randint(1, 30),
            "is_layering": 0,
        })

    # Inject layering chains: A -> M1 -> M2 -> M3 -> B around fraud wallets
    for fw in fraud_wallets:
        chain_length = random.randint(3, 6)
        nodes = [fw] + random.sample(wallets, chain_length)
        for i in range(len(nodes) - 1):
            edges.append({
                "src": nodes[i], "dst": nodes[i + 1],
                "weight": float(np.random.uniform(45_000_000, 50_000_000)),  # smurfing
                "tx_count": random.randint(5, 25),
                "is_layering": 1,
            })

    return pd.DataFrame(edges)


def main(out_dir: Path, n_individuals: int, n_corp: int,
         n_wallets: int, n_tx: int) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    print(f"[1/4] Generating entities  (ind={n_individuals}, corp={n_corp}, wallets={n_wallets})")
    entities = _gen_entities(n_individuals, n_corp, n_wallets)
    entities.to_csv(out_dir / "entities.csv", index=False)
    print(f"      -> {len(entities):,} entities written")

    print(f"[2/4] Generating transactions (target n={n_tx:,})")
    transactions = _gen_transactions(entities, n_tx)
    transactions.to_csv(out_dir / "transactions.csv", index=False)
    print(f"      -> {len(transactions):,} transactions written")

    print("[3/4] Generating crypto wallet graph")
    edges = _gen_crypto_graph(entities)
    edges.to_csv(out_dir / "crypto_edges.csv", index=False)
    print(f"      -> {len(edges):,} edges written")

    print("[4/4] Writing known-bad wallet labels for Layer 2 supervision")
    bad = entities[(entities.entity_type == "wallet") & (entities.is_fraud == 1)][["entity_id"]]
    bad.columns = ["wallet_id"]
    bad["label"] = 1
    bad.to_csv(out_dir / "known_bad_wallets.csv", index=False)
    print(f"      -> {len(bad):,} known-bad wallets")
    print(f"\n[OK] Sample data ready in: {out_dir.resolve()}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate FinCrime sample data")
    parser.add_argument("--out", type=Path, default=Path("data/sample"))
    parser.add_argument("--individuals", type=int, default=5000)
    parser.add_argument("--corporates", type=int, default=500)
    parser.add_argument("--wallets", type=int, default=2000)
    parser.add_argument("--transactions", type=int, default=30000)
    args = parser.parse_args()

    main(args.out, args.individuals, args.corporates, args.wallets, args.transactions)
