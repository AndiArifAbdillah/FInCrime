"""Beneficial Ownership (UBO) tracking — FATF Recommendations 24-25.

Per Perpres No.13/2018, badan hukum Indonesia wajib mengungkap Pemilik
Manfaat Akhir (UBO). System builds a graph of shareholding and traces
to UBO, plus detects shell company indicators.

Shell company red flags (FATF + OECD):
    - Multiple corporate layers (>= 3 levels)
    - Director/shareholder also acts in many other companies
    - Registered address shared with many other companies
    - No physical operations, just postal box
    - Country of incorporation = offshore secrecy jurisdiction
    - Recently registered + high transaction volume
    - Nominee directors
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from typing import Optional

import networkx as nx

from src.common.logger import get_logger

log = get_logger("private.ubo")


# ----- Offshore secrecy jurisdictions (FATF + Tax Justice Network FSI 2023) -----
OFFSHORE_JURISDICTIONS = {
    "VG", "KY", "BM", "PA", "LU", "LI", "CW", "VU", "BS", "BZ", "GG",
    "JE", "IM", "MC", "AW", "SC", "MU", "AG", "MS", "AI", "TC", "MH",
    "NA", "WS", "VC", "GI", "MT", "CY", "HK", "SG", "AE",  # AE/SG/HK partial
}


@dataclass
class CorporateEntity:
    entity_id: str                     # NPWP/SK Menkumham number or generated
    legal_name: str
    legal_form: str = "PT"             # PT, CV, Yayasan, Koperasi, ...
    country_of_incorp: str = "ID"
    registered_address: str = ""
    incorporated_date: Optional[date] = None
    npwp: str = ""
    sk_menkumham: str = ""             # Surat Keputusan number
    business_purpose: str = ""
    is_active: bool = True
    has_physical_office: bool = True
    declared_ubo: list[str] = field(default_factory=list)  # KTP IDs of declared UBOs


@dataclass
class ShareholderLink:
    """Link in the ownership graph. Either an individual or another corporate."""
    owner_id: str                      # parent
    owned_id: str                      # subsidiary
    owner_type: str = "individual"     # individual | corporate
    share_pct: float = 0.0
    is_director: bool = False
    is_commissioner: bool = False
    appointed_date: Optional[date] = None


# ============================================================
# UBO Tracker
# ============================================================
class UBOTracker:
    """In-memory graph of corporate ownership for UBO tracing."""

    def __init__(self):
        # Directed graph: owner -> owned, with attributes
        self.G = nx.DiGraph()
        self._entities: dict[str, CorporateEntity] = {}
        self._individuals: set[str] = set()

    # ----- Build -----
    def add_entity(self, entity: CorporateEntity) -> None:
        self._entities[entity.entity_id] = entity
        self.G.add_node(entity.entity_id, node_type="corporate", **{
            "legal_name": entity.legal_name,
            "country": entity.country_of_incorp,
            "address": entity.registered_address,
        })

    def add_individual(self, individual_id: str, name: str = "",
                       is_pep: bool = False, country: str = "ID") -> None:
        self._individuals.add(individual_id)
        self.G.add_node(individual_id, node_type="individual",
                        name=name, is_pep=is_pep, country=country)

    def add_shareholding(self, link: ShareholderLink) -> None:
        # ensure owner node exists
        if link.owner_id not in self.G:
            if link.owner_type == "individual":
                self.add_individual(link.owner_id)
            else:
                # placeholder corporate
                self.G.add_node(link.owner_id, node_type="corporate",
                                legal_name=link.owner_id)
        self.G.add_edge(link.owner_id, link.owned_id,
                        share_pct=link.share_pct,
                        is_director=link.is_director,
                        is_commissioner=link.is_commissioner)

    # ----- Trace UBO -----
    def trace_ubo(self, entity_id: str, max_depth: int = 6,
                  threshold_pct: float = 25.0) -> list[dict]:
        """Walk upward from `entity_id` to find ultimate beneficial owners.

        FATF threshold: ownership/control of >= 25%.

        Returns list of UBO dicts: {entity_id, name, share_pct, depth, is_pep}.
        """
        if entity_id not in self.G:
            return []

        # BFS upward (in_edges = owners)
        ubos: list[dict] = []
        visited: set[str] = set()
        queue: list[tuple[str, float, int]] = [(entity_id, 100.0, 0)]

        while queue:
            current, cumulative_pct, depth = queue.pop(0)
            if current in visited or depth > max_depth:
                continue
            visited.add(current)

            in_edges = list(self.G.in_edges(current, data=True))
            if not in_edges:
                # terminal — current is an owner with no further owners above
                node = self.G.nodes.get(current, {})
                if node.get("node_type") == "individual" and cumulative_pct >= threshold_pct:
                    ubos.append({
                        "entity_id": current,
                        "name": node.get("name", ""),
                        "node_type": "individual",
                        "is_pep": node.get("is_pep", False),
                        "country": node.get("country", ""),
                        "effective_pct": round(cumulative_pct, 2),
                        "depth": depth,
                    })
                continue

            for owner, _, edata in in_edges:
                pct = float(edata.get("share_pct", 0))
                next_pct = cumulative_pct * (pct / 100.0)
                queue.append((owner, next_pct, depth + 1))

                # If owner is individual & has direct stake passing threshold, record
                owner_node = self.G.nodes.get(owner, {})
                if owner_node.get("node_type") == "individual" and next_pct >= threshold_pct:
                    ubos.append({
                        "entity_id": owner,
                        "name": owner_node.get("name", ""),
                        "node_type": "individual",
                        "is_pep": owner_node.get("is_pep", False),
                        "country": owner_node.get("country", ""),
                        "effective_pct": round(next_pct, 2),
                        "depth": depth + 1,
                    })

        # dedupe by entity_id, keep highest pct
        out: dict[str, dict] = {}
        for u in ubos:
            k = u["entity_id"]
            if k not in out or out[k]["effective_pct"] < u["effective_pct"]:
                out[k] = u
        return sorted(out.values(), key=lambda x: -x["effective_pct"])


# ============================================================
# Shell company detector
# ============================================================
def detect_shell_company(entity: CorporateEntity,
                          tracker: Optional[UBOTracker] = None,
                          shared_address_count: int = 0,
                          tx_volume_idr: float = 0,
                          tx_count: int = 0) -> dict:
    """Score how likely `entity` is a shell company. Returns indicators + score."""
    indicators: list[str] = []
    score = 0.0

    # ---- Offshore jurisdiction ----
    if entity.country_of_incorp.upper() in OFFSHORE_JURISDICTIONS:
        indicators.append(f"offshore_jurisdiction:{entity.country_of_incorp}")
        score += 0.3

    # ---- No physical office ----
    if not entity.has_physical_office:
        indicators.append("no_physical_office")
        score += 0.25

    # ---- Recently incorporated + high volume ----
    if entity.incorporated_date:
        age_days = (date.today() - entity.incorporated_date).days
        if age_days < 365 and tx_volume_idr >= 1_000_000_000:
            indicators.append(f"young_entity_high_volume:{age_days}d")
            score += 0.3
        elif age_days < 90:
            indicators.append(f"very_recent:{age_days}d")
            score += 0.1

    # ---- Shared address with many other companies ----
    if shared_address_count >= 5:
        indicators.append(f"shared_address_{shared_address_count}_companies")
        score += 0.2

    # ---- Multi-layer corporate structure (UBO chain depth) ----
    if tracker:
        ubos = tracker.trace_ubo(entity.entity_id)
        max_depth = max((u["depth"] for u in ubos), default=0)
        if max_depth >= 3:
            indicators.append(f"ownership_layers_{max_depth}")
            score += 0.15
        if not ubos:
            indicators.append("ubo_not_traceable")
            score += 0.25

    # ---- Very low or no employees inferred from business purpose absence ----
    if not entity.business_purpose:
        indicators.append("no_declared_business_purpose")
        score += 0.05

    score = min(score, 1.0)
    return {
        "entity_id": entity.entity_id,
        "legal_name": entity.legal_name,
        "shell_score": round(score, 3),
        "indicators": indicators,
        "is_likely_shell": score >= 0.6,
    }
