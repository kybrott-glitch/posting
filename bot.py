"""
Megen Post Bot — Guest Mode edition
- Admin PM: /newpost to create posts with premium emoji + buttons
- Anywhere: @botusername code → bot replies directly into that chat (no join needed)
"""

import logging
import re
import json
from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ConversationHandler,
    TypeHandler,
    ContextTypes,
    filters,
)
from telegram.constants import ParseMode

from config import BOT_TOKEN, ADMIN_IDS
from database import db

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

# ── Conversation states ───────────────────────────────────────────────────────
ASK_CODE, ASK_TEXT, ASK_BUTTONS, CONFIRM = range(4)


def is_admin(user_id: int) -> bool:
    return user_id in ADMIN_IDS


def build_keyboard(buttons: list) -> InlineKeyboardMarkup | None:
    if not buttons:
        return None
    rows = [[InlineKeyboardButton(text=b["label"], url=b["url"])] for b in buttons]
    return InlineKeyboardMarkup(rows)


# ── /start ────────────────────────────────────────────────────────────────────

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("⛔ No access.")
        return
    await update.message.reply_text(
        "👑 <b>Megen Post Bot</b>\n\n"
        "Commands:\n"
        "/newpost — Create a post\n"
        "/listposts — See all posts\n"
        "/deletepost &lt;code&gt; — Remove a post\n\n"
        "Then in any chat, mention <code>@yourbotname code</code> "
        "and the bot will reply with the post.",
        parse_mode=ParseMode.HTML,
    )


# ── /newpost conversation ─────────────────────────────────────────────────────

async def newpost_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return ConversationHandler.END
    context.user_data["np"] = {}
    await update.message.reply_text(
        "📝 <b>Step 1/3 — Code</b>\n\n"
        "Give this post a short code (letters, numbers, hyphens only).\n"
        "Example: <code>summer-drop</code>, <code>promo1</code>, <code>nft-launch</code>\n\n"
        "This is what users will type after your bot username.",
        parse_mode=ParseMode.HTML,
    )
    return ASK_CODE


async def newpost_code(update: Update, context: ContextTypes.DEFAULT_TYPE):
    code = update.message.text.strip().lower()
    if not re.match(r'^[a-z0-9\-]+$', code):
        await update.message.reply_text("❌ Letters, numbers, hyphens only. Try again:")
        return ASK_CODE
    if db.get_post(code):
        await update.message.reply_text(
            f"❌ Code <code>{code}</code> already exists. Pick another:",
            parse_mode=ParseMode.HTML,
        )
        return ASK_CODE

    context.user_data["np"]["code"] = code
    await update.message.reply_text(
        "✅ Code set!\n\n"
        "📝 <b>Step 2/3 — Post text</b>\n\n"
        "Send your message. Use HTML formatting:\n"
        "<code>&lt;b&gt;bold&lt;/b&gt;</code>, <code>&lt;i&gt;italic&lt;/i&gt;</code>, "
        "<code>&lt;a href='url'&gt;link&lt;/a&gt;</code>\n\n"
        "For custom premium emoji:\n"
        "<code>&lt;tg-emoji emoji-id='5368324170671202286'&gt;🔥&lt;/tg-emoji&gt;</code>",
        parse_mode=ParseMode.HTML,
    )
    return ASK_TEXT


async def newpost_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["np"]["text"] = update.message.text or ""
    await update.message.reply_text(
        "✅ Text saved!\n\n"
        "📝 <b>Step 3/3 — Buttons</b>\n\n"
        "Add up to 5 inline buttons, one per line:\n"
        "<code>🔥 Buy Now | https://fragment.com</code>\n"
        "<code>🔵 Channel | https://t.me/yourchannel</code>\n\n"
        "Emoji in the label = the 'color'. Or /skip for no buttons.",
        parse_mode=ParseMode.HTML,
    )
    return ASK_BUTTONS


async def newpost_buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    buttons = []
    if text != "/skip":
        lines = [l.strip() for l in text.split("\n") if l.strip()]
        if len(lines) > 5:
            await update.message.reply_text("❌ Max 5 buttons. Try again:")
            return ASK_BUTTONS
        for line in lines:
            if "|" not in line:
                await update.message.reply_text(
                    f"❌ Bad format: <code>{line}</code>\nUse: Label | https://url",
                    parse_mode=ParseMode.HTML,
                )
                return ASK_BUTTONS
            label, url = line.split("|", 1)
            url = url.strip()
            if not url.startswith("http"):
                await update.message.reply_text(f"❌ Invalid URL: <code>{url}</code>", parse_mode=ParseMode.HTML)
                return ASK_BUTTONS
            buttons.append({"label": label.strip(), "url": url})

    context.user_data["np"]["buttons"] = buttons
    np = context.user_data["np"]
    btn_preview = "\n".join(f"  • {b['label']} → {b['url']}" for b in buttons) or "  (none)"

    await update.message.reply_text(
        f"📋 <b>Preview</b>\n\n"
        f"Code: <code>{np['code']}</code>\n"
        f"Text: <i>{np['text'][:120]}{'…' if len(np['text']) > 120 else ''}</i>\n"
        f"Buttons:\n{btn_preview}\n\n"
        "Send /confirm to save or /cancel to discard.",
        parse_mode=ParseMode.HTML,
    )
    return CONFIRM


async def newpost_skip_buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    update.message.text = "/skip"
    return await newpost_buttons(update, context)


async def newpost_confirm(update: Update, context: ContextTypes.DEFAULT_TYPE):
    np = context.user_data["np"]
    db.save_post(code=np["code"], text=np["text"], buttons=np["buttons"])
    me = await context.bot.get_me()
    await update.message.reply_text(
        f"✅ Post <code>{np['code']}</code> saved!\n\n"
        f"Use it anywhere: mention <code>@{me.username} {np['code']}</code> in any chat.",
        parse_mode=ParseMode.HTML,
    )
    context.user_data.clear()
    return ConversationHandler.END


async def newpost_cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    await update.message.reply_text("❌ Cancelled.")
    return ConversationHandler.END


# ── /listposts ────────────────────────────────────────────────────────────────

async def list_posts(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return
    posts = db.get_all_posts()
    if not posts:
        await update.message.reply_text("No posts yet. Use /newpost.")
        return
    lines = [f"• <code>{p['code']}</code> — {len(p['buttons'])} button(s)" for p in posts]
    await update.message.reply_text(
        "📚 <b>Saved Posts:</b>\n\n" + "\n".join(lines),
        parse_mode=ParseMode.HTML,
    )


# ── /deletepost ───────────────────────────────────────────────────────────────

async def delete_post(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return
    if not context.args:
        await update.message.reply_text("Usage: /deletepost &lt;code&gt;", parse_mode=ParseMode.HTML)
        return
    code = context.args[0].lower()
    if db.delete_post(code):
        await update.message.reply_text(f"🗑 Post <code>{code}</code> deleted.", parse_mode=ParseMode.HTML)
    else:
        await update.message.reply_text(f"❌ Post <code>{code}</code> not found.", parse_mode=ParseMode.HTML)


# ── Guest Mode handler ────────────────────────────────────────────────────────

async def handle_guest_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Fired when Telegram sends a guest_message update (bot tagged in a chat it hasn't joined).
    PTB 21.6 doesn't know this field yet (Bot API May 2026), so it lands in update.api_kwargs.
    """
    guest = update.api_kwargs.get("guest_message") if update.api_kwargs else None
    if not guest:
        return

    # Log the raw structure so we can see exactly what Telegram sends
    logger.info(f"[GUEST] raw guest_message dict: {guest}")

    # guest is a raw dict — guest_query_id is a field on the Message object itself
    raw_text = (guest.get("text") or "").strip()

    # Try all possible locations for the query ID
    guest_query_id = (
        guest.get("guest_query_id")          # on the message object itself (API docs)
        or guest.get("id")                    # fallback
    )

    logger.info(f"[GUEST] text={raw_text!r}, guest_query_id={guest_query_id!r}")

    if not guest_query_id:
        logger.warning(f"[GUEST] No guest_query_id found. Full dict keys: {list(guest.keys())}")
        return

    # Strip the bot mention (@username) from the text to isolate the code
    me = await context.bot.get_me()
    code = re.sub(rf'@{re.escape(me.username)}\s*', '', raw_text, flags=re.IGNORECASE).strip().lower()
    code = re.sub(r'\s+', '-', code)  # allow spaces as separators too

    if not code:
        await _answer_guest(context, guest_query_id, text="❓ Send a post code after my username.")
        return

    post = db.get_post(code)
    if not post:
        await _answer_guest(
            context,
            guest_query_id,
            text=f"❌ No post found for code: <code>{code}</code>",
            parse_mode="HTML",
        )
        return

    keyboard = build_keyboard(post["buttons"])
    await _answer_guest(
        context,
        guest_query_id,
        text=post["text"],
        parse_mode="HTML",
        reply_markup=keyboard,
    )


async def _answer_guest(context, guest_query_id: str, text: str, parse_mode: str = None, reply_markup=None):
    """
    Calls answerGuestQuery via raw Bot API.
    The API expects content wrapped in a 'message' object (InputBotInlineMessageText style).
    """
    message = {
        "type": "text",
        "text": text,
    }
    if parse_mode:
        message["parse_mode"] = parse_mode
    if reply_markup:
        message["reply_markup"] = reply_markup.to_dict()

    await context.bot.do_api_request(
        endpoint="answerGuestQuery",
        api_kwargs={
            "guest_query_id": guest_query_id,
            "message": message,
        },
    )


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("listposts", list_posts))
    app.add_handler(CommandHandler("deletepost", delete_post))

    # /newpost conversation
    app.add_handler(ConversationHandler(
        entry_points=[CommandHandler("newpost", newpost_start)],
        states={
            ASK_CODE:    [MessageHandler(filters.TEXT & ~filters.COMMAND, newpost_code)],
            ASK_TEXT:    [MessageHandler(filters.TEXT & ~filters.COMMAND, newpost_text)],
            ASK_BUTTONS: [
                CommandHandler("skip", newpost_skip_buttons),
                MessageHandler(filters.TEXT & ~filters.COMMAND, newpost_buttons),
            ],
            CONFIRM: [
                CommandHandler("confirm", newpost_confirm),
                CommandHandler("cancel",  newpost_cancel),
            ],
        },
        fallbacks=[CommandHandler("cancel", newpost_cancel)],
    ))

    # Guest mode — raw Update type filter for guest_message field
    app.add_handler(TypeHandler(Update, handle_guest_message), group=1)

    logger.info("Bot is running.")
    # ALL_TYPES covers standard PTB update types. We append "guest_message" manually
    # since PTB 21.6 doesn't know it yet — Telegram will still send it.
    allowed = list(Update.ALL_TYPES) + ["guest_message"]
    app.run_polling(allowed_updates=allowed, drop_pending_updates=True)


if __name__ == "__main__":
    main()
