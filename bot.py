import asyncio
import logging
from aiogram import Bot, Dispatcher, F
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.types import Message
from aiogram.filters import Command

# ================== CONFIG ==================
TOKEN = "YOUR_BOT_TOKEN_HERE"   # ← Put your token here
# ===========================================

# Fixed Bot initialization
bot = Bot(
    token=TOKEN,
    default=DefaultBotProperties(parse_mode=ParseMode.HTML)
)

dp = Dispatcher()

# ----------------- Start Command -----------------
@dp.message(Command("start"))
async def cmd_start(message: Message):
    await message.answer(
        "👋 Hi! I'm a Guest Mode enabled bot.\n\n"
        "You can now mention me with <code>@YourBot</code> in any chat!"
    )


# ----------------- Guest Mode Handler -----------------
@dp.message(F.guest_query_id)
async def guest_mode_handler(message: Message):
    user = message.guest_bot_caller_user or message.from_user
    query_text = message.text or "[media or non-text message]"

    logging.info(f"Guest query from {user.full_name} ({user.id})")

    reply_text = (
        f"👋 Hello <b>{user.full_name}</b>!\n\n"
        f"You tagged me in this chat.\n"
        f"Message: <i>{query_text}</i>\n\n"
        "I'm working in <b>Guest Mode</b> 🚀"
    )

    await message.answer_guest_query(reply_text)


# ----------------- Regular messages -----------------
@dp.message()
async def echo(message: Message):
    if message.guest_query_id:
        return  # already handled by guest handler
    await message.answer("I received your message normally.")


async def main():
    logging.basicConfig(level=logging.INFO)
    print("🤖 Bot started successfully with Guest Mode!")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
