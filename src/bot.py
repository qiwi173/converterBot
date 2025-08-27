from __future__ import annotations

import asyncio
from typing import Optional

from aiogram import Bot, Dispatcher, F, Router
from aiogram.filters import Command
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from aiogram.utils.keyboard import InlineKeyboardBuilder

from .config import get_settings
from .rates import RatesService
from .parser import parse_convert, parse_alert
from .db import Database
from .scheduler import run_notifier
from .keyboards import get_main_keyboard, get_currency_keyboard, get_operator_keyboard


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
            "💡 <b>Выбери действие:</b>"
        )
        await message.answer(welcome_text, parse_mode="HTML", reply_markup=get_main_keyboard())

    @dp.message(Command("help"))
    async def help_handler(message: Message):
        await message.answer(HELP_TEXT, parse_mode="HTML")

    @dp.message(Command("subs"))
    async def list_subs(message: Message):
        items = await db.list_subscriptions(message.from_user.id)
        if not items:
            await message.answer("📭 У тебя пока нет подписок.\n\n💡 Создай первую подписку на курс валюты!", reply_markup=get_main_keyboard())
            return
        
        lines = ["📋 <b>Твои подписки:</b>\n"]
        for i, x in enumerate(items, 1):
            lines.append(f"{i}. {x['base']}/{x['quote']} {x['operator']} {x['threshold']}")
        
        text = "\n".join(lines)
        await message.answer(text, parse_mode="HTML", reply_markup=get_main_keyboard())

    @dp.message(Command("unsub"))
    async def unsub(message: Message):
        parts = message.text.split()
        if len(parts) < 3:
            await message.answer("❌ Используй: <code>/unsub BTC USD</code>", parse_mode="HTML")
            return
        
        base, quote = parts[1].upper(), parts[2].upper()
        removed = await db.remove_subscription(message.from_user.id, base, quote)
        
        if removed:
            await message.answer(f"✅ Подписка {base}/{quote} удалена!", reply_markup=get_main_keyboard())
        else:
            await message.answer(f"❌ Подписка {base}/{quote} не найдена.", reply_markup=get_main_keyboard())

    @dp.callback_query(F.data == "main_menu")
    async def main_menu_handler(callback: CallbackQuery):
        await callback.message.edit_text(
            "👋 <b>Главное меню QuickConverterBot</b>\n\n"
            "Выбери действие:",
            parse_mode="HTML",
            reply_markup=get_main_keyboard()
        )
        await callback.answer()

    @dp.callback_query(F.data == "convert")
    async def convert_handler(callback: CallbackQuery):
        await callback.message.edit_text(
            "🔄 <b>Конвертация валют</b>\n\n"
            "Выбери базовую валюту:",
            parse_mode="HTML",
            reply_markup=get_currency_keyboard()
        )
        await callback.answer()

    @dp.callback_query(F.data == "subscriptions")
    async def subscriptions_handler(callback: CallbackQuery):
        await callback.message.edit_text(
            "🔔 <b>Подписки на курсы</b>\n\n"
            "Выбери базовую валюту для мониторинга:",
            parse_mode="HTML",
            reply_markup=get_currency_keyboard()
        )
        await callback.answer()

    @dp.callback_query(F.data == "help")
    async def help_callback_handler(callback: CallbackQuery):
        await callback.message.edit_text(
            HELP_TEXT,
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[[
                InlineKeyboardButton(text="⬅️ Назад", callback_data="main_menu")
            ]])
        )
        await callback.answer()

    @dp.callback_query(F.data == "about")
    async def about_handler(callback: CallbackQuery):
        about_text = (
            "ℹ️ <b>О QuickConverterBot</b>\n\n"
            "🚀 <b>Версия:</b> 2.0\n"
            "📅 <b>Обновлено:</b> Август 2024\n\n"
            "✨ <b>Возможности:</b>\n"
            "• Конвертация 11+ фиат валют\n"
            "• Конвертация 9+ криптовалют\n"
            "• Уведомления о курсах\n"
            "• Красивый интерфейс\n\n"
            "🔧 <b>Технологии:</b>\n"
            "• Python + aiogram 3.x\n"
            "• SQLite база данных\n"
            "• Реальные API курсов\n\n"
            "💻 <b>Разработчик:</b> @qiwi173"
        )
        
        await callback.message.edit_text(
            about_text,
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[[
                InlineKeyboardButton(text="⬅️ Назад", callback_data="main_menu")
            ]])
        )
        await callback.answer()

    @dp.callback_query(F.data.startswith("quick_"))
    async def quick_convert_handler(callback: CallbackQuery):
        # Обработка быстрых конвертаций
        data = callback.data
        if data == "quick_usd_eur":
            rate = await rates.get_rate("USD", "EUR")
            if rate:
                result = 100 * rate
                text = f"💱 <b>100 USD → EUR</b>\n\n💵 100 USD = {result:.2f} EUR\n📊 Курс: 1 USD = {rate:.4f} EUR"
            else:
                text = "❌ Не удалось получить курс USD/EUR"
        
        elif data == "quick_btc_usd":
            rate = await rates.get_rate("BTC", "USD")
            if rate:
                result = 1 * rate
                text = f"💱 <b>1 BTC → USD</b>\n\n₿ 1 BTC = ${result:,.2f}\n📊 Курс: 1 BTC = ${rate:,.2f}"
            else:
                text = "❌ Не удалось получить курс BTC/USD"
        
        elif data == "quick_eth_usd":
            rate = await rates.get_rate("ETH", "USD")
            if rate:
                result = 1 * rate
                text = f"💱 <b>1 ETH → USD</b>\n\n⚡ 1 ETH = ${result:,.2f}\n📊 Курс: 1 ETH = ${rate:,.2f}"
            else:
                text = "❌ Не удалось получить курс ETH/USD"
        
        elif data == "quick_sol_usd":
            rate = await rates.get_rate("SOL", "USD")
            if rate:
                result = 1 * rate
                text = f"💱 <b>1 SOL → USD</b>\n\n💎 1 SOL = ${result:.2f}\n📊 Курс: 1 SOL = ${rate:.4f}"
            else:
                text = "❌ Не удалось получить курс SOL/USD"
        
        else:
            text = "❌ Неизвестная быстрая конвертация"
        
        await callback.message.edit_text(
            text,
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[[
                InlineKeyboardButton(text="🔄 Еще раз", callback_data=data),
                InlineKeyboardButton(text="⬅️ Назад", callback_data="main_menu")
            ]])
        )
        await callback.answer()

    @dp.callback_query(F.data.startswith("currency_"))
    async def currency_handler(callback: CallbackQuery):
        user_id = callback.from_user.id
        currency = callback.data.split("_")[1]

        state = user_states.get(user_id, {"step": "base"})
        if state["step"] == "base":
            user_states[user_id] = {"step": "quote", "base": currency}
            await callback.message.edit_text(
                f"🔄 <b>Конвертация {currency}</b>\n\n"
                f"Теперь выбери валюту для конвертации:",
                parse_mode="HTML",
                reply_markup=get_currency_keyboard()
            )
        elif state["step"] == "quote":
            base = state["base"]
            quote = currency
            if base == quote:
                await callback.answer("Выбери другую валюту!", show_alert=True)
                return
            user_states[user_id] = {"step": "amount", "base": base, "quote": quote}
            await callback.message.edit_text(
                f"🔄 <b>Конвертация {base} → {quote}</b>\n\n"
                f"Введи сумму для конвертации:",
                parse_mode="HTML"
            )
        else:
            user_states[user_id] = {"step": "base"}
            await callback.message.edit_text(
                "🔄 <b>Конвертация валют</b>\n\n"
                "Выбери базовую валюту:",
                parse_mode="HTML",
                reply_markup=get_currency_keyboard()
            )
        await callback.answer()

    @dp.message(F.text)
    async def text_handler(message: Message):
        user_id = message.from_user.id
        state = user_states.get(user_id)
        if state and state.get("step") == "amount":
            try:
                amount = float(message.text.replace(",", "."))
            except ValueError:
                await message.answer("❌ Введи корректную сумму (например, 100.5)")
                return
            base = state["base"]
            quote = state["quote"]
            rate = await rates.get_rate(base, quote)
            if rate is None:
                await message.answer("❌ Не удалось получить курс сейчас.")
                return
            result = amount * rate
            await message.answer(
                f"💱 <b>Конвертация завершена!</b>\n\n"
                f"📊 <b>Курс:</b> 1 {base} = {rate:.6g} {quote}\n"
                f"💵 <b>Результат:</b> {amount} {base} = {result:.6g} {quote}",
                parse_mode="HTML",
                reply_markup=get_main_keyboard()
            )
            user_states[user_id] = {"step": "base"}
            return

        # Проверяем на подписку
        alert = parse_alert(message.text)
        if alert:
            await db.add_subscription(
                user_id=message.from_user.id,
                base=alert.base,
                quote=alert.quote,
                operator=alert.operator,
                threshold=alert.value,
            )
            
            # Красивое сообщение об успешной подписке
            success_text = (
                f"✅ <b>Подписка создана!</b>\n\n"
                f"🔔 <b>Уведомлю когда:</b>\n"
                f"{alert.base}/{alert.quote} {alert.operator} {alert.value}\n\n"
                f"💡 <b>Управление:</b>\n"
                f"• Посмотреть все: /subs\n"
                f"• Удалить: /unsub {alert.base} {alert.quote}"
            )
            
            await message.answer(
                success_text, 
                parse_mode="HTML",
                reply_markup=get_main_keyboard()
            )
            return

        # Проверяем на конвертацию
        cq = parse_convert(message.text)
        if cq:
            rate = await rates.get_rate(cq.base, cq.quote)
            if rate is None:
                await message.answer(
                    "❌ Не удалось получить курс сейчас.\n\n💡 Попробуй позже или используй кнопки выше!",
                    reply_markup=get_main_keyboard()
                )
                return
            
            result = cq.amount * rate
            
            # Красивое сообщение о конвертации
            convert_text = (
                f"💱 <b>Конвертация завершена!</b>\n\n"
                f"📊 <b>Курс:</b> 1 {cq.base} = {rate:.6g} {cq.quote}\n"
                f"💵 <b>Результат:</b> {cq.amount} {cq.base} = {result:.6g} {cq.quote}\n\n"
                f"🔄 <b>Хочешь еще?</b>"
            )
            
            await message.answer(
                convert_text,
                parse_mode="HTML",
                reply_markup=get_main_keyboard()
            )
            return

        # Непонятный запрос
        await message.answer(
            "❓ <b>Не понял запрос</b>\n\n"
            "💡 <b>Примеры:</b>\n"
            "• <code>100 USD to EUR</code>\n"
            "• <code>уведоми, если BTC > 50000 to USD</code>\n\n"
            "🔘 <b>Или используй кнопки:</b>",
            parse_mode="HTML",
            reply_markup=get_main_keyboard()
        )

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


