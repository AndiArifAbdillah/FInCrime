"""FinCrime adapter for Bank Indonesia's Project Garuda — Rupiah Digital DLT.

This module is a STUB / sketch showing how FinCrime AML compliance pipeline
could consume transaction events from the wholesale Rupiah Digital cash ledger
(w-Rupiah Digital) when Bank Indonesia opens DLT API access.

BI Project Garuda PoC (Dec 2024) tested two DLT platforms:
    1. Hyperledger Besu (Kaleido)
    2. R3 Corda

This adapter shows abstract integration for BOTH — the same FinCrime pipeline
(Layer 0/1/2/3) works regardless of underlying DLT platform.

Design principles:
    - DLT-agnostic: speaks both Besu and Corda event formats
    - Permissioned-DLT aware: validating nodes are known wholesalers
    - Privacy-preserving: respects BI privacy model (selective disclosure)
    - Compliance-by-design: every event hits Layer 1 fraud detection
    - Audit-ready: every check logged to immutable audit log

Reference documents:
    - White Paper CBDC 2022 (Bank Indonesia, 30 Nov 2022)
    - Consultative Paper Wholesale Rupiah Digital (31 Jan 2023)
    - Laporan PoC Wholesale Rupiah Digital (Dec 2024)
"""
from __future__ import annotations

import os
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional

from src.common.logger import get_logger
from src.common.schemas import Transaction, Channel
from src.multichain.unified import ChainTransaction

log = get_logger("multichain.rupiah_digital")


# ============================================================
# Types matching Project Garuda DLT design
# ============================================================
class GarudaTier(str, Enum):
    """Two tiers per BI design."""
    WHOLESALE = "w-rupiah"      # bank-to-bank, PoC selesai Dec 2024
    RETAIL = "r-rupiah"          # future end-state, public access


class GarudaNodeRole(str, Enum):
    """Validating node roles per Consultative Paper Tahap I."""
    VALIDATING = "validating_node"           # wholesaler — validates + holds tokens
    NON_VALIDATING = "non_validating_node"   # non-wholesaler — holds tokens only
    NONODE = "nonode"                         # observer only


class GarudaTxType(str, Enum):
    """Use cases di immediate state PoC."""
    ISSUANCE = "issuance"                # BI → wholesaler (penerbitan)
    DESTRUCTION = "destruction"          # wholesaler → BI (pemusnahan)
    TRANSFER = "transfer"                # antar-peserta
    SETTLEMENT = "settlement"            # final settlement


@dataclass
class GarudaParticipant:
    """A participant in the wholesale DLT — bank or non-bank LJK."""
    participant_id: str                  # e.g., "BANK-MANDIRI-001"
    legal_name: str
    tier: str                            # GarudaTier value
    role: str                            # GarudaNodeRole value
    is_validating: bool
    npwp: str = ""
    kyc_level: int = 2                   # CBDC participants are by definition KYC-cleared


@dataclass
class GarudaDLTEvent:
    """Canonical event consumed from Hyperledger Besu / R3 Corda."""
    event_id: str                        # DLT tx hash
    timestamp: datetime
    tier: str                            # w-rupiah or r-rupiah
    tx_type: str                         # issuance/destruction/transfer/settlement
    sender_participant_id: str
    receiver_participant_id: str
    amount_idr: float                    # already in IDR (CBDC denominated in IDR)
    block_height: int
    validating_nodes: list[str] = field(default_factory=list)  # who validated
    smart_contract_id: Optional[str] = None   # if triggered by smart contract
    is_settlement_final: bool = True


# ============================================================
# Adapter: convert DLT event → FinCrime Transaction schema
# ============================================================
def dlt_event_to_transaction(event: GarudaDLTEvent) -> Transaction:
    """Convert a Garuda DLT event into FinCrime canonical Transaction.

    This allows Layer 0/1/2 to process w-Rupiah Digital transactions
    without any pipeline changes.
    """
    # Map DLT event to FinCrime canonical Transaction schema
    return Transaction(
        tx_id=f"GARUDA_{event.event_id}",
        channel=Channel.BANK,            # treat CBDC as bank channel
        timestamp=event.timestamp,
        sender_id=event.sender_participant_id,
        receiver_id=event.receiver_participant_id,
        amount_idr=event.amount_idr,
        currency="IDR",
        country_from="ID",
        country_to="ID",
        chain="rupiah-digital",          # special chain identifier
        tx_hash=event.event_id,
        sender_age_days=999,             # CBDC participants are institutional
        sender_tx_count_7d=0,            # populated from history later
        is_high_risk_jurisdiction=False,  # all participants are KYC-cleared
    )


def dlt_event_to_chain_transaction(event: GarudaDLTEvent) -> ChainTransaction:
    """For Layer 2 GraphSAGE GNN — emit ChainTransaction format."""
    return ChainTransaction(
        chain="rupiah-digital",
        tx_hash=event.event_id,
        block_height=event.block_height,
        timestamp=event.timestamp,
        sender=event.sender_participant_id,
        receiver=event.receiver_participant_id,
        amount_native=event.amount_idr,
        amount_idr=event.amount_idr,
        token_symbol="IDR-D",            # Rupiah Digital ticker
        is_token_transfer=False,
        fee_native=0.0,                  # no fee in BI wholesale model
    )


# ============================================================
# Consumer stub — would subscribe to BI DLT API when available
# ============================================================
class RupiahDigitalConsumer:
    """Stub consumer for w-Rupiah Digital cash ledger events.

    In production:
        - Subscribes to Hyperledger Besu event log via Web3.py
        - Or to R3 Corda RPC stream
        - Filters events to those involving monitored institutions
        - Forwards to FinCrime ingestion pipeline (Kafka)
    """

    def __init__(self, dlt_platform: str = "besu",
                 dlt_endpoint: Optional[str] = None,
                 monitored_participants: Optional[list[str]] = None):
        if dlt_platform not in ("besu", "corda"):
            raise ValueError(f"Unsupported DLT platform: {dlt_platform}")
        self.dlt_platform = dlt_platform
        self.dlt_endpoint = dlt_endpoint or os.environ.get(
            "GARUDA_DLT_ENDPOINT", "https://api.garuda.bi.go.id/v1/dlt"
        )
        self.monitored = set(monitored_participants or [])
        log.info("rupiah_digital.consumer.init",
                 platform=dlt_platform,
                 endpoint=self.dlt_endpoint,
                 monitored_count=len(self.monitored))

    def connect(self) -> bool:
        """Connect to BI DLT API. Returns False until BI opens access."""
        log.warning("rupiah_digital.dlt_api_not_available",
                    note="BI Garuda DLT API expected to open 2027 post-pilot")
        return False

    def stream_events(self):
        """Iterator over DLT events. Currently yields nothing — placeholder."""
        if not self.connect():
            return iter([])
        # In production: subscribe to DLT event stream
        # For Besu: web3.eth.subscribe(...)
        # For Corda: corda_rpc.start_flow_observer(...)
        raise NotImplementedError(
            "Will be implemented when BI opens Garuda DLT API access (target 2027)"
        )

    def process_event(self, event: GarudaDLTEvent) -> dict:
        """Apply full FinCrime pipeline to a single DLT event.

        Flow:
            1. Convert to FinCrime Transaction schema
            2. Layer 1 fraud detection (IsolationForest + Autoencoder + rules)
            3. Layer 2 GNN tracing (if suspicious)
            4. Layer 3 auto-LTKM (if confirmed suspicious)
            5. Audit log entry (POJK + UU PDP compliant)

        This is the SAME pipeline used for bank/e-wallet/crypto transactions —
        demonstrating DLT-agnostic compatibility.
        """
        try:
            from src.layer1_fraud_detection import FraudDetector
            from src.observability import audit_log
        except ImportError as e:
            log.warning("rupiah_digital.pipeline_unavailable", error=str(e))
            return {"status": "skipped", "reason": str(e)}

        tx = dlt_event_to_transaction(event)

        # Audit log: record that this CBDC event was processed
        audit_log.record(
            event_type="cbdc_transaction_screened",
            actor="rupiah_digital_consumer",
            subject=event.event_id,
            layer="layer1",
            action="score",
            payload={
                "tier": event.tier,
                "tx_type": event.tx_type,
                "amount_idr": event.amount_idr,
            },
            model_version="0.1.0",
        )

        # Layer 1: real-time fraud detection
        try:
            detector = FraudDetector()
            prediction = detector.predict_one(tx)
        except FileNotFoundError:
            log.warning("rupiah_digital.layer1_not_trained")
            return {"status": "queued", "reason": "Layer 1 model not loaded"}

        result = {
            "event_id": event.event_id,
            "tier": event.tier,
            "is_anomaly": prediction.is_anomaly,
            "anomaly_score": prediction.anomaly_score,
            "triggered_rules": [str(r) for r in prediction.triggered_rules],
        }

        # If suspicious → escalate to Layer 2 + Layer 3
        if prediction.is_anomaly:
            log.info("rupiah_digital.anomaly_detected",
                     event=event.event_id, score=prediction.anomaly_score)
            # In production, would chain to Layer 2 trace + Layer 3 LTKM gen
            result["escalation"] = "layer2_layer3_pipeline"

        return result


# ============================================================
# Demo: simulated DLT event for testing
# ============================================================
def demo_garuda_event() -> GarudaDLTEvent:
    """Return a sample Garuda DLT event for testing."""
    return GarudaDLTEvent(
        event_id="0xGARUDA-DEMO-001",
        timestamp=datetime.utcnow(),
        tier=GarudaTier.WHOLESALE.value,
        tx_type=GarudaTxType.TRANSFER.value,
        sender_participant_id="BANK-MANDIRI-001",
        receiver_participant_id="BANK-BCA-001",
        amount_idr=10_000_000_000,     # Rp 10 miliar wholesale transfer
        block_height=12345,
        validating_nodes=["BANK-MANDIRI-001", "BANK-BRI-001", "BANK-BNI-001"],
        smart_contract_id=None,
        is_settlement_final=True,
    )


if __name__ == "__main__":
    import sys
    from pathlib import Path as _Path
    sys.path.insert(0, str(_Path(__file__).resolve().parent.parent.parent))
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    print("FinCrime adapter for Project Garuda Rupiah Digital — demo")
    print()

    event = demo_garuda_event()
    print(f"Sample DLT event: {event.event_id}")
    print(f"  Tier:    {event.tier}")
    print(f"  Type:    {event.tx_type}")
    print(f"  From:    {event.sender_participant_id}")
    print(f"  To:      {event.receiver_participant_id}")
    print(f"  Amount:  Rp {event.amount_idr:,.0f}")
    print()

    # Convert to FinCrime Transaction
    tx = dlt_event_to_transaction(event)
    print(f"-> FinCrime Transaction:")
    print(f"   tx_id={tx.tx_id}")
    print(f"   amount={tx.amount_idr:,.0f}, channel={tx.channel}")
    print()

    # Process through pipeline (will queue if Layer 1 not trained)
    consumer = RupiahDigitalConsumer(dlt_platform="besu")
    result = consumer.process_event(event)
    print(f"-> Pipeline result: {result}")
