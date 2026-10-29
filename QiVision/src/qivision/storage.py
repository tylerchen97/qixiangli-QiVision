"""SQLite 存储。默认不保存原始舌象图片(隐私),仅保存结构化结果。"""
from __future__ import annotations

import json
import sqlite3
import threading
from datetime import datetime, timezone
from pathlib import Path


class Storage:
    def __init__(self, db_path: str):
        if db_path != ":memory:":
            Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        self._conn = sqlite3.connect(db_path, check_same_thread=False)
        self._conn.row_factory = sqlite3.Row
        self._lock = threading.Lock()
        with self._lock:
            self._conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS sessions (
                    id TEXT PRIMARY KEY, user_id TEXT NOT NULL, created_at TEXT NOT NULL,
                    profile_json TEXT NOT NULL, result_json TEXT NOT NULL);
                CREATE INDEX IF NOT EXISTS idx_sessions_user ON sessions(user_id, created_at);
                CREATE TABLE IF NOT EXISTS feedback (
                    id INTEGER PRIMARY KEY AUTOINCREMENT, session_id TEXT NOT NULL,
                    created_at TEXT NOT NULL, data_json TEXT NOT NULL);
                """
            )

    @staticmethod
    def _now() -> str:
        return datetime.now(timezone.utc).isoformat(timespec="seconds")

    def save_session(self, sid: str, user_id: str, profile: dict, result: dict) -> None:
        with self._lock:
            self._conn.execute(
                "INSERT OR REPLACE INTO sessions VALUES (?,?,?,?,?)",
                (sid, user_id, self._now(), json.dumps(profile, ensure_ascii=False),
                 json.dumps(result, ensure_ascii=False)),
            )
            self._conn.commit()

    def get_session(self, sid: str) -> dict | None:
        with self._lock:
            row = self._conn.execute("SELECT * FROM sessions WHERE id=?", (sid,)).fetchone()
        if not row:
            return None
        return {
            "id": row["id"], "user_id": row["user_id"], "created_at": row["created_at"],
            "profile": json.loads(row["profile_json"]), "result": json.loads(row["result_json"]),
        }

    def user_history(self, user_id: str) -> list[dict]:
        with self._lock:
            rows = self._conn.execute(
                "SELECT * FROM sessions WHERE user_id=? ORDER BY created_at ASC, rowid ASC", (user_id,)
            ).fetchall()
        out = []
        for r in rows:
            res = json.loads(r["result_json"])
            syn = res.get("syndrome")
            if not syn:
                continue
            out.append({
                "session_id": r["id"], "created_at": r["created_at"], "primary": syn["primary"],
                "balance_index": syn["balance_index"], "scores": syn["scores"],
            })
        return out

    def save_feedback(self, sid: str, data: dict) -> None:
        with self._lock:
            self._conn.execute(
                "INSERT INTO feedback (session_id, created_at, data_json) VALUES (?,?,?)",
                (sid, self._now(), json.dumps(data, ensure_ascii=False)),
            )
            self._conn.commit()
