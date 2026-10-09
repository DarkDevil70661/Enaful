import asyncio

from pyrogram import filters
from pyrogram.enums import ChatMembersFilter
from pyrogram.errors import FloodWait

from PritiMusic import app
from PritiMusic.misc import SUDOERS
from PritiMusic.utils.database import (
    get_active_chats,
    get_authuser_names,
    get_client,
    get_served_chats,
    get_served_users,
)
from PritiMusic.utils.decorators.language import language
from PritiMusic.utils.formatters import alpha_to_int
from config import adminlist

IS_BROADCASTING = False


@app.on_message(filters.command("broadcast") & SUDOERS)
@language
async def braodcast_message(client, message, _):
    global IS_BROADCASTING
    query = ""
    
    if message.reply_to_message:
        x = message.reply_to_message.id
        y = message.chat.id
    else:
        if len(message.command) < 2:
            return await message.reply_text(_["broad_2"])
        
        query = message.text.split(None, 1)[1]
        
        # Clean up tags from the text
        flags = ["-pinloud", "-pin", "-nobot", "-assistant", "-user", "-chats"]
        for flag in flags:
            if flag in query:
                query = query.replace(flag, "").strip()
                
        if query == "":
            return await message.reply_text(_["broad_8"])

    IS_BROADCASTING = True
    await message.reply_text(_["broad_1"])

    # ==========================================
    # 🎯 MODE LOGIC (Chats, Users, or Both)
    # ==========================================
    send_to_chats = True
    send_to_users = True

    if "-user" in message.text and "-chats" not in message.text:
        send_to_chats = False
    elif "-chats" in message.text and "-user" not in message.text:
        send_to_users = False

    if "-nobot" in message.text:
        send_to_chats = False
        send_to_users = False

    # ==========================================
    # 1. BROADCAST TO GROUPS (Chats)
    # ==========================================
    if send_to_chats:
        sent = 0
        pin = 0
        schats = await get_served_chats()
        for chat in schats:
            chat_id = int(chat["chat_id"])
            try:
                m = (
                    await app.forward_messages(chat_id, y, x)
                    if message.reply_to_message
                    else await app.send_message(chat_id, text=query)
                )
                if "-pinloud" in message.text:
                    try:
                        await m.pin(disable_notification=False)
                        pin += 1
                    except:
                        pass
                elif "-pin" in message.text:
                    try:
                        await m.pin(disable_notification=True)
                        pin += 1
                    except:
                        pass
                sent += 1
                await asyncio.sleep(0.2)
            except FloodWait as fw:
                flood_time = int(fw.value)
                if flood_time > 200:
                    continue
                await asyncio.sleep(flood_time)
            except:
                continue
        try:
            await message.reply_text(_["broad_3"].format(sent, pin))
        except:
            pass

    # ==========================================
    # 2. BROADCAST TO USERS (Private DMs)
    # ==========================================
    if send_to_users:
        susr = 0
        susers = await get_served_users()
        for user in susers:
            user_id = int(user["user_id"])
            try:
                m = (
                    await app.forward_messages(user_id, y, x)
                    if message.reply_to_message
                    else await app.send_message(user_id, text=query)
                )
                susr += 1
                await asyncio.sleep(0.2)
            except FloodWait as fw:
                flood_time = int(fw.value)
                if flood_time > 200:
                    continue
                await asyncio.sleep(flood_time)
            except:
                pass
        try:
            await message.reply_text(_["broad_4"].format(susr))
        except:
            pass

    # ==========================================
    # 3. BROADCAST TO ASSISTANT DIALOGS
    # ==========================================
    if "-assistant" in message.text:
        aw = await message.reply_text(_["broad_5"])
        text = _["broad_6"]
        from PritiMusic.core.userbot import assistants

        for num in assistants:
            sent = 0
            try:
                client_ast = await get_client(num)
                async for dialog in client_ast.get_dialogs():
                    try:
                        (await client_ast.forward_messages(dialog.chat.id, y, x)) if message.reply_to_message else (await client_ast.send_message(dialog.chat.id, text=query))
                        sent += 1
                        await asyncio.sleep(3)
                    except FloodWait as fw:
                        flood_time = int(fw.value)
                        if flood_time > 200:
                            continue
                        await asyncio.sleep(flood_time)
                    except:
                        continue
                text += _["broad_7"].format(num, sent)
            except:
                pass
        try:
            await aw.edit_text(text)
        except:
            pass
            
    IS_BROADCASTING = False


async def auto_clean():
    while not await asyncio.sleep(10):
        try:
            served_chats = await get_active_chats()
            for chat_id in served_chats:
                if chat_id not in adminlist:
                    adminlist[chat_id] = []
                    async for user in app.get_chat_members(
                        chat_id, filter=ChatMembersFilter.ADMINISTRATORS
                    ):
                        if user.privileges.can_manage_video_chats:
                            adminlist[chat_id].append(user.user.id)
                    authusers = await get_authuser_names(chat_id)
                    for user in authusers:
                        user_id = await alpha_to_int(user)
                        adminlist[chat_id].append(user_id)
        except:
            continue


asyncio.create_task(auto_clean())
