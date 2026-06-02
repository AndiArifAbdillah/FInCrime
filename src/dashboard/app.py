"""FinCrime — Compliance Officer Dashboard (Streamlit).

Run:
    streamlit run src/dashboard/app.py
"""
from __future__ import annotations

from datetime import datetime
from pathlib import Path

import pandas as pd
import streamlit as st

from src.common.config import settings
from src.common.schemas import Entity, Transaction, Channel

# ---------- Page config ----------
st.set_page_config(
    page_title="FinCrime — Compliance Dashboard",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.title("FinCrime — Compliance Dashboard")
st.caption("End-to-End Financial Crime Intelligence System for Indonesia • Bank Indonesia PIDI")


@st.cache_resource
def load_scorer():
    from src.layer0_risk_scoring import RiskScorer
    return RiskScorer()


@st.cache_resource
def load_detector():
    from src.layer1_fraud_detection import FraudDetector
    return FraudDetector()


@st.cache_resource
def load_tracer():
    from src.layer2_gnn_tracing import CryptoTracer
    return CryptoTracer()


@st.cache_resource
def load_reporter():
    from src.layer3_regtech import ReportGenerator
    return ReportGenerator()


@st.cache_data
def load_sample():
    sd = settings.app_data_dir / "sample"
    return {
        "entities": pd.read_csv(sd / "entities.csv") if (sd / "entities.csv").exists() else pd.DataFrame(),
        "transactions": pd.read_csv(sd / "transactions.csv") if (sd / "transactions.csv").exists() else pd.DataFrame(),
        "edges": pd.read_csv(sd / "crypto_edges.csv") if (sd / "crypto_edges.csv").exists() else pd.DataFrame(),
    }


# ---------- Sidebar ----------
section = st.sidebar.radio("Navigate", [
    "📊 Overview",
    "👤 Layer 0 — Risk Score",
    "💳 Layer 1 — Fraud Alerts",
    "🕸️ Layer 2 — Crypto Tracing",
    "📄 Layer 3 — PPATK Reports",
])

st.sidebar.markdown("---")
st.sidebar.caption(f"Env: `{settings.app_env}`")
st.sidebar.caption(f"Models: `{settings.app_models_dir}`")

# ---------- Overview ----------
if section.startswith("📊"):
    sample = load_sample()
    c1, c2, c3, c4 = st.columns(4)
    n_entities = len(sample["entities"]) if not sample["entities"].empty else 0
    n_tx = len(sample["transactions"]) if not sample["transactions"].empty else 0
    n_fraud_e = int(sample["entities"]["is_fraud"].sum()) if "is_fraud" in sample["entities"].columns else 0
    n_fraud_t = int(sample["transactions"]["is_fraud"].sum()) if "is_fraud" in sample["transactions"].columns else 0
    c1.metric("Entities", f"{n_entities:,}")
    c2.metric("Transactions", f"{n_tx:,}")
    c3.metric("Fraud Entities", f"{n_fraud_e:,}", delta_color="off")
    c4.metric("Fraud Transactions", f"{n_fraud_t:,}", delta_color="off")

    if not sample["transactions"].empty:
        st.subheader("Transaction volume by channel")
        agg = sample["transactions"].groupby("channel")["amount_idr"].agg(["count", "sum"]).reset_index()
        agg.columns = ["channel", "tx_count", "total_amount_idr"]
        st.bar_chart(agg.set_index("channel")["tx_count"])
    else:
        st.info("Run `python scripts/generate_sample_data.py` to generate demo data.")

# ---------- Layer 0 ----------
elif section.startswith("👤"):
    st.subheader("Layer 0 — Entity Risk Scoring")
    st.write("Score a customer/wallet entity and view SHAP top factors.")

    with st.form("layer0"):
        col1, col2, col3 = st.columns(3)
        with col1:
            entity_id = st.text_input("Entity ID", "IND_000001")
            entity_type = st.selectbox("Entity Type", ["individual", "corporate", "wallet"])
            country = st.selectbox("Country", ["ID", "KP", "IR", "MM", "AF"])
        with col2:
            age_days = st.number_input("Account age (days)", 0, 10000, 365)
            kyc_level = st.slider("KYC Level", 0, 2, 1)
            txn_count = st.number_input("Transactions / 30d", 0, 10000, 50)
        with col3:
            volume = st.number_input("Volume / 30d (IDR)", 0.0, value=1e8, format="%.0f")
            pep = st.checkbox("PEP flag", value=False)
            sanction = st.checkbox("Sanction flag", value=False)
        submit = st.form_submit_button("Score Entity", type="primary")
        if submit:
            try:
                scorer = load_scorer()
                ent = Entity(
                    entity_id=entity_id,
                    entity_type=entity_type,
                    country=country,
                    age_days=int(age_days),
                    kyc_level=int(kyc_level),
                    txn_count_30d=int(txn_count),
                    total_volume_30d=float(volume),
                    avg_tx_amount=float(volume) / max(int(txn_count), 1),
                    distinct_counterparties_30d=min(int(txn_count), 30),
                    pep_flag=bool(pep),
                    sanction_flag=bool(sanction),
                    has_crypto_activity=False,
                )
                result = scorer.score_one(ent, with_shap=True)
                c1, c2 = st.columns([1, 2])
                with c1:
                    st.metric("Risk Score", f"{result.score:.1f} / 100", f"Level: {result.level}")
                with c2:
                    if result.top_factors:
                        df = pd.DataFrame(result.top_factors)
                        st.write("**Top SHAP factors**")
                        st.dataframe(df, use_container_width=True)
            except Exception as e:
                st.error(f"Error: {e}")

# ---------- Layer 1 ----------
elif section.startswith("💳"):
    st.subheader("Layer 1 — Real-time Fraud Detection")
    sample = load_sample()
    if sample["transactions"].empty:
        st.warning("No sample transactions. Generate data first.")
    else:
        n = st.slider("Number of transactions to score", 10, 1000, 100, step=10)
        sub = sample["transactions"].head(n)
        if st.button("Run Layer 1 batch scoring", type="primary"):
            try:
                from src.common.utils import rows_to_transactions
                det = load_detector()
                txs = rows_to_transactions(r for _, r in sub.iterrows())
                preds = det.predict_batch(txs)
                df = pd.DataFrame([{
                    "tx_id": p.tx_id,
                    "anomaly_score": p.anomaly_score,
                    "is_anomaly": p.is_anomaly,
                    "triggered_rules": ", ".join(p.triggered_rules),
                } for p in preds])
                anom = int(df["is_anomaly"].sum())
                st.metric("Anomalies detected", f"{anom} / {len(df)}")
                st.dataframe(df.sort_values("anomaly_score", ascending=False),
                             use_container_width=True, height=400)
            except Exception as e:
                st.error(str(e))

# ---------- Layer 2 ----------
elif section.startswith("🕸️"):
    st.subheader("Layer 2 — GNN Crypto Tracing")
    sample = load_sample()
    if sample["entities"].empty:
        st.warning("Generate sample data first.")
    else:
        wallets = sample["entities"][sample["entities"].entity_type == "wallet"].entity_id.tolist()
        seed = st.selectbox("Pick a seed wallet to trace", wallets[:200])
        hops = st.slider("Hops", 1, 4, 2)
        if st.button("Trace", type="primary"):
            try:
                tracer = load_tracer()
                if tracer.mode == "graph-only":
                    st.info("Mode: **graph-only** (NetworkX layering + heuristic). "
                            "For full GraphSAGE GNN scoring, install PyTorch + torch-geometric.")
                else:
                    st.success("Mode: **GraphSAGE GNN** (full)")
                result = tracer.trace(seed, hops=hops)
                c1, c2, c3 = st.columns(3)
                c1.metric("Layering Score", f"{result.layering_score:.4f}")
                c2.metric("Subgraph Size", result.subgraph_size)
                c3.metric("Flagged Wallets", len(result.flagged_wallets))
                st.write("**Explanation:**", result.explanation)
                if result.pattern_types:
                    st.warning("Patterns: " + ", ".join(result.pattern_types))
                if result.flagged_wallets:
                    st.write("**Flagged wallets:**")
                    st.code("\n".join(result.flagged_wallets[:30]))
            except FileNotFoundError as e:
                st.error(f"Sample data missing: {e}")
            except Exception as e:
                st.error(f"Tracing failed: {e}")

# ---------- Layer 3 ----------
elif section.startswith("📄"):
    st.subheader("Layer 3 — Automated PPATK Reports")
    reports_dir = settings.app_data_dir / "reports"
    reports_dir.mkdir(parents=True, exist_ok=True)
    files = sorted(reports_dir.glob("*.html"), reverse=True)
    if not files:
        st.info("No reports generated yet. Use the API or trace a wallet to create one.")
    else:
        choice = st.selectbox("Select a report", [f.stem for f in files])
        path = reports_dir / f"{choice}.html"
        if path.exists():
            st.download_button("📥 Download HTML",
                               data=path.read_bytes(),
                               file_name=path.name,
                               mime="text/html")
            json_path = reports_dir / f"{choice}.json"
            if json_path.exists():
                st.download_button("📥 Download JSON",
                                   data=json_path.read_bytes(),
                                   file_name=json_path.name,
                                   mime="application/json")
            st.markdown("---")
            st.components.v1.html(path.read_text(encoding="utf-8"), height=900, scrolling=True)
