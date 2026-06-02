"""Layer 2 — GNN tracing smoke tests."""
import pytest
import networkx as nx

from src.layer2_gnn_tracing.patterns import detect_layering, extract_subgraph


def _layering_graph() -> nx.DiGraph:
    """A→B→C→D chain of sub-50M IDR transfers (smurfing)."""
    G = nx.DiGraph()
    G.add_edge("A", "B", weight=45_000_000, tx_count=10)
    G.add_edge("B", "C", weight=47_000_000, tx_count=8)
    G.add_edge("C", "D", weight=46_000_000, tx_count=12)
    return G


def test_detect_layering_finds_chain():
    G = _layering_graph()
    ev = detect_layering(G, "A", min_chain_len=3)
    assert ev.smurfing_edges >= 3
    assert ev.layering_score > 0
    assert len(ev.chains) >= 1


def test_detect_layering_clean_graph():
    G = nx.DiGraph()
    G.add_edge("A", "B", weight=100_000_000)
    ev = detect_layering(G, "A")
    assert ev.smurfing_edges == 0


def test_extract_subgraph():
    G = _layering_graph()
    sub = extract_subgraph(G, "B", hops=1)
    assert "A" in sub and "C" in sub
