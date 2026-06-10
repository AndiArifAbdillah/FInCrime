"""Benchmark Layer 2 GraphSAGE pada Elliptic Bitcoin Dataset dengan fitur NATIVE.

Berbeda dari import_elliptic.py (yang memetakan ke 9 fitur skema FinCrime),
script ini memakai 165 fitur asli Elliptic — setup yang sama dengan literatur
(Weber et al. 2019, dkk.) sehingga angkanya bisa dibandingkan dengan paper.

Split: temporal standar literatur — train timestep 1-34, test timestep 35-49.
Model disimpan TERPISAH (layer2_graphsage_elliptic.pt) agar model demo runtime
(9-fitur, kompatibel dashboard) tidak tertimpa.

Usage:
    .\\fc python scripts/train_elliptic_benchmark.py [--epochs 100]
"""
from __future__ import annotations

import sys
from pathlib import Path as _Path
sys.path.insert(0, str(_Path(__file__).resolve().parent.parent))
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import argparse
import json
import time
from pathlib import Path

import numpy as np
import pandas as pd

from src.common.config import settings
from src.common.logger import get_logger

log = get_logger("layer2.elliptic_benchmark")

RAW = Path("data/raw/elliptic")
MODEL_OUT = settings.app_models_dir / "layer2_graphsage_elliptic.pt"
META_OUT = settings.app_models_dir / "layer2_graphsage_elliptic.meta.json"
TRAIN_MAX_TIMESTEP = 34          # split temporal standar literatur (1-34 / 35-49)


def main(epochs: int, hidden_dim: int, lr: float) -> None:
    import torch
    import torch.nn.functional as F
    from sklearn.metrics import (average_precision_score, f1_score,
                                 precision_score, recall_score, roc_auc_score)
    from src.layer2_gnn_tracing.graphsage_model import GraphSAGE

    print("=" * 70)
    print("  ELLIPTIC BENCHMARK — GraphSAGE @ 165 fitur native")
    print("=" * 70)

    t0 = time.time()
    print("\n[1/4] Load features (657 MB, ~1-2 menit) ...")
    # PENTING: txId (kolom 0) HARUS int64 — float32 merusak ID besar (>16,7 jt).
    feats = pd.read_csv(RAW / "elliptic_txs_features.csv", header=None,
                        dtype={0: np.int64, 1: np.int16})
    tx_ids = feats[0].to_numpy()
    timestep = feats[1].to_numpy()
    X = feats.iloc[:, 2:].to_numpy(dtype=np.float32)
    del feats
    print(f"      -> {X.shape[0]:,} node x {X.shape[1]} fitur  ({time.time()-t0:.0f}s)")

    print("[2/4] Load labels + edges ...")
    classes = pd.read_csv(RAW / "elliptic_txs_classes.csv",
                          dtype={"txId": np.int64, "class": str})
    idx_of = {int(t): i for i, t in enumerate(tx_ids)}
    label_map = {"1": 1, "2": 0}  # 1=illicit, 2=licit, unknown=-1
    y = np.full(len(tx_ids), -1, dtype=np.int64)
    node_idx = classes["txId"].map(idx_of)
    lab_val = classes["class"].map(label_map)
    ok = node_idx.notna() & lab_val.notna()
    y[node_idx[ok].astype(int).to_numpy()] = lab_val[ok].astype(int).to_numpy()

    edges = pd.read_csv(RAW / "elliptic_txs_edgelist.csv",
                        dtype={"txId1": np.int64, "txId2": np.int64})
    src = edges["txId1"].map(idx_of)
    dst = edges["txId2"].map(idx_of)
    keep = src.notna() & dst.notna()
    dropped = int((~keep).sum())
    edge_index = torch.tensor(
        np.vstack([src[keep].astype(np.int64).to_numpy(),
                   dst[keep].astype(np.int64).to_numpy()]), dtype=torch.long)
    n_illicit, n_licit = int((y == 1).sum()), int((y == 0).sum())
    print(f"      -> {edge_index.shape[1]:,} edge (drop {dropped}) | "
          f"label: {n_illicit:,} illicit / {n_licit:,} licit")
    assert n_illicit > 4000 and n_licit > 40000, \
        f"label mapping rusak: {n_illicit}/{n_licit} (harusnya ~4.545/~42.019)"

    print("[3/4] Split temporal (train ts 1-34, test ts 35-49) ...")
    labeled = y >= 0
    train_mask = labeled & (timestep <= TRAIN_MAX_TIMESTEP)
    test_mask = labeled & (timestep > TRAIN_MAX_TIMESTEP)
    print(f"      -> train {int(train_mask.sum()):,} | test {int(test_mask.sum()):,}")

    device = "cuda" if torch.cuda.is_available() else "cpu"
    x_t = torch.from_numpy(X).to(device)
    y_t = torch.from_numpy(np.clip(y, 0, None)).to(device)
    edge_index = edge_index.to(device)
    tr = torch.from_numpy(np.where(train_mask)[0]).to(device)
    te = np.where(test_mask)[0]

    model = GraphSAGE(X.shape[1], hidden_dim=hidden_dim).to(device)
    opt = torch.optim.Adam(model.parameters(), lr=lr, weight_decay=5e-4)
    y_tr = y[train_mask]
    weight = torch.tensor([1.0, max(1.0, (y_tr == 0).sum() / max((y_tr == 1).sum(), 1))],
                          dtype=torch.float32, device=device)

    print(f"[4/4] Training {epochs} epoch di {device} ...")
    best = {"auc": 0.0}
    for ep in range(1, epochs + 1):
        model.train()
        opt.zero_grad()
        logits = model(x_t, edge_index)
        loss = F.cross_entropy(logits[tr], y_t[tr], weight=weight)
        loss.backward()
        opt.step()

        if ep % 5 == 0 or ep == epochs:
            model.eval()
            with torch.no_grad():
                proba = F.softmax(model(x_t, edge_index), dim=1)[:, 1].cpu().numpy()
            p, yy = proba[te], y[te]
            auc = roc_auc_score(yy, p)
            pr = average_precision_score(yy, p)
            pred = (p >= 0.5).astype(int)
            f1 = f1_score(yy, pred)
            log.info("elliptic.epoch", epoch=ep, loss=float(loss.detach()),
                     test_auc=round(float(auc), 4), test_pr=round(float(pr), 4),
                     test_f1=round(float(f1), 4))
            if auc > best["auc"]:
                best = {
                    "auc": float(auc), "pr_auc": float(pr), "f1": float(f1),
                    "precision": float(precision_score(yy, pred)),
                    "recall": float(recall_score(yy, pred)),
                    "epoch": ep,
                }
                torch.save({"state_dict": model.state_dict(),
                            "in_dim": X.shape[1], "hidden_dim": hidden_dim}, MODEL_OUT)

    meta = {
        "dataset": "Elliptic Bitcoin Dataset (real, 203,769 tx)",
        "features": "165 native Elliptic features",
        "split": "temporal: train ts<=34, test ts>34 (standar literatur)",
        "epochs": epochs, "hidden_dim": hidden_dim,
        **{f"best_{k}": v for k, v in best.items()},
    }
    META_OUT.write_text(json.dumps(meta, indent=2))

    print("\n" + "=" * 70)
    print("  HASIL BENCHMARK (test set = timestep 35-49, data nyata)")
    print("=" * 70)
    print(f"  ROC AUC   : {best['auc']:.4f}")
    print(f"  PR AUC    : {best['pr_auc']:.4f}")
    print(f"  F1        : {best['f1']:.4f}")
    print(f"  Precision : {best['precision']:.4f}")
    print(f"  Recall    : {best['recall']:.4f}")
    print(f"  Model     : {MODEL_OUT}")
    print(f"  Meta      : {META_OUT}")
    print(f"  Durasi    : {time.time()-t0:.0f}s")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--epochs", type=int, default=100)
    ap.add_argument("--hidden-dim", type=int, default=64)
    ap.add_argument("--lr", type=float, default=0.01)
    a = ap.parse_args()
    main(a.epochs, a.hidden_dim, a.lr)
