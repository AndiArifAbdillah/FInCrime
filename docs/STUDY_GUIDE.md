# 📚 FinCrime — Panduan Belajar "Kuasai Luar-Dalam"

> Dokumen ini untuk **memahami project sampai akar** — bukan sekadar tahu fiturnya.
> Cocok dipakai: (1) belajar mandiri, (2) onboarding anggota tim, (3) contekan saat
> presentasi/defense ke juri Bank Indonesia.
>
> **Cara pakai:** ikuti urutan tingkat 1→5. Tiap bagian punya *"✅ Tes Diri"* —
> kalau bisa jawab tanpa lihat catatan, berarti kamu paham.

---

## 🗺️ Urutan belajar tercepat (ringkas)

1. Baca **[`scripts/run_pipeline.py`](../scripts/run_pipeline.py)** — seluruh cerita project dalam 1 file.
2. Baca **[`src/common/schemas.py`](../src/common/schemas.py)** — "kontrak data" yang menyatukan 4 layer.
3. Dalami **3 algoritma kunci**: SHAP (L0), Autoencoder (L1), GraphSAGE (L2).
4. Hafalkan **angka penting** (bawah) + latih **Tanya-Jawab Juri**.

---

# TINGKAT 1 — Fondasi Domain (kenapa project ini ada)

FinCrime = sistem AI untuk **mendeteksi & mencegah kejahatan keuangan** (anti pencucian
uang / AML-CFT) di Indonesia, real-time dan terintegrasi.

### Glosarium wajib
| Istilah | Arti singkat |
|---------|--------------|
| **AML / CFT** | Anti-Money Laundering / Counter-Financing of Terrorism |
| **LTKM** | Laporan Transaksi Keuangan Mencurigakan → ke PPATK |
| **LTKT** | Laporan Transaksi Keuangan Tunai (≥ Rp 500 juta/hari) |
| **PPATK** | Pusat Pelaporan & Analisis Transaksi Keuangan (regulator AML Indonesia) |
| **GRIPS** | Format/sistem pelaporan resmi PPATK |
| **KYC → CDD → EDD** | Know Your Customer → Customer Due Diligence → Enhanced DD (untuk risiko tinggi) |
| **Smurfing** | Pecah uang besar jadi banyak transaksi kecil di bawah ambang lapor |
| **Layering** | Alirkan dana lewat rantai banyak rekening/wallet untuk menyamarkan asal |
| **Structuring** | Istilah umum memecah transaksi menghindari ambang pelaporan |
| **Privacy coin** | Crypto anonim (Monero/Zcash/Dash) — tak bisa di-trace internal |
| **PFAK / Bappebti** | Daftar aset kripto legal di Indonesia (privacy coin TIDAK masuk) |
| **PEP** | Politically Exposed Person (pejabat/orang berpengaruh = risiko tinggi) |

### Regulasi yang dirujuk
POJK No.12/2024 (anti-fraud), UU TPPU No.8/2010, UU PDP No.27/2022,
FATF Recommendations (10, 16 Travel Rule, 22-25), format PPATK GRIPS.

**✅ Tes Diri:** *"Kenapa beli Monero di exchange Indonesia langsung jadi indikator suspicious?"*
(Jawab: privacy coin tidak masuk daftar PFAK Bappebti → aktivitasnya melanggar/abnormal by default.)

---

# TINGKAT 2 — Arsitektur Besar & Aliran Data

### Pipeline 4 layer (baca `run_pipeline.py` untuk lihat aslinya)

```
  Transaksi/Entitas masuk
        │
        ▼
  ┌─────────────┐   skor risiko entitas 0–100 + SHAP
  │  LAYER 0    │   (XGBoost) — "siapa yang berisiko?"
  └─────────────┘
        │
        ▼
  ┌─────────────┐   anomaly score 0–1 per transaksi
  │  LAYER 1    │   (IsolationForest + Autoencoder + rules) — "transaksi mana yang aneh?"
  └─────────────┘
        │
        ▼
  ┌─────────────┐   layering score + jaringan wallet
  │  LAYER 2    │   (GraphSAGE GNN + NetworkX) — "bagaimana dana mengalir?"
  └─────────────┘
        │
        ▼
  ┌─────────────┐   LTKM/LTKT otomatis (HTML/PDF/JSON)
  │  LAYER 3    │   (Jinja2 + Claude LLM) — "buatkan laporannya"
  └─────────────┘
        │
        ▼
   Compliance officer review → submit ke PPATK
```

### Kontrak data — `src/common/schemas.py` (PALING PENTING)
Semua layer "bicara" lewat schema **Pydantic** ini (validasi otomatis):

- **Input:** `Transaction` (tx_id, channel, amount_idr, sender/receiver, chain…), `Entity` (entity_id, kyc_level, pep_flag, sanction_flag…)
- **Output:** `RiskScore` (L0), `FraudPrediction` (L1), `GraphTraceResult` (L2), `Alert`
- **Enum:** `Channel` (bank/ewallet/crypto), `RiskLevel` (low→critical), `AlertType` (smurfing, layering, …)

**✅ Tes Diri:** *"Apa bedanya `Entity` dan `Transaction`, dan layer mana pakai yang mana?"*
(Entity = subjek/akun → Layer 0. Transaction = 1 transaksi → Layer 1. Wallet+edges → Layer 2.)

---

# TINGKAT 3 — Otak Tiap Layer 🧠 (bagian terpenting untuk dipelajari)

## Layer 0 — Risk Scoring (XGBoost + SHAP)
**File:** `src/layer0_risk_scoring/` (features.py, train.py, predict.py)

- **Tujuan:** beri skor risiko **0–100** per entitas + alasannya.
- **XGBoost** = ratusan pohon keputusan bertingkat (gradient boosting) — sangat kuat untuk data tabular.
- **Fitur (dari `features.py`):** umur akun, kyc_level, jumlah & volume transaksi 30 hari, velocity, konsentrasi lawan transaksi, flag PEP/sanksi, aktivitas crypto, `low_kyc_high_volume`, negara berisiko tinggi.
- **SHAP** = teknik *explainability*: menjawab **"fitur mana yang membuat skor ini tinggi?"** — KRUSIAL karena regulator wajib bisa menjelaskan kenapa seseorang ditandai. Output `top_factors` di dashboard.
- **Ambang:** RISK_SCORE_HIGH=70, RISK_SCORE_CRITICAL=85. Performa: **ROC AUC 0,79** (data sintetis).

**✅ Tes Diri:** *"Kalau skor 93/100, bagaimana sistem menjelaskan kenapa?"* → SHAP top factors (mis. txn_count tinggi, ada aktivitas crypto, flag sanksi).

## Layer 1 — Fraud Detection (Isolation Forest + Autoencoder + Rules)
**File:** `src/layer1_fraud_detection/` (detector.py, autoencoder.py, rules.py, features.py)

- **Tujuan:** beri **anomaly score 0–1** per transaksi.
- **Isolation Forest** (unsupervised) = cari **outlier** — titik yang "mudah dipisahkan" dari kerumunan.
- **Autoencoder** (neural net) = dilatih "menggambar ulang" transaksi normal; kalau **gagal menggambar ulang** (reconstruction error tinggi) → anomali.
- **Skor gabungan** = `0.5 × IsolationForest + 0.5 × Autoencoder`.
- **Rule engine** = deteksi pola bernama: smurfing, volume spike, transfer ke yurisdiksi berisiko.
- **Label:** kena rule spesifik → `SMURFING` dll; skor ML tinggi tanpa rule cocok → `ANOMALOUS_PATTERN`.
- **Ambang internal smurfing Rp 50 juta** (≠ ambang lapor LTKT Rp 500 juta).

**✅ Tes Diri:** *"Akun biasa terima Rp 5jt, tiba-tiba Rp 70jt — apakah ketangkap?"* → Ya (nominal jauh dari normal), tapi via "besar secara umum", bukan "aneh untuk akun ini" (versi sekarang belum punya baseline per-akun).

## Layer 2 — GNN Crypto Tracing (GraphSAGE)
**File:** `src/layer2_gnn_tracing/` (graphsage_model.py, train.py, trace.py, graph_builder.py, neo4j_client.py)

- **Tujuan:** lacak **aliran dana di jaringan wallet** + skor layering.
- **GNN (Graph Neural Network)** = neural net yang bekerja di atas **graph** (titik=wallet, garis=transaksi). Lewat **message passing**, tiap node "belajar" dari tetangganya.
- **GraphSAGE** = arsitektur GNN (2 lapis `SAGEConv`, agregasi mean) untuk klasifikasi node fraud/tidak.
- **Kenapa graph?** Pencucian uang = layering (rantai banyak hop). Database tabel lambat menjawab "cari jalur A→wallet-sanksi 5 lompatan"; graph + GNN native & cepat.
- **NetworkX** = deteksi rantai layering (DFS) + hop smurfing (band Rp 40–50jt).
- **Neo4j** = database graph untuk simpan wallet di produksi.
- **Benchmark NYATA:** di **Elliptic Bitcoin Dataset** (203.769 transaksi, 165 fitur, split temporal literatur) → **ROC AUC 0,92** (sejalan paper). Script: `scripts/train_elliptic_benchmark.py`.

**✅ Tes Diri:** *"GNN-mu beda apa dari rule biasa, dan apa buktinya?"* → GNN belajar representasi node & menangkap pola layering yang invisible bagi rule; bukti = ROC AUC 0,92 di data Bitcoin nyata.

## Layer 3 — Regtech / Pelaporan (Jinja2 + LLM)
**File:** `src/layer3_regtech/report_generator.py` + templates `*.html.j2`

- **Tujuan:** ubah hasil 3 layer → **LTKM/LTKT otomatis** sesuai format PPATK.
- **Jinja2** = template engine (isi data ke kerangka HTML).
- **LTKT** dipicu kalau transaksi tunai ≥ **Rp 500 juta**/hari.
- **Narasi LLM (Claude Haiku)** = tulis "Ringkasan Kecurigaan" Bahasa Indonesia formal; **fallback template** kalau `ANTHROPIC_API_KEY` kosong.
- **PDF:** WeasyPrint → fallback **Chrome/Edge headless** (Windows tanpa GTK).
- Hasil: HTML + JSON + PDF, plus audit log immutable.

**✅ Tes Diri:** *"Kenapa LTKM bisa < 5 menit padahal manual 1–3 hari?"* → otomasi penuh: data 3 layer → template + LLM → laporan siap review.

---

# TINGKAT 4 — Tulang Punggung Engineering

| Komponen | Fungsi | File/letak |
|----------|--------|------------|
| **FastAPI** | REST API 62+ endpoint (otak penyaji data) | `src/api/` |
| **Pydantic** | Validasi schema otomatis | `src/common/schemas.py` |
| **Kafka** | "Ban berjalan" data transaksi real-time | `src/ingestion/kafka_*` |
| **Neo4j** | Database graph (Layer 2) | `src/layer2_gnn_tracing/neo4j_client.py` |
| **Prometheus + Grafana** | Pantau metrik & kesehatan sistem | `src/observability/`, `deployment/grafana/` |
| **MLflow** | Catat tiap training + versi model | `src/mlops/` |
| **Docker / Kubernetes** | Bungkus & deploy semua service | `docker/`, `deployment/kubernetes/` |
| **Web UI (vanilla JS + PWA)** | Dashboard 13 tab | `src/web/` |
| **OFAC/UN/DTTOT** | Screening sanksi internasional | `src/ingestion/sanctions_loader.py` |

---

# 📌 Angka & Fakta untuk DIHAFAL

- **4 layer**, 62+ REST endpoint, 13 tab UI, 14/14 test lolos
- **Layer 0:** ROC AUC **0,79** (sintetis) · **Layer 2:** ROC AUC **0,92** (Elliptic NYATA)
- Ambang **LTKT Rp 500 juta** · deteksi smurfing internal **Rp 50 juta**
- **OFAC** 19.041 entitas + 313 alamat crypto · **UN** 1.004 entitas
- **Elliptic** 203.769 transaksi Bitcoin, 4.545 illicit berlabel
- Waktu LTKM: **1–3 hari → 5 menit**
- 5 chain (BTC/ETH/BSC/Polygon/Tron) — 1 key Etherscan V2 untuk semua EVM
- Privacy coin: Monero/Zcash/Dash — **tidak bisa trace internal**, dipantau via on/off-ramp

---

# 🎤 TINGKAT 5 — Tanya-Jawab Juri (Defense Prep)

> Latih jawab lisan tanpa baca. Ini pertanyaan yang paling mungkin muncul.

**Q: Bagaimana sistem tahu transaksi Rp 48jt itu smurfing, bukan transaksi biasa?**
A: Layer 1 rule engine mendeteksi nominal yang berulang persis di bawah ambang (band 40–50jt), pola yang sengaja "ngumpet" dari trigger pelaporan. Plus skor anomali ML.

**Q: GNN kalian beneran bisa apa? Jangan-jangan cuma buzzword.**
A: GraphSAGE kami di-benchmark pada Elliptic Bitcoin Dataset — data transaksi Bitcoin nyata berlabel — dengan split temporal standar literatur, mencapai **ROC AUC 0,92**, sejalan publikasi akademis. Bukan klaim, bisa direproduksi (`train_elliptic_benchmark.py`).

**Q: Kalau AI salah menuduh orang yang tidak bersalah?**
A: Tiga lapis pertanggungjawaban: (1) **SHAP** menjelaskan alasan tiap skor, (2) sistem hanya memberi flag — keputusan akhir di **compliance officer** (EDD), (3) **audit log immutable** mencatat setiap prediksi untuk diaudit.

**Q: Privacy coin kan tak bisa dilacak — lalu kalian klaim bisa apa?**
A: Kami jujur tidak mengklaim trace internal Monero (mustahil secara kriptografis, bahkan Chainalysis tidak bisa). Kami pakai standar industri: pantau **pintu masuk/keluar (on/off-ramp)** ke exchange pendukung privacy coin + auto-flag karena di luar daftar PFAK Bappebti.

**Q: Apa hubungannya dengan Project Garuda / CBDC BI?**
A: Tidak terintegrasi — Garuda masih PoC tertutup dan kami tidak mengklaim itu. Tapi arsitektur kami **DLT-agnostic**, jadi **siap menjadi lapisan AML/CFT** saat BI membuka akses, sejalan kebutuhan integritas yang BI sebut di White Paper CBDC.

**Q: Datanya nyata atau sintetis?**
A: Jujur campuran: sanksi OFAC/UN **nyata** (live), benchmark Layer 2 **nyata** (Elliptic), sebagian training **sintetis** (IBM AML/PaySim) karena data bank asli butuh MoU. Roadmap: pilot dengan data nyata via OJK Sandbox.

**Q: Kenapa pakai 'Layer', bukan istilah lain?**
A: Istilah arsitektur baku, konsisten dengan kode & diagram; menghindari bentrok dengan "Tahap 2" (submission).

---

## 🧭 Rencana belajar 1 minggu (saran)
- **Hari 1–2:** Tingkat 1 (domain) + baca `run_pipeline.py` & `schemas.py`
- **Hari 3:** Layer 0 (XGBoost + SHAP) — buka `features.py`, jalankan `.\fc.ps1 demo`
- **Hari 4:** Layer 1 (anomali) + Layer 2 (GNN)
- **Hari 5:** Layer 3 + engineering (FastAPI, Kafka, Neo4j)
- **Hari 6:** Hafal angka + latihan Tanya-Jawab Juri (lisan)
- **Hari 7:** Mock presentation dengan tim — tiap orang jelaskan layer-nya

---

*Dokumen ini ringkasan; sumber kebenaran tetap kode di `src/`. Kalau ragu, buka file-nya
langsung — semua path sudah dicantumkan di atas.*
