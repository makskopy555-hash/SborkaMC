import time
import aiosqlite

from config import DB_PATH

_CREATE_TABLE = """
CREATE TABLE IF NOT EXISTS subscriptions (
    user_id      INTEGER PRIMARY KEY,
    username     TEXT,
    expires_at   INTEGER NOT NULL,
    invite_link  TEXT,
    active       INTEGER NOT NULL DEFAULT 1,
    created_at   INTEGER NOT NULL,
    updated_at   INTEGER NOT NULL
);
"""


async def init_db() -> None:
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(_CREATE_TABLE)
        await db.commit()


async def get_subscription(user_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            "SELECT * FROM subscriptions WHERE user_id = ?", (user_id,)
        )
        row = await cursor.fetchone()
        return dict(row) if row else None


async def upsert_subscription(
    user_id: int, username: str | None, expires_at: int, invite_link: str
) -> None:
    now = int(time.time())
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            """
            INSERT INTO subscriptions (user_id, username, expires_at, invite_link, active, created_at, updated_at)
            VALUES (?, ?, ?, ?, 1, ?, ?)
            ON CONFLICT(user_id) DO UPDATE SET
                username = excluded.username,
                expires_at = excluded.expires_at,
                invite_link = excluded.invite_link,
                active = 1,
                updated_at = excluded.updated_at
            """,
            (user_id, username, expires_at, invite_link, now, now),
        )
        await db.commit()


async def get_expired(now_ts: int | None = None):
    now_ts = now_ts if now_ts is not None else int(time.time())
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            "SELECT * FROM subscriptions WHERE active = 1 AND expires_at < ?",
            (now_ts,),
        )
        rows = await cursor.fetchall()
        return [dict(r) for r in rows]


async def deactivate(user_id: int) -> None:
    now = int(time.time())
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "UPDATE subscriptions SET active = 0, updated_at = ? WHERE user_id = ?",
            (now, user_id),
        )
        await db.commit()
