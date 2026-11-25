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
    # FastAPI may open a dependency's connection in one worker thread and close it in another.
    # Each connection still serves a single request at a time, so crossing threads is safe.
    db = sqlite3.connect(path, timeout=5, check_same_thread=False)
    db.row_factory = sqlite3.Row
    db.execute("PRAGMA foreign_keys=ON")
    try:
        with db:
            yield db
    finally:
        db.close()


def initialize():
    with connection() as db:
        db.execute("PRAGMA journal_mode=WAL")
        db.execute("""CREATE TABLE IF NOT EXISTS utilisateurs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nom TEXT NOT NULL,
            email TEXT NOT NULL UNIQUE,
            mot_de_passe_hash TEXT NOT NULL,
            cree_le TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        )""")
        db.execute("""CREATE TABLE IF NOT EXISTS analyses (
            id TEXT PRIMARY KEY,
            title TEXT NOT NULL,
            created_at TEXT NOT NULL,
            score REAL NOT NULL CHECK(score >= 0 AND score <= 100),
            is_demo INTEGER NOT NULL DEFAULT 0,
            payload TEXT NOT NULL
        )""")
        columns = {row["name"] for row in db.execute("PRAGMA table_info(analyses)")}
        if "utilisateur_id" not in columns:
            db.execute("ALTER TABLE analyses ADD COLUMN utilisateur_id INTEGER REFERENCES utilisateurs(id)")
        db.execute("CREATE INDEX IF NOT EXISTS analyses_owner_date ON analyses(utilisateur_id, created_at DESC)")


def save(title: str, result: dict, is_demo: bool = False, utilisateur_id: int | None = None) -> dict:
    payload = json.dumps(result, ensure_ascii=False, allow_nan=False)
    if len(payload.encode("utf-8")) > 2 * 1024 * 1024:
        raise ValueError("Le rapport dépasse la taille maximale de 2 Mo.")
    item = {"id": str(uuid4()), "title": title, "created_at": datetime.now(UTC).isoformat(),
            "score": result["score"], "is_demo": is_demo}
    with connection() as db:
        db.execute("INSERT INTO analyses (id, title, created_at, score, is_demo, payload, utilisateur_id) VALUES (?, ?, ?, ?, ?, ?, ?)",
                   (item["id"], item["title"], item["created_at"], item["score"], is_demo, payload, utilisateur_id))
    return item


def list_saved(limit: int, offset: int, utilisateur_id: int) -> dict:
    with connection() as db:
        count = db.execute("SELECT COUNT(*) FROM analyses WHERE utilisateur_id = ?", (utilisateur_id,)).fetchone()[0]
        items = db.execute("SELECT id, title, created_at, score, is_demo FROM analyses WHERE utilisateur_id = ? ORDER BY created_at DESC, id "
                           "LIMIT ? OFFSET ?", (utilisateur_id, limit, offset)).fetchall()
    return {"items": [dict(row) for row in items], "total": count}


def get_saved(analysis_id: str, utilisateur_id: int) -> dict | None:
    with connection() as db:
        row = db.execute("SELECT * FROM analyses WHERE id = ? AND utilisateur_id = ?", (analysis_id, utilisateur_id)).fetchone()
    if row is None:
        return None
    item = dict(row)
    item.pop("utilisateur_id", None)
    item["result"] = json.loads(item.pop("payload"))
    return item


def delete_saved(analysis_id: str, utilisateur_id: int) -> bool:
    with connection() as db:
        deleted = db.execute("DELETE FROM analyses WHERE id = ? AND utilisateur_id = ?", (analysis_id, utilisateur_id)).rowcount
    return deleted == 1
