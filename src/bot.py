from __future__ import annotations

import asyncio
from typing import Optional

from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command
from aiogram.types import Message

from .config import get_settings
from .rates import RatesService
from .parser import parse_convert, parse_alert
from .db import Database
from .scheduler import run_notifier


HELP_TEXT = (
    "🔄 <b>Конвертация валют:</b>\n"
    "• 100 USD to EUR — доллары в евро\n"
    "• 50 EUR to RUB — евро в рубли\n"
    "• 1000 RUB to UAH — рубли в гривны\n"
    "• 25 GBP to JPY — фунты в йены\n"
    "• 100 CAD to AUD — канадские доллары в австралийские\n\n"
    
    "🪙 <b>Конвертация криптовалют:</b>\n"
    "• 1 BTC to USD — биткоин в доллары\n"
    "• 10 ETH to EUR — эфириум в евро\n"
    "• 1000 USDT to RUB — тезер в рубли\n"
    "• 5 SOL to USD — солана в доллары\n"
    "• 0.5 ETH to BTC — эфириум в биткоин\n\n"
    
    "🔔 <b>Подписки на курсы:</b>\n"
    "• уведоми, если BTC &gt; 50000 to USD\n"
    "• alert если ETH &lt; 3000 to USD\n"
    "• notify когда SOL &gt; 100 to USD\n"
    "• уведоми, если RUB &gt; 80 to USD\n"
    "• alert если EUR &lt; 0.8 to USD\n\n"
    
    "📋 <b>Команды:</b>\n"
    "• /start — приветствие\n"
    "• /help — эта справка\n"
    "• /subs — список подписок\n"
    "• /unsub BTC USD — удалить подписку\n\n"
    
    "💡 <b>Поддерживаемые валюты:</b>\n"
    "Фиат: USD, EUR, GBP, JPY, CHF, CNY, AUD, CAD, RUB, UAH, KZT\n"
    "Крипта: BTC, ETH, USDT, BNB, XRP, SOL, TON, DOGE, TRX"
)


async def create_app():
    settings = get_settings()
    bot = Bot(token=settings.bot_token)
    dp = Dispatcher()
    db = Database(settings.database_path)
    await db.init()
    rates = RatesService(user_agent=settings.user_agent)

    @dp.message(Command("start"))
    async def start_handler(message: Message):
        welcome_text = (
            "👋 <b>Привет! Я QuickConverterBot</b>\n\n"
            "Я конвертирую валюты и криптовалюты в реальном времени!\n\n"
            "💡 <b>Быстрый старт:</b>\n"
            "• Напиши: <code>100 USD to EUR</code>\n"
            "• Подпишись: <code>уведоми, если BTC > 50000 to USD</code>\n\n"
            "📚 <b>Подробная справка:</b> /help"
        )
        await message.answer(welcome_text, parse_mode="HTML")

    @dp.message(Command("help"))
    async def help_handler(message: Message):
        await message.answer(HELP_TEXT, parse_mode="HTML")

    @dp.message(Command("subs"))
    async def list_subs(message: Message):
        items = await db.list_subscriptions(message.from_user.id)
        if not items:
            await message.answer("Подписок нет.")
            return
        lines = [
            f"{i+1}. {x['base']}/{x['quote']} {x['operator']} {x['threshold']}"
            for i, x in enumerate(items)
        ]
        await message.answer("\n".join(lines))

    @dp.message(Command("unsub"))
    async def unsub(message: Message):
        parts = message.text.split()
        if len(parts) < 3:
            await message.answer("Используй: /unsub BTC USD")
            return
        base, quote = parts[1].upper(), parts[2].upper()
        removed = await db.remove_subscription(message.from_user.id, base, quote)
        if removed:
            await message.answer("Подписка удалена.")
        else:
            await message.answer("Подписка не найдена.")

    @dp.message(F.text)
    async def text_handler(message: Message):
        text = message.text.strip()
        alert = parse_alert(text)
        if alert:
            await db.add_subscription(
                user_id=message.from_user.id,
                base=alert.base,
                quote=alert.quote,
                operator=alert.operator,
                threshold=alert.value,
            )
            await message.answer(
                f"Ок, уведомлю если {alert.base}/{alert.quote} {alert.operator} {alert.value}"
            )
            return

        cq = parse_convert(text)
        if cq:
            rate = await rates.get_rate(cq.base, cq.quote)
            if rate is None:
                await message.answer("Не удалось получить курс сейчас. Попробуй позже.")
                return
            result = cq.amount * rate
            await message.answer(f"{cq.amount} {cq.base} = {result:.6g} {cq.quote}\nКурс: {rate:.6g}")
            return

        await message.answer("Не понял запрос. Примеры: '100 USD to EUR', 'уведоми, если BTC > 50000 to USD'")

    return bot, dp, db, rates


async def run_bot():
    bot, dp, db, rates = await create_app()
    notifier_task = asyncio.create_task(run_notifier(bot, db, rates))
    try:
        await dp.start_polling(bot)
    finally:
        notifier_task.cancel()
        try:
            await notifier_task
        except Exception:
            pass
        await rates.close()


if __name__ == "__main__":
    asyncio.run(run_bot())


