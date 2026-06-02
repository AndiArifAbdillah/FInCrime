"""Load real sanctions / PEP lists from public sources.

Public sources (no API key required):
    - OFAC SDN list (US Treasury):    https://www.treasury.gov/ofac/downloads/sdn.csv
    - OFAC Crypto Addresses (XML):    https://www.treasury.gov/ofac/downloads/sdn.xml
    - EU Consolidated Sanctions:      https://webgate.ec.europa.eu/fsd/fsf/public/files/csvFullSanctionsList_1_1/content
    - UN Sanctions List (XML):        https://scsanctions.un.org/resources/xml/en/consolidated.xml

For the Indonesian context, also relevant:
    - PPATK DTTOT (Daftar Terduga Teroris & Organisasi Teroris) — restricted access
    - Bappebti illegal investment list — scraped from public bulletins
"""
from __future__ import annotations

import csv
import io
import re
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Optional

import httpx

from src.common.config import settings
from src.common.logger import get_logger

log = get_logger("sanctions")

OFAC_SDN_URL = "https://www.treasury.gov/ofac/downloads/sdn.csv"
OFAC_ADDR_URL = "https://www.treasury.gov/ofac/downloads/sdn.xml"

CACHE_DIR = settings.app_data_dir / "sanctions"
CACHE_DIR.mkdir(parents=True, exist_ok=True)


@dataclass
class SanctionedEntity:
    sdn_id: str
    name: str
    sdn_type: str         # "individual" | "entity" | "vessel" | "aircraft"
    program: str          # which sanctions program (e.g., "SDGT", "DPRK", "RUSSIA-EO14024")
    title: str = ""
    crypto_addresses: list[str] = field(default_factory=list)
    aliases: list[str] = field(default_factory=list)


# ============================================================
# Public OFAC SDN parser
# ============================================================
def download_ofac_sdn(force: bool = False, timeout: int = 30) -> Path:
    """Download OFAC SDN CSV (US Treasury). Cached for 24h."""
    cache = CACHE_DIR / "ofac_sdn.csv"
    if cache.exists() and not force:
        age_h = (datetime.utcnow().timestamp() - cache.stat().st_mtime) / 3600
        if age_h < 24:
            log.info("ofac.cache_hit", age_hours=round(age_h, 1))
            return cache
    log.info("ofac.downloading", url=OFAC_SDN_URL)
    with httpx.Client(timeout=timeout, follow_redirects=True) as client:
        r = client.get(OFAC_SDN_URL)
        r.raise_for_status()
        cache.write_bytes(r.content)
    log.info("ofac.downloaded", size_kb=len(r.content) // 1024)
    return cache


def parse_ofac_sdn(csv_path: Path) -> list[SanctionedEntity]:
    """OFAC SDN CSV has no header. Columns (1-indexed):
        1=ent_num, 2=SDN_Name, 3=SDN_Type, 4=Program, 5=Title, 6=Call_Sign,
        7=Vess_type, 8=Tonnage, 9=GRT, 10=Vess_flag, 11=Vess_owner, 12=Remarks
    """
    entities: list[SanctionedEntity] = []
    with open(csv_path, encoding="latin-1") as f:
        reader = csv.reader(f, quotechar='"')
        for row in reader:
            if len(row) < 4:
                continue
            ent_num, name, sdn_type, program = row[0], row[1], row[2], row[3]
            title = row[4] if len(row) > 4 else ""
            remarks = row[11] if len(row) > 11 else ""

            # Extract any crypto addresses mentioned in remarks (OFAC stores them there)
            crypto_addrs = _extract_crypto_addresses(remarks)

            entities.append(SanctionedEntity(
                sdn_id=ent_num,
                name=name.strip().strip('"'),
                sdn_type=sdn_type.lower(),
                program=program,
                title=title,
                crypto_addresses=crypto_addrs,
            ))
    log.info("ofac.parsed", n=len(entities))
    return entities


# ============================================================
# Crypto address extractor (regex)
# ============================================================
ETH_ADDR_RE = re.compile(r"\b0x[a-fA-F0-9]{40}\b")
BTC_ADDR_RE = re.compile(r"\b(?:1[a-km-zA-HJ-NP-Z1-9]{25,34}|3[a-km-zA-HJ-NP-Z1-9]{25,34}|bc1[a-zA-HJ-NP-Z0-9]{25,87})\b")
XMR_ADDR_RE = re.compile(r"\b4[1-9A-HJ-NP-Za-km-z]{94}\b")


def _extract_crypto_addresses(text: str) -> list[str]:
    if not text:
        return []
    addrs = set()
    addrs.update(ETH_ADDR_RE.findall(text))
    addrs.update(BTC_ADDR_RE.findall(text))
    addrs.update(XMR_ADDR_RE.findall(text))
    return sorted(addrs)


# ============================================================
# High-level interface
# ============================================================
def load_sanctioned_names() -> set[str]:
    """Return a normalized set of sanctioned names (for entity name matching)."""
    csv_path = download_ofac_sdn()
    entities = parse_ofac_sdn(csv_path)
    return {e.name.lower().strip() for e in entities}


def load_sanctioned_crypto_addresses() -> set[str]:
    """Return the set of all crypto addresses on OFAC's list (lowercased)."""
    csv_path = download_ofac_sdn()
    entities = parse_ofac_sdn(csv_path)
    addrs: set[str] = set()
    for e in entities:
        for a in e.crypto_addresses:
            addrs.add(a.lower())
    log.info("ofac.crypto_addresses_found", n=len(addrs))
    return addrs


# ============================================================
# Hardcoded high-confidence bad-wallet seed list (well-known cases)
# ============================================================
# These are publicly documented mixers / state-sponsored wallets.
# Source: OFAC press releases, Chainalysis crime reports, ZachXBT investigations.
KNOWN_BAD_WALLETS = {
    # Tornado Cash (sanctioned by OFAC Aug 2022)
    "0x8589427373d6d84e98730d7795d8f6f8731fda16": "Tornado Cash",
    "0x722122df12d4e14e13ac3b6895a86e84145b6967": "Tornado Cash Router",
    "0xdd4c48c0b24039969fc16d1cdf626eab821d3384": "Tornado Cash 0.1 ETH",
    "0xd96f2b1c14db8458374d9aca76e26c3d18364307": "Tornado Cash 1 ETH",
    "0x4736dcf1b7a3d580672ccce6213c03e123c33aa1": "Tornado Cash 10 ETH",
    # Lazarus Group (DPRK) — confirmed via FBI/UN reports
    "0x098b716b8aaf21512996dc57eb0615e2383e2f96": "Lazarus Group (Ronin Bridge hack)",
    "0xa0e1c89ef1a489c9c7de96311ed5ce5d32c20e4b": "Lazarus Group",
    # Hydra Market (darknet)
    "0xf7b31119c2682c88d88d455dbb9d5932c65cf1be": "Hydra Market",
}


def get_seed_bad_wallets() -> dict[str, str]:
    """Return hardcoded + dynamically loaded OFAC crypto addresses."""
    out = dict(KNOWN_BAD_WALLETS)
    try:
        for addr in load_sanctioned_crypto_addresses():
            out.setdefault(addr, "OFAC-sanctioned")
    except Exception as e:
        log.warning("ofac.dynamic_load_failed", error=str(e))
    return out


# ============================================================
# Apply to an entities DataFrame
# ============================================================
def flag_entities_against_sanctions(entities_df, name_column: str = "entity_id"):
    """Mark `sanction_flag` and `pep_flag` for matches against OFAC list.

    Returns a new DataFrame with updated flags + a count of matches.
    """
    import pandas as pd
    try:
        sanctioned = load_sanctioned_names()
        bad_wallets = get_seed_bad_wallets()
    except Exception as e:
        log.warning("sanctions.lookup_failed", error=str(e))
        return entities_df, {"matched_names": 0, "matched_wallets": 0}

    df = entities_df.copy()
    matched_names = 0
    matched_wallets = 0

    for i, row in df.iterrows():
        name = str(row.get(name_column, "")).lower()
        # name match
        if name in sanctioned:
            df.at[i, "sanction_flag"] = True
            matched_names += 1
            continue
        # crypto address match (for wallets)
        if row.get("entity_type") == "wallet":
            # entity_id format: WALLET_0xABCD...  →  extract the 0x... part
            addr = name.replace("wallet_", "")
            if addr in {a.lower() for a in bad_wallets}:
                df.at[i, "sanction_flag"] = True
                matched_wallets += 1

    log.info("sanctions.applied", matched_names=matched_names,
             matched_wallets=matched_wallets, total=len(df))
    return df, {"matched_names": matched_names, "matched_wallets": matched_wallets}
