from __future__ import annotations

import asyncio
from typing import Callable

from aiogram import Bot

from .db import Database
from .rates import RatesService
from .config import get_settings


def _compare(value: float, op: str, threshold: float) -> bool:
    if op == ">":
        return value > threshold
    if op == ">=":
        return value >= threshold
    if op == "<":
        return value < threshold
    if op == "<=":
        return value <= threshold
    if op == "==":
        return abs(value - threshold) < 1e-12
    return False


async def run_notifier(bot: Bot, db: Database, rates: RatesService):
    settings = get_settings()
    interval = settings.scheduler_interval_seconds
    while True:
        try:
            subs = await db.all_subscriptions()
            for sub in subs:
                rate = await rates.get_rate(sub["base"], sub["quote"])
                if rate is None:
                    continue
                if _compare(rate, sub["operator"], sub["threshold"]):
                    text = (
                        f"Сработало условие: {sub['base']}/{sub['quote']} "
                        f"{sub['operator']} {sub['threshold']} (текущий: {rate:.6g})"
                    )
                    try:
                        await bot.send_message(sub["user_id"], text)
                    except Exception:
                        pass
        except Exception:
            pass
        await asyncio.sleep(interval)


