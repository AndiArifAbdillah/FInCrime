"""Humanizer — terjemahkan skor mentah ML menjadi bahasa Indonesia awam.

Modul ini SATU SUMBER KEBENARAN untuk semua penjelasan yang ditampilkan ke
pengguna non-teknis (compliance officer, regulator BI/OJK/PPATK).

Setiap fungsi mengembalikan dict dengan field konsisten:
    {
        "label":      str  — verdict singkat (mis. "KRITIS")
        "emoji":      str  — indikator visual
        "color":      str  — hex untuk UI
        "plain":      str  — penjelasan 1 kalimat bahasa awam
        "action":     str  — rekomendasi tindakan
        "severity":   int  — 0=aman, 1=rendah, 2=sedang, 3=tinggi, 4=kritis
    }
"""
from __future__ import annotations

# ============================================================
# Warna severity (konsisten dengan UI)
# ============================================================
COLOR_SAFE = "#22c55e"      # hijau
COLOR_LOW = "#84cc16"       # hijau-kuning
COLOR_MEDIUM = "#f59e0b"    # amber
COLOR_HIGH = "#f97316"      # oranye
COLOR_CRITICAL = "#ef4444"  # merah


# ============================================================
# 1. RISK SCORE (Layer 0) — skala 0-100
# ============================================================
def explain_risk_score(score: float) -> dict:
    """Terjemahkan risk score 0-100 entitas/nasabah."""
    if score >= 85:
        return {
            "label": "KRITIS",
            "emoji": "🔴",
            "color": COLOR_CRITICAL,
            "severity": 4,
            "plain": f"Entitas ini SANGAT BERISIKO ({score:.0f}/100). "
                     "Indikasi kuat keterlibatan kejahatan keuangan.",
            "action": "WAJIB: Blokir transaksi, lakukan Enhanced Due Diligence (EDD), "
                      "dan siapkan laporan LTKM ke PPATK.",
        }
    if score >= 70:
        return {
            "label": "TINGGI",
            "emoji": "🟠",
            "color": COLOR_HIGH,
            "severity": 3,
            "plain": f"Entitas ini berisiko tinggi ({score:.0f}/100). "
                     "Beberapa indikator mencurigakan terdeteksi.",
            "action": "Lakukan review manual oleh petugas senior + monitoring ketat. "
                      "Pertimbangkan EDD.",
        }
    if score >= 40:
        return {
            "label": "SEDANG",
            "emoji": "🟡",
            "color": COLOR_MEDIUM,
            "severity": 2,
            "plain": f"Entitas ini berisiko sedang ({score:.0f}/100). "
                     "Perlu pemantauan rutin.",
            "action": "Monitor transaksi berkala. Tidak perlu tindakan segera.",
        }
    return {
        "label": "RENDAH",
        "emoji": "🟢",
        "color": COLOR_SAFE,
        "severity": 1 if score >= 15 else 0,
        "plain": f"Entitas ini relatif aman ({score:.0f}/100). "
                 "Tidak ada indikator signifikan.",
        "action": "Tidak perlu tindakan. Lanjutkan monitoring standar.",
    }


# ============================================================
# 2. FRAUD ANOMALY SCORE (Layer 1) — skala 0-1
# ============================================================
def explain_fraud_score(score: float, rules: list[str] | None = None) -> dict:
    """Terjemahkan anomaly score 0-1 sebuah transaksi."""
    rules = rules or []
    rule_text = _humanize_rules(rules)

    if score >= 0.85:
        return {
            "label": "SANGAT MENCURIGAKAN",
            "emoji": "🔴",
            "color": COLOR_CRITICAL,
            "severity": 4,
            "plain": f"Transaksi ini sangat menyimpang dari pola normal "
                     f"({score*100:.0f}% anomali). {rule_text}",
            "action": "WAJIB: Tahan transaksi, investigasi segera, siapkan LTKM.",
        }
    if score >= 0.70:
        return {
            "label": "MENCURIGAKAN",
            "emoji": "🟠",
            "color": COLOR_HIGH,
            "severity": 3,
            "plain": f"Transaksi ini mencurigakan ({score*100:.0f}% anomali). {rule_text}",
            "action": "Review prioritas tinggi oleh compliance officer.",
        }
    if score >= 0.50:
        return {
            "label": "PERLU REVIEW",
            "emoji": "🟡",
            "color": COLOR_MEDIUM,
            "severity": 2,
            "plain": f"Transaksi sedikit menyimpang ({score*100:.0f}% anomali). {rule_text}",
            "action": "Masukkan ke antrian review. Monitor.",
        }
    return {
        "label": "NORMAL",
        "emoji": "🟢",
        "color": COLOR_SAFE,
        "severity": 0,
        "plain": f"Transaksi dalam batas normal ({score*100:.0f}% anomali).",
        "action": "Tidak perlu tindakan.",
    }


# ============================================================
# 3. LAYERING SCORE (Layer 2) — skala 0-1
# ============================================================
def explain_layering_score(score: float, chains: int = 0,
                           suspicious_value: float = 0.0) -> dict:
    """Terjemahkan layering score 0-1 dari graph tracing."""
    val_text = ""
    if suspicious_value > 0:
        val_text = f" Total nilai mencurigakan Rp {suspicious_value:,.0f}."
    chain_text = f" Ditemukan {chains} rantai pencucian." if chains else ""

    if score >= 0.6:
        return {
            "label": "TERINDIKASI PENCUCIAN UANG",
            "emoji": "🔴",
            "color": COLOR_CRITICAL,
            "severity": 4,
            "plain": "Wallet ini menunjukkan pola LAYERING (pencucian uang berlapis) "
                     f"yang kuat.{chain_text}{val_text}",
            "action": "WAJIB: Generate LTKM, eskalasi ke unit investigasi, "
                      "telusuri wallet terkait.",
        }
    if score >= 0.3:
        return {
            "label": "POLA MENCURIGAKAN",
            "emoji": "🟠",
            "color": COLOR_HIGH,
            "severity": 3,
            "plain": f"Wallet ini punya beberapa indikasi layering.{chain_text}{val_text}",
            "action": "Review jaringan transaksi lebih lanjut.",
        }
    if score > 0:
        return {
            "label": "INDIKASI RINGAN",
            "emoji": "🟡",
            "color": COLOR_MEDIUM,
            "severity": 2,
            "plain": f"Ada sedikit indikasi pola tidak biasa.{chain_text}",
            "action": "Monitor. Belum perlu tindakan.",
        }
    return {
        "label": "BERSIH",
        "emoji": "🟢",
        "color": COLOR_SAFE,
        "severity": 0,
        "plain": "Tidak ada pola layering terdeteksi pada wallet ini.",
        "action": "Tidak perlu tindakan.",
    }


# ============================================================
# 4. GNN FRAUD SCORE (Layer 2) — skala 0-1
# ============================================================
def explain_gnn_score(score: float) -> dict:
    """Terjemahkan GNN fraud probability 0-1."""
    if score >= 0.7:
        return {
            "label": "TINGGI", "emoji": "🔴", "color": COLOR_CRITICAL, "severity": 4,
            "plain": f"Model AI memprediksi wallet ini {score*100:.0f}% kemungkinan fraud "
                     "berdasarkan analisis jaringan transaksinya.",
            "action": "Kombinasikan dengan layering score untuk keputusan akhir.",
        }
    if score >= 0.4:
        return {
            "label": "SEDANG", "emoji": "🟡", "color": COLOR_MEDIUM, "severity": 2,
            "plain": f"Model AI memprediksi {score*100:.0f}% kemungkinan fraud.",
            "action": "Perlu konfirmasi dari indikator lain.",
        }
    return {
        "label": "RENDAH", "emoji": "🟢", "color": COLOR_SAFE, "severity": 0,
        "plain": f"Model AI menilai wallet ini relatif aman ({score*100:.0f}% fraud). "
                 "CATATAN: skor AI bergantung kualitas data latih — "
                 "selalu cek skor layering juga.",
        "action": "Cek layering score untuk verifikasi.",
    }


# ============================================================
# 5. SHAP FACTOR TRANSLATION — fitur teknis → bahasa awam
# ============================================================
_FEATURE_LABELS = {
    "sanction_flag": "Terdaftar di daftar sanksi (OFAC/PPATK)",
    "pep_flag": "Politically Exposed Person (PEP)",
    "has_crypto_activity": "Memiliki aktivitas mata uang kripto",
    "is_corporate": "Berbentuk badan usaha/korporat",
    "is_wallet": "Berupa wallet kripto",
    "is_high_risk_country": "Berasal dari negara berisiko tinggi (FATF)",
    "low_kyc_high_volume": "KYC rendah tapi volume transaksi besar",
    "kyc_level": "Tingkat verifikasi identitas (KYC)",
    "age_days": "Umur akun/rekening",
    "txn_count_30d": "Jumlah transaksi 30 hari terakhir",
    "total_volume_30d": "Total nilai transaksi 30 hari",
    "avg_tx_amount": "Rata-rata nilai per transaksi",
    "distinct_counterparties_30d": "Jumlah pihak berbeda yang bertransaksi",
    "counterparty_concentration": "Konsentrasi mitra transaksi",
    "velocity_30d": "Kecepatan transaksi (transaksi per hari)",
    "log_total_volume": "Total volume transaksi (skala log)",
    "log_avg_amount": "Rata-rata nilai transaksi (skala log)",
}


def humanize_shap_factor(feature: str, contribution: float) -> dict:
    """Terjemahkan satu SHAP factor jadi bahasa awam."""
    label = _FEATURE_LABELS.get(feature, feature.replace("_", " ").title())
    if contribution > 0:
        direction = "menaikkan"
        effect = "⬆ memperberat risiko"
        color = COLOR_CRITICAL if contribution > 1.0 else COLOR_HIGH
    else:
        direction = "menurunkan"
        effect = "⬇ mengurangi risiko"
        color = COLOR_SAFE

    strength = ("sangat kuat" if abs(contribution) > 2.0 else
                "kuat" if abs(contribution) > 1.0 else
                "sedang" if abs(contribution) > 0.3 else
                "ringan")

    return {
        "feature": feature,
        "label": label,
        "contribution": contribution,
        "direction": direction,
        "effect": effect,
        "strength": strength,
        "color": color,
        "plain": f"{label} — {effect} (pengaruh {strength})",
    }


def humanize_shap_list(factors: list[dict]) -> list[dict]:
    """Terjemahkan list SHAP factors (dari API)."""
    out = []
    for f in factors:
        feature = f.get("feature", "")
        contribution = float(f.get("contribution", 0))
        h = humanize_shap_factor(feature, contribution)
        h["value"] = f.get("value")
        out.append(h)
    return out


# ============================================================
# Helper: rule names → bahasa awam
# ============================================================
_RULE_LABELS = {
    "smurfing": "Transaksi dipecah di bawah ambang pelaporan (smurfing)",
    "volume_spike": "Lonjakan volume tidak wajar",
    "high_risk_jurisdiction": "Transfer ke yurisdiksi berisiko tinggi",
    "blacklist_hit": "Pihak terkait ada di daftar hitam",
    "anomalous_pattern": "Pola transaksi anomali terdeteksi AI",
    "near_threshold_50m": "Nilai mendekati ambang Rp 50 juta",
}


def _humanize_rules(rules: list[str]) -> str:
    if not rules:
        return ""
    # Strip enum prefix kalau ada (AlertType.SMURFING -> smurfing)
    clean = []
    for r in rules:
        r = str(r).split(".")[-1].lower()
        clean.append(_RULE_LABELS.get(r, r.replace("_", " ")))
    return "Indikator: " + "; ".join(clean) + "."


def humanize_rules_list(rules: list[str]) -> list[str]:
    """Public version — return list of human-readable rule strings."""
    out = []
    for r in rules:
        r = str(r).split(".")[-1].lower()
        out.append(_RULE_LABELS.get(r, r.replace("_", " ").title()))
    return out


# ============================================================
# 6. CHANNEL & severity label helpers
# ============================================================
def channel_label(channel: str) -> str:
    return {
        "bank": "Bank",
        "ewallet": "E-Wallet",
        "crypto": "Kripto",
    }.get(str(channel).lower(), channel)


def severity_badge(severity: int) -> dict:
    return {
        4: {"label": "KRITIS", "emoji": "🔴", "color": COLOR_CRITICAL},
        3: {"label": "TINGGI", "emoji": "🟠", "color": COLOR_HIGH},
        2: {"label": "SEDANG", "emoji": "🟡", "color": COLOR_MEDIUM},
        1: {"label": "RENDAH", "emoji": "🟢", "color": COLOR_LOW},
        0: {"label": "AMAN", "emoji": "🟢", "color": COLOR_SAFE},
    }.get(severity, {"label": "—", "emoji": "⚪", "color": "#888"})
