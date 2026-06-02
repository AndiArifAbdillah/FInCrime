"""GraphSAGE model definition + simple GCN fallback if PyG missing."""
from __future__ import annotations

try:
    import torch
    import torch.nn as nn
    import torch.nn.functional as F
    from torch_geometric.nn import SAGEConv
    _PYG_AVAILABLE = True
except ImportError:
    _PYG_AVAILABLE = False


if _PYG_AVAILABLE:
    class GraphSAGE(nn.Module):
        """2-layer GraphSAGE for wallet fraud node-classification."""

        def __init__(self, in_dim: int, hidden_dim: int = 64, out_dim: int = 2, dropout: float = 0.3):
            super().__init__()
            self.conv1 = SAGEConv(in_dim, hidden_dim, aggr="mean")
            self.conv2 = SAGEConv(hidden_dim, hidden_dim, aggr="mean")
            self.dropout = dropout
            self.classifier = nn.Linear(hidden_dim, out_dim)

        def forward(self, x, edge_index):
            h = self.conv1(x, edge_index)
            h = F.relu(h)
            h = F.dropout(h, p=self.dropout, training=self.training)
            h = self.conv2(h, edge_index)
            h = F.relu(h)
            h = F.dropout(h, p=self.dropout, training=self.training)
            return self.classifier(h)

        @torch.no_grad()
        def fraud_proba(self, x, edge_index):
            self.eval()
            logits = self.forward(x, edge_index)
            return F.softmax(logits, dim=1)[:, 1]
else:
    # Fallback: simple MLP — only loses message-passing benefit.
    class GraphSAGE:  # type: ignore[no-redef]
        def __init__(self, *a, **k):
            raise ImportError("torch_geometric not installed. `pip install torch-geometric`")
