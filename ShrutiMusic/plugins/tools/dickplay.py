from pyrogram import Client, filters
from pyrogram.types import Message
import random
from ShrutiMusic.core.mongo import mongodb  # ensure it's async (Motor)

# -----------------------------
# Helper function to send errors
async def safe_send(message: Message, text: str):
    try:
        await message.reply_text(text)
    except Exception as e:
        print(f"[send error] Failed to send message: {e}")

# -----------------------------
# /grow command
@Client.on_message(filters.command("grow", prefixes="/"))
async def grow(client: Client, message: Message):
    if message.chat.type == "private":
        await safe_send(message, "This command can only be used in groups!")
        return
    try:
        size = random.randint(1, 20)
        await safe_send(message, f"{message.from_user.first_name}'s 🍆 grew to {size} cm!")
        try:
            result = await mongodb.dick_sizes.update_one(
                {"user_id": message.from_user.id},
                {"$set": {"size": size, "user_name": message.from_user.first_name}},
                upsert=True
            )
            print(f"[MongoDB] Updated size for {message.from_user.id}: {result.raw_result}")
        except Exception as db_error:
            print(f"[MongoDB Error] {db_error}")
            await safe_send(message, f"⚠️ DB Error: {db_error}")
    except Exception as e:
        await safe_send(message, f"⚠️ Error: {e}")

# -----------------------------
# /dick command
@Client.on_message(filters.command("dick", prefixes="/"))
async def dick(client: Client, message: Message):
    if message.chat.type == "private":
        await safe_send(message, "This command can only be used in groups!")
        return
    try:
        try:
            doc = await mongodb.dick_sizes.find_one({"user_id": message.from_user.id})
        except Exception as db_error:
            doc = None
            print(f"[MongoDB Error] {db_error}")
            await safe_send(message, f"⚠️ DB Error: {db_error}")
        size = doc["size"] if doc else random.randint(1, 20)
        await safe_send(message, f"{message.from_user.first_name}'s current 🍆 size is {size} cm")
    except Exception as e:
        await safe_send(message, f"⚠️ Error: {e}")

# -----------------------------
# /compare command
@Client.on_message(filters.command("compare", prefixes="/"))
async def compare(client: Client, message: Message):
    if message.chat.type == "private":
        await safe_send(message, "This command can only be used in groups!")
        return
    if not message.reply_to_message:
        await safe_send(message, "Reply to someone's message to compare sizes!")
        return
    try:
        try:
            user1_doc = await mongodb.dick_sizes.find_one({"user_id": message.from_user.id})
            user2_doc = await mongodb.dick_sizes.find_one({"user_id": message.reply_to_message.from_user.id})
        except Exception as db_error:
            user1_doc = user2_doc = None
            print(f"[MongoDB Error] {db_error}")
            await safe_send(message, f"⚠️ DB Error: {db_error}")

        user1_size = user1_doc["size"] if user1_doc else random.randint(1, 20)
        user2_size = user2_doc["size"] if user2_doc else random.randint(1, 20)

        if user1_size > user2_size:
            winner = message.from_user.first_name
        elif user2_size > user1_size:
            winner = message.reply_to_message.from_user.first_name
        else:
            winner = "It's a tie!"

        await safe_send(message,
                        f"{message.from_user.first_name}: {user1_size} cm\n"
                        f"{message.reply_to_message.from_user.first_name}: {user2_size} cm\n"
                        f"🏆 Winner: {winner}")
    except Exception as e:
        await safe_send(message, f"⚠️ Error: {e}")

# -----------------------------
# /fight command
@Client.on_message(filters.command("fight", prefixes="/"))
async def fight(client: Client, message: Message):
    if message.chat.type == "private":
        await safe_send(message, "This command can only be used in groups!")
        return
    if not message.reply_to_message:
        await safe_send(message, "Reply to someone's message to fight!")
        return
    try:
        user1_size = random.randint(1, 20)
        user2_size = random.randint(1, 20)
        winner = message.from_user.first_name if user1_size >= user2_size else message.reply_to_message.from_user.first_name

        await safe_send(message,
                        f"{message.from_user.first_name} 🍆 {user1_size} cm\n"
                        f"{message.reply_to_message.from_user.first_name} 🍆 {user2_size} cm\n"
                        f"🏆 Winner: {winner}")
    except Exception as e:
        await safe_send(message, f"⚠️ Error: {e}")

# -----------------------------
# /dtop command
@Client.on_message(filters.command("dtop", prefixes="/"))
async def dtop(client: Client, message: Message):
    if message.chat.type == "private":
        await safe_send(message, "This command can only be used in groups!")
        return
    try:
        try:
            top_users_cursor = mongodb.dick_sizes.find().sort("size", -1).limit(10)
        except Exception as db_error:
            top_users_cursor = []
            print(f"[MongoDB Error] {db_error}")
            await safe_send(message, f"⚠️ DB Error: {db_error}")

        text = "🍆 Top Dick Sizes:\n"
        async for user in top_users_cursor:
            text += f"{user.get('user_name', user['user_id'])}: {user['size']} cm\n"

        await safe_send(message, text)
    except Exception as e:
        await safe_send(message, f"⚠️ Error: {e}")

# -----------------------------
# /dhelp command
@Client.on_message(filters.command("dhelp", prefixes="/"))
async def dhelp(client: Client, message: Message):
    try:
        help_text = (
            "/grow — Grow your 🍆 randomly\n"
            "/fight — Reply to someone and fight; the bigger one wins\n"
            "/dick — Check your current 🍆 size\n"
            "/compare — Reply to someone to compare sizes\n"
            "/dtop — Show top sizes in this group\n"
            "/dhelp — Show this help message"
        )
        await safe_send(message, help_text)
    except Exception as e:
        await safe_send(message, f"⚠️ Error: {e}")
