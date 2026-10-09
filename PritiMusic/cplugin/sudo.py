from pyrogram import filters, Client
from pyrogram.types import Message
from PritiMusic import app
from PritiMusic.misc import SUDOERS
from PritiMusic.utils.database import clonebotdb
from PritiMusic.utils.extraction import extract_user

# --- HELPER: Check Permissions ---
async def is_clone_owner(client, message):
    user_id = message.from_user.id
    bot_id = client.me.id
    
    # 1. Allow Main Bot Sudoers
    if user_id in SUDOERS:
        return True
    
    # 2. Allow Clone Bot Owner
    clone_data = await clonebotdb.find_one({"bot_id": bot_id})
    if clone_data and clone_data.get("user_id") == user_id:
        return True
        
    return False

# =====================================================================
# COMMANDS
# =====================================================================

@Client.on_message(filters.command(["addsudo", "setsudo"]) & filters.group)
async def clone_add_sudo(client: Client, message: Message):
    if not await is_clone_owner(client, message):
        return
    
    if not message.reply_to_message and len(message.command) != 2:
        return await message.reply_text("❌ **Usage:** `/addsudo @User` or Reply to user.")

    user = await extract_user(message)
    if not user:
        return await message.reply_text("❌ **User not found.**")

    bot_id = client.me.id
    clone_data = await clonebotdb.find_one({"bot_id": bot_id})
    owner_id = clone_data.get("user_id")

    if user.id == owner_id:
        return await message.reply_text("⚠️ **They are already the Owner.**")
    
    if user.id == bot_id:
        return await message.reply_text("⚠️ **You cannot add the bot as a sudoer.**")

    # ✅ Optimized: Use $addToSet to prevent duplicates automatically
    await clonebotdb.update_one(
        {"bot_id": bot_id},
        {"$addToSet": {"sudoers": user.id}},
        upsert=True
    )
    
    await message.reply_text(f"✅ {user.mention} **has been promoted to Bot Admin!**")


@Client.on_message(filters.command(["delsudo", "rmsudo"]) & filters.group)
async def clone_del_sudo(client: Client, message: Message):
    if not await is_clone_owner(client, message):
        return

    if not message.reply_to_message and len(message.command) != 2:
        return await message.reply_text("❌ **Usage:** `/delsudo @User` or Reply to user.")

    user = await extract_user(message)
    if not user:
        return await message.reply_text("❌ **User not found.**")

    bot_id = client.me.id
    
    # Update Database
    await clonebotdb.update_one(
        {"bot_id": bot_id},
        {"$pull": {"sudoers": user.id}}
    )
    
    await message.reply_text(f"✅ {user.mention} **has been removed from Admin list.**")


@Client.on_message(filters.command(["delallsudo", "rmallsudo"]) & filters.group)
async def clone_del_all_sudo(client: Client, message: Message):
    if not await is_clone_owner(client, message):
        return
        
    bot_id = client.me.id
    
    await clonebotdb.update_one(
        {"bot_id": bot_id},
        {"$set": {"sudoers": []}}
    )
    
    await message.reply_text("✅ **All Bot Admins have been removed successfully.**")


@Client.on_message(filters.command(["sudolist", "sudoers", "adminlist"]) & filters.group)
async def clone_sudo_list(client: Client, message: Message):
    bot_id = client.me.id
    
    clone_data = await clonebotdb.find_one({"bot_id": bot_id})
    if not clone_data:
        return await message.reply_text("❌ **Bot Data Not Found.**")
    
    # Owner Info
    try:
        owner_id = clone_data.get("user_id")
        owner_obj = await client.get_users(owner_id)
        owner_name = owner_obj.mention
    except:
        owner_name = "Unknown"

    sudoers = clone_data.get("sudoers", [])
    
    text = f"🛡️ **{client.me.first_name} Admin List:**\n\n"
    text += f"👑 **Owner:** {owner_name}\n"
    
    if not sudoers:
        text += "\n❌ **No Sudoers (Admins) assigned.**"
    else:
        text += "\n👮 **Sudoers:**\n"
        for user_id in sudoers:
            try:
                user = await client.get_users(user_id)
                text += f"┣ {user.mention}\n"
            except:
                text += f"┣ User ID: `{user_id}`\n"

    await message.reply_text(text)
