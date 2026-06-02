"""Pattern detection (smurfing, layering) on the wallet graph."""
from __future__ import annotations

from dataclasses import dataclass

import networkx as nx


@dataclass
class LayeringEvidence:
    seed: str
    chains: list[list[str]]     # each chain is a list of wallet IDs
    smurfing_edges: int
    suspicious_value: float
    layering_score: float       # 0..1


def detect_layering(G: nx.DiGraph, seed: str, *, max_depth: int = 5,
                    min_chain_len: int = 3,
                    smurf_low: float = 40_000_000,
                    smurf_high: float = 49_999_999) -> LayeringEvidence:
    """Walk outwards from `seed` and collect chains that look like layering.

    A *layering chain* is a path of length >= min_chain_len where each hop's
    edge weight is within (smurf_low, smurf_high) — i.e., sub-50M IDR smurfed
    transfers chained across multiple hops to obscure provenance.
    """
    if seed not in G:
        return LayeringEvidence(seed=seed, chains=[], smurfing_edges=0,
                                suspicious_value=0.0, layering_score=0.0)

    chains: list[list[str]] = []
    smurf_edges = 0
    susp_value = 0.0

    def dfs(node: str, path: list[str], depth: int) -> None:
        nonlocal smurf_edges, susp_value
        if depth >= max_depth:
            if len(path) >= min_chain_len:
                chains.append(path.copy())
            return
        out_edges = list(G.out_edges(node, data=True))
        if not out_edges:
            if len(path) >= min_chain_len:
                chains.append(path.copy())
            return
        for _, nxt, data in out_edges:
            w = float(data.get("weight", 0))
            if smurf_low <= w <= smurf_high:
                smurf_edges += 1
                susp_value += w
                if nxt in path:  # no cycles
                    continue
                path.append(nxt)
                dfs(nxt, path, depth + 1)
                path.pop()
            else:
                if len(path) >= min_chain_len:
                    chains.append(path.copy())

    dfs(seed, [seed], 0)

    # Score: density of smurfed paths normalized
    # heuristic: tanh of evidence
    import math
    raw = smurf_edges * 0.15 + len(chains) * 0.25 + min(susp_value / 1e10, 1.0) * 0.5
    score = float(math.tanh(raw))
    return LayeringEvidence(seed=seed, chains=chains,
                            smurfing_edges=smurf_edges,
                            suspicious_value=susp_value,
                            layering_score=round(score, 4))


def extract_subgraph(G: nx.DiGraph, seed: str, hops: int = 2) -> nx.DiGraph:
    """Return the ego-net (forward + backward) within `hops` hops of `seed`."""
    if seed not in G:
        return nx.DiGraph()
    nodes = {seed}
    frontier = {seed}
    for _ in range(hops):
        nxt: set[str] = set()
        for n in frontier:
            nxt |= set(G.successors(n))
            nxt |= set(G.predecessors(n))
        nodes |= nxt
        frontier = nxt
    return G.subgraph(nodes).copy()
