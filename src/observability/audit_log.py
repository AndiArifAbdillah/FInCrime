"""Immutable audit log — required by POJK No.12/2024 + UU PDP No.27/2022.

Append-only SQLite log of every prediction, report generation, and case change.
Used for:
    - Compliance audits (BI, OJK, PPATK on-site visits)
    - Forensic investigation
    - Model accountability (which model version made which decision)
"""
from __future__ import annotations

import json
import sqlite3
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Optional

from src.common.config import settings
from src.common.logger import get_logger
from src.common.utils import now_iso, make_id

log = get_logger("audit")

DEFAULT_DB = settings.app_data_dir / "fincrime_audit.db"


@dataclass
class AuditEvent:
    event_id: str
    event_type: str           # "prediction" | "report_generated" | "case_status_change" | "data_access" | ...
    actor: str                # "system" | user_id
    subject: str              # entity_id / report_id / case_id
    layer: str = ""           # "layer0" | "layer1" | "layer2" | "layer3" | "api"
    action: str = ""          # "score" | "create" | "update" | "delete" | "download"
    payload: dict | None = None  # diff or metadata
    model_version: str = ""
    timestamp: str = ""
    ip_address: str = ""


class AuditLog:
    """Append-only SQLite audit log. Never DELETE."""

    def __init__(self, db_path: Optional[Path] = None):
        self.db_path = db_path or DEFAULT_DB
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_schema()

    @contextmanager
    def _conn(self):
        conn = sqlite3.connect(self.db_path)
        try:
            yield conn
            conn.commit()
        finally:
            conn.close()

    def _init_schema(self):
        with self._conn() as c:
            c.executescript("""
                CREATE TABLE IF NOT EXISTS audit_events (
                    event_id        TEXT PRIMARY KEY,
                    event_type      TEXT NOT NULL,
                    actor           TEXT,
                    subject         TEXT,
                    layer           TEXT,
                    action          TEXT,
                    payload_json    TEXT,
                    model_version   TEXT,
                    timestamp       TEXT NOT NULL,
                    ip_address      TEXT
                );
                CREATE INDEX IF NOT EXISTS idx_audit_type_ts ON audit_events(event_type, timestamp);
                CREATE INDEX IF NOT EXISTS idx_audit_subject ON audit_events(subject);
                CREATE INDEX IF NOT EXISTS idx_audit_actor ON audit_events(actor);
            """)

    def record(self, *, event_type: str, actor: str = "system",
               subject: str = "", layer: str = "", action: str = "",
               payload: dict | None = None,
               model_version: str = "",
               ip_address: str = "") -> str:
        event_id = make_id("evt")
        with self._conn() as c:
            c.execute(
                "INSERT INTO audit_events "
                "(event_id, event_type, actor, subject, layer, action, payload_json, "
                "model_version, timestamp, ip_address) "
                "VALUES (?,?,?,?,?,?,?,?,?,?)",
                (event_id, event_type, actor, subject, layer, action,
                 json.dumps(payload) if payload else None,
                 model_version, now_iso(), ip_address),
            )
        return event_id

    def query(self, *, event_type: str | None = None,
              subject: str | None = None, actor: str | None = None,
              since: str | None = None, limit: int = 100) -> list[dict]:
        conds: list[str] = []
        args: list[Any] = []
        if event_type:
            conds.append("event_type = ?")
            args.append(event_type)
        if subject:
            conds.append("subject = ?")
            args.append(subject)
        if actor:
            conds.append("actor = ?")
            args.append(actor)
        if since:
            conds.append("timestamp >= ?")
            args.append(since)
        where = "WHERE " + " AND ".join(conds) if conds else ""
        args.append(limit)
        with self._conn() as c:
            c.row_factory = sqlite3.Row
            # `where` is assembled from fixed "col = ?" fragments only; all
            # user values are bound via ?-parameters below.
            rows = c.execute(
                f"SELECT * FROM audit_events {where} ORDER BY timestamp DESC LIMIT ?",  # nosec B608
                args,
            ).fetchall()
        out = []
        for r in rows:
            d = dict(r)
            if d.get("payload_json"):
                try:
                    d["payload"] = json.loads(d["payload_json"])
                except Exception:
                    d["payload"] = None
            d.pop("payload_json", None)
            out.append(d)
        return out

    def stats(self) -> dict:
        with self._conn() as c:
            total = c.execute("SELECT COUNT(*) FROM audit_events").fetchone()[0]
            by_type = dict(c.execute(
                "SELECT event_type, COUNT(*) FROM audit_events GROUP BY event_type"
            ).fetchall())
        return {"total": total, "by_type": by_type}


# Module-level singleton
audit_log = AuditLog()
