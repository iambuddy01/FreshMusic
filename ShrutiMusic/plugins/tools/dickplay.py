import random
from pyrogram import Client, filters
from pyrogram.types import Message
from ShrutiMusic.core.mongo import mongodb  # ✅ your existing Mongo connection

# Mongo collection for dick sizes
dickdb = mongodb.dickplay

# Helper: get user’s size (default = 10cm)
async def get_size(user_id: int) -> float:
    user = await dickdb.find_one({"user_id": user_id})
    return user["size"] if user else 10.0

# Helper: update size
async def update_size(user_id: int, new_size: float):
    await dickdb.update_one(
        {"user_id": user_id},
        {"$set": {"size": new_size}},
        upsert=True
    )

# 🍆 /grow — grow your size
@Client.on_message(filters.command("grow", prefixes=".") & ~filters.edited)
async def grow_dick(client: Client, message: Message):
    user_id = message.from_user.id
    user_name = message.from_user.first_name

    growth = round(random.uniform(0.1, 5.0), 2)
    old_size = await get_size(user_id)
    new_size = round(old_size + growth, 2)
    await update_size(user_id, new_size)

    await message.reply_text(
        f"🍆 {user_name}'s dick grew by {growth} cm!\n"
        f"📏 Current size: {new_size} cm"
    )

# 🥶 /shrink — shrink your size
@Client.on_message(filters.command("shrink", prefixes=".") & ~filters.edited)
async def shrink_dick(client: Client, message: Message):
    user_id = message.from_user.id
    user_name = message.from_user.first_name

    shrink = round(random.uniform(0.1, 3.0), 2)
    old_size = await get_size(user_id)
    new_size = max(1.0, round(old_size - shrink, 2))
    await update_size(user_id, new_size)

    await message.reply_text(
        f"🥶 {user_name}'s dick shrunk by {shrink} cm!\n"
        f"📏 Current size: {new_size} cm"
    )

# 📊 /stats — show your current size
@Client.on_message(filters.command("stats", prefixes=".") & ~filters.edited)
async def check_stats(client: Client, message: Message):
    user_id = message.from_user.id
    user_name = message.from_user.first_name
    size = await get_size(user_id)

    await message.reply_text(f"📊 {user_name}'s current size: {size} cm 🍆")

# 🏆 /top — top 10 users by size
@Client.on_message(filters.command("top", prefixes=".") & ~filters.edited)
async def leaderboard(client: Client, message: Message):
    top_users = dickdb.find().sort("size", -1).limit(10)
    leaderboard_text = "🏆 **Top 10 Dicks:**\n\n"
    rank = 1

    async for user in top_users:
        try:
            name = (await client.get_users(user["user_id"])).first_name
        except:
            name = "Unknown User"
        leaderboard_text += f"{rank}. {name}: {user['size']} cm 🍆\n"
        rank += 1

    if rank == 1:
        leaderboard_text = "No stats recorded yet!"

    await message.reply_text(leaderboard_text)
