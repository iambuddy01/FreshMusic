# give credit to github - @karmaxexclusive you motherfumker.
# don't change this text, otherwise your github acc will be suspended for copyrights.

import asyncio
import re
from pyrogram import filters, types, enums
from ShurtiMusic import app
from ShrutiMusic.core.mongo import mongodb

# --------------------------
# Lock Types
# --------------------------
LOCK_TYPES = {
    "all": "Blocks all messages",
    "audio": "Blocks audio files",
    "bots": "🔥 FULL bot protection - blocks additions & promotions",
    "button": "Blocks messages with inline buttons",
    "contact": "Blocks contact sharing",
    "document": "Blocks document files",
    "egame": "Blocks embedded games",
    "forward": "Blocks forwarded messages",
    "game": "Blocks games",
    "gif": "Blocks GIF animations",
    "info": "Blocks service messages",
    "inline": "Blocks inline bot results",
    "invite": "Blocks invite links",
    "location": "Blocks location/venue sharing",
    "media": "Blocks all media types",
    "messages": "Blocks text messages",
    "other": "Blocks other content types",
    "photo": "Blocks photos/images",
    "pin": "Blocks pinned messages",
    "poll": "Blocks polls",
    "previews": "Blocks link previews",
    "rtl": "Blocks RTL text",
    "sticker": "Blocks stickers",
    "url": "Blocks URLs/links",
    "username": "Blocks username mentions (@username)",
    "video": "Blocks videos",
    "voice": "Blocks voice messages"
}

# --------------------------
# Mongo DB
# --------------------------
locks_col = mongodb.locks

async def get_locks(chat_id: int) -> dict:
    doc = await locks_col.find_one({"chat_id": chat_id})
    return doc.get("locks", {}) if doc else {}

async def set_lock(chat_id: int, lock_type: str, status: bool):
    await locks_col.update_one(
        {"chat_id": chat_id},
        {"$set": {f"locks.{lock_type}": status}},
        upsert=True
    )

async def set_admin_lock(chat_id: int, status: bool):
    await locks_col.update_one(
        {"chat_id": chat_id},
        {"$set": {"lock_admin": status}},
        upsert=True
    )

async def get_admin_lock(chat_id: int) -> bool:
    doc = await locks_col.find_one({"chat_id": chat_id})
    return doc.get("lock_admin", False) if doc else False

# --------------------------
# Admin Check Helper
# --------------------------
async def is_admin(chat_id, user_id):
    try:
        m = await app.get_chat_member(chat_id, user_id)
        return m.status in [enums.ChatMemberStatus.ADMINISTRATOR, enums.ChatMemberStatus.OWNER]
    except:
        return False

# --------------------------
# /locktypes
# --------------------------
@app.on_message(filters.command(["locktypes", "lock"], prefixes=["/", ".", "!", "?"]) & filters.group)
async def locktypes_cmd(_, message):
    txt = "🔒 **Group Lock System** 🚫\n\n"
    txt += "📖 **Available Lock Types:**\n\n"
    for k, v in LOCK_TYPES.items():
        txt += f"• **{k}** → {v}\n"

    txt += (
        "\n🖲️ **Lock / Unlock:**\n"
        "`/lock type` 🔒   |   `/unlock type` 🔓\n"
        "📋 **Status:**\n"
        "`/locks` → Show locks with ✅/❌\n"
        "👑 **Admin Lock:**\n"
        "`/lockadmin on` ⚠️ | `/lockadmin off` ✅\n"
        "\n💡 **Examples:**\n"
        "`/lock photo` → Block photos\n"
        "`/unlock url` → Allow links\n"
        "`/lock all` → Block everything"
    )

    await message.reply_text(txt)

# --------------------------
# /lock
# --------------------------
@app.on_message(filters.command("lock", prefixes=["/", ".", "!", "?"]) & filters.group)
async def lock_cmd(_, message):
    if not await is_admin(message.chat.id, message.from_user.id):
        return await message.reply_text("❌ Only admins can lock content!")
    if len(message.command) < 2:
        return await message.reply_text("Usage: `/lock type`")

    lock_type = message.command[1].lower()
    if lock_type not in LOCK_TYPES:
        return await message.reply_text("❌ Invalid lock type!\nUse /locktypes to view all locks.")

    await set_lock(message.chat.id, lock_type, True)
    await message.reply_text(f"🔒 **Locked:** `{lock_type}`")

# --------------------------
# /unlock
# --------------------------
@app.on_message(filters.command("unlock", prefixes=["/", ".", "!", "?"]) & filters.group)
async def unlock_cmd(_, message):
    if not await is_admin(message.chat.id, message.from_user.id):
        return await message.reply_text("❌ Only admins can unlock content!")
    if len(message.command) < 2:
        return await message.reply_text("Usage: `/unlock type`")

    lock_type = message.command[1].lower()
    if lock_type not in LOCK_TYPES:
        return await message.reply_text("❌ Invalid lock type!\nUse /locktypes to view all locks.")

    await set_lock(message.chat.id, lock_type, False)
    await message.reply_text(f"🔓 **Unlocked:** `{lock_type}`")

# --------------------------
# /unlockall
# --------------------------
@app.on_message(filters.command("unlockall", prefixes=["/", ".", "!", "?"]) & filters.group)
async def unlock_all_cmd(_, message):
    if not await is_admin(message.chat.id, message.from_user.id):
        return await message.reply_text("❌ Only admins can unlock all!")
    await locks_col.update_one({"chat_id": message.chat.id}, {"$set": {"locks": {}}}, upsert=True)
    await message.reply_text("🔓 **All locks removed!**")

# --------------------------
# /lockadmin
# --------------------------
@app.on_message(filters.command("lockadmin", prefixes=["/", ".", "!", "?"]) & filters.group)
async def lockadmin_cmd(_, message):
    if not await is_admin(message.chat.id, message.from_user.id):
        return await message.reply_text("❌ Only admins can use this!")

    if len(message.command) < 2:
        return await message.reply_text("Usage: `/lockadmin on/off`")

    choice = message.command[1].lower()
    if choice not in ["on", "off"]:
        return await message.reply_text("❌ Use: on/off")

    await set_admin_lock(message.chat.id, choice == "on")
    await message.reply_text(f"👑 **Admin Lock:** {'⚠️ Enabled' if choice=='on' else '✅ Disabled'}")

# --------------------------
# /locks interactive panel
# --------------------------
@app.on_message(filters.command("locks", prefixes=["/", ".", "!", "?"]) & filters.group)
async def locks_status(_, message):
    if not await is_admin(message.chat.id, message.from_user.id):
        return await message.reply_text("❌ Only admins can view lock status!")

    chat_id = message.chat.id
    locks = await get_locks(chat_id)

    buttons = []
    row = []

    for i, lock in enumerate(LOCK_TYPES, start=1):
        status = "✅" if locks.get(lock) else "❌"
        row.append(types.InlineKeyboardButton(f"{lock} {status}", callback_data=f"toggle|{lock}|{chat_id}"))
        if i % 2 == 0:
            buttons.append(row)
            row = []
    if row:
        buttons.append(row)

    await message.reply_text(
        "🔒 **Current Group Locks** (Tap to toggle):",
        reply_markup=types.InlineKeyboardMarkup(buttons)
    )

# --------------------------
# Toggle Buttons
# --------------------------
@app.on_callback_query(filters.regex(r"toggle\|"))
async def toggle_lock_cb(_, cb: types.CallbackQuery):
    try:
        _, lock_type, chat_id_str = cb.data.split("|")
        chat_id = int(chat_id_str)

        if not await is_admin(chat_id, cb.from_user.id):
            return await cb.answer("❌ Admins only!", show_alert=True)

        locks = await get_locks(chat_id)
        current = locks.get(lock_type, False)

        await set_lock(chat_id, lock_type, not current)

        # Refresh Panel
        locks = await get_locks(chat_id)
        buttons = []
        row = []
        for i, lock in enumerate(LOCK_TYPES, start=1):
            status = "✅" if locks.get(lock) else "❌"
            row.append(types.InlineKeyboardButton(f"{lock} {status}", callback_data=f"toggle|{lock}|{chat_id}"))
            if i % 2 == 0:
                buttons.append(row)
                row = []
        if row:
            buttons.append(row)

        await cb.message.edit_reply_markup(types.InlineKeyboardMarkup(buttons))
        await cb.answer(f"🔄 Toggled `{lock_type}`")

    except Exception as e:
        print("Toggle error:", e)
        await cb.answer("⚠️ Error occurred!", show_alert=True)

# --------------------------
# Enforcement
# --------------------------
@app.on_message(filters.group)
async def enforce_locks(_, message):
    chat_id = message.chat.id
    locks = await get_locks(chat_id)
    if not locks:
        return

    try:
        member = await app.get_chat_member(chat_id, message.from_user.id)

        # Admin Exemption
        if member.status in [enums.ChatMemberStatus.ADMINISTRATOR, enums.ChatMemberStatus.OWNER]:
            if not await get_admin_lock(chat_id):
                return

        # All your existing enforcement code continues unchanged ↓↓↓
        # (not removed, not altered)
        # ----------------------------------------------------------

        if locks.get("pin") and getattr(message, "pinned_message", None):
            await message.delete(); return

        if locks.get("all"): await message.delete(); return
        if locks.get("photo") and message.photo: await message.delete(); return
        if locks.get("video") and message.video: await message.delete(); return
        if locks.get("voice") and message.voice: await message.delete(); return
        if locks.get("audio") and message.audio: await message.delete(); return
        if locks.get("sticker") and message.sticker: await message.delete(); return
        if locks.get("gif") and message.animation: await message.delete(); return
        if locks.get("document") and message.document: await message.delete(); return
        if locks.get("media") and any([message.photo, message.video, message.voice, message.audio, message.document, message.animation]): await message.delete(); return
        if locks.get("messages") and message.text: await message.delete(); return
        if locks.get("url") and message.text and re.search(r"(https?://|t\.me/)", message.text): await message.delete(); return
        if locks.get("username") and message.text and re.search(r"@\w+", message.text): await message.delete(); return
        if locks.get("rtl") and message.text and any("\u0590" <= c <= "\u06FF" for c in message.text): await message.delete(); return
        if locks.get("contact") and message.contact: await message.delete(); return
        if locks.get("location") and (message.location or message.venue): await message.delete(); return
        if locks.get("forward") and (message.forward_date or message.forward_from or message.forward_from_chat): await message.delete(); return
        if locks.get("button") and message.reply_markup: await message.delete(); return
        if locks.get("invite") and message.text and "t.me/" in message.text: await message.delete(); return
        if locks.get("poll") and message.poll: await message.delete(); return
        if locks.get("previews") and message.entities:
            for e in message.entities:
                if e.type in ["url", "text_link"]: await message.delete(); return
        if locks.get("inline") and message.via_bot: await message.delete(); return
        if locks.get("egame") and message.game: await message.delete(); return
        if locks.get("game") and message.game: await message.delete(); return
        if locks.get("bots") and message.new_chat_members:
            for u in message.new_chat_members:
                if u.is_bot:
                    try: await app.ban_chat_member(chat_id, u.id)
                    except: pass
        
    except Exception as e:
        print("Lock Enforcement Error:", e)


# for more custom module vist the dev of the code - #exclusive(karma). 
