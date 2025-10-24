from pyrogram import Client, filters
from pyrogram.types import Message
from ShrutiMusic.core.mongo import mongodb
import random
import logging

LOGGER = logging.getLogger(__name__)

dickdb = mongodb.dickdata  # MongoDB collection

# --------------------------
# /grow — Grow your 🍆 randomly
# --------------------------
@Client.on_message(filters.command("grow", prefixes="/") & ~filters.edited)
async def grow_dick(client: Client, message: Message):
    try:
        if message.chat.type == "private":
            await message.reply_text("❌ This command can only be used in groups!")
            return

        user_id = message.from_user.id
        user = await dickdb.find_one({"user_id": user_id})
        new_size = random.randint(1, 25)
        if user:
            await dickdb.update_one({"user_id": user_id}, {"$set": {"size": new_size}})
        else:
            await dickdb.insert_one({"user_id": user_id, "size": new_size})

        await message.reply_text(f"🍆 {message.from_user.first_name}'s dick size is **{new_size} cm**!")

    except Exception as e:
        LOGGER.exception(f"Error in /grow: {e}")
        await message.reply_text(f"⚠️ An error occurred: {e}")

# --------------------------
# /fight - Tag someone to fight
# --------------------------
@Client.on_message(filters.command("fight", prefixes="/") & ~filters.edited)
async def dick_fight(client: Client, message: Message):
    try:
        if message.chat.type == "private":
            await message.reply_text("❌ This command can only be used in groups!")
            return

        if not message.reply_to_message:
            await message.reply_text("❌ Reply to someone's message to fight them!")
            return

        user1_id = message.from_user.id
        user2_id = message.reply_to_message.from_user.id

        # Ensure both users have sizes
        for uid in [user1_id, user2_id]:
            user = await dickdb.find_one({"user_id": uid})
            if not user:
                size = random.randint(1, 25)
                await dickdb.insert_one({"user_id": uid, "size": size})

        u1 = await dickdb.find_one({"user_id": user1_id})
        u2 = await dickdb.find_one({"user_id": user2_id})

        winner = message.from_user.first_name if u1["size"] >= u2["size"] else message.reply_to_message.from_user.first_name
        fight_text = (
            f"⚔️ **Fight Results:**\n\n"
            f"{message.from_user.first_name}: {u1['size']} cm\n"
            f"{message.reply_to_message.from_user.first_name}: {u2['size']} cm\n\n"
            f"🏆 Winner: {winner}!"
        )
        await message.reply_text(fight_text)

    except Exception as e:
        LOGGER.exception(f"Error in /fight: {e}")
        await message.reply_text(f"⚠️ An error occurred: {e}")

# --------------------------
# /dick — Check your current 🍆 size
# --------------------------
@Client.on_message(filters.command("dick", prefixes="/") & ~filters.edited)
async def check_dick(client: Client, message: Message):
    try:
        if message.chat.type == "private":
            await message.reply_text("❌ This command can only be used in groups!")
            return

        user_id = message.from_user.id
        user = await dickdb.find_one({"user_id": user_id})
        if not user:
            await message.reply_text("❌ You don't have a size yet! Use /grow first.")
            return

        await message.reply_text(f"🍆 {message.from_user.first_name}'s current size: **{user['size']} cm**!")

    except Exception as e:
        LOGGER.exception(f"Error in /dick: {e}")
        await message.reply_text(f"⚠️ An error occurred: {e}")

# --------------------------
# /compare — Compare with someone
# --------------------------
@Client.on_message(filters.command("compare", prefixes="/") & ~filters.edited)
async def compare_dick(client: Client, message: Message):
    try:
        if message.chat.type == "private":
            await message.reply_text("❌ This command can only be used in groups!")
            return

        if not message.reply_to_message:
            await message.reply_text("❌ Reply to someone's message to compare sizes!")
            return

        user1_id = message.from_user.id
        user2_id = message.reply_to_message.from_user.id

        u1 = await dickdb.find_one({"user_id": user1_id})
        u2 = await dickdb.find_one({"user_id": user2_id})

        if not u1:
            await message.reply_text("❌ You don't have a size yet! Use /grow first.")
            return
        if not u2:
            await message.reply_to_message.reply_text("❌ They don't have a size yet! Ask them to use /grow first.")
            return

        if u1["size"] > u2["size"]:
            result = f"💪 {message.from_user.first_name} wins!"
        elif u1["size"] < u2["size"]:
            result = f"💪 {message.reply_to_message.from_user.first_name} wins!"
        else:
            result = "🤝 It's a tie!"

        compare_text = (
            f"🍆 **Comparison:**\n\n"
            f"{message.from_user.first_name}: {u1['size']} cm\n"
            f"{message.reply_to_message.from_user.first_name}: {u2['size']} cm\n\n"
            f"{result}"
        )
        await message.reply_text(compare_text)

    except Exception as e:
        LOGGER.exception(f"Error in /compare: {e}")
        await message.reply_text(f"⚠️ An error occurred: {e}")

# --------------------------
# /dickhelp — Show help
# --------------------------
@Client.on_message(filters.command("dickhelp", prefixes="/") & ~filters.edited)
async def dick_help(client: Client, message: Message):
    try:
        help_text = (
            "🍆 **DickGrowerBot Commands:**\n\n"
            "/grow — Grow your 🍆 randomly\n"
            "/fight — Reply to someone to fight and see who wins\n"
            "/dick — Check your current 🍆 size\n"
            "/compare — Reply to someone to compare sizes\n"
            "/dickhelp — Show this help message"
        )
        await message.reply_text(help_text)
    except Exception as e:
        LOGGER.exception(f"Error in /dickhelp: {e}")
        await message.reply_text(f"⚠️ An error occurred: {e}")
