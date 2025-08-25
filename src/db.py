from __future__ import annotations

import aiosqlite


CREATE_SQL = """
CREATE TABLE IF NOT EXISTS subscriptions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    base TEXT NOT NULL,
    quote TEXT NOT NULL,
    operator TEXT NOT NULL,
    threshold REAL NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_subscriptions_user ON subscriptions(user_id);
CREATE INDEX IF NOT EXISTS idx_subscriptions_pair ON subscriptions(base, quote);
"""


class Database:
    def __init__(self, path: str) -> None:
        self._path = path

    async def init(self) -> None:
        async with aiosqlite.connect(self._path) as db:
            await db.executescript(CREATE_SQL)
            await db.commit()

    async def add_subscription(self, user_id: int, base: str, quote: str, operator: str, threshold: float) -> None:
        async with aiosqlite.connect(self._path) as db:
            await db.execute(
                "INSERT INTO subscriptions(user_id, base, quote, operator, threshold) VALUES (?, ?, ?, ?, ?)",
                (user_id, base.upper(), quote.upper(), operator, threshold),
            )
            await db.commit()

    async def remove_subscription(self, user_id: int, base: str, quote: str) -> int:
        async with aiosqlite.connect(self._path) as db:
            cur = await db.execute(
                "DELETE FROM subscriptions WHERE user_id = ? AND base = ? AND quote = ?",
                (user_id, base.upper(), quote.upper()),
            )
            await db.commit()
            return cur.rowcount or 0

    async def list_subscriptions(self, user_id: int):
        async with aiosqlite.connect(self._path) as db:
            cur = await db.execute(
                "SELECT base, quote, operator, threshold FROM subscriptions WHERE user_id = ? ORDER BY base, quote",
                (user_id,),
            )
            rows = await cur.fetchall()
            return [
                {
                    "base": r[0],
                    "quote": r[1],
                    "operator": r[2],
                    "threshold": r[3],
                }
                for r in rows
            ]

    async def all_subscriptions(self):
        async with aiosqlite.connect(self._path) as db:
            cur = await db.execute(
                "SELECT id, user_id, base, quote, operator, threshold FROM subscriptions",
            )
            rows = await cur.fetchall()
            return [
                {
                    "id": r[0],
                    "user_id": r[1],
                    "base": r[2],
                    "quote": r[3],
                    "operator": r[4],
                    "threshold": r[5],
                }
                for r in rows
            ]


