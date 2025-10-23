import os
import zipfile
import tempfile
import shutil
import requests
import subprocess
import asyncio
from pyrogram import filters
from pyrogram.types import Message
from ShrutiMusic import app
from ShrutiMusic.misc import SUDOERS
from config import OWNER_ID
from motor.motor_asyncio import AsyncIOMotorClient

# MongoDB setup (persistent lock)
MONGO_URL = os.getenv("MONGO_DB_URI")
mongo_client = AsyncIOMotorClient(MONGO_URL)
db = mongo_client["ShrutiMusic"]
lock_collection = db["git_upload_lock"]

# Temporary GitHub credential cache
GIT_CONFIG = {}

# ---------- Helper Functions ---------- #

def run(cmd, cwd=None):
    """Run shell command safely."""
    try:
        subprocess.run(
            cmd, cwd=cwd, shell=True, check=True,
            stdout=subprocess.PIPE, stderr=subprocess.PIPE
        )
    except subprocess.CalledProcessError as e:
        if "nothing to commit" in str(e):
            return
        raise e


async def is_upload_locked():
    """Check if upload is locked in DB."""
    data = await lock_collection.find_one({"_id": "lock_state"})
    return data and data.get("locked", False)


async def set_upload_lock(state: bool):
    """Set upload lock in DB."""
    await lock_collection.update_one(
        {"_id": "lock_state"},
        {"$set": {"locked": state}},
        upsert=True
    )


async def create_repo(token, repo_name, private=True):
    """Create a GitHub repo."""
    def _create():
        headers = {"Authorization": f"token {token}"}
        data = {"name": repo_name, "private": private}
        r = requests.post("https://api.github.com/user/repos", json=data, headers=headers)
        if r.status_code == 422:
            return f"⚠️ Repo **{repo_name}** already exists."
        elif r.ok:
            return f"✅ Repo **{repo_name}** created successfully."
        else:
            return f"❌ Failed to create repo:\n`{r.text}`"
    return await asyncio.to_thread(_create)


async def upload_to_github(username, email, token, zip_path, repo_name, branch="main", private=True, msg: Message = None):
    """Upload ZIP content to GitHub with watermark and progress updates."""
    temp_dir = tempfile.mkdtemp()
    await asyncio.to_thread(zipfile.ZipFile(zip_path, "r").extractall, temp_dir)

    # Flatten nested folder if present
    items = os.listdir(temp_dir)
    if len(items) == 1 and os.path.isdir(os.path.join(temp_dir, items[0])):
        nested = os.path.join(temp_dir, items[0])
        for f in os.listdir(nested):
            shutil.move(os.path.join(nested, f), temp_dir)
        shutil.rmtree(nested)

    # Add watermark to every .py file with progress
    py_files = []
    for root, _, files in os.walk(temp_dir):
        for file in files:
            if file.endswith(".py"):
                py_files.append(os.path.join(root, file))

    total_files = len(py_files)
    if msg:
        progress = await msg.reply_text("💾 Watermarking files… 0%")

    for i, file_path in enumerate(py_files, 1):
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                code = f.read()
            top = "# ᴀʟʟʙᴏᴛsᴜᴘᴘᴏʀᴛ © github.com\n"
            bottom = "\n\nfrom Love 🎀 #ᴀʟʟʙᴏᴛsᴜᴘᴘᴏʀᴛ\n"
            if not code.strip().startswith("# ᴀʟʟʙᴏᴛsᴜᴘᴘᴏʀᴛ"):
                code = top + code
            if not code.strip().endswith("#ᴀʟʟʙᴏᴛsᴜᴘᴘᴏʀᴛ"):
                code += bottom
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(code)
        except Exception as e:
            if msg:
                await msg.edit(f"❌ Error watermarking `{os.path.basename(file_path)}`:\n`{e}`")
            continue

        if msg:
            percent = int(i / total_files * 100)
            await msg.edit(f"💾 Watermarking files… {percent}%")

    # GitHub upload
    repo_url = f"https://{token}@github.com/{username}/{repo_name}.git"

    def _git_ops():
        run("git init", cwd=temp_dir)
        run(f'git config user.email "{email}"', cwd=temp_dir)
        run(f'git config user.name "{username}"', cwd=temp_dir)
        run("git add .", cwd=temp_dir)
        run('git commit --allow-empty -m "ᴀʟʟʙᴏᴛsᴜᴘᴘᴏʀᴛ"', cwd=temp_dir)
        run(f"git branch -M {branch}", cwd=temp_dir)
        run("git remote remove origin || true", cwd=temp_dir)
        run(f"git remote add origin {repo_url}", cwd=temp_dir)
        run(f"git push -u origin {branch} --force", cwd=temp_dir)

    await asyncio.to_thread(_git_ops)
    shutil.rmtree(temp_dir)

    visibility = "Private" if private else "Public"
    return (
        f"✅ REPO **{repo_name}** UPLOADED SUCCESSFULLY!\n\n"
        f"🔒 Visibility: **{visibility}**\n"
        f"🌿 Branch: **{branch}**\n"
        f"🔗 URL: https://github.com/{username}/{repo_name}"
    )

# ---------- Commands ---------- #

@app.on_message(filters.command("gitconfig"))
async def git_config(_, message: Message):
    """Save GitHub credentials temporarily."""
    if len(message.command) != 4:
        return await message.reply_text("» **Usage:** `/gitconfig username email token`")

    username, email, token = message.command[1:]
    user_id = message.from_user.id
    GIT_CONFIG[user_id] = {"username": username, "email": email, "token": token}

    await message.reply_text("✅ **GitHub Config Set Successfully!**\n_Valid for 5 minutes._")

    # Expire after 5 minutes
    await asyncio.sleep(300)
    if user_id in GIT_CONFIG:
        del GIT_CONFIG[user_id]


@app.on_message(filters.command("gitupload"))
async def git_upload(_, message: Message):
    """Upload replied ZIP to GitHub repo."""
    user_id = message.from_user.id
    locked = await is_upload_locked()

    if locked and user_id != OWNER_ID:
        return await message.reply_text(
            "🚫 **THIS FEATURE IS RIGHT NOW LOCKED, PLEASE ASK PERMISSION FROM THE OWNER TO UNLOCK IT.**"
        )

    if not message.reply_to_message or not message.reply_to_message.document:
        return await message.reply_text("» **Reply to a ZIP file** with this command!")

    if len(message.command) != 4:
        return await message.reply_text("» **Usage:** `/gitupload repo_name private/public branch_name`")

    if user_id not in GIT_CONFIG:
        return await message.reply_text("⚠️ **No GitHub config found!**\nUse `/gitconfig` first.")

    repo_name, visibility, branch = message.command[1:]
    private = visibility.lower() == "private"
    creds = GIT_CONFIG[user_id]

    zip_path = await message.reply_to_message.download()
    progress_msg = await message.reply_text("📤 **Uploading to GitHub... Please wait!**")

    try:
        result_msg = await create_repo(creds["token"], repo_name, private)
        upload_msg = await upload_to_github(
            creds["username"], creds["email"], creds["token"],
            zip_path, repo_name, branch, private, msg=progress_msg
        )
        await progress_msg.edit(f"{result_msg}\n\n{upload_msg}")
    except Exception as e:
        await progress_msg.edit(f"❌ **Upload failed:**\n`{e}`")
    finally:
        os.remove(zip_path)


@app.on_message(filters.command("gitlock") & filters.user(OWNER_ID))
async def git_lock(_, message: Message):
    """Lock public uploads (Owner only)."""
    await set_upload_lock(True)
    await message.reply_text("🔒 **Git upload locked!** Only Owner can unlock it.")


@app.on_message(filters.command("gitunlock") & filters.user(OWNER_ID))
async def git_unlock(_, message: Message):
    """Unlock public uploads (Owner only)."""
    await set_upload_lock(False)
    await message.reply_text("🔓 **Git upload unlocked!** Public users can use `/gitupload` again.")
