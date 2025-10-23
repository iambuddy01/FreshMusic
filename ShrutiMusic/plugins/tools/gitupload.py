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
from ShrutiMusic.core.mongo import mongo  # your existing mongo instance


# ────────────────────────────────
#   Temporary GitHub Credential Cache
# ────────────────────────────────
GIT_CONFIG = {}
LOCK_KEY = "github_upload_lock"


# ────────────────────────────────
#   Helper: Run shell commands
# ────────────────────────────────
def run(cmd, cwd=None):
    subprocess.run(cmd, cwd=cwd, shell=True, check=True,
                   stdout=subprocess.PIPE, stderr=subprocess.PIPE)


# ────────────────────────────────
#   Helper: Add watermark to .py files
# ────────────────────────────────
def add_watermark_to_py_files(folder_path: str):
    """Add watermark on top and bottom of every .py file."""
    top_mark = "# ᴀʟʟʙᴏᴛsᴜᴘᴘᴏʀᴛ © github.com\n"
    bottom_mark = "# from Love 🎀 #ᴀʟʟʙᴏᴛsᴜᴘᴘᴏʀᴛ\n"

    for root, _, files in os.walk(folder_path):
        for file in files:
            if file.endswith(".py"):
                file_path = os.path.join(root, file)
                try:
                    with open(file_path, "r+", encoding="utf-8") as f:
                        content = f.read().strip()

                        if not content.startswith(top_mark.strip()):
                            content = top_mark + "\n" + content

                        if not content.endswith(bottom_mark.strip()):
                            content = content + "\n\n" + bottom_mark

                        f.seek(0)
                        f.write(content)
                        f.truncate()
                except Exception:
                    pass


# ────────────────────────────────
#   GitHub Helpers (Async-Safe)
# ────────────────────────────────
async def create_repo(token, repo_name, private=True):
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


async def upload_to_github(username, email, token, zip_path, repo_name, branch="main", private=True):
    def _upload():
        temp_dir = tempfile.mkdtemp()
        with zipfile.ZipFile(zip_path, "r") as zip_ref:
            zip_ref.extractall(temp_dir)

        # Flatten nested folders if any
        items = os.listdir(temp_dir)
        if len(items) == 1 and os.path.isdir(os.path.join(temp_dir, items[0])):
            nested = os.path.join(temp_dir, items[0])
            for f in os.listdir(nested):
                shutil.move(os.path.join(nested, f), temp_dir)
            shutil.rmtree(nested)

        # Add watermark before committing
        add_watermark_to_py_files(temp_dir)

        repo_url = f"https://{token}@github.com/{username}/{repo_name}.git"
        run("git init", cwd=temp_dir)
        run(f'git config user.email "{email}"', cwd=temp_dir)
        run(f'git config user.name "{username}"', cwd=temp_dir)
        run("git add .", cwd=temp_dir)
        run('git commit -m "ᴀʟʟʙᴏᴛsᴜᴘᴘᴏʀᴛ"', cwd=temp_dir)
        run(f"git branch -M {branch}", cwd=temp_dir)
        run("git remote remove origin || true", cwd=temp_dir)
        run(f"git remote add origin {repo_url}", cwd=temp_dir)
        run(f"git push -u origin {branch} --force", cwd=temp_dir)
        shutil.rmtree(temp_dir)

        visibility = "Private" if private else "Public"
        return (
            f"✅ **{repo_name}** uploaded successfully!\n\n"
            f"🔒 Visibility: **{visibility}**\n"
            f"🌿 Branch: **{branch}**\n"
            f"🔗 [View on GitHub](https://github.com/{username}/{repo_name})"
        )

    return await asyncio.to_thread(_upload)


# ────────────────────────────────
#   MongoDB Persistent Lock Helper
# ────────────────────────────────
async def is_locked():
    doc = await mongo.github.find_one({"_id": LOCK_KEY})
    return doc and doc.get("locked", False)


async def set_lock_state(state: bool):
    await mongo.github.update_one({"_id": LOCK_KEY}, {"$set": {"locked": state}}, upsert=True)


# ────────────────────────────────
#   Commands
# ────────────────────────────────

@app.on_message(filters.command("gitconfig"))
async def git_config(_, message: Message):
    """Save GitHub credentials temporarily."""
    if len(message.command) != 4:
        return await message.reply_text("» **Usage:** `/gitconfig username email token`")

    username, email, token = message.command[1:]
    user_id = message.from_user.id
    GIT_CONFIG[user_id] = {"username": username, "email": email, "token": token}

    await message.reply_text("✅ **GitHub config saved!**\n_Valid for 5 minutes._")

    await asyncio.sleep(300)
    GIT_CONFIG.pop(user_id, None)


@app.on_message(filters.command("gitupload"))
async def git_upload(_, message: Message):
    """Upload replied ZIP to GitHub repo."""
    user_id = message.from_user.id
    locked = await is_locked()

    if locked and user_id != OWNER_ID:
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
        result_msg = await create_repo(creds["token"], repo_name, private)
        upload_msg = await upload_to_github(
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
    await set_lock_state(True)
    await message.reply_text("🔒 **Git upload locked!** Only owner can unlock it.")


@app.on_message(filters.command("gitunlock") & filters.user(OWNER_ID))
async def git_unlock(_, message: Message):
    await set_lock_state(False)
    await message.reply_text("🔓 **Git upload unlocked!** Everyone can now use `/gitupload` again.")
