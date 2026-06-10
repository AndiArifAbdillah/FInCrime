"""DTTOT (Daftar Terduga Teroris dan Organisasi Teroris) + UN consolidated list loader.

Sources (publicly accessible):
    - UN Security Council Consolidated List (XML):
      https://scsanctions.un.org/resources/xml/en/consolidated.xml
    - PPATK DTTOT — the official Indonesian list. Public access varies; PPATK
      publishes summaries via press releases & periodic updates. For the
      prototype we use a representative seed list + UN list (which Indonesia
      adopts via Perpres No.20/2018).

For production: institutions with PPATK MoU get direct API access via SIPESAT.
"""
from __future__ import annotations

import defusedxml.ElementTree as ET  # safe parser: downloaded XML is untrusted input
from dataclasses import dataclass, field
from src.common.utils import utc_now
from pathlib import Path
from typing import Optional

import httpx

from src.common.config import settings
from src.common.logger import get_logger

log = get_logger("integrations.dttot")

UN_LIST_URL = "https://scsanctions.un.org/resources/xml/en/consolidated.xml"

CACHE_DIR = settings.app_data_dir / "sanctions"
CACHE_DIR.mkdir(parents=True, exist_ok=True)


@dataclass
class DTTOTEntry:
    list_id: str           # UN ref id
    name: str
    aliases: list[str] = field(default_factory=list)
    list_type: str = "individual"   # "individual" | "entity"
    designation_date: str = ""
    program: str = "UN_CONSOLIDATED"
    nationality: str = ""
    is_indonesian_priority: bool = False


# ============================================================
# UN consolidated XML download / parse
# ============================================================
def download_un_list(force: bool = False, timeout: int = 30) -> Path:
    cache = CACHE_DIR / "un_consolidated.xml"
    if cache.exists() and not force:
        age_h = (utc_now().timestamp() - cache.stat().st_mtime) / 3600
        if age_h < 24:
            log.info("dttot.cache_hit", age_hours=round(age_h, 1))
            return cache
    log.info("dttot.downloading", url=UN_LIST_URL)
    with httpx.Client(timeout=timeout, follow_redirects=True,
                      headers={"User-Agent": "FinCrime-AI/0.1 (research)"}) as client:
        r = client.get(UN_LIST_URL)
        r.raise_for_status()
        cache.write_bytes(r.content)
    log.info("dttot.downloaded", size_kb=len(r.content) // 1024)
    return cache


def parse_un_list(xml_path: Path) -> list[DTTOTEntry]:
    out: list[DTTOTEntry] = []
    try:
        tree = ET.parse(xml_path)
        root = tree.getroot()
    except ET.ParseError as e:
        log.warning("dttot.parse_failed", error=str(e))
        return out

    # XML uses element <INDIVIDUAL> and <ENTITY>
    for ind in root.iter():
        tag = ind.tag.lower()
        if tag not in ("individual", "entity"):
            continue
        list_id = (ind.findtext("REFERENCE_NUMBER") or ind.findtext("DATAID") or "").strip()
        full_name_parts = []
        for k in ("FIRST_NAME", "SECOND_NAME", "THIRD_NAME", "FOURTH_NAME"):
            v = ind.findtext(k)
            if v:
                full_name_parts.append(v.strip())
        if not full_name_parts:
            v = ind.findtext("NAME") or ind.findtext("FIRST_NAME")
            if v:
                full_name_parts.append(v.strip())
        name = " ".join(full_name_parts).strip()
        if not name:
            continue
        aliases = []
        for alias in ind.iter():
            if alias.tag.upper().endswith("ALIAS"):
                an = alias.findtext("ALIAS_NAME") or ""
                if an.strip():
                    aliases.append(an.strip())
        nat = ind.findtext("NATIONALITY/VALUE") or ""
        prog = ind.findtext("UN_LIST_TYPE") or "UN_CONSOLIDATED"
        out.append(DTTOTEntry(
            list_id=list_id, name=name,
            aliases=aliases,
            list_type="individual" if tag == "individual" else "entity",
            program=prog,
            nationality=nat,
            is_indonesian_priority=("IDN" in nat.upper() or "INDONESIA" in nat.upper()),
        ))
    log.info("dttot.parsed", n=len(out),
             indonesian_priority=sum(1 for e in out if e.is_indonesian_priority))
    return out


# ============================================================
# Indonesian DTTOT seed list (publicly cited entries)
# ============================================================
# These are organizations/individuals publicly designated by Indonesian authorities
# (KPK, Densus 88, PPATK press releases). For full DTTOT, partnership with PPATK
# via SIPESAT is required.
DTTOT_INDONESIAN_SEED = [
    DTTOTEntry(list_id="ID-001", name="Jamaah Islamiyah", list_type="entity",
               program="DTTOT_INDONESIA", is_indonesian_priority=True),
    DTTOTEntry(list_id="ID-002", name="Jamaah Ansharut Daulah", list_type="entity",
               program="DTTOT_INDONESIA", is_indonesian_priority=True,
               aliases=["JAD"]),
    DTTOTEntry(list_id="ID-003", name="Mujahidin Indonesia Timur", list_type="entity",
               program="DTTOT_INDONESIA", is_indonesian_priority=True,
               aliases=["MIT", "Eastern Indonesia Mujahideen"]),
    DTTOTEntry(list_id="ID-004", name="Jamaah Ansharut Tauhid", list_type="entity",
               program="DTTOT_INDONESIA", is_indonesian_priority=True,
               aliases=["JAT"]),
]


# ============================================================
# Public interface
# ============================================================
def load_all_dttot() -> list[DTTOTEntry]:
    """Combine UN list + Indonesian seed entries. Returns deduped list."""
    entries = list(DTTOT_INDONESIAN_SEED)
    try:
        xml = download_un_list()
        entries.extend(parse_un_list(xml))
    except Exception as e:
        log.warning("dttot.un_load_failed", error=str(e))
    # dedupe by name (case-insensitive)
    seen: dict[str, DTTOTEntry] = {}
    for e in entries:
        k = e.name.lower().strip()
        if k and k not in seen:
            seen[k] = e
    return list(seen.values())


def screening_index() -> dict[str, DTTOTEntry]:
    """Build a name -> entry index for fast matching."""
    out: dict[str, DTTOTEntry] = {}
    for e in load_all_dttot():
        out[e.name.lower().strip()] = e
        for a in e.aliases:
            out[a.lower().strip()] = e
    return out


def screen_name(name: str, index: Optional[dict] = None) -> Optional[DTTOTEntry]:
    """Returns the DTTOTEntry if `name` matches an entry (exact or alias)."""
    idx = index or screening_index()
    return idx.get(name.lower().strip())


def screen_entities_df(df, name_column: str = "entity_id", index: Optional[dict] = None):
    """Apply DTTOT screening to a pandas DataFrame, return df + match stats."""
    idx = index or screening_index()
    df = df.copy()
    df["dttot_match"] = False
    df["dttot_program"] = ""
    matched = 0
    for i, row in df.iterrows():
        name = str(row.get(name_column, "")).lower().strip()
        hit = idx.get(name)
        if hit:
            df.at[i, "dttot_match"] = True
            df.at[i, "dttot_program"] = hit.program
            matched += 1
    log.info("dttot.screened", matched=matched, total=len(df))
    return df, {"matched": matched, "total": len(df), "index_size": len(idx)}
