import os
import zipfile
import tempfile
import shutil
import subprocess
import asyncio
import requests
from pyrogram import filters
from pyrogram.types import Message
from ShrutiMusic import app  # Change to your bot base import
from ShrutiMusic.misc import SUDOERS
from config import OWNER_ID
from ShrutiMusic.core.mongo import mongodb

# Temporary GitHub credentials cache
GIT_CONFIG = {}

# MongoDB collection for persistent lock
GIT_DB = mongodb.gitupload

# ---------- Helper Functions ---------- #

def run(cmd, cwd=None):
    """Run shell command safely."""
    try:
        subprocess.run(cmd, cwd=cwd, shell=True, check=True,
                       stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    except subprocess.CalledProcessError as e:
        if "nothing to commit" in str(e):
            return
        raise e


def create_repo(token, repo_name, private=True):
    """Create GitHub repo (blocking)."""
    headers = {"Authorization": f"token {token}"}
    data = {"name": repo_name, "private": private}
    r = requests.post("https://api.github.com/user/repos", json=data, headers=headers)
    if r.status_code == 422:
        return f"⚠️ Repo **{repo_name}** already exists."
    elif r.ok:
        return f"✅ Repo **{repo_name}** created successfully."
    else:
        return f"❌ Failed to create repo:\n`{r.text}`"


def upload_to_github(username, email, token, zip_path, repo_name, branch="main", private=True):
    """Upload ZIP contents to GitHub (blocking)."""
    temp_dir = tempfile.mkdtemp()
    with zipfile.ZipFile(zip_path, "r") as zip_ref:
        zip_ref.extractall(temp_dir)

    # Flatten nested folder if present
    items = os.listdir(temp_dir)
    if len(items) == 1 and os.path.isdir(os.path.join(temp_dir, items[0])):
        nested = os.path.join(temp_dir, items[0])
        for f in os.listdir(nested):
            shutil.move(os.path.join(nested, f), temp_dir)
        shutil.rmtree(nested)

    repo_url = f"https://{token}@github.com/{username}/{repo_name}.git"
    run("git init", cwd=temp_dir)
    run(f'git config user.email "{email}"', cwd=temp_dir)
    run(f'git config user.name "{username}"', cwd=temp_dir)
    run("git add .", cwd=temp_dir)
    run('git commit --allow-empty -m "Initial upload from bot"', cwd=temp_dir)
    run(f"git branch -M {branch}", cwd=temp_dir)
    run("git remote remove origin || true", cwd=temp_dir)
    run(f"git remote add origin {repo_url}", cwd=temp_dir)
    run(f"git push -u origin {branch} --force", cwd=temp_dir)
    shutil.rmtree(temp_dir)

    visibility = "Private" if private else "Public"
    return (
        f"✅ REPO **{repo_name}** UPLOADED SUCCESSFULLY!\n\n"
        f"🔒 Visibility: **{visibility}**\n"
        f"🌿 Branch: **{branch}**\n"
        f"🔗 URL: https://github.com/{username}/{repo_name}"
    )


# ---------- MongoDB Lock Helpers ---------- #

async def get_lock_state() -> bool:
    doc = await GIT_DB.find_one({"_id": "lock"})
    return doc["locked"] if doc else False

async def set_lock_state(state: bool):
    await GIT_DB.update_one({"_id": "lock"}, {"$set": {"locked": state}}, upsert=True)


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
    is_owner_or_sudo = user_id == OWNER_ID or user_id in SUDOERS

    locked = await get_lock_state()
    if locked and user_id != OWNER_ID:  # Only owner bypasses lock
        return await message.reply_text(
            "🚫 **THIS FEATURE IS RIGHT NOW LOCKED!**\n"
            "Please ask permission from the owner to unlock it."
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
    msg = await message.reply_text("📤 **Uploading to GitHub... Please wait!**")

    try:
        # Run blocking calls in separate thread
        result_msg = await asyncio.to_thread(create_repo, creds["token"], repo_name, private)
        upload_msg = await asyncio.to_thread(
            upload_to_github,
            creds["username"], creds["email"], creds["token"],
            zip_path, repo_name, branch, private
        )
        await msg.edit(f"{result_msg}\n\n{upload_msg}")
    except Exception as e:
        await msg.edit(f"❌ **Upload failed:**\n`{e}`")
    finally:
        if os.path.exists(zip_path):
            os.remove(zip_path)


@app.on_message(filters.command("gitlock") & filters.user(OWNER_ID))
async def git_lock(_, message: Message):
    """Lock uploads (owner-only)."""
    await set_lock_state(True)
    await message.reply_text("🔒 **Git upload locked!** Only Owner can use it now.")


@app.on_message(filters.command("gitunlock") & filters.user(OWNER_ID))
async def git_unlock(_, message: Message):
    """Unlock uploads (owner-only)."""
    await set_lock_state(False)
    await message.reply_text("🔓 **Git upload unlocked!** Public users can now use `/gitupload`.")
