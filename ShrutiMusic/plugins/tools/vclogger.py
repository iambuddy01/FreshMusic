import random
from pyrogram import filters
from pyrogram.types import Message
from config import BANNED_USERS
from ShrutiMusic import app
from ShrutiMusic.misc import SUDOERS
from ShrutiMusic.utils.database.database import get_vclogger_status, set_vclogger_status
from ShrutiMusic.core.call import Nand


# ---------------- VC LOGGER TOGGLE ----------------

@app.on_message(filters.command(["vclogger"]) & ~filters.private & ~BANNED_USERS)
async def toggle_vclogger(_, message: Message):
    if not message.from_user or not message.chat:
        return

    # Only admins or sudoers can toggle
    if message.from_user.id not in SUDOERS:
        member = await message.chat.get_member(message.from_user.id)
        if member.status not in ("administrator", "creator"):
            return await message.reply_text("❌ Only admins can manage VC Logger!")

    if len(message.command) == 1:
        status = await get_vclogger_status(message.chat.id)
        return await message.reply_text(
            f"🎤 **ᴠᴄʟᴏɢɢᴇʀ sᴛᴀᴛᴜs:** {'✅ Enabled' if status else '❌ Disabled'}"
        )

    arg = message.command[1].lower()
    if arg in ["on", "enable", "yes"]:
        await set_vclogger_status(message.chat.id, True)
        await message.reply_text("✅ **ᴠᴄʟᴏɢɢᴇʀ ᴇɴᴀʙʟᴇᴅ!** I’ll greet VC joins & leaves 🎧")
    elif arg in ["off", "disable", "no"]:
        await set_vclogger_status(message.chat.id, False)
        await message.reply_text("❌ **ᴠᴄʟᴏɢɢᴇʀ ᴅɪsᴀʙʟᴇᴅ!** I’ll stay quiet 🤫")
    else:
        await message.reply_text("Usage: `/vclogger on | off | yes | no | enable | disable`")


# ---------------- VC JOIN / LEAVE MESSAGES ----------------

JOIN_MSGS = [
    "🎧 {user} joined the VC — let's vibe!",
    "🔥 {user} hopped into the VC — party time!",
    "🎤 {user} is here — welcome aboard!",
    "💫 {user} entered the VC — music mode activated!",
    "🎶 {user} joined — the fun just started!"
]

LEAVE_MSGS = [
    "👋 {user} left the VC — see ya!",
    "😢 {user} disconnected — we'll miss you!",
    "🎧 {user} hopped off — catch you later!",
    "💨 {user} left — the vibe got quieter.",
    "🕊 {user} left the VC — peace out!"
]


@Nand.on_participant_joined()
async def vc_user_joined(_, chat_id: int, user_id: int):
    if not await get_vclogger_status(chat_id):
        return
    try:
        user = await app.get_users(user_id)
        msg = random.choice(JOIN_MSGS).format(user=user.mention)
        await app.send_message(chat_id, msg)
    except Exception:
        pass


@Nand.on_participant_left()
async def vc_user_left(_, chat_id: int, user_id: int):
    if not await get_vclogger_status(chat_id):
        return
    try:
        user = await app.get_users(user_id)
        msg = random.choice(LEAVE_MSGS).format(user=user.mention)
        await app.send_message(chat_id, msg)
    except Exception:
        pass
