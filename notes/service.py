""" Lesson Notes module

Responsibility: saving and retrieving a teacher's note for each child per lesson.
Prototype label: BUILT - as designed, but using SQLite instead of PostgreSQL.
This module owns the 'notes' table; no other module reads it directly.
"""
import sqlite3
from dataclasses import dataclass
from datetime import datetime


@dataclass
class Note:
    child_id: str
    lesson_id: str
    text: str
    saved_at: str


class NotesService:
    # Interface: save_note(child_id, lesson_id, text) -> Note

    def __init__(self, db_path="splashback.db"):
        self._db_path = db_path
        with self._connect() as conn:
            conn.execute(
                """CREATE TABLE IF NOT EXISTS notes (
                       child_id  TEXT NOT NULL,
                       lesson_id TEXT NOT NULL,
                       text      TEXT NOT NULL,
                       saved_at  TEXT NOT NULL,
                       PRIMARY KEY (child_id, lesson_id)
                   )"""
            )

    def _connect(self):
        return sqlite3.connect(self._db_path)

    def save_note(self, child_id, lesson_id, text):
        if not text or not text.strip():
            raise ValueError("Note cannot be empty")
        note = Note(child_id, lesson_id, text.strip(), datetime.now().isoformat(timespec="seconds"))
        with self._connect() as conn:
            # Saving again for the same child and lesson replaces the earlier note.
            conn.execute(
                "INSERT OR REPLACE INTO notes VALUES (?, ?, ?, ?)",
                (note.child_id, note.lesson_id, note.text, note.saved_at),
            )
        return note

    def get_note(self, child_id, lesson_id):
        with self._connect() as conn:
            row = conn.execute(
                "SELECT child_id, lesson_id, text, saved_at FROM notes "
                "WHERE child_id = ? AND lesson_id = ?",
                (child_id, lesson_id),
            ).fetchone()
        return Note(*row) if row else None