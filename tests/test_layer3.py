"""Layer 3 — Regtech report tests."""
from datetime import datetime

from src.layer3_regtech.report_generator import (
    ReportGenerator, LTKMPayload,
    build_ltkm_from_trace, build_ltkt_from_transactions,
)


def _trace():
    return {
        "layering_score": 0.82,
        "path_count": 3,
        "pattern_types": ["smurfing", "layering"],
        "explanation": "test",
        "flagged_wallets": ["WALLET_X"],
    }


def test_ltkm_build_and_render(tmp_path):
    payload = build_ltkm_from_trace(
        subject_id="WALLET_X",
        subject_name="Suspect Wallet",
        trace_result=_trace(),
        risk_score=88.0,
    )
    gen = ReportGenerator()
    html = gen.render_ltkm_html(payload)
    assert "LAPORAN TRANSAKSI KEUANGAN MENCURIGAKAN" in html
    assert "WALLET_X" in html
    paths = gen.write(payload, tmp_path)
    assert (tmp_path / f"{payload.report_id}.html").exists()


def test_ltkt_threshold_not_met():
    payload = build_ltkt_from_transactions(
        customer_id="C", customer_name="Customer",
        customer_type="individual",
        transactions=[{"amount_idr": 100_000_000, "tx_id": "t1",
                       "timestamp": "2026-05-21T10:00:00",
                       "channel": "bank", "receiver_id": "X"}],
    )
    assert payload is None


def test_ltkt_threshold_met():
    txs = [{"amount_idr": 300_000_000, "tx_id": f"t{i}",
            "timestamp": "2026-05-21T10:00:00",
            "channel": "bank", "receiver_id": "X"} for i in range(2)]
    payload = build_ltkt_from_transactions(
        customer_id="C", customer_name="Customer",
        customer_type="individual",
        transactions=txs,
    )
    assert payload is not None
    assert payload.total_amount == 600_000_000
