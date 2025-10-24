import os
import asyncio
import traceback
from pyrogram import Client, filters
from pyrogram.types import Message
from pytgcalls import PyTgCalls, StreamType
from pytgcalls.types import AudioPiped
from pydub import AudioSegment

# ============================================================
# 🔧 IMPORT CONFIG
from config import OWNER_ID
from ShrutiMusic.core.userbot import assistants

TEMP_DIR = "downloads"
os.makedirs(TEMP_DIR, exist_ok=True)

# ============================================================
# 🧠 GLOBAL VARIABLES
bass_file = None
playing_group = None
loop_task = None
awaiting_bass = False

assistant = None
call_py = None

# ============================================================
# 🔥 Helper: Send error to owner
async def send_error(bot: Client, err: Exception):
    tb = "".join(traceback.format_exception(type(err), err, err.__traceback__))
    try:
        await bot.send_message(OWNER_ID, f"⚠️ **Error in Bass Module:**\n\n`{tb}`")
    except Exception:
        print("Failed to send error to owner:", tb)

# ============================================================
# 🔧 Helper: Get assistant safely
def get_assistant():
    global assistant, call_py
    if assistant and call_py:
        return True
    if not assistants:
        return False
    assistant = assistants[0]
    call_py = PyTgCalls(assistant)
    return True

# ============================================================
# 🎵 /bass COMMAND — start interaction
@Client.on_message(filters.private & filters.user(OWNER_ID) & filters.command("bass", prefixes=["/", "."]))
async def bass_start(bot: Client, message: Message):
    global awaiting_bass
    try:
        if not get_assistant():
            return await message.reply_text("❌ No assistant client available right now.")
        awaiting_bass = True
        await message.reply_text(
            "🎙 **Send a voice message or audio file** to apply extreme bass boost & loud volume.\n\n"
            "After processing, I’ll ask for the group ID where to play it on loop 🔊"
        )
    except Exception as e:
        await send_error(bot, e)

# ============================================================
# 🎶 Handle incoming voice/audio from owner
@Client.on_message(filters.private & filters.user(OWNER_ID) & (filters.voice | filters.audio))
async def bass_voice_handler(bot: Client, message: Message):
    global bass_file, awaiting_bass
    if not awaiting_bass:
        return  # Ignore if not requested via /bass
    if not get_assistant():
        return await message.reply_text("❌ No assistant client available right now.")

    awaiting_bass = False
    try:
        m = await message.reply_text("🎧 Downloading your voice/audio...")
        file_path = await message.download(file_name=f"{TEMP_DIR}/input.ogg")

        await m.edit_text("🎚️ Applying extreme bass boost & loud volume...")

        sound = AudioSegment.from_file(file_path)
        bass = sound.low_pass_filter(100).apply_gain(+25) + sound
        boosted = bass + 15  # Extra volume gain

        bass_path = f"{TEMP_DIR}/bass_boosted.mp3"
        boosted.export(bass_path, format="mp3")
        bass_file = bass_path

        await m.edit_text(
            "✅ Bass boosted successfully!\n\n"
            "Now send the **Group ID** where to play this bass loop (e.g. `-1001234567890`)."
        )
    except Exception as e:
        await send_error(bot, e)
        await message.reply_text(f"❌ Error during bass processing:\n`{e}`")

# ============================================================
# 🎯 Handle group ID input to start playback
@Client.on_message(filters.private & filters.user(OWNER_ID) & filters.text)
async def bass_group_receiver(bot: Client, message: Message):
    global playing_group, bass_file, loop_task
    if not bass_file or not os.path.exists(bass_file):
        return
    if not get_assistant():
        return await message.reply_text("❌ No assistant client available right now.")

    try:
        group_id = int(message.text.strip())
    except ValueError:
        return await message.reply_text("❌ Invalid group ID. It should look like `-1001234567890`.")

    playing_group = group_id
    await message.reply_text(f"🚀 Joining VC in **{group_id}** and starting loud bass loop...")

    try:
        await call_py.join_group_call(
            group_id,
            AudioPiped(bass_file),
            stream_type=StreamType().local_stream
        )
        loop_task = asyncio.create_task(loop_bass(bot, group_id, bass_file))
    except Exception as e:
        await send_error(bot, e)
        await message.reply_text(f"❌ Failed to join VC:\n`{e}`")

# ============================================================
# 🔁 Infinite Bass Loop Function
async def loop_bass(bot: Client, group_id: int, bass_file: str):
    try:
        duration = AudioSegment.from_file(bass_file).duration_seconds
    except Exception:
        duration = 10

    while True:
        try:
            await call_py.join_group_call(
                group_id,
                AudioPiped(bass_file),
                stream_type=StreamType().local_stream
            )
            await asyncio.sleep(duration)
        except asyncio.CancelledError:
            break
        except Exception as e:
            await send_error(bot, e)
            await asyncio.sleep(2)

# ============================================================
# 🛑 /stopbass — stop playback and leave VC
@Client.on_message(filters.user(OWNER_ID) & filters.command(["stopbass", "bassoff"], prefixes=["/", "."]))
async def stop_bass(bot: Client, message: Message):
    global loop_task, playing_group
    if not get_assistant():
        return await message.reply_text("❌ No assistant client available right now.")

    try:
        if playing_group:
            await call_py.leave_group_call(playing_group)
            playing_group = None
        if loop_task:
            loop_task.cancel()
            loop_task = None
        await message.reply_text("🛑 Stopped bass playback and left VC.")
    except Exception as e:
        await send_error(bot, e)
        await message.reply_text(f"⚠️ Error stopping bass:\n`{e}`")
