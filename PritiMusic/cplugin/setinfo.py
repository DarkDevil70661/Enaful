import asyncio
from pyrogram import Client, filters
from pyrogram.types import Message
from PritiMusic import app
from PritiMusic.misc import SUDOERS
from PritiMusic.utils.decorators.language import language
from PritiMusic.utils.database.clonedb import (
    get_owner_id_from_db,
    get_cloned_support_chat,
    get_cloned_support_channel,
    clonebotdb
)
from config import SUPPORT_CHAT, OWNER_ID

# --- Helper: Clean URL ---
def clean_input(value):
    """Removes t.me, https, @ etc to store pure username/slug"""
    if "joinchat" in value:
        return value.strip()
    value = value.replace("https://", "").replace("http://", "")
    value = value.replace("t.me/", "").replace("telegram.me/", "")
    value = value.replace("@", "")
    return value.strip("/")

# --- Helper: Auth Check ---
async def check_auth(bot_id, user_id):
    if user_id in SUDOERS:
        return True
    
    c_owner = await get_owner_id_from_db(bot_id)
    if user_id == c_owner:
        return True
        
    return False

# --- Helper: Get Logging Info ---
async def get_logging_status(bot_id):
    data = await clonebotdb.find_one({"bot_id": bot_id})
    return data.get("logging", True) if data else True

async def get_log_channel(bot_id):
    data = await clonebotdb.find_one({"bot_id": bot_id})
    return data.get("logchannel") if data else None


# =====================================================================
# COMMANDS
# =====================================================================

@Client.on_message(filters.command(["setchannel", "setcchannel"]))
async def set_channel(client: Client, message: Message):
    bot_id = client.me.id
    
    if not await check_auth(bot_id, message.from_user.id):
        return await message.reply_text("❌ **Only Bot Owner can use this.**")
    
    if len(message.command) < 2:
        return await message.reply_text("Usage: `/setchannel @username`")
    
    value = clean_input(message.command[1])
    
    await clonebotdb.update_one(
        {"bot_id": bot_id},
        {"$set": {"channel": value}},
        upsert=True
    )
    await message.reply_text(f"✅ **Channel Set To:** `{value}`")


@Client.on_message(filters.command(["setsupport", "setcsupport"]))
async def set_support(client: Client, message: Message):
    bot_id = client.me.id
    
    if not await check_auth(bot_id, message.from_user.id):
        return await message.reply_text("❌ **Only Bot Owner can use this.**")
    
    if len(message.command) < 2:
        return await message.reply_text("Usage: `/setsupport @username`")

    value = clean_input(message.command[1])
    
    await clonebotdb.update_one(
        {"bot_id": bot_id},
        {"$set": {"support": value}},
        upsert=True
    )
    await message.reply_text(f"✅ **Support Group Set To:** `{value}`")


@Client.on_message(filters.command(["botinfo", "cinfo"]))
async def bot_info(client: Client, message: Message):
    bot_id = client.me.id
    
    if not await check_auth(bot_id, message.from_user.id):
        return await message.reply_text("❌ **Only Bot Owner can use this.**")

    channel = await get_cloned_support_channel(bot_id) or "Not Set"
    support = await get_cloned_support_chat(bot_id) or "Not Set"
    
    log_status = await get_logging_status(bot_id)
    log_channel = await get_log_channel(bot_id) or "Not Set"
    
    await message.reply_text(
        f"📊 **{client.me.first_name} Info:**\n\n"
        f"🆔 **Bot ID:** `{bot_id}`\n"
        f"📢 **Channel:** {channel}\n"
        f"💬 **Support:** {support}\n\n"
        f"📝 **Logger:** {'✅' if log_status else '❌'}\n"
        f"📂 **Log Channel:** `{log_channel}`"
    )


# --- LOGGER SETTINGS ---

@Client.on_message(filters.command(["logger", "clogger"]))
async def toggle_logging(client: Client, message: Message):
    bot_id = client.me.id
    
    if not await check_auth(bot_id, message.from_user.id):
        return await message.reply_text("❌ **Only Bot Owner can use this.**")

    if len(message.command) != 2:
        return await message.reply_text("Usage: `/logger [enable|disable]`")

    state = message.command[1].lower()
    
    if state == "enable":
        status = True
        text = "✅ **Logging Enabled!**"
    elif state == "disable":
        status = False
        text = "❌ **Logging Disabled!**"
    else:
        return await message.reply_text("Usage: `/logger [enable|disable]`")
    
    await clonebotdb.update_one(
        {"bot_id": bot_id},
        {"$set": {"logging": status}},
        upsert=True
    )
    await message.reply_text(text)


@Client.on_message(filters.command(["setlogger", "setlogchannel"]))
async def set_log_channel(client: Client, message: Message):
    bot_id = client.me.id
    
    if not await check_auth(bot_id, message.from_user.id):
        return await message.reply_text("❌ **Only Bot Owner can use this.**")

    if len(message.command) != 2:
        return await message.reply_text("Usage: `/setlogger -100xxxxxxxx`")

    try:
        group_id = int(message.command[1])
    except:
        return await message.reply_text("❌ Invalid Chat ID. Make sure it starts with `-100`")

    if not str(group_id).startswith("-100"):
        return await message.reply_text("❌ Invalid Group ID. Must start with `-100`")

    # Verify Bot Permission
    try:
        await client.send_message(group_id, "✅ **Logger Channel Set Successfully!**")
    except:
        return await message.reply_text("❌ **Error:** I cannot send messages to that channel. Make me Admin first!")

    await clonebotdb.update_one(
        {"bot_id": bot_id},
        {"$set": {"logchannel": group_id, "logging": True}}, # Auto Enable
        upsert=True
    )
    
    await message.reply_text(f"✅ **Log Channel Set To:** `{group_id}`")
