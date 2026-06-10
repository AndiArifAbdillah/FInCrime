"""Feature & prediction drift detection.

PSI (Population Stability Index) and KS (Kolmogorov-Smirnov) statistic are the
two most common metrics used in model monitoring. Rules of thumb:

    PSI < 0.10  : no significant population change
    PSI 0.10-0.25 : moderate change
    PSI >= 0.25 : significant change (retraining advised)

    KS statistic > 0.20 : distributions meaningfully different
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

import numpy as np


@dataclass
class FeatureDrift:
    feature: str
    psi: float
    ks_stat: float
    ks_pvalue: float
    severity: str          # "low" | "medium" | "high"


@dataclass
class DriftReport:
    overall_psi: float
    overall_severity: str
    feature_drifts: list[FeatureDrift]
    n_baseline: int
    n_current: int


def compute_psi(baseline: np.ndarray, current: np.ndarray,
                n_bins: int = 10) -> float:
    """Population Stability Index between two 1D arrays."""
    baseline = np.asarray(baseline, dtype=float)
    current = np.asarray(current, dtype=float)
    baseline = baseline[np.isfinite(baseline)]
    current = current[np.isfinite(current)]
    if len(baseline) == 0 or len(current) == 0:
        return 0.0
    # Use baseline quantiles as bin edges
    edges = np.unique(np.quantile(baseline, np.linspace(0, 1, n_bins + 1)))
    if len(edges) < 2:
        return 0.0
    bh, _ = np.histogram(baseline, bins=edges)
    ch, _ = np.histogram(current, bins=edges)
    bh = bh / max(bh.sum(), 1)
    ch = ch / max(ch.sum(), 1)
    eps = 1e-6
    return float(np.sum((ch - bh) * np.log((ch + eps) / (bh + eps))))


def compute_ks_stat(baseline: np.ndarray, current: np.ndarray) -> tuple[float, float]:
    """Two-sample KS test statistic + approximate p-value."""
    from scipy.stats import ks_2samp
    baseline = np.asarray(baseline, dtype=float)
    current = np.asarray(current, dtype=float)
    baseline = baseline[np.isfinite(baseline)]
    current = current[np.isfinite(current)]
    if len(baseline) < 2 or len(current) < 2:
        return 0.0, 1.0
    result = ks_2samp(baseline, current)
    return float(result.statistic), float(result.pvalue)


def _severity(psi: float, ks: float) -> str:
    if psi >= 0.25 or ks >= 0.30:
        return "high"
    if psi >= 0.10 or ks >= 0.15:
        return "medium"
    return "low"


def compute_feature_drift_report(baseline_df, current_df,
                                  features: Optional[list[str]] = None) -> DriftReport:
    """Compute drift across multiple numeric features.

    baseline_df / current_df: pandas DataFrame
    features: list of column names to test (default: all numeric).
    """
    import pandas as pd
    cols = features or [c for c in baseline_df.columns if
                        c in current_df.columns and
                        pd.api.types.is_numeric_dtype(baseline_df[c])]
    drifts: list[FeatureDrift] = []
    for col in cols:
        b = baseline_df[col].values
        c = current_df[col].values
        psi = compute_psi(b, c)
        ks, pval = compute_ks_stat(b, c)
        drifts.append(FeatureDrift(
            feature=col, psi=round(psi, 4),
            ks_stat=round(ks, 4), ks_pvalue=round(pval, 4),
            severity=_severity(psi, ks),
        ))
    drifts.sort(key=lambda f: -f.psi)
    overall = float(np.mean([d.psi for d in drifts])) if drifts else 0.0
    return DriftReport(
        overall_psi=round(overall, 4),
        overall_severity=_severity(overall, 0),
        feature_drifts=drifts,
        n_baseline=len(baseline_df),
        n_current=len(current_df),
    )
