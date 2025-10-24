from pyrogram import Client, filters
from pyrogram.types import Message
from ShrutiMusic.core.mongo import mongodb
import random

# ----------------------
# /grow — Grow your 🍆 randomly
@Client.on_message(filters.command("grow", prefixes="/"))
async def grow(client: Client, message: Message):
    try:
        if message.chat.type == "private":
            await message.reply_text("❌ This command can only be used in groups!")
            return

        user_id = message.from_user.id
        size = random.randint(5, 30)
        await mongodb.dickplay.update_one(
            {"user_id": user_id},
            {"$set": {"size": size}},
            upsert=True
        )
        await message.reply_text(f"🍆 Your dick grew to **{size} cm**!")
    except Exception as e:
        await message.reply_text(f"⚠️ Error: {e}")

# ----------------------
# /dick — Check your current 🍆 size
@Client.on_message(filters.command("dick", prefixes="/"))
async def check_dick(client: Client, message: Message):
    try:
        if message.chat.type == "private":
            await message.reply_text("❌ This command can only be used in groups!")
            return

        user = await mongodb.dickplay.find_one({"user_id": message.from_user.id})
        if user:
            await message.reply_text(f"🍆 Your current dick size is **{user['size']} cm**")
        else:
            await message.reply_text("You haven't grown your 🍆 yet. Use `/grow` to start!")
    except Exception as e:
        await message.reply_text(f"⚠️ Error: {e}")

# ----------------------
# /compare — Reply to someone to compare your 🍆 size
@Client.on_message(filters.command("compare", prefixes="/") & filters.reply)
async def compare_dick(client: Client, message: Message):
    try:
        if message.chat.type == "private":
            await message.reply_text("❌ This command can only be used in groups!")
            return

        user1 = await mongodb.dickplay.find_one({"user_id": message.from_user.id})
        user2 = await mongodb.dickplay.find_one({"user_id": message.reply_to_message.from_user.id})

        if not user1 or not user2:
            await message.reply_text("Both users need to have grown their 🍆 first!")
            return

        if user1["size"] > user2["size"]:
            winner = message.from_user.first_name
        elif user1["size"] < user2["size"]:
            winner = message.reply_to_message.from_user.first_name
        else:
            winner = "Both are equal!"

        await message.reply_text(
            f"{message.from_user.first_name}: {user1['size']} cm\n"
            f"{message.reply_to_message.from_user.first_name}: {user2['size']} cm\n\n"
            f"🏆 Winner: {winner}"
        )
    except Exception as e:
        await message.reply_text(f"⚠️ Error: {e}")

# ----------------------
# /fight - tag someone to fight with your 🍆
@Client.on_message(filters.command("fight", prefixes="/") & filters.reply)
async def fight(client: Client, message: Message):
    try:
        if message.chat.type == "private":
            await message.reply_text("❌ This command can only be used in groups!")
            return

        user1 = await mongodb.dickplay.find_one({"user_id": message.from_user.id})
        user2 = await mongodb.dickplay.find_one({"user_id": message.reply_to_message.from_user.id})

        if not user1 or not user2:
            await message.reply_text("Both users need to have grown their 🍆 first!")
            return

        total1 = user1["size"] + random.randint(1, 10)
        total2 = user2["size"] + random.randint(1, 10)

        if total1 > total2:
            winner = message.from_user.first_name
        elif total1 < total2:
            winner = message.reply_to_message.from_user.first_name
        else:
            winner = "It's a tie!"

        await message.reply_text(
            f"{message.from_user.first_name}: {user1['size']} + bonus = {total1}\n"
            f"{message.reply_to_message.from_user.first_name}: {user2['size']} + bonus = {total2}\n\n"
            f"🏆 Winner: {winner}"
        )
    except Exception as e:
        await message.reply_text(f"⚠️ Error: {e}")

# ----------------------
# /dtop — Show top 5 users
@Client.on_message(filters.command("dtop", prefixes="/"))
async def dick_top(client: Client, message: Message):
    try:
        if message.chat.type == "private":
            await message.reply_text("❌ This command can only be used in groups!")
            return

        top = await mongodb.dickplay.find().sort("size", -1).limit(5).to_list(length=5)
        if not top:
            await message.reply_text("No data available yet. Grow your 🍆 first!")
            return

        text = "🏆 **Top DickGrowers:**\n\n"
        for idx, user in enumerate(top, start=1):
            try:
                user_info = await client.get_users(user['user_id'])
                name = user_info.first_name
                if user_info.last_name:
                    name += f" {user_info.last_name}"
            except:
                name = f"User {user['user_id']}"
            text += f"{idx}. {name} — {user['size']} cm\n"
        
        await message.reply_text(text)
    except Exception as e:
        await message.reply_text(f"⚠️ Error: {e}")

# ----------------------
# /dhelp — Show help
@Client.on_message(filters.command("dhelp", prefixes="/"))
async def dick_help(client: Client, message: Message):
    try:
        help_text = (
            "**DickGrower Bot Commands:**\n\n"
            "/grow — Grow your 🍆 randomly\n"
            "/fight — Tag someone to fight and see who wins\n"
            "/dick — Check your current 🍆 size\n"
            "/compare — Reply to someone to compare 🍆 size\n"
            "/dtop — Show top users with the largest 🍆\n"
            "/dhelp — Show this help message"
        )
        await message.reply_text(help_text)
    except Exception as e:
        await message.reply_text(f"⚠️ Error: {e}")
