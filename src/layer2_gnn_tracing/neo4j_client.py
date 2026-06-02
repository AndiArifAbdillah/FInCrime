"""Thin Neo4j client for persisting/querying the wallet graph in production."""
from __future__ import annotations

from contextlib import contextmanager
from typing import Iterable

try:
    from neo4j import GraphDatabase, Driver
    _NEO4J_AVAILABLE = True
except ImportError:
    _NEO4J_AVAILABLE = False

from src.common.config import settings
from src.common.logger import get_logger

log = get_logger("layer2.neo4j")


class Neo4jClient:
    """Minimal client. No-ops gracefully if neo4j driver isn't installed."""

    def __init__(self, uri: str | None = None, user: str | None = None,
                 password: str | None = None):
        self.uri = uri or settings.neo4j_uri
        self.user = user or settings.neo4j_user
        self.password = password or settings.neo4j_password
        self._driver = None
        if _NEO4J_AVAILABLE:
            try:
                self._driver = GraphDatabase.driver(self.uri, auth=(self.user, self.password))
                self._driver.verify_connectivity()
                log.info("neo4j.connected", uri=self.uri)
            except Exception as e:
                log.warning("neo4j.unavailable", error=str(e))
                self._driver = None

    def close(self):
        if self._driver:
            self._driver.close()

    @contextmanager
    def session(self):
        if not self._driver:
            yield None
            return
        with self._driver.session() as s:
            yield s

    # ----- schema setup -----
    def setup_constraints(self) -> None:
        with self.session() as s:
            if not s:
                return
            s.run("CREATE CONSTRAINT wallet_id IF NOT EXISTS "
                  "FOR (w:Wallet) REQUIRE w.id IS UNIQUE")

    # ----- bulk ingest -----
    def upsert_wallets(self, wallets: Iterable[dict]) -> None:
        with self.session() as s:
            if not s:
                return
            s.run(
                """
                UNWIND $batch AS w
                MERGE (n:Wallet {id: w.id})
                SET n.chain = w.chain,
                    n.fraud_score = w.fraud_score,
                    n.is_known_bad = w.is_known_bad
                """,
                batch=list(wallets),
            )

    def upsert_edges(self, edges: Iterable[dict]) -> None:
        with self.session() as s:
            if not s:
                return
            s.run(
                """
                UNWIND $batch AS e
                MATCH (a:Wallet {id: e.src})
                MATCH (b:Wallet {id: e.dst})
                MERGE (a)-[r:TRANSFER]->(b)
                SET r.weight = e.weight,
                    r.tx_count = e.tx_count
                """,
                batch=list(edges),
            )

    # ----- query helpers -----
    def k_hop_neighbors(self, wallet_id: str, hops: int = 2) -> list[dict]:
        cypher = f"""
        MATCH path = (w:Wallet {{id: $id}})-[:TRANSFER*1..{hops}]-(n:Wallet)
        RETURN DISTINCT n.id AS id, n.fraud_score AS fraud_score
        """
        with self.session() as s:
            if not s:
                return []
            return [dict(r) for r in s.run(cypher, id=wallet_id)]
