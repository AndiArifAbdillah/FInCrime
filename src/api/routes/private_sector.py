"""Private Sector AML endpoints (DNFBP, Property, HVA, UBO, Shell company)."""
from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from src.private_sector.dnfbp import (
    DNFBPTransaction, screen_dnfbp_transaction, DNFBP_THRESHOLDS_IDR,
)
from src.private_sector.property import PropertyTransaction, PropertyMonitor
from src.private_sector.high_value_assets import (
    HighValueAsset, HVAMonitor, HVA_THRESHOLDS_IDR,
)
from src.private_sector.beneficial_ownership import (
    UBOTracker, CorporateEntity, ShareholderLink, detect_shell_company,
)

router = APIRouter()

# Shared in-memory UBO tracker (in production: persist to DB)
_ubo = UBOTracker()


# ============================================================
# DNFBP
# ============================================================
class DNFBPRequest(BaseModel):
    tx_id: str
    category: str
    reporter_id: str
    customer_id: str
    amount_idr: float
    payment_method: str = "transfer"
    cash_portion_idr: float = 0.0
    customer_country: str = "ID"
    customer_risk_score: float = 0.0
    customer_on_pep_list: bool = False
    customer_on_sanctions: bool = False


@router.get("/v1/private/dnfbp/thresholds")
def dnfbp_thresholds():
    return {"thresholds_idr": DNFBP_THRESHOLDS_IDR}


@router.post("/v1/private/dnfbp/screen")
def screen_dnfbp(req: DNFBPRequest):
    tx = DNFBPTransaction(
        tx_id=req.tx_id, category=req.category,
        reporter_id=req.reporter_id, customer_id=req.customer_id,
        amount_idr=req.amount_idr, payment_method=req.payment_method,
        cash_portion_idr=req.cash_portion_idr, customer_country=req.customer_country,
    )
    alert = screen_dnfbp_transaction(
        tx,
        customer_risk_score=req.customer_risk_score,
        customer_on_pep_list=req.customer_on_pep_list,
        customer_on_sanctions=req.customer_on_sanctions,
    )
    return {"alert": alert.__dict__ if alert else None, "clean": alert is None}


# ============================================================
# Property
# ============================================================
class PropertyRequest(BaseModel):
    tx_id: str
    notary_id: str = ""
    buyer_id: str
    buyer_country: str = "ID"
    seller_id: str = ""
    property_type: str = "RUMAH"
    sale_price_idr: float
    appraised_value_idr: float = 0.0
    cash_portion_idr: float = 0.0
    mortgage_idr: float = 0.0
    payment_method: str = "transfer"


@router.post("/v1/private/property/screen")
def screen_property(req: PropertyRequest):
    tx = PropertyTransaction(
        tx_id=req.tx_id, notary_id=req.notary_id,
        buyer_id=req.buyer_id, buyer_country=req.buyer_country,
        seller_id=req.seller_id, property_type=req.property_type,
        sale_price_idr=req.sale_price_idr,
        appraised_value_idr=req.appraised_value_idr,
        cash_portion_idr=req.cash_portion_idr,
        mortgage_idr=req.mortgage_idr,
        payment_method=req.payment_method,
    )
    return {"alerts": PropertyMonitor().screen(tx), "tx_id": req.tx_id}


# ============================================================
# High-Value Assets
# ============================================================
class HVARequest(BaseModel):
    tx_id: str
    asset_class: str
    asset_description: str
    dealer_id: str = ""
    buyer_id: str
    amount_idr: float
    payment_method: str = "transfer"
    cash_portion_idr: float = 0.0
    serial_number: str = ""
    is_resale: bool = False
    buyer_risk_score: float = 0.0
    buyer_on_pep_list: bool = False


@router.get("/v1/private/hva/thresholds")
def hva_thresholds():
    return {"thresholds_idr": HVA_THRESHOLDS_IDR}


@router.post("/v1/private/hva/screen")
def screen_hva(req: HVARequest):
    tx = HighValueAsset(
        tx_id=req.tx_id, asset_class=req.asset_class,
        asset_description=req.asset_description, dealer_id=req.dealer_id,
        buyer_id=req.buyer_id, amount_idr=req.amount_idr,
        payment_method=req.payment_method,
        cash_portion_idr=req.cash_portion_idr,
        serial_number=req.serial_number, is_resale=req.is_resale,
    )
    return {
        "alerts": HVAMonitor().screen(
            tx,
            buyer_risk_score=req.buyer_risk_score,
            buyer_on_pep_list=req.buyer_on_pep_list,
        ),
        "tx_id": req.tx_id,
    }


# ============================================================
# UBO / Beneficial Ownership
# ============================================================
class EntityCreate(BaseModel):
    entity_id: str
    legal_name: str
    legal_form: str = "PT"
    country_of_incorp: str = "ID"
    registered_address: str = ""
    business_purpose: str = ""
    has_physical_office: bool = True


class IndividualCreate(BaseModel):
    individual_id: str
    name: str
    is_pep: bool = False
    country: str = "ID"


class ShareholdingCreate(BaseModel):
    owner_id: str
    owned_id: str
    owner_type: str = "individual"
    share_pct: float = 0.0
    is_director: bool = False
    is_commissioner: bool = False


@router.post("/v1/private/ubo/entity")
def ubo_add_entity(req: EntityCreate):
    _ubo.add_entity(CorporateEntity(**req.model_dump()))
    return {"ok": True, "node_count": _ubo.G.number_of_nodes()}


@router.post("/v1/private/ubo/individual")
def ubo_add_individual(req: IndividualCreate):
    _ubo.add_individual(**req.model_dump())
    return {"ok": True}


@router.post("/v1/private/ubo/shareholding")
def ubo_add_shareholding(req: ShareholdingCreate):
    _ubo.add_shareholding(ShareholderLink(**req.model_dump()))
    return {"ok": True, "edge_count": _ubo.G.number_of_edges()}


@router.get("/v1/private/ubo/trace/{entity_id}")
def ubo_trace(entity_id: str, max_depth: int = 6, threshold_pct: float = 25.0):
    return {
        "entity_id": entity_id,
        "ubos": _ubo.trace_ubo(entity_id, max_depth, threshold_pct),
        "graph_size": _ubo.G.number_of_nodes(),
    }


@router.get("/v1/private/ubo/shell/{entity_id}")
def ubo_shell_check(entity_id: str):
    ent = _ubo._entities.get(entity_id)
    if not ent:
        raise HTTPException(404, f"Entity {entity_id} belum terdaftar di UBO graph")
    return detect_shell_company(ent, tracker=_ubo)


@router.post("/v1/private/ubo/seed-demo")
def ubo_seed_demo():
    """Seed a small demo graph: PT A -> PT B (offshore) -> Mr. Z (PEP)."""
    from datetime import date
    _ubo.add_entity(CorporateEntity(
        entity_id="PT_MAJU_BERSAMA",
        legal_name="PT Maju Bersama Investasi",
        country_of_incorp="ID",
        registered_address="Jl. Sudirman 123, Jakarta",
        business_purpose="Investasi properti",
        incorporated_date=date(2024, 1, 15),
    ))
    _ubo.add_entity(CorporateEntity(
        entity_id="BVI_HOLDING_001",
        legal_name="Global Holdings Ltd",
        country_of_incorp="VG",
        registered_address="Road Town, Tortola, BVI (PO Box)",
        business_purpose="",
        has_physical_office=False,
        incorporated_date=date(2024, 8, 1),
    ))
    _ubo.add_individual("KTP_3175020101800001", "Budi Hartono",
                        is_pep=True, country="ID")
    _ubo.add_shareholding(ShareholderLink(
        owner_id="BVI_HOLDING_001", owned_id="PT_MAJU_BERSAMA",
        owner_type="corporate", share_pct=95.0))
    _ubo.add_shareholding(ShareholderLink(
        owner_id="KTP_3175020101800001", owned_id="BVI_HOLDING_001",
        owner_type="individual", share_pct=100.0, is_director=True))
    return {
        "ok": True,
        "ubo_for_PT_MAJU_BERSAMA": _ubo.trace_ubo("PT_MAJU_BERSAMA"),
        "shell_check_BVI": detect_shell_company(
            _ubo._entities["BVI_HOLDING_001"], tracker=_ubo,
        ),
    }
