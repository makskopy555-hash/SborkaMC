"""
Разовый скрипт, чтобы узнать числовой ID приватного канала.

Как пользоваться:
1. Добавь бота в приватный канал со сборками как АДМИНИСТРАТОРА
   (права можно дать минимальные, главное — добавить в админы).
2. Запусти этот скрипт локально:  python get_channel_id.py
3. Напиши любое сообщение в канал (или перешли любое старое сообщение заново).
4. В консоли появится что-то вроде: Channel ID: -1001234567890
5. Это значение и есть SHOP_CHANNEL_ID для переменных окружения.
6. После этого скрипт можно удалить/не использовать — он не нужен в проде.
"""

import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.types import Message

from config import BOT_TOKEN

logging.basicConfig(level=logging.INFO)


async def main() -> None:
    bot = Bot(token=BOT_TOKEN)
    dp = Dispatcher()

    @dp.channel_post()
    async def on_channel_post(message: Message) -> None:
        print(f"Channel ID: {message.chat.id}  (название: {message.chat.title})")

    print("Жду сообщение в канале... (Ctrl+C чтобы остановить)")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
