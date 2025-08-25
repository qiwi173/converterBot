from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Optional

from dotenv import load_dotenv


load_dotenv()


@dataclass(frozen=True)
class Settings:
    bot_token: str
    database_path: str = "data/db.sqlite3"
    scheduler_interval_seconds: int = 60
    user_agent: str = "QuickConverterBot/1.0"


def get_settings() -> Settings:
    token: Optional[str] = os.getenv("BOT_TOKEN")
    if not token:
        raise RuntimeError("BOT_TOKEN не задан в переменных окружения (.env)")
    db_path = os.getenv("DATABASE_PATH", "data/db.sqlite3")
    interval = int(os.getenv("SCHEDULER_INTERVAL_SECONDS", "60"))
    user_agent = os.getenv("USER_AGENT", "QuickConverterBot/1.0")
    return Settings(bot_token=token, database_path=db_path, scheduler_interval_seconds=interval, user_agent=user_agent)


