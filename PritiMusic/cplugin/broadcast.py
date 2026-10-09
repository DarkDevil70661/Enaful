import asyncio
from pyrogram import filters, Client
from pyrogram.errors import FloodWait, InputUserDeactivated, UserIsBlocked, PeerIdInvalid
from pyrogram.types import Message

from PritiMusic import app
from PritiMusic.misc import SUDOERS
from PritiMusic.utils.database import (
    get_served_chats_clone,
    get_served_users_clone,
)
from PritiMusic.utils.database.clonedb import clonebotdb
from PritiMusic.utils.decorators.language import language
from config import SUPPORT_CHAT

# ✅ FIX: Dictionary Lock (Taaki ek bot ka broadcast dusre ko na roke)
BROADCAST_LOCK = {}

@Client.on_message(filters.command(["broadcast", "gcast", "bcast"]))
@language
async def broadcast_message(client: Client, message: Message, _):
    bot_id = client.me.id
    user_id = message.from_user.id

    # 1. AUTH CHECK (Clone Owner + SUDOERS)
    clone_data = await clonebotdb.find_one({"bot_id": bot_id})
    owner_id = clone_data.get("user_id") if clone_data else None

    if user_id != owner_id and user_id not in SUDOERS:
        return await message.reply_text(_["c_brod_1"].format(SUPPORT_CHAT))

    # 2. CHECK LOCK
    if BROADCAST_LOCK.get(bot_id):
        return await message.reply_text("⏳ **Broadcast is already running. Please wait.**")

    # 3. PARSE QUERY / REPLY
    if message.reply_to_message:
        query = message.text.split(None, 1)[1] if len(message.command) > 1 else ""
    else:
        if len(message.command) < 2:
            return await message.reply_text(_["broad_2"])
        query = message.text.split(None, 1)[1]

    # Clean flags
    flags = ["-pin", "-nobot", "-pinloud", "-user"]
    query_to_send = query
    for flag in flags:
        query_to_send = query_to_send.replace(flag, "").strip()

    if not message.reply_to_message and not query_to_send:
        return await message.reply_text(_["broad_8"])

    # 4. START BROADCAST
    BROADCAST_LOCK[bot_id] = True
    status_msg = await message.reply_text(_["broad_1"])
    
    sent = 0
    pin_count = 0
    failed = 0

    try:
        # --- PART A: BROADCAST TO GROUPS ---
        if "-nobot" not in message.text:
            served_chats = await get_served_chats_clone(bot_id)
            
            for chat in served_chats:
                try:
                    chat_id = int(chat["chat_id"])
                    
                    # Send or Forward
                    if message.reply_to_message:
                        m = await client.forward_messages(
                            chat_id, 
                            message.chat.id, 
                            message.reply_to_message.id
                        )
                    else:
                        m = await client.send_message(chat_id, text=query_to_send)
                    
                    # Pin Logic
                    if "-pin" in message.text or "-pinloud" in message.text:
                        try:
                            msg_obj = m[0] if isinstance(m, list) else m
                            notify = "-pinloud" in message.text
                            await msg_obj.pin(disable_notification=not notify)
                            pin_count += 1
                        except:
                            pass
                            
                    sent += 1
                    await asyncio.sleep(0.2)
                    
                except FloodWait as fw:
                    await asyncio.sleep(int(fw.value))
                except Exception:
                    failed += 1
                    continue
            
            await message.reply_text(_["broad_3"].format(sent, pin_count))

        # --- PART B: BROADCAST TO USERS (Optional) ---
        if "-user" in message.text:
            susr = 0
            served_users = await get_served_users_clone(bot_id)
            
            for user in served_users:
                try:
                    user_id = int(user["user_id"])
                    
                    if message.reply_to_message:
                        await client.forward_messages(
                            user_id, 
                            message.chat.id, 
                            message.reply_to_message.id
                        )
                    else:
                        await client.send_message(user_id, text=query_to_send)
                        
                    susr += 1
                    await asyncio.sleep(0.2)
                    
                except FloodWait as fw:
                    await asyncio.sleep(int(fw.value))
                except Exception:
                    pass
            
            await message.reply_text(_["broad_4"].format(susr))

    finally:
        # Lock Release
        BROADCAST_LOCK[bot_id] = False
        await status_msg.delete()
