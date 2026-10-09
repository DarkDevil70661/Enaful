import asyncio
import os
import random
from pyrogram import filters, Client
from pyrogram.errors import (
    FloodWait, UserAdminInvalid, PeerIdInvalid, 
    UserIsBlocked, InputUserDeactivated, 
    AuthKeyUnregistered, UserDeactivated,
    UserNotParticipant, ChatAdminRequired
)
from pyrogram.types import Message

from PritiMusic import app
from PritiMusic.misc import SUDOERS
from PritiMusic.utils.database.clonedb import (
    get_all_clones, 
    get_served_chats_clone
)
from PritiMusic.utils.decorators.language import language
from PritiMusic.utils.extraction import extract_user
from config import API_ID, API_HASH, START_IMG_URL, LOGGER_ID 

# Global Flag to Stop Process
IS_CGBAN_RUNNING = False

def get_random_cgban_img():
    if START_IMG_URL:
        if isinstance(START_IMG_URL, list):
            return random.choice(START_IMG_URL)
        return START_IMG_URL
    return "https://telegra.ph/file/2e3d368e77c449c287430.jpg"

@app.on_message(filters.command(["stopcgban", "stopclonegban"]) & SUDOERS)
async def stop_cgban_process(client, message):
    global IS_CGBAN_RUNNING
    if not IS_CGBAN_RUNNING:
        return await message.reply_text("❌ **Abhi koi Gban process nahi chal raha.**")
    
    IS_CGBAN_RUNNING = False
    await message.reply_text("🛑 **Rok diya gaya hai!**\nCurrent batch khatam hote hi ruk jayega.")

# --- MAIN LOGIC: Clone Ban Executor ---
async def execute_ban_via_clone(token, bot_id, user_id, unban=False):
    groups_affected = 0
    status = "FAILED"
    
    try:
        # 1. Clone ke saare groups nikalo Database se
        chats = await get_served_chats_clone(bot_id)
        if not chats:
            return 0, "NO_CHATS"

        # 2. Clone Client Start karo (RAM mein)
        async with Client(
            f"cgban_{bot_id}",
            api_id=API_ID,
            api_hash=API_HASH,
            bot_token=token,
            in_memory=True,
            no_updates=True
        ) as clone_app:
            
            # 3. Har Group mein check karo aur ban karo
            for chat in chats:
                chat_id = int(chat['chat_id'])
                try:
                    if unban:
                        await clone_app.unban_chat_member(chat_id, user_id)
                    else:
                        # Ye line "Search & Ban" dono ka kaam karegi
                        await clone_app.ban_chat_member(chat_id, user_id)
                    
                    groups_affected += 1
                    await asyncio.sleep(0.1) # Fast processing
                
                except UserNotParticipant:
                    # User group me nahi hai - Ignore karo
                    continue
                except (UserAdminInvalid, ChatAdminRequired):
                    # Clone admin nahi hai - Ignore karo
                    continue
                except PeerIdInvalid:
                    # Chat exist nahi karti - Ignore karo
                    continue
                except FloodWait as e:
                    # Agar FloodWait 10 sec se kam hai toh wait karo, varna skip
                    if int(e.value) > 10:
                        continue
                    await asyncio.sleep(int(e.value))
                except Exception:
                    continue
            
            status = "SUCCESS"
            
    except (AuthKeyUnregistered, UserDeactivated):
        status = "TOKEN_EXPIRED"
    except Exception as e:
        status = "ERROR"
        
    return groups_affected, status

@app.on_message(filters.command(["cgban", "clonegban"]) & SUDOERS)
@language
async def clone_global_ban_all(client, message: Message, _):
    global IS_CGBAN_RUNNING
    
    if IS_CGBAN_RUNNING:
        return await message.reply_text("⚠️ **Pehle se ek Gban chal raha hai!**")

    # User Extract
    user = await extract_user(message)
    if not user:
        return await message.reply_text("❌ **User nahi mila.** Reply karein ya ID dein.")

    if user.id == message.from_user.id:
        return await message.reply_text("❌ **Khud ko ban karoge?**")
    elif user.id in SUDOERS:
        return await message.reply_text("❌ **Sudo User ko ban nahi kar sakte.**")
    
    # Reason
    reason = "Spamming/Abuse"
    if len(message.command) > 2:
        reason = message.text.split(None, 2)[2]
    elif message.reply_to_message and len(message.command) > 1:
        reason = message.text.split(None, 1)[1]

    IS_CGBAN_RUNNING = True
    
    try:
        mystic = await message.reply_photo(
            photo=get_random_cgban_img(),
            caption=f"☢️ **CLONE GLOBAL BAN CHALU**\n\n**Target:** {user.mention}\n**ID:** `{user.id}`\n**Reason:** `{reason}`\n\n🔄 **Saare Clones ko activate kar raha hoon...**",
        )

        # Clone List Fetch
        all_clones = []
        async for c in get_all_clones():
            all_clones.append(c)
            
        if not all_clones:
            await mystic.edit_text("❌ **Database mein koi Clone Bot nahi mila.**")
            return

        await mystic.edit_caption(f"☢️ **ATTACK MODE ON**\n\n**Target:** {user.mention}\n**Total Clones:** {len(all_clones)}\n⚡ **Har group mein dhoondh kar ban kiya ja raha hai...**")

        total_clones = len(all_clones)
        active_clones_used = 0
        total_groups_banned = 0
        REPORT_LOGS = [f"CLONE GBAN REPORT\nTarget: {user.id}\nReason: {reason}\n"]
        BATCH_SIZE = 5  # Ek baar mein 5 clones (Safe Limit)
        
        for i in range(0, total_clones, BATCH_SIZE):
            if not IS_CGBAN_RUNNING: break
            
            batch = all_clones[i:i + BATCH_SIZE]
            tasks = []
            
            for clone in batch:
                token = clone.get('token')
                bot_id = clone.get('bot_id')
                bot_user = clone.get('username', 'Unknown')
                
                if token and bot_id:
                    task = asyncio.create_task(execute_ban_via_clone(token, bot_id, user.id, unban=False))
                    tasks.append((task, bot_user))

            # Task Execution
            for task, bot_user in tasks:
                affected, status = await task
                if status == "SUCCESS":
                    active_clones_used += 1
                
                if affected > 0:
                    total_groups_banned += affected
                    REPORT_LOGS.append(f"@{bot_user}: Found & Banned in {affected} chats.")
                elif status == "TOKEN_EXPIRED":
                    REPORT_LOGS.append(f"@{bot_user}: Bot Token Expired.")

            # Progress Update (Har 10 clone ke baad)
            if i % 10 == 0:
                try:
                    await mystic.edit_caption(
                        f"☢️ **CLONE GBAN STATUS**\n\n"
                        f"🤖 **Clones Checked:** {i}/{total_clones}\n"
                        f"🚫 **Groups Banned:** {total_groups_banned}\n"
                        f"⏳ **Process chal raha hai...**"
                    )
                except:
                    pass

        # Final Report
        final_text = (
            f"✅ **Clone Gban Complete!**\n\n"
            f"👤 **Target:** {user.mention}\n"
            f"📝 **Reason:** `{reason}`\n"
            f"🤖 **Active Clones:** {active_clones_used}/{total_clones}\n"
            f"🚫 **Total Groups Banned:** {total_groups_banned}\n"
            f"⚠️ **Note:** Jaha user mila, waha ban kar diya gaya."
        )
        
        await mystic.edit_caption(final_text)
        
        # File Report
        if len(REPORT_LOGS) > 1:
            file_name = f"cgban_{user.id}.txt"
            with open(file_name, "w", encoding="utf-8") as f:
                f.write("\n".join(REPORT_LOGS))
            try:
                await message.reply_document(file_name, caption=f"📊 **Full Ban Report**")
                os.remove(file_name)
            except:
                pass

        # Logger
        if LOGGER_ID:
            try:
                await app.send_message(
                    LOGGER_ID,
                    f"**☢️ #CLONE_GLOBAL_BAN**\n\n**Admin:** {message.from_user.mention}\n**Target:** {user.mention}\n**Total Bans:** {total_groups_banned}"
                )
            except:
                pass
                
    except Exception as e:
        await message.reply_text(f"❌ **Error:** {str(e)}")
        
    finally:
        IS_CGBAN_RUNNING = False

# Ungban Code (Same Logic for Unban)
@app.on_message(filters.command(["cungban", "cloneungban"]) & SUDOERS)
@language
async def clone_global_unban_all(client, message: Message, _):
    global IS_CGBAN_RUNNING
    
    if IS_CGBAN_RUNNING:
        return await message.reply_text("⚠️ **Process already running!**")

    user = await extract_user(message)
    if not user:
        return await message.reply_text("❌ **User not found.**")

    IS_CGBAN_RUNNING = True
    
    try:
        mystic = await message.reply_photo(
            photo=get_random_cgban_img(),
            caption=f"🕊️ **CLONE UNBAN CHALU**\n\n**Target:** {user.mention}\n🔄 **Saare Clones check kar raha hoon...**",
        )

        all_clones = []
        async for c in get_all_clones():
            all_clones.append(c)

        total_groups_unbanned = 0
        BATCH_SIZE = 10
        
        for i in range(0, len(all_clones), BATCH_SIZE):
            if not IS_CGBAN_RUNNING: break
            batch = all_clones[i:i + BATCH_SIZE]
            tasks = []
            
            for clone in batch:
                token = clone.get('token')
                bot_id = clone.get('bot_id')
                if token and bot_id:
                    task = asyncio.create_task(execute_ban_via_clone(token, bot_id, user.id, unban=True))
                    tasks.append(task)

            for task in tasks:
                affected, status = await task
                total_groups_unbanned += affected
                
        await mystic.edit_caption(
            f"✅ **Clone Unban Complete!**\n\n"
            f"👤 **Target:** {user.mention}\n"
            f"🕊️ **Groups Unbanned:** {total_groups_unbanned}"
        )

    except Exception as e:
        await message.reply_text(f"❌ **Error:** {str(e)}")

    finally:
        IS_CGBAN_RUNNING = False
