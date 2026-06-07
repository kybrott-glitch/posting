import asyncio
import logging
from aiogram import Bot, Dispatcher, F
from aiogram.types import Message
from aiogram.filters import Command

# ================== CONFIG ==================
TOKEN = "8016460613:AAGc257gnXmeaYBz6I1jTtRnx9Qph1n6ofw"   # ← Get from @BotFather
# ===========================================

bot = Bot(token=TOKEN, parse_mode="HTML")
dp = Dispatcher()

# ----------------- Commands -----------------
@dp.message(Command("start"))
async def cmd_start(message: Message):
    await message.answer(
        "👋 Hi! I'm a Guest Mode enabled bot.\n\n"
        "You can now mention me with <code>@YourBot</code> in any chat!"
    )


# ----------------- Guest Mode Handler -----------------
@dp.message(F.guest_query_id)   # This catches messages where the bot was mentioned as guest
async def guest_mode_handler(message: Message):
    user = message.guest_bot_caller_user or message.from_user
    chat = message.guest_bot_caller_chat or message.chat

    query_text = message.text or "some media"

    logging.info(f"Guest query from {user.full_name} in chat {chat.title or chat.id}")

    reply_text = (
        f"👋 Hello <b>{user.full_name}</b>!\n\n"
        f"You mentioned me in this chat.\n"
        f"Message: <i>{query_text}</i>\n\n"
        "I'm working in Guest Mode 🚀"
    )

    # Two ways to reply:
    # 1. Using shortcut (recommended)
    await message.answer_guest_query(reply_text)

    # 2. Or manually:
    # await bot.answer_guest_query(
    #     guest_query_id=message.guest_query_id,
    #     text=reply_text
    # )


# ----------------- Regular messages (when bot is added normally) -----------------
@dp.message()
async def echo(message: Message):
    if message.guest_query_id:  # safety check
        return
    await message.answer("I received your message normally.")


async def main():
    logging.basicConfig(level=logging.INFO)
    print("🤖 Bot started with Guest Mode support!")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
