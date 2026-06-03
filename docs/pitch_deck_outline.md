# FinCrime — Pitch Deck Outline untuk Juri PIDI

> 15 slide × ~2 menit per slide = 30 menit total (atau 12 slide kalau presentasi cepat 20 menit)
> Format: PowerPoint 16:9 widescreen
> Brand: FinCrime (warna primer biru #4f8fff, dark theme matching dashboard)

---

## 🎬 Outline 15 Slide

### Slide 1 — Cover
**Visual**: Logo FinCrime di tengah, dark background, gradien biru

```
FinCrime
End-to-End Financial Crime Intelligence System for Indonesia

Submission Tahap 2 — PIDI Bank Indonesia 2026

Tim FinCrime (Universitas Gunadarma + Universitas Sultan Ageng Tirtayasa)
```

---

### Slide 2 — Problem
**Visual**: 3 angka besar (statistic) + ikon

```
Indonesia kehilangan TRILIUNAN Rupiah karena celah AML

Rp 800 miliar   →  Pencucian uang berbasis kripto (PPATK, CNBC 2024)
Rp 142 triliun  →  Kerugian investasi ilegal (OJK, Infobank 2024)
75.000+         →  LTKM/tahun, banyak terlambat 1-3 hari

DNFBP supervision = gap utama FATF Mutual Evaluation 2023
```

---

### Slide 3 — Tiga Akar Masalah
**Visual**: 3 kolom dengan ikon

```
1. SILO DATA              2. FRAUD REAKTIF          3. LTKM MANUAL
   Bank ↔ E-wallet ↔        Rule-based, FP            1-3 hari per laporan
   Crypto ↔ DNFBP            tinggi, miss layering     DNFBP zero coverage
   tidak terhubung
```

---

### Slide 4 — Solusi: 4 Layer FinCrime
**Visual**: Arsitektur 4-layer pipeline horizontal flow

```
INGESTION ──→ LAYER 0 ──→ LAYER 1 ──→ LAYER 2 ──→ LAYER 3 ──→ PPATK
              Risk Score   Fraud      GNN Trace    Auto LTKM
              XGBoost      IF + AE    GraphSAGE    Jinja2 + LLM
              <100ms       <500ms     <2s          5 menit
```

Tagline: "Dari ingestion ke LTKM dalam 5 menit"

---

### Slide 5 — Demo Live
**Visual**: Screenshot dashboard 12 tab + arrows menunjukkan flow

```
Live Demo (2 menit):
1. Tab Live Trace → trace wallet sanctioned Tornado Cash
2. Tab Layer 1 → 28 anomaly detected dari 100 tx
3. Tab Layer 3 → preview LTKM real-time (LLM narrative bahasa Indonesia)
4. Demo Ctrl+K command palette
```

**(Show dashboard di full screen, bukan slide statis)**

---

### Slide 6 — Coverage Lengkap (FATF Compliance)
**Visual**: 5 ikon vertical alignment

```
COVERAGE FATF RECOMMENDATIONS

✓ Rec 10 — CDD                          Layer 0 risk scoring
✓ Rec 11 — Record-keeping               Audit log immutable
✓ Rec 20 — STR Reporting                Auto-LTKM
✓ Rec 22-23 — DNFBP                     Private Sector AML module
✓ Rec 24-25 — Beneficial Ownership      UBO Tracker + Shell Co detector
✓ Rec 32 — Cross-border                 Multi-chain crypto support
```

---

### Slide 7 — Real Data Integration
**Visual**: 10 logo data source dalam grid

```
10 Sumber Data Real Sudah Terintegrasi:

OFAC SDN (19,000+ entitas, 313 alamat crypto)
UN Consolidated List (1,004 entitas)
DTTOT Indonesia (seed)
5 media Indonesia (Kompas, Detik, Tempo, Antara, CNN ID)
5 blockchain (BTC, ETH, BSC, Polygon, Tron)
```

---

### Slide 8 — DIFFERENTIATOR: CBDC-Ready
**Visual**: Highlight slide — full attention

```
🎯 FinCrime adalah satu-satunya AML platform Indonesia
   yang dirancang DLT-AGNOSTIC dan CBDC-READY

Bank Indonesia sendiri (White Paper CBDC 2022):
"...pemenuhan komitmen Anti Pencucian Uang dan
 Pencegahan Pendanaan Terorisme..."

→ FinCrime menjawab 3/5 risiko utama CBDC Garuda

Saat Rupiah Digital launch (target 2027), FinCrime siap
men-trace transaksi w-Rupiah Digital dalam minggu, bukan tahun.
```

**(Slide paling kritis — selling point utama ke juri BI)**

---

### Slide 9 — Architectural Alignment Garuda
**Visual**: Diagram dari `docs/cbdc_garuda_alignment.md`

```
PROJECT GARUDA (BI)              FinCrime AML Layer

w-Rupiah Digital DLT       ────→  Layer 2 GraphSAGE GNN
(Besu / R3 Corda)                 (DLT-agnostic)

r-Rupiah Digital (retail)  ────→  Layer 3 auto-LTKM
(future)                          (DNFBP-compatible)

Smart Contract             ────→  Rule engine + WebSocket
                                  (programmable compliance)
```

---

### Slide 10 — Progress sejak Tahap 1
**Visual**: Before/After comparison

```
TAHAP 1 (Konsep)              TAHAP 2 (40+ komponen working)

✗ Layer 0–3 konseptual    ✓ Semua layer end-to-end terverifikasi
✗ Mockup UI               ✓ Web UI 12 tab + Mobile PWA + Telegram bot
✗ Layer 2 prototype       ✓ GraphSAGE full + multi-chain + UBO + DNFBP
✗ Sample sintetis         ✓ Real OFAC 19k entitas auto-refresh
✗ No observability        ✓ Prometheus + Grafana + MLflow + Airflow
                          ✓ NEW: DLT-agnostic untuk CBDC Garuda
```

---

### Slide 11 — Business Model & Market
**Visual**: Funnel diagram

```
TARGET MARKET (~36,500 institusi wajib lapor)

Tier-1 banks (Mandiri, BCA, BRI, BNI)     → Enterprise Rp 250jt/bln
Tier-2/3 banks + Fintech (~2,000)          → Professional Rp 25jt/bln
DNFBP (notaris, properti, dll ~30,000)    → Free tier (acquisition)
Regulator (OJK, BI, PPATK)                 → Free (subsidi nasional)

Y1 revenue target: Rp 2-3 miliar
Y3 revenue target: Rp 25-40 miliar
Break-even: Y2
```

---

### Slide 12 — Team
**Visual**: 4 foto + nama + peran

```
TIM 4 ORANG LINTAS-INSTITUSI

Andi Arif Abdillah (Gunadarma) — Project Lead + Layer 2 GNN
Raya Sesan Firdaus (Gunadarma) — Layer 0 + Sanctions
Rambu Ilalang (Gunadarma) — Layer 1 + MLOps
TB Muhammad Fikri Arsyad (Universitas Sultan Ageng Tirtayasa) — Layer 3 + Dashboard
```

---

### Slide 13 — Roadmap 3 Tahun
**Visual**: Timeline horizontal

```
2026 Q4 → 2027 Q1 ────→ 2027 Q2-3 ────→ 2028+

PIDI         OJK Sandbox      Pilot 3 bank +     Rupiah Digital
Submission   + PPATK MoU       2 DNFBP            integration
                                                  ASEAN expansion
```

---

### Slide 14 — Ask
**Visual**: 3 bullet besar

```
YANG KAMI MINTA DARI PIDI BANK INDONESIA

1. SEED FUNDING — untuk pilot dengan bank partner
   (Rp 500 juta — Rp 1 miliar)

2. ACCESS — fast-track ke OJK Regulatory Sandbox
   + introduction ke PPATK SIPESAT

3. CBDC PATHWAY — kesempatan integrasi awal dengan
   BI Innovation Lab untuk Garuda Phase 2 (2027)
```

---

### Slide 15 — Closing & Call to Action
**Visual**: Logo + tagline

```
FinCrime
Compliance Infrastructure untuk Indonesia Digital

Built today.  Future-proof tomorrow.

   GitHub: github.com/[USERNAME]/fincrime
   Demo:    [link demo video]
   Email:   andi.arifabdillah@gmail.com
   ===
   Terima kasih, Bapak/Ibu Juri 🙏
```

---

## 🎤 Speaker Notes — Key Phrases per Slide

| Slide | Talking points |
|-------|----------------|
| 1 | "Kami tim FinCrime dari Gunadarma dan Universitas Sultan Ageng Tirtayasa. Solusi kami: end-to-end financial crime intelligence." |
| 2 | "Indonesia kehilangan triliunan rupiah. Sumber: PPATK, OJK, FATF Mutual Eval 2023." |
| 3 | "Tiga akar masalah yang kami identifikasi di Tahap 1, masih relevan di Tahap 2." |
| 4 | "4-layer pipeline. Setiap layer punya target latency. Total <5 menit end-to-end." |
| 5 | "Daripada cerita, mari kami tunjukkan langsung." **(SWITCH TO DEMO)** |
| 6 | "FATF compliance bukan checkbox — kami sudah implementasi 6 recommendation utama." |
| 7 | "Bukan mockup. Ini real OFAC list yang ter-update tiap 24 jam." |
| 8 | "Ini titik kritis." **(PAUSE)** "BI sendiri yang bilang AML adalah requirement CBDC. Kami sudah siap." |
| 9 | "DLT-agnostic bukan klaim — adapter sudah ada di repository, tinggal connect ke BI API saat available." |
| 10 | "Bukan polishing kosmetik — 40+ komponen baru yang bisa di-audit di GitHub." |
| 11 | "Model bisnis tier-based. Free untuk DNFBP kecil — drive adoption. Enterprise untuk bank besar — revenue." |
| 12 | "4 orang, 4 universitas. Kontribusi terdokumentasi di GitHub commit history." |
| 13 | "Roadmap 3 tahun. Tahun 3 ASEAN expansion." |
| 14 | "Yang kami minta: seed funding + sandbox access + CBDC pathway. Combined value lebih besar dari uang grant." |
| 15 | "Terima kasih. Siap untuk Q&A." |

---

## 🎨 Design Guidelines

| Element | Spec |
|---------|------|
| **Aspect ratio** | 16:9 widescreen |
| **Background** | Dark navy (#07090f) atau white — konsisten |
| **Primary color** | #4f8fff (FinCrime blue) |
| **Accent color** | #22c55e (success green) untuk capaian |
| **Warning color** | #ef4444 (red) untuk problem statement |
| **Font heading** | DM Sans / Inter / Segoe UI Bold |
| **Font body** | DM Sans / Segoe UI Regular |
| **Font code/data** | IBM Plex Mono / Consolas |
| **Slide number** | Bottom right, small, 60% opacity |
| **Logo** | Top left every slide (kecuali Slide 1) |

---

## 📐 Slide Templates

### Title Slide Template (Slide 1)
```
[CENTER ALIGN]
[Logo FinCrime — size 200x200px]
[Title FinCrime — 60pt bold]
[Subtitle — 24pt regular]
[Author info — 16pt]
```

### Content Slide Template
```
[Logo top-left small]                            [Slide # bottom-right]
[Header — 32pt bold blue]
─────────────────────────────────────────
[Content area — flexible, max 6 bullet]
[Charts/diagrams allowed]
[Footer: FinCrime — Submission Tahap 2 PIDI 2026]
```

### Demo Slide Template
```
"LIVE DEMO" — placeholder
(Switch ke aplikasi real, bukan slide statis)
```

---

## 🛠 Tools untuk Buat Slide

| Tool | Kelebihan |
|------|-----------|
| **PowerPoint** | Standard, semua orang punya |
| **Google Slides** | Kolaboratif, mudah share |
| **Pitch.com** | Modern templates, mudah |
| **Canva** | Banyak template profesional |
| **Beamer (LaTeX)** | Untuk akademis formal |

**Recommended**: Google Slides + Canva templates.

---

## ⏱ Timing Recommendation

| Format | Durasi total | Per slide |
|--------|--------------|-----------|
| **Quick pitch** (10 menit) | 10 menit | ~40 detik (skip slide 9, 13) |
| **Standard** (15 menit) | 15 menit | 1 menit |
| **Deep dive** (30 menit) | 30 menit | 2 menit + 5 menit Q&A |

---

## 🎤 Q&A Preparation — Top 5 Predicted Questions

| Q | A |
|---|---|
| 1. "Bagaimana kalau pakai Monero?" | Section 5.5 di proposal — on/off-ramp monitoring, sejalan dengan Bappebti tidak include privacy coins |
| 2. "Apa beda dari Chainalysis?" | Slide 11 — fokus Indonesia + DNFBP + harga affordable + CBDC-ready |
| 3. "Berapa biaya untuk bank tier-2?" | Slide 11 — Professional Rp 25 juta/bulan |
| 4. "Kapan production-ready?" | Pilot Q3 2027 via OJK Sandbox, full launch Q4 2028 |
| 5. "Sudah ada bank yang commit?" | Belum — yang kami minta dari PIDI adalah introduksi dan fast-track sandbox |

---

## 📝 Backup Slides (untuk Q&A panjang)

| Backup # | Topik |
|----------|-------|
| B1 | Detail GraphSAGE architecture (layers, hidden dim, training data) |
| B2 | Detail FATF Recommendations compliance matrix |
| B3 | Cost breakdown Tahun 1 (Rp 280 juta operational + 1.6 miliar SDM) |
| B4 | Security: ISO 27001 roadmap + UU PDP compliance details |
| B5 | Privacy coin strategy detail (3-tier matrix) |
| B6 | Investigation Timeline canvas viz screenshot |
| B7 | Apache Airflow DAG schedule (4 DAGs) |
| B8 | Prometheus + Grafana dashboard screenshot |
