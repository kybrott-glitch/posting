# 📨 Megen Post Bot

A Telegram bot that stores rich posts with **custom premium emoji** and **colored inline buttons**, then lets you send them anywhere via inline query.

---

## Setup

```bash
pip install -r requirements.txt
```

Edit `config.py`:
- Set `BOT_TOKEN` from @BotFather
- Set your `ADMIN_IDS` (your Telegram user ID)

Enable inline mode in @BotFather:
```
/setinline → @yourbot → Set placeholder text (e.g. "Type #code")
```

Run:
```bash
python bot.py
```

---

## Usage

### Creating a post (admin PM only)

```
/newpost
```

The bot will walk you through 3 steps:

**Step 1 — Code**
Pick a short identifier: `summer-drop`, `promo1`, `nft-launch`

**Step 2 — Text**
Send your message using HTML formatting. For premium emoji:

```html
<tg-emoji emoji-id="5368324170671202286">🔥</tg-emoji> Big announcement!

Check out our <b>new drop</b> — <tg-emoji emoji-id="5373141891321699086">💎</tg-emoji> limited edition.
```

> ⚠️ The bot owner must have **Telegram Premium** for custom emoji to render properly in bot messages. If you do, they show up in the inline send.

**Step 3 — Buttons**
Add up to 5 buttons, one per line:

```
🔥 Buy Now | https://fragment.com
🔵 Join Channel | https://t.me/yourchannel
🟣 Trade | https://t.me/yourbot
```

Then `/confirm` to save.

---

### Sending a post inline

In **any chat**, type:

```
@yourbotname #summer-drop
```

The post appears as a result — tap to send it with full formatting and buttons.

---

## Commands

| Command | Description |
|---|---|
| `/newpost` | Create a new post (admin) |
| `/listposts` | List all saved posts (admin) |
| `/deletepost <code>` | Delete a post by code (admin) |

---

## Premium Emoji — How it works

Telegram's `<tg-emoji emoji-id="...">` HTML tag renders animated custom emoji in messages sent by bots **if the bot owner has Telegram Premium**.

To find emoji IDs:
1. Send a custom emoji in a chat via Telethon or API
2. Read back the `MessageEntityCustomEmoji` entity — the `document_id` is the emoji ID
3. Or use @stickers / emoji packs and inspect via Telethon

Example Telethon snippet to get emoji IDs:
```python
from telethon.sync import TelegramClient

with TelegramClient('session', api_id, api_hash) as client:
    msg = client.get_messages('me', limit=1)[0]
    for e in msg.entities:
        print(type(e).__name__, getattr(e, 'document_id', None))
```

---

## Button Colors

Telegram doesn't natively support colored URL buttons — color comes from the emoji you put in the label:

| Emoji prefix | Visual feel |
|---|---|
| 🔴 🟠 | Urgency / CTA |
| 🟢 ✅ | Positive / Buy |
| 🔵 🟣 | Info / Channel |
| ⚡ 🔥 | Hype / Drop |
| 💎 👑 | Premium / Exclusive |

---

## File structure

```
tgpostbot/
├── bot.py          # Main bot logic
├── database.py     # SQLite layer
├── config.py       # Token + admin IDs
├── requirements.txt
└── posts.db        # Auto-created on first run
```
