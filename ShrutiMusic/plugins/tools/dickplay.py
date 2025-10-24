import random
from pyrogram import Client, filters
from pyrogram.types import Message

from ShrutiMusic.core.mongo import mongodb

# Collection for dickplay
dick_collection = mongodb.dickplay

# ===================== HELP CMD =====================
@Client.on_message(filters.command("dhelp", prefixes="/"))
async def dick_help(client: Client, message: Message):
    try:
        if message.chat.type == "private":
            await message.reply_text("⚠ This command can only be used in groups!")
            return

        help_text = """
🍆 **DickGrow Commands**
/grow - Grow your 🍆 randomly  
/dick - Check your current 🍆 size  
/compare - Reply to someone to compare your 🍆 size  
/fight - Tag someone and your 🍆 fight happens  
/dtop - Show top 5 dick sizes in this group  
/dhelp - Show this help message
"""
        await message.reply_text(help_text)
    except Exception as e:
        await message.reply_text(f"⚠ Error: {e}")

# ===================== GROW CMD =====================
@Client.on_message(filters.command("grow", prefixes="/"))
async def grow_dick(client: Client, message: Message):
    try:
        if message.chat.type == "private":
            await message.reply_text("⚠ This command can only be used in groups!")
            return

        user_id = message.from_user.id
        size = random.randint(5, 30)

        await dick_collection.update_one(
            {"user_id": user_id, "chat_id": message.chat.id},
            {"$set": {"size": size}},
            upsert=True
        )
        await message.reply_text(f"🍆 {message.from_user.first_name}, your dick grew to **{size} cm**!")
    except Exception as e:
        await message.reply_text(f"⚠ Error: {e}")

# ===================== DICK CMD =====================
@Client.on_message(filters.command("dick", prefixes="/"))
async def check_dick(client: Client, message: Message):
    try:
        if message.chat.type == "private":
            await message.reply_text("⚠ This command can only be used in groups!")
            return

        user_id = message.from_user.id
        data = await dick_collection.find_one({"user_id": user_id, "chat_id": message.chat.id})

        if data:
            size = data["size"]
            await message.reply_text(f"🍆 {message.from_user.first_name}, your dick size is **{size} cm**.")
        else:
            await message.reply_text("🍆 You haven't grown yet! Use /grow to grow your dick.")
    except Exception as e:
        await message.reply_text(f"⚠ Error: {e}")

# ===================== COMPARE CMD =====================
@Client.on_message(filters.command("compare", prefixes="/"))
async def compare_dick(client: Client, message: Message):
    try:
        if message.chat.type == "private":
            await message.reply_text("⚠ This command can only be used in groups!")
            return

        if not message.reply_to_message:
            await message.reply_text("⚠ Reply to someone's message to compare sizes!")
            return

        user1_id = message.from_user.id
        user2_id = message.reply_to_message.from_user.id

        data1 = await dick_collection.find_one({"user_id": user1_id, "chat_id": message.chat.id})
        data2 = await dick_collection.find_one({"user_id": user2_id, "chat_id": message.chat.id})

        if not data1 or not data2:
            await message.reply_text("⚠ Both users must have grown their dicks first!")
            return

        size1 = data1["size"]
        size2 = data2["size"]

        if size1 > size2:
            winner = message.from_user.first_name
        elif size2 > size1:
            winner = message.reply_to_message.from_user.first_name
        else:
            winner = "It's a tie!"

        await message.reply_text(
            f"🍆 {message.from_user.first_name}: {size1} cm\n"
            f"🍆 {message.reply_to_message.from_user.first_name}: {size2} cm\n"
            f"🏆 Winner: {winner}"
        )
    except Exception as e:
        await message.reply_text(f"⚠ Error: {e}")

# ===================== FIGHT CMD =====================
@Client.on_message(filters.command("fight", prefixes="/"))
async def fight_dick(client: Client, message: Message):
    try:
        if message.chat.type == "private":
            await message.reply_text("⚠ This command can only be used in groups!")
            return

        if not message.reply_to_message:
            await message.reply_text("⚠ Reply to someone's message to fight!")
            return

        user1_id = message.from_user.id
        user2_id = message.reply_to_message.from_user.id

        data1 = await dick_collection.find_one({"user_id": user1_id, "chat_id": message.chat.id})
        data2 = await dick_collection.find_one({"user_id": user2_id, "chat_id": message.chat.id})

        if not data1 or not data2:
            await message.reply_text("⚠ Both users must have grown their dicks first!")
            return

        power1 = data1["size"] + random.randint(0, 10)
        power2 = data2["size"] + random.randint(0, 10)

        if power1 > power2:
            winner = message.from_user.first_name
        elif power2 > power1:
            winner = message.reply_to_message.from_user.first_name
        else:
            winner = "It's a tie!"

        await message.reply_text(
            f"⚔ Fight Result:\n"
            f"{message.from_user.first_name} (Power: {power1}) vs "
            f"{message.reply_to_message.from_user.first_name} (Power: {power2})\n"
            f"🏆 Winner: {winner}"
        )
    except Exception as e:
        await message.reply_text(f"⚠ Error: {e}")

# ===================== TOP CMD =====================
@Client.on_message(filters.command("dtop", prefixes="/"))
async def dick_top(client: Client, message: Message):
    try:
        if message.chat.type == "private":
            await message.reply_text("⚠ This command can only be used in groups!")
            return

        top_users = dick_collection.find({"chat_id": message.chat.id}).sort("size", -1).limit(5)
        text = "🍆 **Top Dick Sizes in this Group:**\n"
        async for user in top_users:
            text += f"{user['size']} cm — {user['_id']}\n"
        await message.reply_text(text)
    except Exception as e:
        await message.reply_text(f"⚠ Error: {e}")
