import asyncio
import logging
from aiogram import Bot, Dispatcher, F
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.types import Message
from aiogram.filters import Command

TOKEN = "8016460613:AAGc257gnXmeaYBz6I1jTtRnx9Qph1n6ofw"   # ← Change this

bot = Bot(
    token=TOKEN,
    default=DefaultBotProperties(parse_mode=ParseMode.HTML)
)

dp = Dispatcher()

@dp.message(Command("start"))
async def cmd_start(message: Message):
    await message.answer("✅ Bot is running!\nTag me like @YourBot hello")

# === IMPROVED GUEST MODE HANDLER ===
@dp.message(F.guest_query_id)          # Primary filter
async def guest_mode_handler(message: Message):
    try:
        user = message.guest_bot_caller_user or message.from_user
        text = message.text or "[non-text message]"

        logging.info(f"✅ Guest query received from {user.full_name} in chat {message.chat.id}")

        reply = (
            f"👋 Hi <b>{user.full_name}</b>!\n\n"
            f"You tagged me!\n"
            f"Your message: <i>{text}</i>\n\n"
            "<b>Guest Mode Working</b> ✅"
        )

        await message.answer_guest_query(reply)
        print("✅ Replied successfully in Guest Mode")
        
    except Exception as e:
        print(f"Error in guest handler: {e}")


# Fallback for normal chats
@dp.message()
async def normal_handler(message: Message):
    if message.guest_query_id:
        return
    await message.answer("Bot received normal message.")


async def main():
    logging.basicConfig(level=logging.INFO)
    print("🤖 Bot started - Guest Mode should work now")
    await dp.start_polling(bot, skip_updates=True)


if __name__ == "__main__":
    asyncio.run(main())
