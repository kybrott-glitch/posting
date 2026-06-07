"""
Telegram Inline Post Bot
- Admin-only post creation with premium emoji + colored inline buttons
- Inline query: @botusername #code → sends the post anywhere
"""

import logging
import re
import json
from telegram import (
    Update,
    InlineQueryResultArticle,
    InputTextMessageContent,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    InlineQueryResultCachedDocument,
)
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    InlineQueryHandler,
    ConversationHandler,
    ContextTypes,
    filters,
)
from telegram.constants import ParseMode
import uuid

from config import BOT_TOKEN, ADMIN_IDS
from database import db

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

# Conversation states
(
    ASK_CODE,
    ASK_TEXT,
    ASK_BUTTONS,
    CONFIRM,
) = range(4)


def is_admin(user_id: int) -> bool:
    return user_id in ADMIN_IDS


# ─── /start ───────────────────────────────────────────────────────────────────

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not is_admin(user_id):
        await update.message.reply_text("⛔ You don't have access to this bot.")
        return

    await update.message.reply_text(
        "👑 *Megen Post Bot*\n\n"
        "Commands:\n"
        "/newpost — Create a new post\n"
        "/listposts — View all saved posts\n"
        "/deletepost — Delete a post by code\n\n"
        "Once created, use `@yourbotname #code` in any chat to send a post.",
        parse_mode=ParseMode.MARKDOWN,
    )


# ─── /newpost conversation ────────────────────────────────────────────────────

async def newpost_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return ConversationHandler.END

    context.user_data["new_post"] = {}
    await update.message.reply_text(
        "📝 *New Post Setup*\n\n"
        "Step 1/3 — Enter a short *code* for this post (letters, numbers, hyphens only).\n"
        "Example: `summer-drop` or `promo1`\n\n"
        "This is what you'll type as `#code` in the inline query.",
        parse_mode=ParseMode.MARKDOWN,
    )
    return ASK_CODE


async def newpost_code(update: Update, context: ContextTypes.DEFAULT_TYPE):
    code = update.message.text.strip().lower()
    if not re.match(r'^[a-z0-9\-]+$', code):
        await update.message.reply_text(
            "❌ Invalid code. Use only letters, numbers, and hyphens. Try again:"
        )
        return ASK_CODE

    if db.get_post(code):
        await update.message.reply_text(
            f"❌ Code `{code}` already exists. Use /deletepost first or pick another code:",
            parse_mode=ParseMode.MARKDOWN,
        )
        return ASK_CODE

    context.user_data["new_post"]["code"] = code
    await update.message.reply_text(
        "✅ Code set!\n\n"
        "Step 2/3 — Send the *post text*.\n\n"
        "You can use:\n"
        "• HTML formatting (`<b>`, `<i>`, `<code>`, `<a href='...'>`, etc.)\n"
        "• Custom emoji like `<tg-emoji emoji-id='12345'>🔥</tg-emoji>`\n\n"
        "Just paste your full message content:",
        parse_mode=ParseMode.MARKDOWN,
    )
    return ASK_TEXT


async def newpost_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Store raw text with entities (to preserve premium emoji)
    msg = update.message
    context.user_data["new_post"]["text"] = msg.text or msg.caption or ""
    context.user_data["new_post"]["entities"] = (
        [e.to_dict() for e in msg.entities] if msg.entities else []
    )

    await update.message.reply_text(
        "✅ Text saved!\n\n"
        "Step 3/3 — Add *inline buttons* (up to 5).\n\n"
        "Format each button on a new line:\n"
        "`Button Label | https://link.com`\n\n"
        "For colored buttons, prefix the label:\n"
        "`🟢 Buy Now | https://...`\n"
        "`🔴 Urgent | https://...`\n"
        "`🔵 Info | https://...`\n\n"
        "Send /skip to add no buttons.",
        parse_mode=ParseMode.MARKDOWN,
    )
    return ASK_BUTTONS


async def newpost_buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    buttons = []

    if text != "/skip":
        lines = [l.strip() for l in text.split("\n") if l.strip()]
        if len(lines) > 5:
            await update.message.reply_text("❌ Maximum 5 buttons. Try again:")
            return ASK_BUTTONS

        for line in lines:
            if "|" not in line:
                await update.message.reply_text(
                    f"❌ Invalid format: `{line}`\nUse: `Label | https://url`",
                    parse_mode=ParseMode.MARKDOWN,
                )
                return ASK_BUTTONS
            parts = line.split("|", 1)
            label = parts[0].strip()
            url = parts[1].strip()
            if not url.startswith("http"):
                await update.message.reply_text(
                    f"❌ Invalid URL: `{url}`", parse_mode=ParseMode.MARKDOWN
                )
                return ASK_BUTTONS
            buttons.append({"label": label, "url": url})

    context.user_data["new_post"]["buttons"] = buttons
    post = context.user_data["new_post"]

    # Preview
    btn_preview = "\n".join(
        [f"  • {b['label']} → {b['url']}" for b in buttons]
    ) or "  (none)"

    await update.message.reply_text(
        f"📋 *Preview your post:*\n\n"
        f"*Code:* `#{post['code']}`\n"
        f"*Text:* _{post['text'][:100]}{'...' if len(post['text']) > 100 else ''}_\n"
        f"*Buttons:*\n{btn_preview}\n\n"
        "Send /confirm to save, or /cancel to discard.",
        parse_mode=ParseMode.MARKDOWN,
    )
    return CONFIRM


async def newpost_skip_buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["new_post"]["buttons"] = []
    return await newpost_buttons(update, context)


async def newpost_confirm(update: Update, context: ContextTypes.DEFAULT_TYPE):
    post = context.user_data["new_post"]
    db.save_post(
        code=post["code"],
        text=post["text"],
        entities=post.get("entities", []),
        buttons=post["buttons"],
    )
    await update.message.reply_text(
        f"✅ Post `#{post['code']}` saved!\n\n"
        f"Use it anywhere: `@{context.bot.username} #{post['code']}`",
        parse_mode=ParseMode.MARKDOWN,
    )
    context.user_data.clear()
    return ConversationHandler.END


async def newpost_cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    await update.message.reply_text("❌ Post creation cancelled.")
    return ConversationHandler.END


# ─── /listposts ───────────────────────────────────────────────────────────────

async def list_posts(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return

    posts = db.get_all_posts()
    if not posts:
        await update.message.reply_text("No posts saved yet. Use /newpost to create one.")
        return

    lines = []
    for p in posts:
        btn_count = len(p["buttons"])
        lines.append(f"• `#{p['code']}` — {btn_count} button(s)")

    await update.message.reply_text(
        "📚 *Saved Posts:*\n\n" + "\n".join(lines),
        parse_mode=ParseMode.MARKDOWN,
    )


# ─── /deletepost ──────────────────────────────────────────────────────────────

async def delete_post(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return

    args = context.args
    if not args:
        await update.message.reply_text(
            "Usage: `/deletepost <code>`", parse_mode=ParseMode.MARKDOWN
        )
        return

    code = args[0].lstrip("#").lower()
    if db.delete_post(code):
        await update.message.reply_text(f"🗑 Post `#{code}` deleted.", parse_mode=ParseMode.MARKDOWN)
    else:
        await update.message.reply_text(f"❌ Post `#{code}` not found.", parse_mode=ParseMode.MARKDOWN)


# ─── Inline query handler ─────────────────────────────────────────────────────

def build_keyboard(buttons: list) -> InlineKeyboardMarkup | None:
    if not buttons:
        return None

    # Build rows: 1 button per row for clean look (up to 5)
    rows = []
    for btn in buttons:
        rows.append([InlineKeyboardButton(text=btn["label"], url=btn["url"])])

    return InlineKeyboardMarkup(rows)


async def inline_query(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.inline_query.query.strip()

    # Match #code pattern
    match = re.match(r'^#([a-z0-9\-]+)$', query.lower())
    if not match:
        # Show hint if they type nothing or just #
        if query == "" or query == "#":
            await update.inline_query.answer(
                [],
                switch_pm_text="Type #code to send a post",
                switch_pm_parameter="inline_help",
                cache_time=0,
            )
        return

    code = match.group(1)
    post = db.get_post(code)
    if not post:
        await update.inline_query.answer(
            [],
            switch_pm_text=f"Post #{code} not found",
            switch_pm_parameter="inline_help",
            cache_time=0,
        )
        return

    keyboard = build_keyboard(post["buttons"])

    result = InlineQueryResultArticle(
        id=str(uuid.uuid4()),
        title=f"📨 Post #{post['code']}",
        description=post["text"][:100],
        input_message_content=InputTextMessageContent(
            message_text=post["text"],
            parse_mode=ParseMode.HTML,
        ),
        reply_markup=keyboard,
    )

    await update.inline_query.answer(
        [result],
        cache_time=0,  # Don't cache so edits reflect immediately
    )


# ─── Main ─────────────────────────────────────────────────────────────────────

def main():
    app = Application.builder().token(BOT_TOKEN).build()

    # /start
    app.add_handler(CommandHandler("start", start))

    # /newpost conversation
    conv = ConversationHandler(
        entry_points=[CommandHandler("newpost", newpost_start)],
        states={
            ASK_CODE: [MessageHandler(filters.TEXT & ~filters.COMMAND, newpost_code)],
            ASK_TEXT: [MessageHandler(filters.TEXT & ~filters.COMMAND, newpost_text)],
            ASK_BUTTONS: [
                CommandHandler("skip", newpost_skip_buttons),
                MessageHandler(filters.TEXT & ~filters.COMMAND, newpost_buttons),
            ],
            CONFIRM: [
                CommandHandler("confirm", newpost_confirm),
                CommandHandler("cancel", newpost_cancel),
            ],
        },
        fallbacks=[CommandHandler("cancel", newpost_cancel)],
    )
    app.add_handler(conv)

    # /listposts, /deletepost
    app.add_handler(CommandHandler("listposts", list_posts))
    app.add_handler(CommandHandler("deletepost", delete_post))

    # Inline queries
    app.add_handler(InlineQueryHandler(inline_query))

    logger.info("Bot started.")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
