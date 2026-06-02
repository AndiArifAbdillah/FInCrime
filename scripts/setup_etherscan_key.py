"""Interactive setup helper untuk Etherscan API key.

Usage:
    .\fc python scripts/setup_etherscan_key.py
"""
from __future__ import annotations
import sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import httpx

PROJECT_ROOT = Path(__file__).resolve().parent.parent
ENV_FILE = PROJECT_ROOT / ".env"
ENV_EXAMPLE = PROJECT_ROOT / ".env.example"


def print_instructions():
    print()
    print("=" * 70)
    print("  ETHERSCAN API KEY SETUP — 3 LANGKAH SEDERHANA")
    print("=" * 70)
    print()
    print("LANGKAH 1: Daftar gratis di Etherscan")
    print("-" * 70)
    print("  1. Buka browser: https://etherscan.io/register")
    print("  2. Isi email + password → submit")
    print("  3. Cek email kamu untuk link verifikasi → klik")
    print()
    print("LANGKAH 2: Generate API Key")
    print("-" * 70)
    print("  1. Login: https://etherscan.io/login")
    print("  2. Buka API Keys page: https://etherscan.io/myapikey")
    print("  3. Klik tombol '+ Add'")
    print("  4. Beri nama (mis: 'FinCrime') → 'Create New API Key'")
    print("  5. Copy key yang muncul (format: 32 karakter hex)")
    print()
    print("LANGKAH 3: Paste key di prompt berikut, atau Ctrl+C untuk skip")
    print("-" * 70)
    print()


def update_env_file(key: str) -> Path:
    """Update .env file dengan ETHERSCAN_API_KEY."""
    # Pastikan .env ada (copy dari .env.example kalau belum)
    if not ENV_FILE.exists():
        if ENV_EXAMPLE.exists():
            ENV_FILE.write_text(ENV_EXAMPLE.read_text(encoding="utf-8"), encoding="utf-8")
            print(f"  ✓ .env dibuat dari .env.example")
        else:
            ENV_FILE.write_text("", encoding="utf-8")

    text = ENV_FILE.read_text(encoding="utf-8")
    lines = text.splitlines()
    new_line = f"ETHERSCAN_API_KEY={key}"
    found = False
    for i, line in enumerate(lines):
        if line.startswith("ETHERSCAN_API_KEY="):
            lines[i] = new_line
            found = True
            break
    if not found:
        lines.append(new_line)
    ENV_FILE.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return ENV_FILE


def verify_key(key: str) -> bool:
    """Test key dengan call API ringan."""
    print()
    print("  Verifying key with Etherscan...")
    try:
        r = httpx.get(
            "https://api.etherscan.io/api",
            params={
                "module": "stats", "action": "ethsupply", "apikey": key,
            },
            timeout=10,
        )
        data = r.json()
        if data.get("status") == "1":
            return True
        print(f"  ❌ Etherscan menolak key: {data.get('message')} — {data.get('result')}")
        return False
    except Exception as e:
        print(f"  ⚠ Network error: {e}")
        print(f"     (Key tetap disimpan, coba lagi nanti)")
        return False


def main():
    print_instructions()

    try:
        key = input("Paste Etherscan API Key disini: ").strip()
    except KeyboardInterrupt:
        print("\n\n  Skip — kamu bisa set manual nanti di .env:")
        print("    ETHERSCAN_API_KEY=YourKeyHere\n")
        return

    if not key:
        print("\n  ❌ Key kosong. Skip.\n")
        return

    if len(key) < 20:
        print(f"\n  ⚠ Key terlalu pendek ({len(key)} char). Etherscan key biasanya 32+ char.")
        confirm = input("  Tetap simpan? (y/N): ").strip().lower()
        if confirm != "y":
            print("\n  Skip.\n")
            return

    env_path = update_env_file(key)
    print(f"\n  ✓ Key disimpan di {env_path}")

    if verify_key(key):
        print(f"\n  ✓ Key VALID — Etherscan terhubung")
        print()
        print("=" * 70)
        print("  ✅ SETUP BERHASIL!")
        print("=" * 70)
        print()
        print("  Restart server lalu coba di tab Multi-chain Crypto:")
        print()
        print("    1. Di terminal yang jalankan '.\\fc web':")
        print("       - Tekan Ctrl+C")
        print("       - Jalankan: .\\fc web")
        print()
        print("    2. Browser refresh (Ctrl+F5)")
        print()
        print("    3. Tab 'Multi-chain Crypto' → paste address ETH real:")
        print("       0x8589427373d6d84e98730d7795d8f6f8731fda16  (Tornado Cash)")
        print()
        print("    4. Klik 'Fetch' → akan tampil 15 transaksi REAL!")
        print()


if __name__ == "__main__":
    main()
