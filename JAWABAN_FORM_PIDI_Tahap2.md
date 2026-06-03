# JAWABAN FORM PIDI TAHAP 2 — FinCrime

> Cara pakai: tiap pertanyaan di bawah punya 1 jawaban berbentuk TEKS (tanpa tabel).
> Copy isi di dalam blok, lalu paste ke kolom "Your answer" yang sesuai di form.
> Tanda [ISI: ...] = harus kamu ganti sendiri. Urutan ini sama dengan urutan di form (32 pertanyaan).

---

## 1. ID Tim

[ISI: kode tim dari email konfirmasi pendaftaran PIDI, contoh P0041]

---

## 2. Nama Tim

FinCrime

---

## 3. Proposal Title

FinCrime: End-to-End Financial Crime Intelligence System for Indonesia

---

## 4. Team Composition
*(Sebutkan nama ketua dan anggota, serta peran masing-masing dalam project ini.)*

Tim FinCrime adalah kolaborasi lintas-institusi dengan empat anggota berperan spesifik:

- Andi Arif Abdillah (Universitas Gunadarma) — Project Lead & ML/Blockchain Engineer. Layer 2 (GraphSAGE GNN crypto tracing), integrasi multi-chain (BTC/ETH/BSC/Polygon/Tron), dan Privacy Coin Monitor.

- Raya Sesan Firdaus (Universitas Gunadarma) — ML & Data Engineer. Layer 0 (XGBoost Risk Scoring + SHAP), sanctions screening OFAC/UN/DTTOT, dan negative news scraper.

- Rambu Ilalang (Universitas Gunadarma) — Backend & MLOps Engineer. Layer 1 (Isolation Forest + Autoencoder), FastAPI, Docker/Kubernetes, observability Prometheus+Grafana, dan Airflow.

- TB Muhammad Fikri Arsyad (Universitas Sultan Ageng Tirtayasa) — Fullstack Developer. Layer 3 (regtech LTKM/LTKT), dashboard web 13 tab, mobile PWA, dan Telegram bot.

---

## 5. Executive Summary
*(Jelaskan versi terbaru dari solusi Anda, termasuk problem utama, pendekatan solusi, dan dampak utama yang ditargetkan.)*

FinCrime adalah sistem AI terintegrasi untuk mendeteksi dan mencegah kejahatan keuangan di Indonesia secara real-time. Sistem mengombinasikan empat layer: (1) Risk Scoring berbasis XGBoost+SHAP, (2) Fraud Detection real-time dengan Isolation Forest + Autoencoder, (3) Crypto Tracing menggunakan GraphSAGE GNN multi-chain (BTC/ETH/BSC/Polygon/Tron) plus Privacy Coin Monitor untuk Monero/Zcash/Dash, dan (4) Auto-generated LTKM/LTKT dengan narasi LLM Claude.

Sejak Tahap 1, tim telah membangun 40+ komponen end-to-end terverifikasi: web UI 13 tab termasuk Privacy Coin Monitor, mobile PWA, integrasi OFAC real-time (1.000+ entitas sanksi + 313 alamat crypto), modul deteksi privacy coin berbasis on/off-ramp monitoring sesuai standar industri, serta Prometheus+Grafana observability.

Sistem menargetkan reduksi waktu pembuatan LTKM dari 1-3 hari menjadi 5 menit, sesuai POJK No.12/2024, UU PDP No.27/2022, dan FATF Recommendations 22-25.

---

## 6. Problem Statement
*(Sesuai dengan penulisan Problem Statement yang sesuai.)*

Strengthening Financial Resilience and Innovation — Risk Management

---

## 7. Primary Sub-Problem Statement
*(Sesuai dengan penulisan Sub-Problem Statement yang sesuai, boleh lebih dari 1.)*

- Fraud Detection Systems (FDS)
- AML/CFT and Transaction Tracing including crypto
- Regtech & Suptech
- Alternative Data Utilization / Credit Scoring

---

## 8. Problem Validation
*(Apa masalah inti yang Anda selesaikan saat ini? Jelaskan akar masalahnya.)*

Masalah inti yang FinCrime selesaikan adalah ketidakmampuan sistem pemantauan keuangan Indonesia saat ini untuk mendeteksi kejahatan keuangan—khususnya pencucian uang berbasis kripto, termasuk penggunaan privacy coin seperti Monero dan Zcash—secara real-time dan terintegrasi. Tiga akar masalah utama:

Pertama, silo data antar-institusi membuat pelacakan dana lintas-instrumen (bank, e-wallet, crypto) hampir mustahil dilakukan holistik. Kedua, fraud detection konvensional bersifat reaktif dan berbasis rule statis, menghasilkan false positive tinggi sekaligus melewatkan pola layering kompleks. Ketiga, pelaku makin sering memindahkan dana ke privacy coin untuk memutus jejak, padahal mayoritas tools dalam negeri belum punya strategi pemantauan pintu masuk/keluar (on/off-ramp) privacy coin sama sekali.

POJK No.12/2024 menuntut strategi anti-fraud proaktif, akurat, dan auditable. PPATK mencatat pencucian uang berbasis kripto mencapai Rp 800 miliar (CNBC, 2024), dan OJK mencatat kerugian investasi ilegal Rp 142 triliun (Infobank, 2024). Bappebti juga TIDAK memasukkan Monero/Zcash/Dash ke daftar PFAK, sehingga aktivitas privacy coin di exchange Indonesia adalah indikator suspicious yang wajib dipantau.

---

## 9. Problem–Solution Mapping
*(Jelaskan secara eksplisit hubungan antara problem → mekanisme solusi → outcome.)*

Pemetaan eksplisit problem → mekanisme solusi → outcome:

Problem 1: Silo data lintas-instrumen keuangan.
Solusi: Arsitektur API-driven microservices dengan ingestion pipeline (Apache Kafka) yang menggabungkan transaksi bank, e-wallet, dan blockchain on-chain ke dalam stream terintegrasi.
Outcome: Visibilitas holistik aliran dana lintas-instrumen.

Problem 2: Fraud detection reaktif dengan false positive tinggi.
Solusi: Ensemble Layer 1 (Isolation Forest + PyTorch Autoencoder + rule engine) untuk deteksi anomali adaptif, dilanjutkan Layer 2 GraphSAGE GNN multi-chain.
Outcome: Deteksi proaktif dalam hitungan detik dengan target false positive rate < 2%.

Problem 3: Pencucian uang berpindah ke privacy coin yang sulit dilacak.
Solusi: Privacy Coin Monitor — strategi on/off-ramp monitoring berstandar industri yang men-flag wallet transparent (BTC/ETH) yang kirim/terima dana dari exchange pendukung Monero/Zcash, plus auto-flag karena privacy coin di luar daftar PFAK Bappebti. Dilengkapi modul LTKM otomatis (Layer 3 Jinja2 + Claude LLM) sesuai format PPATK GRIPS.
Outcome: Jejak privacy coin tertangkap di pintu masuk/keluar; waktu pelaporan turun dari 1-3 hari menjadi 5 menit.

---

## 10. Ecosystem Alignment
*(Bagaimana solusi Anda berinteraksi dengan stakeholder dan regulasi?)*

FinCrime dirancang untuk terintegrasi dengan ekosistem regulasi keuangan Indonesia. Di level regulator, sistem disiapkan untuk terhubung dengan PPATK sebagai penerima LTKM/LTKT via GRIPS API, OJK untuk validasi kepatuhan POJK No.12/2024, serta Bappebti untuk pengawasan aset kripto. Posisi Bappebti yang tidak memasukkan privacy coin (Monero/Zcash/Dash) ke daftar PFAK dipakai langsung sebagai aturan auto-flag dalam sistem.

Di level lembaga keuangan, FinCrime menyediakan REST API drop-in untuk core banking (107+ bank umum), e-wallet (GoPay, OVO, Dana), dan exchange kripto berlisensi PFAK; integrasi nyata menyusul melalui MoU dan pilot. Modul terpisah mendukung sektor private/DNFBP (notaris, dealer logam mulia, properti) sesuai FATF Rec 22-23. Output investigasi mendukung PPATK, KPK, dan Kejaksaan.

Sistem patuh UU PDP No.27/2022 (data minimization, enkripsi, audit log immutable). Arsitektur DLT-agnostic juga AML-ready untuk Project Garuda Rupiah Digital. Pilot direncanakan via OJK Regulatory Sandbox 2027.

---

## 11. Solution Approach & Mechanism
*(Jelaskan bagaimana solusi bekerja secara end-to-end.)*

FinCrime bekerja melalui pipeline real-time 4-layer terintegrasi.

Tahap Input: Data dikumpulkan dari transaksi perbankan (REST/Open API), aktivitas e-wallet, dan blockchain multi-chain (Ethereum/Bitcoin/BSC/Polygon/Tron via Etherscan/Blockstream/TronGrid). Semua data dinormalisasi ke schema Pydantic kanonik dan di-stream via Apache Kafka.

Tahap Processing — 4 layer sekuensial:

Layer 0 Risk Scoring: XGBoost dengan SHAP explainability menghasilkan skor risiko 0-100 per entitas dalam <100ms, dengan integrasi OFAC SDN real-time.

Layer 1 Fraud Detection: Ensemble Isolation Forest + PyTorch Autoencoder + rule engine mengevaluasi tiap transaksi terhadap distribusi historis, menghasilkan alert untuk smurfing, volume spike, atau transfer ke yurisdiksi berisiko.

Layer 2 GNN Crypto Tracing + Privacy Coin Monitor: Wallet terflag diteruskan ke graph database Neo4j; GraphSAGE message passing mendeteksi pola layering yang invisible bagi ML konvensional. Untuk privacy coin (Monero/Zcash/Dash) yang secara kriptografis tidak bisa di-trace internal, sistem memakai strategi on/off-ramp monitoring: men-flag wallet yang berinteraksi dengan exchange pendukung privacy coin dan menaikkan risk score karena aset tersebut di luar daftar PFAK Bappebti.

Layer 3 Regtech: Template engine Jinja2 + narasi LLM Claude menyusun LTKM/LTKT otomatis sesuai format PPATK, dengan auto-screening DTTOT/UN/news Indonesia (Kompas, Detik, Tempo, Antara, CNN ID).

Tahap Output: (1) real-time WebSocket alerts ke compliance officer, (2) visualisasi graph interaktif, (3) LTKM/LTKT siap submit ke PPATK GRIPS, (4) audit log immutable. Dilengkapi mobile PWA dan Telegram bot (termasuk command /privacycoin) untuk officer mobile.

---

## 12. Impact Scale & Targets
*(Apa dampak utama solusi Anda? Jelaskan skala dampaknya.)*

FinCrime menargetkan dampak di lima lapisan ekosistem keuangan Indonesia:

Untuk lembaga keuangan: Menurunkan kerugian fraud melalui deteksi proaktif. Indonesia memiliki 107 bank umum dan ribuan fintech. Target pilot: minimal 3 lembaga keuangan dalam 12 bulan pertama.

Untuk regulator (OJK, BI, PPATK, Bappebti): Memberikan visibilitas real-time atas aliran dana mencurigakan, termasuk ekosistem kripto multi-chain dan indikasi konversi ke privacy coin. PPATK menerima puluhan ribu laporan transaksi mencurigakan per tahun; FinCrime mempersingkat waktu generasi laporan dari 1-3 hari menjadi 5 menit.

Untuk ekosistem kripto: Menutup celah privacy coin yang selama ini jadi titik buta AML, dengan pemantauan on/off-ramp dan auto-flag aset non-PFAK.

Untuk masyarakat dan UMKM: Memperluas inklusi keuangan via credit scoring berbasis data alternatif. Lebih dari 50 juta UMKM Indonesia masih unbanked/underbanked.

Untuk Indonesia di level makro: Memperkuat integritas sistem keuangan digital, menurunkan pencucian uang kripto (Rp 800 miliar) dan investasi ilegal (Rp 142 triliun), serta memperbaiki rating FATF Mutual Evaluation Indonesia.

---

## 13. Impact Measurement
*(Bagaimana Anda mengukur keberhasilan solusi secara kuantitatif?)*

Keberhasilan FinCrime diukur dengan indikator kuantitatif di empat dimensi:

KPI Teknis:
- Fraud detection recall > 80% pada dataset IBM AML dan Elliptic Bitcoin
- Precision > 70% (target false positive rate < 2%)
- Inference latency < 100ms (Layer 0), < 500ms (Layer 1), < 2 detik (Layer 2)
- Composite F1-score > 75%
- Model drift PSI < 0.10 (sliding window 2 minggu)
- System uptime > 99.5%

KPI Proses:
- Waktu generasi LTKM/LTKT dari 1-3 hari menjadi 5 menit
- Waktu investigasi cross-instrument dari minggu menjadi jam
- Jumlah laporan per compliance officer per hari naik 10-20x
- Cakupan deteksi privacy coin: Monero, Zcash, Dash via on/off-ramp

KPI Pasar:
- Minimum 3 lembaga keuangan onboarded dalam 12 bulan pertama
- 1 juta+ transaksi diproses per bulan di Tahun 1
- Net Promoter Score compliance officer > 7/10
- Mobile PWA adoption rate > 80%

KPI Outcome Sistemik:
- Minimum 30% reduksi kerugian fraud di lembaga mitra pada Tahun 1
- 50% peningkatan akurasi LTKM yang disubmit ke PPATK
- Median deteksi crypto money laundering dari mingguan menjadi jam
- Peningkatan rating FATF Mutual Evaluation

Pengukuran dilakukan via built-in analytics dashboard (Prometheus+Grafana), immutable audit log, dan validasi pihak ketiga selama pilot di OJK Regulatory Sandbox.

---

## 14. System & Public Value Proposition
*(Nilai sistemik dan publik dari solusi.)*

FinCrime memberikan nilai sistemik melampaui manfaat individu pengguna.

Pertama, memperkuat integritas sistem keuangan Indonesia dengan deteksi fraud proaktif lintas-instrumen, meningkatkan kepercayaan publik terhadap ekosistem keuangan digital.

Kedua, meningkatkan pengawasan ekosistem kripto multi-chain (BTC/ETH/BSC/Polygon/Tron) sekaligus menutup celah privacy coin (Monero/Zcash/Dash) yang selama ini menjadi titik buta utama pencucian uang.

Ketiga, meningkatkan transparansi kepatuhan via LTKM auditable, timestamped, dengan narasi LLM dalam Bahasa Indonesia baku—sejalan dengan FATF Recommendations.

Keempat, mendukung inklusi keuangan via alternative data credit scoring untuk UMKM tanpa riwayat kredit formal.

Kelima, meningkatkan efisiensi regulator. Dengan automasi LTKM, PPATK dan OJK dapat fokus pada investigasi prioritas tinggi.

FinCrime diposisikan bukan sekadar produk SaaS, tetapi sebagai infrastruktur publik untuk integritas finansial Indonesia.

---

## 15. Solution Originality
*(Keunikan/orisinalitas solusi.)*

FinCrime adalah platform AML/CFT pertama di Indonesia yang mengintegrasikan lima hal yang belum pernah disatukan dalam satu produk: (1) GraphSAGE GNN multi-chain untuk crypto tracing real (BTC/ETH/BSC/Polygon/Tron), (2) LLM-powered LTKM narrative dalam Bahasa Indonesia baku, (3) Privacy Coin Monitor — deteksi konversi ke/dari Monero, Zcash, dan Dash melalui strategi on/off-ramp monitoring yang selaras dengan posisi Bappebti (privacy coin tidak masuk daftar PFAK) dan tren regulasi global (EU MiCA, OFAC), (4) auto-sync dengan list sanksi internasional (OFAC SDN 19.000+ entitas + UN Consolidated 1.000+ entitas + DTTOT) plus negative news screening 5 media Indonesia, dan (5) arsitektur DLT-agnostic yang siap menjadi AML compliance layer untuk Project Garuda Rupiah Digital Bank Indonesia.

Pendekatan ini membedakan FinCrime dari produk komersial: Chainalysis (hanya crypto, mahal USD 100k+/tahun), Elliptic (sama), dan Actimize/SAS (hanya bank konvensional). Kami adalah satu-satunya yang menggabungkan kelima dimensi tersebut dengan fokus konteks Indonesia: Bahasa Indonesia baku, regulasi POJK/PMK, format PPATK GRIPS, ambang IDR, dan harga terjangkau untuk institusi tier-2/tier-3.

---

## 16. Technological / Method Innovation
*(Inovasi teknis/metode.)*

Inovasi teknis utama FinCrime:

(1) GraphSAGE GNN untuk crypto tracing — menggantikan rule-based heuristic dengan message-passing neural network yang belajar representasi node, mendeteksi pola layering invisible bagi ML flat. Dilatih pada Elliptic Bitcoin dataset (200k node labeled).

(2) Privacy Coin Monitor — modul yang jujur secara teknis: tidak mengklaim bisa trace internal Monero/Zcash (mustahil secara kriptografis, bahkan bagi Chainalysis), melainkan memakai strategi "trace what's traceable, flag the gateway" — deteksi on/off-ramp ke exchange pendukung privacy coin, matriks 3-tier traceability, dan auto-flag aset non-PFAK Bappebti.

(3) LLM-powered LTKM narrative — integrasi Claude API untuk auto-generate "Ringkasan Kecurigaan" dalam Bahasa Indonesia formal sesuai standar PPATK, dengan fallback template offline.

(4) Multi-chain unified interface — single API mendukung 5 blockchain dengan auto-detect dari format address.

(5) Hybrid ensemble Layer 1 — Isolation Forest + PyTorch Autoencoder + 6 deterministic rules untuk balance recall (ML) vs explainability (rules).

(6) Real-time WebSocket alerts + drift detection PSI/KS untuk MLOps maturity. Semua model di-track via MLflow registry; pipeline scheduled via Apache Airflow.

---

## 17. Creativity in Implementation
*(Kreativitas dalam distribusi, monetisasi, dan engagement.)*

Distribusi mobile-first via Progressive Web App (PWA) — compliance officer install aplikasi dari browser tanpa app store, jalan offline-capable, dengan deep-link shortcut untuk Cases/Screening/Live Trace. Plus Telegram bot untuk investigasi on-the-go dengan command /trace, /risk, /screen, dan /privacycoin langsung dari HP.

Engagement: multi-bahasa (ID/EN toggle), toast notification real-time via WebSocket, dan Command Palette Ctrl+K untuk power user.

Monetisasi tier-based: Free Tier (institusi kecil, max 1.000 tx/bulan), Professional Rp 25 juta/bulan (bank tier-3 + fintech), Enterprise Rp 250 juta/bulan (bank tier-1/2, SLA 99.9%), serta Regulator Subscription gratis untuk OJK/BI/PPATK sebagai subsidi infrastruktur publik.

Workflow: Investigation Cases dengan status flow (open → in_review → escalated → reported → closed), audit log immutable, dan Investigation Timeline canvas viz untuk forensic narrative.

---

## 18. System Architecture
*(Arsitektur sistem.)*

Arsitektur FinCrime berbasis microservices API-driven dengan 7 lapisan logis:

(1) Ingestion Layer: Apache Kafka stream dari bank (REST/SFTP/Open API), e-wallet, blockchain (Etherscan/Blockstream/TronGrid), dan CSV importer (BCA/Mandiri/BRI/BNI auto-detect).

(2) Processing Layer: 4 model AI independen — Layer 0 (XGBoost+SHAP, <100ms), Layer 1 (IsolationForest+Autoencoder+rules, <500ms), Layer 2 (GraphSAGE+NetworkX+Neo4j + Privacy Coin Monitor, <2s), Layer 3 (Jinja2+Claude LLM, <5min end-to-end).

(3) Data Layer: PostgreSQL (cases, audit), Neo4j (wallet graph), ClickHouse (analytics), Redis (cache), MinIO/S3 (model artifacts).

(4) API Layer: FastAPI dengan 62+ endpoints (termasuk /v1/privacy-coin/*), OpenAPI docs, async-ready stateless untuk horizontal scale.

(5) Presentation Layer: Web UI 13 tab termasuk Privacy Coin Monitor (HTML+vanilla JS), Streamlit fallback, mobile PWA installable, Telegram bot.

(6) Observability Layer: Prometheus (metrics), Grafana (7 panels), structlog, immutable audit log, MLflow (experiment + registry).

(7) Orchestration Layer: Apache Airflow 4 DAGs (OFAC daily, news 6 jam, retrain mingguan, drift harian). Docker Compose untuk dev; Kubernetes manifests dengan HPA 3-20 pods untuk production.

Deployment-ready via GitHub Actions CI/CD dengan security scanning + automated tests.

---

## 19. Data & Feasibility
*(Sumber data dan kelayakan.)*

Sumber data FinCrime mencakup data publik (gratis) dan data partner (via MoU):

Data Publik (sudah terintegrasi & terverifikasi):
- OFAC SDN List — 19.041 entitas sanksi + 313 alamat crypto (auto-refresh 24 jam)
- UN Security Council Consolidated List — 1.004 entitas
- FATF FSI 2023 — 32 offshore jurisdictions
- Negative news — RSS Kompas, Detik, Tempo, Antara, CNN ID
- Etherscan, Blockstream (BTC), BscScan, PolygonScan, TronGrid
- CoinGecko — live crypto-to-IDR conversion
- Daftar PFAK Bappebti — acuan aset kripto legal (privacy coin tidak termasuk = basis auto-flag)

Dataset Publik untuk Training (Kaggle):
- IBM AML Transactions — 180M transaksi labeled untuk Layer 1
- Elliptic Bitcoin Dataset — 200k wallet labeled untuk Layer 2 (benchmark GraphSAGE)
- BAF NeurIPS 2022 — 1M bank account fraud records untuk Layer 0
- PaySim — mobile money simulator untuk pola smurfing

Data Partner (target Tahun 1 via MoU):
- Core banking BCA/Mandiri/BRI/BNI Open API
- PPATK SIPESAT DTTOT
- OJK regulatory data feed
- Bappebti registered exchange list

Feasibility tinggi: ~70% kebutuhan data sudah tersedia gratis publik. Validasi sample sintetis 7.500 entitas + 30k transaksi: Layer 0 ROC AUC = 0.79 (target 0.85+ di data real).

---

## 20. Security & Compliance
*(Keamanan dan kepatuhan.)*

FinCrime dirancang security-first dan compliance-by-design:

Compliance Regulasi Indonesia:
- POJK No.12/2024 — proactive anti-fraud strategy
- UU PDP No.27/2022 — data minimization, encryption in transit (TLS) & at rest (KMS), data residency Indonesia
- UU TPPU No.8/2010 + PP No.43/2015 — coverage pihak pelapor
- PPATK GRIPS format — LTKM/LTKT compliant template
- Acuan Bappebti — privacy coin di luar daftar PFAK dipakai sebagai aturan auto-flag

Compliance Internasional:
- FATF Recommendations 10, 11, 16 (Travel Rule), 20, 22-25, 32
- OFAC Sanctions integration — real-time auto-refresh
- UN Security Council Consolidated List
- Selaras tren global pembatasan privacy coin (EU MiCA, OFAC Tornado Cash)

Security Measures (implemented):
- Immutable audit log (append-only) untuk tiap prediction, report, case change
- RBAC ready untuk SSO (Azure AD/Okta via OAuth2)
- Secrets via .env (production: HashiCorp Vault)
- Model versioning via MLflow — full reproducibility audit
- Prometheus monitoring + Grafana alerting
- GitHub Actions security scanning, Docker hardening non-root, K8s SealedSecrets, mTLS antar-microservices

Penetration testing dan ISO 27001 certification direncanakan sebelum production deployment (Tahun 1, Q4 2026).

---

## 21. Implementation Readiness (MVP)
*(Kesiapan implementasi / status MVP.)*

MVP FinCrime SUDAH SELESAI DIBANGUN END-TO-END dan terverifikasi berfungsi. Scope yang sudah live:

- 4 Layer AI Models — terlatih, terdeploy, dapat di-query via API
- 62+ REST API endpoints — OpenAPI docs lengkap (/docs), termasuk /v1/privacy-coin/*
- Web UI 13 tab — Overview, Risk Scoring, Fraud, Tracing, Reports, Live Trace, Cases, Screening, Private Sector AML, Multi-chain, Monitoring, Timeline, Privacy Coin Monitor
- Privacy Coin Monitor — deteksi on/off-ramp Monero/Zcash/Dash, matriks 3-tier traceability, auto-flag aset non-PFAK Bappebti (tab UI + API + Telegram)
- Mobile PWA — installable di HP, offline-capable
- Telegram bot — 7 commands untuk officer mobile (termasuk /privacycoin)
- Real OFAC/UN/DTTOT integration — 1.000+ entitas terload
- Multi-chain crypto — BTC (free), ETH/BSC/Polygon/Tron (free API key)
- LLM-powered LTKM narrative (Claude API)
- Prometheus + Grafana observability (7 panels), MLflow registry, Apache Airflow 4 DAGs
- GitHub Actions CI/CD, Docker Compose + Kubernetes manifests, immutable audit log
- 14/14 pytest passing

Target 3 bulan ke depan: pilot dengan 1 bank mitra di OJK Regulatory Sandbox, integrasi PPATK SIPESAT (perlu MoU), retrain di data real (IBM AML + Elliptic Bitcoin) untuk meningkatkan ROC AUC ke 0.85+.

---

## 22. Value Proposition
*(Nilai utama untuk tiap pengguna.)*

Untuk Compliance Officer (end user):
- LTKM otomatis dalam 5 menit (dari 1-3 hari) dengan narasi LLM Bahasa Indonesia
- Mobile-first via PWA dan Telegram — investigasi dari mana saja, termasuk cek privacy coin via /privacycoin
- Real-time WebSocket alerts — tidak perlu refresh
- Case Management workflow terstruktur

Untuk Bank/Fintech (institusi pelapor):
- Drop-in REST API — integrasi 2-4 minggu (vs Actimize 6-12 bulan)
- Reduksi fraud loss hingga 30% via deteksi proaktif
- Compliance otomatis POJK No.12/2024 — auditable, timestamped
- Pemantauan privacy coin yang sebelumnya jadi titik buta

Untuk Exchange Kripto / PFAK:
- Deteksi on/off-ramp privacy coin sesuai posisi Bappebti
- Travel Rule (FATF Rec 16) support via sanctions & exchange flagging

Untuk Regulator (OJK, BI, PPATK, Bappebti):
- Read-only dashboard real-time atas seluruh lembaga mitra
- Format PPATK GRIPS-compliant
- Cross-instrument visibility (bank, e-wallet, crypto, privacy coin)

---

## 23. Model Revenue / Funding
*(Model pendapatan dan sumber dana.)*

Model revenue tier-based plus regulator subsidy:

(1) SaaS Subscription:
- Free Tier — institusi kecil, max 1.000 tx/bulan, fitur dasar (acquisition tool)
- Professional — Rp 25 juta/bulan: bank tier-3, fintech, koperasi (max 100k tx, semua 4 layer)
- Enterprise — Rp 250 juta/bulan: bank tier-1/2, exchange besar (unlimited, SLA 99.9%, dedicated CSM)

(2) Per-Transaction API: Layer 0 Rp 50/call, Layer 1 Rp 100/call, Layer 2 Rp 500/call (volume discount >1M tx/bulan).

(3) Regulator Subscription: OJK, BI, PPATK, Bappebti — gratis (subsidi infrastruktur publik).

(4) Consulting & Implementation: custom integration core banking Rp 500 juta-2 miliar one-time; compliance audit & training Rp 100-300 juta per engagement.

(5) Funding Sources: Bank Indonesia PIDI grant, OJK Regulatory Sandbox grant, LPDP research grant, strategic investor (bank/fintech holding), World Bank/ADB Financial Inclusion grant.

Target revenue: Tahun 1 Rp 2-3 miliar (3 enterprise + 10 professional), Tahun 2 Rp 8-12 miliar, Tahun 3 Rp 25-40 miliar.

---

## 24. Cost Structure & Sustainability
*(Struktur biaya dan keberlanjutan.)*

Biaya Operasional Tahunan (Tahun 1 estimasi):

- Cloud infrastructure  Rp 150 juta/tahun
- AI inference compute  Rp 50 juta/tahun
- LLM API (Claude untuk ~50k LTKM)  Rp 30 juta/tahun
- Third-party API (Etherscan, BscScan, dll)  Rp 20 juta/tahun
- Security & monitoring tools  Rp 25 juta/tahun
- Domain, SSL, miscellaneous  Rp 5 juta/tahun
- Total operational: ~Rp 280 juta/tahun

Biaya SDM (4 anggota tim + advisor): engineering Rp 1,2 miliar/tahun, DevOps+Security Rp 300 juta/tahun, compliance advisor part-time Rp 100 juta/tahun. Total ~Rp 1,6 miliar/tahun.

Biaya One-Time (Tahun 1) untuk Sertifikasi ISO 27001 (Rp 200 juta), integrasi PPATK SIPESAT + GRIPS API (Rp 100 juta), dan OJK Regulatory Sandbox (Rp 50 juta). 

Sustainability Strategy:

- Break-even di Tahun 2 dengan 8 institusi mitra Enterprise tier
- Revenue diversification (SaaS + per-tx + consulting + grant)
- Open-source non-core untuk komunitas (drive adoption)
- Strategic partnership untuk distribution leverage (Perbanas, INI, AFTECH)
- Reinvest 30% revenue ke R&D


---

## 25. Scalability
*(Skalabilitas teknis, operasional, geografis.)*

Skalabilitas Teknis: stateless FastAPI + Kubernetes HPA (3-20 pods) untuk horizontal scale linear, Kafka partition-based throughput (1k → 100k+ tx/s), Neo4j Enterprise (100M nodes), ClickHouse analytics, Redis cache, TorchServe inference server.

Kapasitas saat ini (single-node dev): 1.000 req/s Layer 0, 500 req/s Layer 1, 50 trace/s Layer 2.
Kapasitas setelah migration minimal (Postgres + 3 pods + Redis): 10.000+ req/s, 100M+ entitas, setara workload BCA Mobile peak.

Skalabilitas Operasional: MLOps automation via Airflow (sanctions refresh harian, retraining mingguan, drift check harian), model registry MLflow untuk A/B testing, multi-tenancy ready (row-level security), SSO integration ready.

Skalabilitas Geografis:
- Tahun 1: pilot 3 bank Indonesia
- Tahun 2: nationwide 30+ bank, 500+ fintech
- Tahun 3: ASEAN expansion (Malaysia, Singapura, Filipina)
- Tahun 5: emerging markets Asia-Africa

Framework FATF yang sama memudahkan ekspansi lintas-negara dengan minor localization.

---

## 26. Partnership & Distribution
*(Strategi partnership dan distribusi.)*

Partnership Regulator: Bank Indonesia (PIDI grant), OJK (Regulatory Sandbox 2027), PPATK (MoU SIPESAT untuk GRIPS API + DTTOT), Bappebti (exchange kripto PFAK + acuan privacy coin).

Partnership Institusi Keuangan: tier-1 banks via OJK Sandbox, tier-2/3 via Perbanas, fintech via AFTECH, e-wallet (GoPay/OVO/Dana) pasca-pilot, exchange kripto via Aspakrindo.

Partnership Sektor Private (DNFBP): Ikatan Notaris Indonesia (30.000+ notaris), APPI properti, Asosiasi Logam Mulia, Pejabat Lelang Kemkeu.

Partnership Akademis & Internasional: Gunadarma + Universitas Sultan Ageng Tirtayasa, Bank Indonesia Institute, ITB/UI/UGM, serta kolaborasi data crypto (Chainalysis/Elliptic) dan World Bank Financial Inclusion.

Channel Distribusi: direct sales (Enterprise), self-service signup (Free/Pro), partner reseller (komisi-based), OJK Sandbox sebagai entry point, open-source non-core.

---

## 27. Problem–Market Fit
*(Seberapa penting masalah ini bagi target pengguna.)*

Masalah AML/CFT sangat penting bagi target pengguna karena:

Lembaga keuangan: POJK No.12/2024 mewajibkan anti-fraud proaktif — non-compliance berisiko denda + pencabutan izin; compliance officer burnout karena kerja manual (LTKM 1-3 hari).

Ekosistem kripto: volume exchange Indonesia Rp 859 triliun (2024, Bappebti), dan pelaku makin memakai privacy coin untuk memutus jejak — mayoritas tools belum memantaunya.

Regulator: PPATK menerima puluhan ribu laporan/tahun, banyak terlambat. Pencucian uang kripto Rp 800 miliar dan investasi ilegal Rp 142 triliun terus meningkat.

Masyarakat: korban investasi ilegal meningkat; UMKM sulit akses kredit formal.

Intensitas: HIGH — sering (harian), mahal (triliunan), wajib (regulated 2025).

---

## 28. Evidence of Demand
*(Bukti permintaan/kebutuhan.)*

Regulatory Demand (mandatory):
- POJK No.12/2024 — anti-fraud system proaktif wajib sebelum 2025
- PP No.43/2015 + PMK No.55/2017 — pihak pelapor wajib lapor PPATK
- FATF Mutual Evaluation 2023 — Indonesia diberi waktu memperbaiki gap supervision
- POJK No.27/2024 — crypto asset oversight transition Bappebti ke OJK

Market Demand (volume):
- ~36.500 institusi wajib lapor (107 bank umum + 1.700 BPR + 350 fintech + DNFBP)
- PPATK menerima 75.000+ LTKM dan 2 juta+ LTKT per tahun
- Crypto exchange volume Indonesia Rp 859 triliun (2024, Bappebti)

Pain Point Interviews (qualitative):
- 5 compliance officer bank menengah: rata-rata 2-3 hari per LTKM, frustrasi tools lama
- Exchange kripto: butuh deteksi cepat untuk on-chain investigation + monitoring privacy coin
- Fintech P2P: butuh real-time fraud detection tapi NICE Actimize terlalu mahal (USD 500k+)

Competitor Landscape: Chainalysis (only crypto, mahal), Actimize/SAS (only banking). Gap confirmed: tidak ada produk end-to-end yang menggabungkan 4 layer + privacy coin monitoring + multi-chain + Bahasa Indonesia + harga affordable. FinCrime mengisi gap ini.

---

## 29. Target Market
*(Segmentasi target market.)*

Primary Market (Tahun 1, ~2.200 institusi keuangan formal): 107 bank umum, 1.700+ BPR, 350+ fintech terdaftar OJK, 12+ exchange kripto PFAK Bappebti.

Secondary Market (Tahun 2, ~85.000 DNFBP): notaris/PPAT, dealer logam mulia, agen properti, KAP, pejabat lelang.

Tertiary Market (Tahun 3+): regulator (OJK, BI, PPATK, Bappebti, KPK, Kejaksaan), law firm AML, audit firm.

User Personas: Bu Sari (35, Compliance Officer bank tier-2, 200+ LTKM/bulan manual); Mas Andi (30, Compliance Lead exchange kripto); Pak Wahyu (45, Pengawas OJK, butuh dashboard read-only).

Go-to-Market: Tahun 1 = 3-5 bank tier-2 via OJK Sandbox; Tahun 2 = nationwide + exchange kripto; Tahun 3 = tier-1 banks + ASEAN.

---

## 30. Adoption Readiness
*(Kesiapan adopsi.)*

Kemudahan Integrasi Teknis:
- REST API drop-in — integrasi core banking 2-4 minggu (vs Actimize 6-12 bulan)
- Self-service signup web < 10 menit (Free/Professional tier)
- Multi-channel input: REST API / Kafka / CSV bulk import
- Pre-built connector BCA/Mandiri/BRI/BNI auto-detect
- Single-command Docker deployment, on-prem ready untuk data residency

Kemudahan Operasional:
- UI Bahasa Indonesia (toggle EN tersedia)
- Mobile PWA + Telegram bot untuk officer mobility
- LTKM auto-generated, officer cukup review + approve

Kemudahan Compliance:
- Format LTKM/LTKT sesuai PPATK GRIPS — copy-paste atau direct submit
- Audit log immutable — siap untuk on-site audit BI/OJK
- MLflow model versioning untuk governance

Change Management: pilot mode parallel run 1-3 bulan, trial 30 hari, money-back guarantee 90 hari (Enterprise). Training: Free = docs+community, Pro = email 24h SLA, Enterprise = dedicated CSM. Time-to-value: <1 minggu fitur dasar, <1 bulan full integration.

---

## 31. Progress Since the 1st Submission
*(Perkembangan sejak submission Tahap 1.)*

Dari konsep (Tahap 1: Layer 2 prototype standalone) menjadi MVP 4-layer end-to-end terverifikasi (40+ komponen):

(1) Core 4-layer terlatih & API-ready: L0 XGBoost+SHAP (ROC AUC 0.79), L1 IsolationForest+Autoencoder, L2 GraphSAGE+NetworkX, L3 Jinja2+Claude LLM.

(2) Frontend: Web UI 13 tab (termasuk Privacy Coin Monitor), mobile PWA, Telegram bot (/privacycoin), WebSocket alerts.

(3) Coverage AML baru: Privacy Coin Monitor (on/off-ramp Monero/Zcash/Dash, auto-flag non-PFAK), multi-chain BTC/ETH/BSC/Polygon/Tron, OFAC (19.041) + UN (1.004) + DTTOT, news scraper 5 media.

(4) MLOps: Prometheus+Grafana, MLflow, Airflow 4 DAGs, audit log immutable, CI/CD, Docker+Kubernetes.

(5) Validasi: 14/14 test lolos, 62+ endpoint, pipeline <30 detik ke LTKM.

---

## 32. Current Status
*(Status saat ini.)*

Status: PROTOTYPE (functional MVP). Sistem 4-layer berjalan end-to-end — 62+ REST API, 13 UI tab, data OFAC/UN live, 14/14 test lolos, LTKM otomatis < 5 menit.

Bukti pendukung: repo GitHub + demo video (lihat Attachment). Target 3 bulan: pilot 1 bank via OJK Sandbox + retrain data real.

---

## Attachment (Link/File)

Link Attachment (URL):
[ISI: GitHub repository, contoh https://github.com/USERNAME/fincrime]
[ISI: Demo video Google Drive, contoh https://drive.google.com/file/d/XXXXX/view]

File/lampiran pendukung (pastikan semua link dapat diakses panitia):
- Repo GitHub (kode lengkap) + demo video
- Pitch deck, diagram arsitektur, screenshot 13 tab UI (termasuk Privacy Coin Monitor)
- Sample LTKM output (PDF), dokumentasi teknis
(Jika panitia meminta 1 file PDF: gabungkan executive summary + diagram + screenshot.)
