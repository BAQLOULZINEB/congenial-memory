"""Explicitly saved reports in a local SQLite database, separate from transient uploads."""
import json
import sqlite3
from contextlib import contextmanager
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

from backend.config import settings

ROOT = Path(__file__).resolve().parents[1]


def database_path() -> Path:
    path = Path(settings().database_path).expanduser()
    return path if path.is_absolute() else ROOT / path


@contextmanager
def connection():
    path = database_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    db = sqlite3.connect(path, timeout=5)
    db.row_factory = sqlite3.Row
    try:
        with db:
            yield db
    finally:
        db.close()


def initialize():
    with connection() as db:
        db.execute("PRAGMA journal_mode=WAL")
        db.execute("""CREATE TABLE IF NOT EXISTS analyses (
            id TEXT PRIMARY KEY,
            title TEXT NOT NULL,
            created_at TEXT NOT NULL,
            score REAL NOT NULL CHECK(score >= 0 AND score <= 100),
            is_demo INTEGER NOT NULL DEFAULT 0,
            payload TEXT NOT NULL
        )""")
        db.execute("CREATE INDEX IF NOT EXISTS analyses_created_at ON analyses(created_at DESC)")


def save(title: str, result: dict, is_demo: bool = False) -> dict:
    payload = json.dumps(result, ensure_ascii=False, allow_nan=False)
    if len(payload.encode("utf-8")) > 2 * 1024 * 1024:
        raise ValueError("Le rapport dépasse la taille maximale de 2 Mo.")
    item = {"id": str(uuid4()), "title": title, "created_at": datetime.now(UTC).isoformat(),
            "score": result["score"], "is_demo": is_demo}
    with connection() as db:
        db.execute("INSERT INTO analyses (id, title, created_at, score, is_demo, payload) VALUES (?, ?, ?, ?, ?, ?)",
                   (item["id"], item["title"], item["created_at"], item["score"], is_demo, payload))
    return item


def list_saved(limit: int, offset: int) -> dict:
    with connection() as db:
        count = db.execute("SELECT COUNT(*) FROM analyses").fetchone()[0]
        items = db.execute("SELECT id, title, created_at, score, is_demo FROM analyses ORDER BY created_at DESC, id "
                           "LIMIT ? OFFSET ?", (limit, offset)).fetchall()
    return {"items": [dict(row) for row in items], "total": count}


def get_saved(analysis_id: str) -> dict | None:
    with connection() as db:
        row = db.execute("SELECT * FROM analyses WHERE id = ?", (analysis_id,)).fetchone()
    if row is None:
        return None
    item = dict(row)
    item["result"] = json.loads(item.pop("payload"))
    return item


def delete_saved(analysis_id: str) -> bool:
    with connection() as db:
        deleted = db.execute("DELETE FROM analyses WHERE id = ?", (analysis_id,)).rowcount
    return deleted == 1
