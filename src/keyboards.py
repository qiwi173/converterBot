from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

def get_main_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="🔄 Конвертировать", callback_data="convert"),
        InlineKeyboardButton(text="🔔 Подписки", callback_data="subscriptions")
    )
    builder.row(
        InlineKeyboardButton(text="💵 USD → EUR", callback_data="quick_usd_eur"),
        InlineKeyboardButton(text="₿ BTC → USD", callback_data="quick_btc_usd")
    )
    builder.row(
        InlineKeyboardButton(text="⚡ ETH → USD", callback_data="quick_eth_usd"),
        InlineKeyboardButton(text="💎 SOL → USD", callback_data="quick_sol_usd")
    )
    builder.row(
        InlineKeyboardButton(text="📋 Мои подписки", callback_data="my_subs"),
        InlineKeyboardButton(text="❌ Удалить подписку", callback_data="delete_sub")
    )
    builder.row(
        InlineKeyboardButton(text="❓ Помощь", callback_data="help"),
        InlineKeyboardButton(text="ℹ️ О боте", callback_data="about")
    )
    return builder.as_markup()

def get_currency_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="🇺🇸 USD", callback_data="currency_USD"),
        InlineKeyboardButton(text="🇪🇺 EUR", callback_data="currency_EUR"),
        InlineKeyboardButton(text="🇷🇺 RUB", callback_data="currency_RUB")
    )
    builder.row(
        InlineKeyboardButton(text="🇬🇧 GBP", callback_data="currency_GBP"),
        InlineKeyboardButton(text="🇯🇵 JPY", callback_data="currency_JPY"),
        InlineKeyboardButton(text="🇨🇭 CHF", callback_data="currency_CHF")
    )
    builder.row(
        InlineKeyboardButton(text="🇨🇳 CNY", callback_data="currency_CNY"),
        InlineKeyboardButton(text="🇦🇺 AUD", callback_data="currency_AUD"),
        InlineKeyboardButton(text="🇨🇦 CAD", callback_data="currency_CAD")
    )
    builder.row(
        InlineKeyboardButton(text="₿ BTC", callback_data="currency_BTC"),
        InlineKeyboardButton(text="⚡ ETH", callback_data="currency_ETH"),
        InlineKeyboardButton(text="💎 USDT", callback_data="currency_USDT")
    )
    builder.row(
        InlineKeyboardButton(text="🪙 BNB", callback_data="currency_BNB"),
        InlineKeyboardButton(text="🌟 XRP", callback_data="currency_XRP"),
        InlineKeyboardButton(text="🔮 SOL", callback_data="currency_SOL")
    )
    builder.row(
        InlineKeyboardButton(text="⬅️ Назад", callback_data="main_menu")
    )
    return builder.as_markup()

def get_operator_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="📈 Больше >", callback_data="operator_>"),
        InlineKeyboardButton(text="📉 Меньше <", callback_data="operator_<")
    )
    builder.row(
        InlineKeyboardButton(text="⬅️ Назад", callback_data="convert")
    )
    return builder.as_markup()