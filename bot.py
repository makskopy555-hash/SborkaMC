import asyncio
import logging
import time
from datetime import datetime, timedelta

from aiogram import Bot, Dispatcher, F, Router
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode, ChatMemberStatus
from aiogram.filters import CommandStart
from aiogram.types import (
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    LabeledPrice,
    Message,
    PreCheckoutQuery,
)
from apscheduler.schedulers.asyncio import AsyncIOScheduler

import config
import db

logging.basicConfig(level=logging.INFO)
log = logging.getLogger("vexworld-bot")

router = Router()

# ---------------------------------------------------------------------------
# Клавиатуры
# ---------------------------------------------------------------------------

def kb_welcome() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="📢 Подписаться", url="https://t.me/VexWorld1")],
            [InlineKeyboardButton(text="✅ Я подписался", callback_data="check_sub")],
        ]
    )


def kb_main_menu() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🛒 Магазин сборок", callback_data="shop")],
            [InlineKeyboardButton(text="💼 Моя подписка", callback_data="my_sub")],
            [InlineKeyboardButton(text="🛠 Тех. поддержка", callback_data="support")],
        ]
    )


def kb_back() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text="⬅️ Назад", callback_data="menu")]]
    )


def kb_shop() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=f"💳 Купить за {config.PRICE_STARS} ⭐",
                    callback_data="buy",
                )
            ],
            [InlineKeyboardButton(text="⬅️ Назад", callback_data="menu")],
        ]
    )


# ---------------------------------------------------------------------------
# Старт / проверка подписки
# ---------------------------------------------------------------------------

WELCOME_TEXT = (
    "Приветствую! 👋\n\n"
    "Вас приветствует <b>VexWorld</b> 🏔 — сервер и магазин сборок Minecraft.\n\n"
    "Чтобы продолжить, подпишитесь на наш канал, а затем нажмите «Я подписался»."
)

MENU_TEXT = "Выберите раздел 👇"

SUPPORT_TEXT = (
    "🛠 <b>Тех. поддержка</b>\n\n"
    "На данный момент сервер на тех. перерыве.\n"
    "Загляните чуть позже — мы уже всё чиним ⚙️✨"
)


@router.message(CommandStart())
async def cmd_start(message: Message) -> None:
    await message.answer(WELCOME_TEXT, reply_markup=kb_welcome())


async def _is_subscribed(bot: Bot, user_id: int) -> bool:
    try:
        member = await bot.get_chat_member(config.CHANNEL_USERNAME, user_id)
    except Exception as e:
        log.warning("get_chat_member failed: %s", e)
        return False
    return member.status in (
        ChatMemberStatus.MEMBER,
        ChatMemberStatus.ADMINISTRATOR,
        ChatMemberStatus.CREATOR,
    )


@router.callback_query(F.data == "check_sub")
async def cb_check_sub(call: CallbackQuery, bot: Bot) -> None:
    if await _is_subscribed(bot, call.from_user.id):
        await call.message.edit_text(MENU_TEXT, reply_markup=kb_main_menu())
    else:
        await call.answer("Вы ещё не подписались на канал ❌", show_alert=True)
        return
    await call.answer()


@router.callback_query(F.data == "menu")
async def cb_menu(call: CallbackQuery) -> None:
    await call.message.edit_text(MENU_TEXT, reply_markup=kb_main_menu())
    await call.answer()


# ---------------------------------------------------------------------------
# Тех. поддержка — пока просто заглушка на всех кнопках, как просили
# ---------------------------------------------------------------------------

@router.callback_query(F.data == "support")
async def cb_support(call: CallbackQuery) -> None:
    await call.message.edit_text(SUPPORT_TEXT, reply_markup=kb_back())
    await call.answer()


# ---------------------------------------------------------------------------
# Магазин сборок / подписка
# ---------------------------------------------------------------------------

@router.callback_query(F.data == "shop")
async def cb_shop(call: CallbackQuery) -> None:
    text = (
        "🛒 <b>Магазин сборок VexWorld</b>\n\n"
        "Доступ к закрытому каналу со сборками.\n"
        f"Срок подписки: {config.SUB_DAYS} дней\n"
        f"Цена: {config.PRICE_STARS} ⭐\n\n"
        "После оплаты бот пришлёт персональную ссылку-приглашение."
    )
    await call.message.edit_text(text, reply_markup=kb_shop())
    await call.answer()


@router.callback_query(F.data == "my_sub")
async def cb_my_sub(call: CallbackQuery) -> None:
    sub = await db.get_subscription(call.from_user.id)
    if sub and sub["active"] and sub["expires_at"] > time.time():
        dt = datetime.fromtimestamp(sub["expires_at"])
        text = (
            "💼 <b>Ваша подписка</b>\n\n"
            f"Статус: ✅ активна\n"
            f"Действует до: {dt.strftime('%d.%m.%Y %H:%M')}"
        )
    else:
        text = (
            "💼 <b>Ваша подписка</b>\n\n"
            "Статус: ❌ нет активной подписки.\n"
            "Загляните в «Магазин сборок», чтобы оформить доступ."
        )
    await call.message.edit_text(text, reply_markup=kb_back())
    await call.answer()


@router.callback_query(F.data == "buy")
async def cb_buy(call: CallbackQuery, bot: Bot) -> None:
    await call.answer()
    await bot.send_invoice(
        chat_id=call.from_user.id,
        title=f"Подписка VexWorld на {config.SUB_DAYS} дней",
        description="Доступ к закрытому каналу со сборками Minecraft.",
        payload=f"sub_{config.SUB_DAYS}d_{call.from_user.id}",
        currency="XTR",  # XTR = Telegram Stars
        prices=[LabeledPrice(label=f"Подписка {config.SUB_DAYS} дней", amount=config.PRICE_STARS)],
    )


@router.pre_checkout_query()
async def pre_checkout(pcq: PreCheckoutQuery) -> None:
    await pcq.answer(ok=True)


@router.message(F.successful_payment)
async def on_successful_payment(message: Message, bot: Bot) -> None:
    user_id = message.from_user.id
    now_ts = int(time.time())

    existing = await db.get_subscription(user_id)
    base_ts = now_ts
    if existing and existing["active"] and existing["expires_at"] > now_ts:
        base_ts = existing["expires_at"]  # продлеваем, а не перезаписываем

    new_expiry_ts = base_ts + config.SUB_DAYS * 86400

    try:
        invite = await bot.create_chat_invite_link(
            chat_id=config.SHOP_CHANNEL_ID,
            member_limit=1,
            expire_date=int(time.time()) + 86400,  # ссылка живёт 24ч на вступление
            name=f"sub_{user_id}_{now_ts}",
        )
        invite_link = invite.invite_link
    except Exception as e:
        log.exception("Не удалось создать invite-ссылку: %s", e)
        await message.answer(
            "Оплата прошла успешно, но возникла ошибка при выдаче доступа. "
            f"Напишите в поддержку: {config.SUPPORT_CONTACT}"
        )
        return

    await db.upsert_subscription(
        user_id=user_id,
        username=message.from_user.username,
        expires_at=new_expiry_ts,
        invite_link=invite_link,
    )

    dt = datetime.fromtimestamp(new_expiry_ts)
    await message.answer(
        "✅ Оплата получена!\n\n"
        f"Вот ваша персональная ссылка на канал со сборками (действует 24ч на вступление):\n{invite_link}\n\n"
        f"Доступ открыт до: {dt.strftime('%d.%m.%Y %H:%M')}"
    )


# ---------------------------------------------------------------------------
# Планировщик: выкидываем из канала тех, у кого закончилась подписка
# ---------------------------------------------------------------------------

async def check_expired_subscriptions(bot: Bot) -> None:
    expired = await db.get_expired()
    for sub in expired:
        user_id = sub["user_id"]
        try:
            await bot.ban_chat_member(config.SHOP_CHANNEL_ID, user_id)
            await bot.unban_chat_member(config.SHOP_CHANNEL_ID, user_id)
            log.info("Подписка истекла, пользователь %s удалён из канала", user_id)
        except Exception as e:
            log.warning("Не удалось удалить %s из канала: %s", user_id, e)
        await db.deactivate(user_id)
        try:
            await bot.send_message(
                user_id,
                "⏳ Ваша подписка на канал со сборками истекла.\n"
                "Чтобы продлить доступ, зайдите в «Магазин сборок» в боте.",
            )
        except Exception:
            pass  # пользователь мог заблокировать бота


# ---------------------------------------------------------------------------
# Точка входа
# ---------------------------------------------------------------------------

async def main() -> None:
    await db.init_db()

    bot = Bot(token=config.BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    dp = Dispatcher()
    dp.include_router(router)

    scheduler = AsyncIOScheduler()
    scheduler.add_job(check_expired_subscriptions, "interval", minutes=30, args=[bot])
    scheduler.start()

    log.info("Бот запущен, начинаю polling...")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
