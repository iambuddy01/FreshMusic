import random
from pyrogram import Client, filters
from FreshMusic.mongo import mongodb

# MongoDB collection
dickdb = mongodb.dickdata


@Client.on_message(filters.command("grow", prefixes="/"))
async def grow_dick(client, message):
    user_id = message.from_user.id
    user = await dickdb.find_one({"user_id": user_id})

    growth = random.randint(1, 5)
    if not user:
        length = 5 + growth
        await dickdb.insert_one({"user_id": user_id, "length": length})
    else:
        length = user["length"] + growth
        await dickdb.update_one({"user_id": user_id}, {"$set": {"length": length}})

    await message.reply_text(
        f"🍆 Your dick grew by {growth} cm!\nNow it's **{length} cm** long!"
    )


@Client.on_message(filters.command("shrink", prefixes="/"))
async def shrink_dick(client, message):
    user_id = message.from_user.id
    user = await dickdb.find_one({"user_id": user_id})

    if not user:
        await message.reply_text("🍆 You don't have a dick yet! Use /grow first.")
        return

    shrink = random.randint(1, 4)
    new_length = max(0, user["length"] - shrink)
    await dickdb.update_one({"user_id": user_id}, {"$set": {"length": new_length}})

    await message.reply_text(
        f"😢 Your dick shrank by {shrink} cm!\nNow it's **{new_length} cm** long!"
    )


@Client.on_message(filters.command("dick", prefixes="/"))
async def check_dick(client, message):
    user_id = message.from_user.id
    user = await dickdb.find_one({"user_id": user_id})

    if not user:
        await message.reply_text("🍆 You don’t have a dick yet! Use /grow to start growing it!")
    else:
        await message.reply_text(f"🍆 Your current dick size is **{user['length']} cm**.")


@Client.on_message(filters.command("compare", prefixes="/"))
async def compare_dick(client, message):
    if not message.reply_to_message:
        await message.reply_text("Reply to someone to compare dicks 🍆")
        return

    user1_id = message.from_user.id
    user2_id = message.reply_to_message.from_user.id

    user1 = await dickdb.find_one({"user_id": user1_id})
    user2 = await dickdb.find_one({"user_id": user2_id})

    if not user1 or not user2:
        await message.reply_text("Both users need to have grown their dicks first using /grow.")
        return

    if user1["length"] > user2["length"]:
        await message.reply_text("🍆 You’re packing more! You win 😎")
    elif user1["length"] < user2["length"]:
        await message.reply_text("😢 You lost! The other one is bigger.")
    else:
        await message.reply_text("😳 It's a tie! Both are the same size 🍆")


@Client.on_message(filters.command("dickhelp", prefixes="/"))
async def dick_help(client, message):
    help_text = """
🍆 **DickPlay Command Help**

Here’s how to use the DickPlay module:

/grow — Grow your 🍆 randomly  
/shrink — Shrink your 🍆 randomly  
/dick — Check your current 🍆 size  
/compare — Reply to someone to compare your 🍆 size  
/dickhelp — Show this help message

💾 Your progress is automatically saved in MongoDB.
"""
    await message.reply_text(help_text, disable_web_page_preview=True)
