"""Review & Approval module.

Responsibility: hold drafts, let the teacher edit them and approve them.
Prototype label: BUILT - as designed. Owns the 'reports' table.
Safety mitigations (risk register): a report cannot be approved until it has
been opened and all warnings are resolved, and it cannot be shared until approved.
"""
import json
import sqlite3
from dataclasses import asdict
from datetime import datetime

from ai_provider.base import DraftItem, DraftReport
from reports.check import DraftWarning


class ApprovalError(Exception):
    pass


def _draft_to_json(draft):
    return json.dumps(asdict(draft))


def _draft_from_json(text):
    data = json.loads(text)
    return DraftReport(
        doing_well=[DraftItem(**item) for item in data["doing_well"]],
        working_on=[DraftItem(**item) for item in data["working_on"]],
        practise_next=[DraftItem(**item) for item in data["practise_next"]],
    )


class ReviewService:
    # Interface: approve(report_id, teacher_id)

    def __init__(self, db_path="splashback.db"):
        self._db_path = db_path
        with self._connect() as conn:
            conn.execute(
                """CREATE TABLE IF NOT EXISTS reports (
                       report_id   INTEGER PRIMARY KEY AUTOINCREMENT,
                       child_id    TEXT NOT NULL,
                       lesson_id   TEXT NOT NULL,
                       draft       TEXT NOT NULL,
                       warnings    TEXT NOT NULL,
                       opened      INTEGER NOT NULL DEFAULT 0,
                       status      TEXT NOT NULL DEFAULT 'draft',
                       approved_by TEXT,
                       approved_at TEXT,
                       UNIQUE (child_id, lesson_id)
                   )"""
            )

    def _connect(self):
        conn = sqlite3.connect(self._db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def submit_draft(self, child_id, lesson_id, draft, warnings):
        # Store a new draft (replacing any earlier draft for this child and lesson)
        with self._connect() as conn:
            conn.execute(
                "INSERT OR REPLACE INTO reports (child_id, lesson_id, draft, warnings) "
                "VALUES (?, ?, ?, ?)",
                (child_id, lesson_id, _draft_to_json(draft),
                 json.dumps([asdict(w) for w in warnings])),
            )

    def get_report(self, child_id, lesson_id):
        with self._connect() as conn:
            row = conn.execute("SELECT * FROM reports WHERE child_id = ? AND lesson_id = ?",
                               (child_id, lesson_id)).fetchone()
        if row is None:
            return None
        report: dict = dict(row)
        report["draft"] = _draft_from_json(row["draft"])
        report["warnings"] = [DraftWarning(**w) for w in json.loads(row["warnings"])]
        return report

    def mark_opened(self, report_id):
        with self._connect() as conn:
            conn.execute("UPDATE reports SET opened = 1 WHERE report_id = ?", (report_id,))

    def update_draft(self, report_id, draft, warnings):
        """Save the teacher's edited draft along with its re-checked warnings."""
        with self._connect() as conn:
            conn.execute(
                "UPDATE reports SET draft = ?, warnings = ?, status = 'draft' WHERE report_id = ?",
                (_draft_to_json(draft), json.dumps([asdict(w) for w in warnings]), report_id),
            )

    def approve(self, report_id, teacher_id):
        with self._connect() as conn:
            row = conn.execute("SELECT opened, warnings FROM reports WHERE report_id = ?",
                               (report_id,)).fetchone()
            if row is None:
                raise ApprovalError("Report not found")
            if not row["opened"]:
                raise ApprovalError("Open and read the report before approving it")
            if json.loads(row["warnings"]):
                raise ApprovalError("Resolve all warnings before approving")
            conn.execute(
                "UPDATE reports SET status = 'approved', approved_by = ?, approved_at = ? "
                "WHERE report_id = ?",
                (teacher_id, datetime.now().isoformat(timespec="seconds"), report_id),
            )

    def is_shareable(self, report_id):
        with self._connect() as conn:
            row = conn.execute("SELECT status FROM reports WHERE report_id = ?",
                               (report_id,)).fetchone()
        return row is not None and row["status"] == "approved"