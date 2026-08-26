from __future__ import annotations

import json
import sqlite3
from pathlib import Path

from .models import Workflow


class WorkflowStore:
    def __init__(self, path: str):
        self.path = path
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        with self._connect() as db:
            db.execute(
                "CREATE TABLE IF NOT EXISTS workflows (id TEXT PRIMARY KEY, payload TEXT NOT NULL)"
            )

    def _connect(self) -> sqlite3.Connection:
        return sqlite3.connect(self.path)

    def save(self, workflow: Workflow) -> None:
        payload = workflow.model_dump_json()
        with self._connect() as db:
            db.execute(
                "INSERT INTO workflows(id,payload) VALUES(?,?) "
                "ON CONFLICT(id) DO UPDATE SET payload=excluded.payload",
                (workflow.id, payload),
            )

    def get(self, workflow_id: str) -> Workflow | None:
        with self._connect() as db:
            row = db.execute("SELECT payload FROM workflows WHERE id=?", (workflow_id,)).fetchone()
        return Workflow.model_validate(json.loads(row[0])) if row else None

    def list(self) -> list[Workflow]:
        with self._connect() as db:
            rows = db.execute("SELECT payload FROM workflows ORDER BY rowid DESC").fetchall()
        return [Workflow.model_validate(json.loads(row[0])) for row in rows]
