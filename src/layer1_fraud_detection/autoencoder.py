"""PyTorch autoencoder for unsupervised anomaly detection.

Falls back to a no-op stub when torch isn't installed, so Layer 1 can still
operate using Isolation Forest + rules only.
"""
from __future__ import annotations

from pathlib import Path

import numpy as np

try:
    import torch
    import torch.nn as nn
    from torch.utils.data import DataLoader, TensorDataset
    _TORCH_AVAILABLE = True
except ImportError:
    _TORCH_AVAILABLE = False


if _TORCH_AVAILABLE:
    class TabularAutoencoder(nn.Module):
        def __init__(self, n_features: int, hidden: int = 32, latent: int = 8, dropout: float = 0.1):
            super().__init__()
            self.encoder = nn.Sequential(
                nn.Linear(n_features, hidden),
                nn.ReLU(),
                nn.Dropout(dropout),
                nn.Linear(hidden, latent),
                nn.ReLU(),
            )
            self.decoder = nn.Sequential(
                nn.Linear(latent, hidden),
                nn.ReLU(),
                nn.Dropout(dropout),
                nn.Linear(hidden, n_features),
            )

        def forward(self, x):
            z = self.encoder(x)
            return self.decoder(z)


    def fit_autoencoder(X: np.ndarray, *, epochs: int = 30, batch_size: int = 256,
                        lr: float = 1e-3, latent: int = 8,
                        device: str | None = None):
        device = device or ("cuda" if torch.cuda.is_available() else "cpu")
        n_features = X.shape[1]
        model = TabularAutoencoder(n_features, latent=latent).to(device)
        opt = torch.optim.Adam(model.parameters(), lr=lr)
        loss_fn = nn.MSELoss()

        X_t = torch.tensor(X, dtype=torch.float32)
        loader = DataLoader(TensorDataset(X_t), batch_size=batch_size, shuffle=True)

        model.train()
        for ep in range(epochs):
            for (batch,) in loader:
                batch = batch.to(device)
                opt.zero_grad()
                recon = model(batch)
                loss = loss_fn(recon, batch)
                loss.backward()
                opt.step()

        model.eval()
        with torch.no_grad():
            recon = model(X_t.to(device)).cpu().numpy()
        err = np.mean((recon - X) ** 2, axis=1)
        threshold = float(np.quantile(err, 0.95))
        return model, threshold


    def reconstruction_error(model, X: np.ndarray, device: str | None = None) -> np.ndarray:
        device = device or ("cuda" if torch.cuda.is_available() else "cpu")
        model.eval()
        with torch.no_grad():
            x_t = torch.tensor(X, dtype=torch.float32).to(device)
            recon = model(x_t).cpu().numpy()
        return np.mean((recon - X) ** 2, axis=1)


    def save_autoencoder(model, path: Path, threshold: float, n_features: int):
        torch.save(
            {"state_dict": model.state_dict(),
             "threshold": threshold,
             "n_features": n_features},
            path,
        )


    def load_autoencoder(path: Path):
        blob = torch.load(path, map_location="cpu", weights_only=True)
        model = TabularAutoencoder(blob["n_features"])
        model.load_state_dict(blob["state_dict"])
        model.eval()
        return model, float(blob["threshold"])

else:
    # ---------- Fallback stubs (no PyTorch) ----------
    # Layer 1 still works using IsolationForest + rules; the autoencoder is skipped.
    class TabularAutoencoder:  # type: ignore[no-redef]
        pass

    def fit_autoencoder(*a, **k):
        raise ImportError(
            "PyTorch not installed — cannot fit the autoencoder. "
            "Install torch or use IsolationForest only via "
            "`train(..., use_autoencoder=False)`."
        )

    def reconstruction_error(*a, **k):
        raise ImportError("PyTorch not installed")

    def save_autoencoder(*a, **k):
        raise ImportError("PyTorch not installed")

    def load_autoencoder(*a, **k):
        raise ImportError("PyTorch not installed")


def torch_available() -> bool:
    return _TORCH_AVAILABLE
