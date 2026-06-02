# Panduan: Menghubungkan FinCrime ke Data Asli

Panduan langkah demi langkah untuk mengganti data sintetis dengan data asli dari tiga sumber:

1. **OFAC Sanctions List** (publik, gratis, tanpa API key)
2. **Etherscan API** (gratis, butuh API key 2 menit)
3. **CSV mutasi rekening bank** (data internal/historis bank)

---

## 1) OFAC Sanctions List

Sumber resmi sanksi US Treasury — 19.000+ entitas + 313 alamat crypto.

```powershell
.\.venv\Scripts\Activate.ps1
python scripts\fetch_sanctions.py
```

Output:
- `data\sanctions\ofac_sdn.csv` — daftar mentah (cache 24 jam)
- Update `data\sample\entities.csv` — flag `sanction_flag=True` untuk match
- Backup `data\sample\entities.pre_sanctions.csv`

**Refresh paksa** (jika ada update dari OFAC):
```powershell
python scripts\fetch_sanctions.py --force-refresh
```

Hasil terverifikasi: **313 alamat crypto sanksi OFAC + 318 total seed wallet** ter-load.

---

## 2) Etherscan API — Data Crypto Real

### 2.1. Dapatkan API Key Gratis (2 menit)

1. Buka https://etherscan.io/register (daftar email)
2. Login → https://etherscan.io/myapikey
3. Klik **+ Add** → kasih nama "FinCrime" → copy key

Limit gratis: 5 req/detik, 100.000 req/hari (lebih dari cukup).

### 2.2. Masukkan ke `.env`

Buat file `.env` (copy dari `.env.example`):

```powershell
Copy-Item .env.example .env
notepad .env
```

Edit baris ini:
```
ETHERSCAN_API_KEY=YOUR_KEY_HERE
```

### 2.3. Pull Data Real

Default-nya menarik transaksi di sekitar wallet Tornado Cash, Lazarus Group, dan alamat OFAC:

```powershell
python scripts\fetch_real_blockchain.py
```

Custom seed + lebih banyak hop:
```powershell
python scripts\fetch_real_blockchain.py `
    --wallets 0x8589427373d6d84e98730d7795d8f6f8731fda16 `
    --limit 100 --hops 2
```

Output:
- `data\real\real_transactions.csv` — transaksi Ethereum asli (canonical schema)
- `data\real\real_crypto_edges.csv` — wallet→wallet edges untuk Layer 2
- `data\real\real_wallets.csv` — entity records dengan flag `sanction_flag` & `is_fraud`

### 2.4. Train Layer 0 + Layer 1 dengan Data Real

```powershell
python -m src.layer0_risk_scoring.train `
    --entities data\real\real_wallets.csv
python -m src.layer1_fraud_detection.train `
    --transactions data\real\real_transactions.csv
```

### 2.5. Train Layer 2 GNN (butuh PyTorch + torch_geometric)

```powershell
# Hanya jika Python 3.11/3.12 dan torch terinstall
python -m src.layer2_gnn_tracing.train `
    --edges data\real\real_crypto_edges.csv `
    --entities data\real\real_wallets.csv
```

---

## 3) CSV Mutasi Rekening Bank

Importer mendukung 4 bank Indonesia (auto-detect) + format generic.

### 3.1. Format yang Didukung

| Bank | Header yang dideteksi |
|------|-----------------------|
| **BCA** | `Tanggal`, `Keterangan`, `Mutasi`, `Saldo` |
| **Mandiri** | `Tanggal`, `Deskripsi`, `Debit`, `Kredit` |
| **BRI** | `Tanggal Transaksi`, `Keterangan`, `Debit`, `Kredit` |
| **BNI** | `TGL`, `KETERANGAN`, `DEBET`, `KREDIT` |
| **Generic** | `date`, `description`, `amount`, `type`, `counterparty` |

### 3.2. Export Statement dari Internet Banking

Setiap bank punya cara berbeda untuk export CSV:
- **BCA**: KlikBCA → Informasi Rekening → Mutasi Rekening → Download
- **Mandiri**: Livin' app → Rekening → Mutasi → 3-titik → Export CSV
- **BRI**: BRImo → Mutasi → Export
- **BNI**: BNI Direct → Account Statement → Excel/CSV

### 3.3. Import + Score

```powershell
# Auto-detect format
python scripts\import_bank_csv.py "C:\path\to\statement.csv" --account 1234567890

# Override format
python scripts\import_bank_csv.py "statement.csv" --account 1234567890 --bank bca

# Banyak file sekaligus (glob)
python scripts\import_bank_csv.py "C:\statements\*.csv" --account 1234567890
```

Output: `data\real\imported_transactions.csv`

### 3.4. Jalankan Deteksi Fraud

```powershell
python scripts\score_real_data.py
```

Output:
- `data\real\scored_transactions.csv` — kolom asli + `anomaly_score`, `is_anomaly`, `rules`
- Cetak top transaksi mencurigakan

**Hasil verifikasi pada contoh BCA dummy** (`data\sample\example_bca_statement.csv`):
- 9 transaksi diimpor
- 7 terdeteksi sebagai anomali (77.8%)
- 4 smurfing terdeteksi otomatis
- 2 transaksi besar (≥500M) terdeteksi sebagai LTKT trigger

---

## 4) Workflow End-to-End Data Real

```powershell
# 1. Update sanctions list (publik, gratis)
python scripts\fetch_sanctions.py

# 2. Pull data crypto Ethereum real (butuh API key Etherscan)
python scripts\fetch_real_blockchain.py

# 3. Import statement bank (data internal)
python scripts\import_bank_csv.py "statement.csv" --account YOUR_ACCT

# 4. Train model di data real
python -m src.layer0_risk_scoring.train --entities data\real\real_wallets.csv
python -m src.layer1_fraud_detection.train --transactions data\real\real_transactions.csv

# 5. Score data baru
python scripts\score_real_data.py --input data\real\imported_transactions.csv

# 6. Generate LTKM otomatis via API
python -m uvicorn src.api.main:app --port 8000
# Browser: http://localhost:8000/docs -> POST /v1/reports/ltkm/auto/{wallet_id}
```

---

## 5) Daftar Sumber Data Publik untuk Eksperimen

| Sumber | URL | Kegunaan |
|--------|-----|----------|
| OFAC SDN | treasury.gov/ofac/downloads/sdn.csv | Sanctions list (sudah otomatis) |
| UN Sanctions | scsanctions.un.org/resources/xml/en/consolidated.xml | UN consolidated list |
| EU Sanctions | webgate.ec.europa.eu/fsd/fsf/public | EU consolidated list |
| Etherscan | etherscan.io | Ethereum on-chain (sudah otomatis) |
| Chainabuse | chainabuse.com | Crowdsourced scam wallets |
| BscScan | bscscan.com | BNB Chain (mirip Etherscan) |
| Polygonscan | polygonscan.com | Polygon (mirip Etherscan) |
| CryptoScamDB | cryptoscamdb.org/api | Public scam database |
| PPATK DTTOT | restricted | Daftar Terduga Teroris (perlu MoU) |

---

## 6) Catatan Compliance

- **UU PDP No.27/2022**: data nasabah bank yang diimpor harus diminimalisasi — sistem ini hanya menyimpan ID rekening pseudonimous, bukan PII lengkap.
- **POJK No.12/2024**: rekomendasi melakukan validasi model di lingkungan terbatas (sandbox) sebelum deployment produksi.
- **PPATK**: submission LTKM/LTKT resmi via API GRIPS hanya bisa dilakukan oleh lembaga pelapor yang sudah ber-MoU dengan PPATK.
