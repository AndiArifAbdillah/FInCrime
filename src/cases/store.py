"""SQLite-backed Case storage.

A 'Case' groups multiple Alerts under a single investigation handled by one
compliance officer. Cases progress through statuses: open → in_review → escalated →
reported → closed.
"""
from __future__ import annotations

import json
import sqlite3
from contextlib import contextmanager
from dataclasses import dataclass, field, asdict
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Optional

from src.common.config import settings
from src.common.logger import get_logger
from src.common.utils import make_id, now_iso

log = get_logger("cases.store")


class CaseStatus(str, Enum):
    OPEN = "open"
    IN_REVIEW = "in_review"
    ESCALATED = "escalated"
    REPORTED = "reported"
    CLOSED = "closed"


@dataclass
class AlertLink:
    alert_type: str       # "fraud_tx", "risk_entity", "trace_wallet"
    alert_ref: str        # tx_id / entity_id / wallet_id
    severity: str         # "low" | "medium" | "high" | "critical"
    score: float
    note: str = ""


@dataclass
class Case:
    case_id: str
    title: str
    subject_id: str             # main subject (wallet/entity)
    subject_type: str           # wallet|individual|corporate
    status: str
    assignee: str
    created_at: str
    updated_at: str
    description: str = ""
    alerts: list[AlertLink] = field(default_factory=list)
    notes: list[dict] = field(default_factory=list)
    report_ids: list[str] = field(default_factory=list)


# ============================================================
# Storage
# ============================================================
DEFAULT_DB = settings.app_data_dir / "fincrime_cases.db"


class CaseStore:
    def __init__(self, db_path: Optional[Path] = None):
        self.db_path = db_path or DEFAULT_DB
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_schema()

    @contextmanager
    def _conn(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        finally:
            conn.close()

    def _init_schema(self):
        with self._conn() as c:
            c.executescript("""
                CREATE TABLE IF NOT EXISTS cases (
                    case_id     TEXT PRIMARY KEY,
                    title       TEXT NOT NULL,
                    subject_id  TEXT NOT NULL,
                    subject_type TEXT,
                    status      TEXT NOT NULL,
                    assignee    TEXT,
                    description TEXT,
                    created_at  TEXT NOT NULL,
                    updated_at  TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS case_alerts (
                    case_id     TEXT NOT NULL,
                    alert_type  TEXT NOT NULL,
                    alert_ref   TEXT NOT NULL,
                    severity    TEXT,
                    score       REAL,
                    note        TEXT,
                    added_at    TEXT NOT NULL,
                    FOREIGN KEY (case_id) REFERENCES cases(case_id) ON DELETE CASCADE
                );

                CREATE TABLE IF NOT EXISTS case_notes (
                    case_id     TEXT NOT NULL,
                    author      TEXT,
                    note        TEXT,
                    created_at  TEXT NOT NULL,
                    FOREIGN KEY (case_id) REFERENCES cases(case_id) ON DELETE CASCADE
                );

                CREATE TABLE IF NOT EXISTS case_reports (
                    case_id     TEXT NOT NULL,
                    report_id   TEXT NOT NULL,
                    PRIMARY KEY (case_id, report_id),
                    FOREIGN KEY (case_id) REFERENCES cases(case_id) ON DELETE CASCADE
                );

                CREATE INDEX IF NOT EXISTS idx_cases_status ON cases(status);
                CREATE INDEX IF NOT EXISTS idx_cases_subject ON cases(subject_id);
            """)

    # ----- CRUD -----
    def create(self, *, title: str, subject_id: str,
               subject_type: str = "wallet", assignee: str = "unassigned",
               description: str = "") -> Case:
        case_id = f"CASE-{datetime.utcnow().strftime('%Y%m%d')}-{make_id('C')[:8].upper()}"
        ts = now_iso()
        with self._conn() as c:
            c.execute(
                "INSERT INTO cases (case_id, title, subject_id, subject_type, status, "
                "assignee, description, created_at, updated_at) "
                "VALUES (?,?,?,?,?,?,?,?,?)",
                (case_id, title, subject_id, subject_type, CaseStatus.OPEN.value,
                 assignee, description, ts, ts),
            )
        log.info("case.created", case_id=case_id, subject=subject_id)
        return Case(case_id=case_id, title=title, subject_id=subject_id,
                    subject_type=subject_type, status=CaseStatus.OPEN.value,
                    assignee=assignee, description=description,
                    created_at=ts, updated_at=ts)

    def list(self, status: Optional[str] = None, limit: int = 50) -> list[Case]:
        with self._conn() as c:
            if status:
                rows = c.execute(
                    "SELECT * FROM cases WHERE status=? ORDER BY updated_at DESC LIMIT ?",
                    (status, limit)).fetchall()
            else:
                rows = c.execute(
                    "SELECT * FROM cases ORDER BY updated_at DESC LIMIT ?",
                    (limit,)).fetchall()
        return [self._row_to_case(r) for r in rows]

    def get(self, case_id: str) -> Optional[Case]:
        with self._conn() as c:
            row = c.execute("SELECT * FROM cases WHERE case_id=?", (case_id,)).fetchone()
            if not row:
                return None
            case = self._row_to_case(row)
            case.alerts = [
                AlertLink(alert_type=r["alert_type"], alert_ref=r["alert_ref"],
                          severity=r["severity"] or "", score=r["score"] or 0.0,
                          note=r["note"] or "")
                for r in c.execute("SELECT * FROM case_alerts WHERE case_id=?",
                                   (case_id,)).fetchall()
            ]
            case.notes = [
                {"author": r["author"], "note": r["note"],
                 "created_at": r["created_at"]}
                for r in c.execute("SELECT * FROM case_notes WHERE case_id=? "
                                   "ORDER BY created_at", (case_id,)).fetchall()
            ]
            case.report_ids = [
                r["report_id"]
                for r in c.execute("SELECT report_id FROM case_reports WHERE case_id=?",
                                   (case_id,)).fetchall()
            ]
            return case

    def _row_to_case(self, r: sqlite3.Row) -> Case:
        return Case(
            case_id=r["case_id"], title=r["title"],
            subject_id=r["subject_id"], subject_type=r["subject_type"] or "",
            status=r["status"], assignee=r["assignee"] or "",
            description=r["description"] or "",
            created_at=r["created_at"], updated_at=r["updated_at"],
        )

    def update_status(self, case_id: str, status: str) -> bool:
        with self._conn() as c:
            cur = c.execute("UPDATE cases SET status=?, updated_at=? WHERE case_id=?",
                            (status, now_iso(), case_id))
            return cur.rowcount > 0

    def assign(self, case_id: str, assignee: str) -> bool:
        with self._conn() as c:
            cur = c.execute("UPDATE cases SET assignee=?, updated_at=? WHERE case_id=?",
                            (assignee, now_iso(), case_id))
            return cur.rowcount > 0

    def add_alert(self, case_id: str, alert: AlertLink) -> None:
        with self._conn() as c:
            c.execute(
                "INSERT INTO case_alerts (case_id, alert_type, alert_ref, severity, score, note, added_at) "
                "VALUES (?,?,?,?,?,?,?)",
                (case_id, alert.alert_type, alert.alert_ref, alert.severity,
                 alert.score, alert.note, now_iso()),
            )
            c.execute("UPDATE cases SET updated_at=? WHERE case_id=?",
                      (now_iso(), case_id))

    def add_note(self, case_id: str, author: str, note: str) -> None:
        with self._conn() as c:
            c.execute(
                "INSERT INTO case_notes (case_id, author, note, created_at) "
                "VALUES (?,?,?,?)",
                (case_id, author, note, now_iso()),
            )
            c.execute("UPDATE cases SET updated_at=? WHERE case_id=?",
                      (now_iso(), case_id))

    def link_report(self, case_id: str, report_id: str) -> None:
        with self._conn() as c:
            c.execute(
                "INSERT OR IGNORE INTO case_reports (case_id, report_id) VALUES (?,?)",
                (case_id, report_id),
            )
            c.execute("UPDATE cases SET updated_at=? WHERE case_id=?",
                      (now_iso(), case_id))

    def stats(self) -> dict:
        with self._conn() as c:
            total = c.execute("SELECT COUNT(*) FROM cases").fetchone()[0]
            by_status = {r["status"]: r["c"] for r in
                         c.execute("SELECT status, COUNT(*) AS c FROM cases GROUP BY status").fetchall()}
        return {"total": total, "by_status": by_status}
