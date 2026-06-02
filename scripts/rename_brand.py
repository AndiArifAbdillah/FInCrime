"""Bulk rename 'FinCrime' → 'FinCrime' across project files.

Strategy:
    - Replace in source code files, docs, templates, configs
    - Skip binary files (.pyc, .joblib, .pt, .docx)
    - Skip __pycache__, .venv*, .git, data/models/, node_modules
    - Generate report of changes per file
"""
from __future__ import annotations
import sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ROOT = Path(__file__).resolve().parent.parent

# Files to skip entirely
SKIP_DIRS = {".venv", ".venv312", ".git", "__pycache__", "node_modules",
             "data/models", "data/mlruns", "data/sanctions", "data/pip-tmp",
             "data/pip-cache"}
SKIP_EXT = {".pyc", ".joblib", ".pt", ".docx", ".pdf", ".png", ".jpg",
            ".jpeg", ".gif", ".db", ".csv"}

# Replacements (order matters — longer phrases first)
REPLACEMENTS = [
    ("FinCrime", "FinCrime"),
]


def should_skip(path: Path) -> bool:
    parts = path.parts
    for skip in SKIP_DIRS:
        if skip in "/".join(parts).replace("\\", "/"):
            return True
    if path.suffix.lower() in SKIP_EXT:
        return True
    return False


def process(path: Path) -> int:
    try:
        text = path.read_text(encoding="utf-8")
    except (UnicodeDecodeError, PermissionError):
        return 0
    original = text
    count = 0
    for old, new in REPLACEMENTS:
        if old in text:
            n = text.count(old)
            text = text.replace(old, new)
            count += n
    if text != original:
        path.write_text(text, encoding="utf-8")
    return count


def main() -> None:
    changed_files = 0
    total_replacements = 0
    print("Scanning project for 'FinCrime' occurrences...")
    print()
    for path in ROOT.rglob("*"):
        if not path.is_file() or should_skip(path):
            continue
        n = process(path)
        if n > 0:
            rel = path.relative_to(ROOT)
            print(f"  {rel}  ({n} replacement{'s' if n != 1 else ''})")
            changed_files += 1
            total_replacements += n
    print()
    print(f"Done: {total_replacements} replacements across {changed_files} files.")


if __name__ == "__main__":
    main()
