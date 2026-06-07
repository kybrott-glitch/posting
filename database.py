"""
SQLite database layer for the post bot.
"""

import sqlite3
import json
import os
from pathlib import Path


DB_PATH = Path(__file__).parent / "posts.db"


class Database:
    def __init__(self):
        self.conn = sqlite3.connect(str(DB_PATH), check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self._init()

    def _init(self):
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS posts (
                code        TEXT PRIMARY KEY,
                text        TEXT NOT NULL,
                entities    TEXT NOT NULL DEFAULT '[]',
                buttons     TEXT NOT NULL DEFAULT '[]',
                created_at  DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        self.conn.commit()

    def save_post(self, code: str, text: str, entities: list, buttons: list):
        self.conn.execute(
            """
            INSERT OR REPLACE INTO posts (code, text, entities, buttons)
            VALUES (?, ?, ?, ?)
            """,
            (code, text, json.dumps(entities), json.dumps(buttons)),
        )
        self.conn.commit()

    def get_post(self, code: str) -> dict | None:
        row = self.conn.execute(
            "SELECT * FROM posts WHERE code = ?", (code,)
        ).fetchone()
        if not row:
            return None
        return {
            "code": row["code"],
            "text": row["text"],
            "entities": json.loads(row["entities"]),
            "buttons": json.loads(row["buttons"]),
        }

    def get_all_posts(self) -> list[dict]:
        rows = self.conn.execute(
            "SELECT * FROM posts ORDER BY created_at DESC"
        ).fetchall()
        return [
            {
                "code": r["code"],
                "text": r["text"],
                "entities": json.loads(r["entities"]),
                "buttons": json.loads(r["buttons"]),
            }
            for r in rows
        ]

    def delete_post(self, code: str) -> bool:
        cur = self.conn.execute("DELETE FROM posts WHERE code = ?", (code,))
        self.conn.commit()
        return cur.rowcount > 0


db = Database()
