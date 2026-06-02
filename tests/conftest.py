"""Pytest fixtures — generate small sample data on demand."""
from __future__ import annotations

from pathlib import Path

import pytest


@pytest.fixture(scope="session")
def sample_dir(tmp_path_factory) -> Path:
    out = tmp_path_factory.mktemp("fincrime-sample")
    from scripts.generate_sample_data import main as gen
    gen(out, n_individuals=200, n_corp=30, n_wallets=100, n_tx=500)
    return out
