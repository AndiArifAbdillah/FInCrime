"""Train the GraphSAGE model for crypto wallet fraud classification."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np

from src.common.config import settings
from src.common.logger import get_logger
from src.common.utils import ensure_model_dir
from .graph_builder import build_pyg_graph

log = get_logger("layer2.train")

MODEL_FILE = "layer2_graphsage.pt"
META_FILE = "layer2_graphsage.meta.json"


def train(edges_csv: Path, entities_csv: Path,
          model_dir: Path | None = None,
          epochs: int = 50,
          hidden_dim: int = 64,
          lr: float = 0.01) -> dict:
    import torch
    import torch.nn.functional as F
    from sklearn.metrics import roc_auc_score, average_precision_score, f1_score
    from .graphsage_model import GraphSAGE

    model_dir = model_dir or ensure_model_dir()
    log.info("layer2.train.start", edges=str(edges_csv), entities=str(entities_csv))

    data, bundle = build_pyg_graph(edges_csv, entities_csv)
    device = "cuda" if torch.cuda.is_available() else "cpu"
    data = data.to(device)
    in_dim = data.x.shape[1]

    model = GraphSAGE(in_dim, hidden_dim=hidden_dim).to(device)
    opt = torch.optim.Adam(model.parameters(), lr=lr, weight_decay=5e-4)

    # train/val split on labeled nodes
    labeled = bundle.labels >= 0
    idx = np.where(labeled)[0]
    np.random.seed(42)
    np.random.shuffle(idx)
    split = int(0.8 * len(idx))
    train_idx = torch.tensor(idx[:split], dtype=torch.long, device=device)
    val_idx = torch.tensor(idx[split:], dtype=torch.long, device=device)

    # class weights
    y_train = data.y[train_idx].cpu().numpy()
    pos = int(y_train.sum())
    neg = int(len(y_train) - pos)
    weight = torch.tensor([1.0, max(1.0, neg / max(pos, 1))], device=device)

    best_auc = 0.0
    for ep in range(1, epochs + 1):
        model.train()
        opt.zero_grad()
        logits = model(data.x, data.edge_index)
        loss = F.cross_entropy(logits[train_idx], data.y[train_idx], weight=weight)
        loss.backward()
        opt.step()

        if ep % 5 == 0 or ep == epochs:
            model.eval()
            with torch.no_grad():
                proba = F.softmax(model(data.x, data.edge_index), dim=1)[:, 1].cpu().numpy()
            y_val = data.y[val_idx].cpu().numpy()
            p_val = proba[val_idx.cpu().numpy()]
            try:
                auc = roc_auc_score(y_val, p_val)
                pr = average_precision_score(y_val, p_val)
            except ValueError:
                auc, pr = float("nan"), float("nan")
            log.info("layer2.train.epoch", epoch=ep, loss=float(loss.detach()),
                     val_auc=float(auc), val_pr=float(pr))
            if auc > best_auc:
                best_auc = float(auc)
                torch.save({
                    "state_dict": model.state_dict(),
                    "in_dim": in_dim,
                    "hidden_dim": hidden_dim,
                }, model_dir / MODEL_FILE)

    meta = {
        "best_val_auc": best_auc,
        "epochs": epochs,
        "in_dim": in_dim,
        "hidden_dim": hidden_dim,
        "model_version": "0.1.0",
    }
    (model_dir / META_FILE).write_text(json.dumps(meta, indent=2))
    log.info("layer2.train.done", **meta)
    return meta


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--edges", type=Path,
                        default=settings.app_data_dir / "sample" / "crypto_edges.csv")
    parser.add_argument("--entities", type=Path,
                        default=settings.app_data_dir / "sample" / "entities.csv")
    parser.add_argument("--model-dir", type=Path, default=settings.app_models_dir)
    parser.add_argument("--epochs", type=int, default=50)
    args = parser.parse_args()
    train(args.edges, args.entities, args.model_dir, epochs=args.epochs)
