# FinCrime + Project Garuda (CBDC Bank Indonesia)

> **Status**: Strategic alignment design document
> **Reference**: BI White Paper CBDC 2022, Consultative Paper Jan 2023, PoC Report Dec 2024
> **Target**: Position FinCrime sebagai AML/CFT compliance layer untuk Rupiah Digital

---

## 1. Konteks: Project Garuda

Project Garuda adalah inisiatif Central Bank Digital Currency (CBDC) Bank Indonesia
untuk menerbitkan **Rupiah Digital** dalam 2 tier:

| Tier | Audience | Status (per Dec 2024) | Platform |
|------|----------|----------------------|----------|
| **w-Rupiah Digital** (wholesale) | Bank + LJK | **PoC Selesai** | Hyperledger Besu + R3 Corda (kandidat) |
| **r-Rupiah Digital** (retail) | Publik | Future end-state | TBD |

**Karakteristik teknis**:
- **DLT permissioned** dengan konsensus **Proof of Authority (PoA)**
- Validating node = wholesaler (bank besar)
- Non-validating node = non-wholesaler (LJK lain)
- **One-tier distribution**: BI → wholesaler langsung
- **Programmability**: smart contract untuk inovasi & efisiensi
- **Privacy-preserving**: selective disclosure via cryptography
- **3i** (interkoneksi, interoperabilitas, integrasi) — antar platform & lintas negara

---

## 2. Mengapa AML/CFT Critical untuk Garuda

Bank Indonesia eksplisit menyebut AML/CFT sebagai requirement integritas Rupiah Digital.

### Kutipan langsung dari dokumen BI:

> **White Paper CBDC 2022 (hal. 16):**
> *"Aspek-aspek seperti penggunaan Digital Rupiah... pengelolaan risiko operasional, perlindungan konsumen, perlindungan data pribadi, dan **integritas keuangan terutama dalam konteks pemenuhan komitmen Anti Pencucian Uang dan Pencegahan Pendanaan Terorisme**"*

> **White Paper CBDC 2022 (hal. 19):**
> *"Digitalisasi ekonomi keuangan juga disertai risiko yang perlu diwaspadai seperti shadow banking, **risiko siber dan fraud, pencucian uang dan pendanaan terorisme**, persaingan usaha tidak sehat, dan penyalahgunaan data konsumen"*

> **White Paper CBDC 2022 (hal. 12):**
> *"Di sisi lain, cryptoassets dan stablecoins juga **membawa risiko pencucian uang dan pendanaan terorisme** serta transaksi terlarang"*

### Mapping: Risiko BI → Modul FinCrime

| Risiko CBDC yang BI khawatirkan | Modul FinCrime yang menangani |
|----------------------------------|-------------------------------|
| **Fraud** (siber + transaksional) | Layer 1 (IsolationForest + Autoencoder + rules) |
| **Pencucian uang** | Layer 2 (GraphSAGE GNN trace) + Layer 3 (LTKM auto) |
| **Pendanaan terorisme** | DTTOT/UN/OFAC screening + News screener |
| **Penyalahgunaan data konsumen** | UU PDP compliance + audit log immutable |
| **Shadow banking** | Cross-instrument tracing |

**3 dari 5 risiko CBDC dijawab langsung oleh FinCrime.**

---

## 3. Arsitektur Integrasi: FinCrime sebagai AML Layer Garuda

```
┌────────────────────────────────────────────────────────────────┐
│              PROJECT GARUDA — RUPIAH DIGITAL                   │
│                                                                │
│   Bank Indonesia (issuer)                                      │
│        │                                                       │
│        ▼                                                       │
│   ┌───────────────────────┐    ┌──────────────────────────┐   │
│   │ w-Rupiah Digital      │    │ r-Rupiah Digital         │   │
│   │ (DLT permissioned PoA)│    │ (future end-state)       │   │
│   │ Hyperledger Besu /    │    │ retail platform          │   │
│   │ R3 Corda              │    │                          │   │
│   └──────────┬────────────┘    └────────────┬─────────────┘   │
│              │                               │                 │
└──────────────┼───────────────────────────────┼─────────────────┘
               │                               │
               │  DLT transaction events       │
               │  (validating node events)     │
               ▼                               ▼
┌────────────────────────────────────────────────────────────────┐
│        FinCrime — AML Compliance Pipeline (existing)           │
│                                                                │
│  ┌─────────────────────────────────────────────────────────┐  │
│  │ Rupiah Digital Adapter (DLT-agnostic)                   │  │
│  │ src/multichain/rupiah_digital_adapter.py                │  │
│  │   - Besu (Web3.py event subscription)                   │  │
│  │   - Corda (RPC observable)                              │  │
│  │   - Convert DLT event → canonical Transaction schema    │  │
│  └─────────────────────────────┬───────────────────────────┘  │
│                                ▼                                │
│  ┌─────────────┐ ┌─────────────┐ ┌──────────────────────┐    │
│  │ Layer 0     │ │ Layer 1     │ │ Layer 2              │    │
│  │ Risk Score  │ │ Fraud Detect│ │ GraphSAGE GNN trace  │    │
│  │ (entity)    │ │ (event)     │ │ (DLT graph)          │    │
│  └──────┬──────┘ └──────┬──────┘ └──────────┬───────────┘    │
│         │               │                    │                 │
│         └───────────────┼────────────────────┘                 │
│                         ▼                                       │
│                  ┌──────────────┐                              │
│                  │ Layer 3      │                              │
│                  │ Auto LTKM/   │                              │
│                  │ LTKT         │                              │
│                  └──────┬───────┘                              │
└─────────────────────────┼──────────────────────────────────────┘
                          │
                          ▼
                  ┌────────────────┐
                  │  PPATK GRIPS   │  (Submission resmi)
                  │  BI Supervisor │  (Real-time dashboard)
                  └────────────────┘
```

---

## 4. Tujuh Titik Persinggungan Garuda ↔ FinCrime

| # | Aspek Desain Garuda | Kebutuhan AML/Compliance | Modul FinCrime yang Match |
|---|---------------------|--------------------------|---------------------------|
| 1 | **DLT Permissioned (PoA)** | Tracing transaksi antar-validating-node | Layer 2 GraphSAGE GNN + Neo4j |
| 2 | **w-Rupiah Digital** (wholesale, PoC Dec 2024 selesai) | Anti-fraud + monitoring volume tinggi antar-bank | Layer 1 IsolationForest + Autoencoder + rules |
| 3 | **r-Rupiah Digital** (retail, future) | LTKM/LTKT untuk transaksi retail publik | Layer 3 auto-LTKM + DNFBP |
| 4 | **Programmability (Smart Contract)** | Compliance rules embedded dalam kontrak | Rule engine + WebSocket alerts |
| 5 | **Identity + Regulatory service** | KYC + sanctions screening built-in | OFAC/UN/DTTOT integration |
| 6 | **Cross-border (3i)** | FATF Travel Rule + behavioral fingerprinting | Multi-chain unified interface |
| 7 | **Privacy + integrity tx** | Selective disclosure untuk regulator | Audit log + RBAC + Case Mgmt |

---

## 5. Roadmap Integrasi

| Fase | Timeline | Aktivitas |
|------|----------|-----------|
| **Phase 0: Saat ini (2026)** | — | FinCrime sudah DLT-agnostic. Layer 2 GNN bisa konsumsi graph apapun. Adapter stub di `src/multichain/rupiah_digital_adapter.py` |
| **Phase 1: BI Sandbox Access** | 2026 Q4 | Apply ke OJK Regulatory Sandbox + BI Innovation Lab untuk dapat akses simulasi DLT |
| **Phase 2: Adapter Implementation** | 2027 Q1 | Implement real Besu event listener + Corda RPC observer (estimasi 3-4 minggu) |
| **Phase 3: Pilot dengan w-Rupiah** | 2027 Q2-Q3 | Pilot integration di Garuda Phase 2 (post-PoC, pre-launch) |
| **Phase 4: r-Rupiah Compliance** | 2028+ | Extend ke retail tier saat r-Rupiah Digital launch |

---

## 6. Differentiation vs Kompetitor

| Vendor | CBDC-Ready? | Indonesian Context | Cost |
|--------|-------------|--------------------|---|
| **Chainalysis** | ❌ (only public chains) | ❌ (US/EU focus) | USD 100k+/year |
| **Elliptic** | ❌ | ❌ | USD 80k+/year |
| **TRM Labs** | ❌ | ❌ | USD 60k+/year |
| **NICE Actimize** | ❌ (only bank rails) | Partial | USD 500k+ implementation |
| **SAS AML** | ❌ | Partial | USD 300k+/year |
| **FinCrime (ours)** | ✅ DLT-agnostic native | ✅ Bahasa, POJK, PMK, GRIPS, IDR | IDR 25 jt/bulan Pro tier |

**FinCrime adalah satu-satunya produk yang DESIGNED to be CBDC-compatible dari awal.**

---

## 7. Implikasi Strategis untuk Indonesia

### A. FATF Mutual Evaluation Improvement
FATF Mutual Evaluation Indonesia 2023 flag **DNFBP supervision + crypto AML** sebagai gap utama. Saat Rupiah Digital launch dengan FinCrime sebagai AML layer:

- ✅ DNFBP gap **tertutup** (FinCrime sudah cover)
- ✅ Crypto AML **terdokumentasi** (multi-chain trace existing)
- ✅ CBDC AML **terbukti compliant** (live audit log)

→ Potensi peningkatan rating dari "Partially Compliant" ke "Largely Compliant"

### B. Indonesia sebagai CBDC Compliance Reference
Kalau Indonesia berhasil launch CBDC dengan AML compliance kelas dunia, posisi BI sebagai **regional thought leader** menguat:
- mBridge (BIS multi-CBDC project)
- Project Dunbar (BIS)
- ASEAN-5 cross-border CBDC

FinCrime bisa di-export sebagai komponen compliance untuk CBDC negara ASEAN lain.

### C. National Sovereignty in Compliance Tech
Saat ini bank Indonesia bergantung pada vendor asing untuk AML (Actimize, SAS, NICE). FinCrime mengurangi dependency tersebut, sejalan dengan agenda kedaulatan digital nasional.

---

## 8. Honest Limitations

1. **BI DLT API belum public** — adapter sekarang masih stub. Real integration butuh BI open access (target 2027 post-Phase 2 PoC).
2. **PoC Hyperledger Besu vs R3 Corda** — BI belum decide final platform. FinCrime support keduanya, jadi tidak terikat pilihan BI.
3. **Privacy model belum final** — Consultative Paper Tahap II/III (retail) belum publish. Adapter design akan adjust mengikuti.
4. **Komersial integration** butuh MoU formal dengan BI Department of Payment System Policy + Innovation Lab.

---

## 9. Kesimpulan

FinCrime tidak hanya sistem AML untuk hari ini — **sistem ini future-proof untuk era CBDC Indonesia**. Investasi yang BI lakukan untuk mendukung FinCrime via PIDI grant akan menghasilkan return ganda:

1. **Hari ini**: Pemenuhan POJK No.12/2024 + FATF Rec 22-25 untuk bank, fintech, dan DNFBP
2. **2027+**: Native AML compliance untuk Project Garuda Rupiah Digital — tanpa biaya re-engineering produk asing
