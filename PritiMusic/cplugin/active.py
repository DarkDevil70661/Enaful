from pyrogram import filters, Client, enums
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from unidecode import unidecode

from PritiMusic import app
from PritiMusic.misc import SUDOERS
from PritiMusic.utils.database import (
    get_active_chats,
    get_active_video_chats,
    remove_active_chat,
    remove_active_video_chat,
)
from PritiMusic.utils.database.clonedb import get_served_chats_clone, clonebotdb

# --- HELPER: Get ONLY This Bot's Chats ---
async def get_my_served_chats(bot_id):
    try:
        chats = await get_served_chats_clone(bot_id)
        return [int(chat["chat_id"]) for chat in chats]
    except:
        return []

# 1. ACTIVE VOICE CHATS LIST
@Client.on_message(filters.command(["activevc", "activevoice", "vc"]))
async def activevc(client: Client, message: Message):
    bot_id = client.me.id
    user_id = message.from_user.id
    
    # Clone Check
    clone_data = await clonebotdb.find_one({"bot_id": bot_id})
    if not clone_data:
        return
        
    owner_id = clone_data.get("user_id")

    # Access Check: Sirf Clone Owner aur Main Bot Sudoers
    if user_id != owner_id and user_id not in SUDOERS:
        return await message.reply_text("❌ **Only the Clone Owner can view this.**")

    mystic = await message.reply_text("» ɢᴇᴛᴛɪɴɢ ᴀᴄᴛɪᴠᴇ ᴠᴏɪᴄᴇ ᴄʜᴀᴛs ʟɪsᴛ...")
    
    # Data Fetching
    active_list = await get_active_chats()  # DB se active list
    my_served_chats = await get_my_served_chats(bot_id) # Is bot ke groups
    
    text = ""
    j = 0
    
    for x in active_list:
        # LOGIC: Agar ye chat ID is bot ke served chats mein nahi hai, to skip karo.
        if x not in my_served_chats:
            continue
            
        try:
            chat_obj = await client.get_chat(x)
            title = chat_obj.title
        except:
            await remove_active_chat(x)
            continue
            
        try:
            if chat_obj.username:
                user = chat_obj.username
                text += f"<b>{j + 1}.</b> <a href=https://t.me/{user}>{unidecode(title).upper()}</a>\n"
            else:
                text += f"<b>{j + 1}.</b> {unidecode(title).upper()}\n"
            j += 1
        except:
            continue
            
    if not text:
        await mystic.edit_text(f"» ɴᴏ ᴀᴄᴛɪᴠᴇ ᴠᴏɪᴄᴇ ᴄʜᴀᴛs ᴏɴ {client.me.mention}.")
    else:
        await mystic.edit_text(
            f"<b>» ʟɪsᴛ ᴏғ ᴄᴜʀʀᴇɴᴛʟʏ ᴀᴄᴛɪᴠᴇ ᴠᴏɪᴄᴇ ᴄʜᴀᴛs :</b>\n\n{text}",
            disable_web_page_preview=True,
        )


# 2. ACTIVE VIDEO CHATS LIST
@Client.on_message(filters.command(["activev", "activevideo", "vvc"]))
async def activevi_(client: Client, message: Message):
    bot_id = client.me.id
    user_id = message.from_user.id
    
    clone_data = await clonebotdb.find_one({"bot_id": bot_id})
    if not clone_data:
        return
        
    owner_id = clone_data.get("user_id")

    if user_id != owner_id and user_id not in SUDOERS:
        return await message.reply_text("❌ **Only the Clone Owner can view this.**")

    mystic = await message.reply_text("» ɢᴇᴛᴛɪɴɢ ᴀᴄᴛɪᴠᴇ ᴠɪᴅᴇᴏ ᴄʜᴀᴛs ʟɪsᴛ...")
    
    active_video_list = await get_active_video_chats()
    my_served_chats = await get_my_served_chats(bot_id)
    
    text = ""
    j = 0
    
    for x in active_video_list:
        if x not in my_served_chats:
            continue
            
        try:
            chat_obj = await client.get_chat(x)
            title = chat_obj.title
        except:
            await remove_active_video_chat(x)
            continue
            
        try:
            if chat_obj.username:
                user = chat_obj.username
                text += f"<b>{j + 1}.</b> <a href=https://t.me/{user}>{unidecode(title).upper()}</a> [<code>{x}</code>]\n"
            else:
                text += f"<b>{j + 1}.</b> {unidecode(title).upper()} [<code>{x}</code>]\n"
            j += 1
        except:
            continue
            
    if not text:
        await mystic.edit_text(f"» ɴᴏ ᴀᴄᴛɪᴠᴇ ᴠɪᴅᴇᴏ ᴄʜᴀᴛs ᴏɴ {client.me.mention}.")
    else:
        await mystic.edit_text(
            f"<b>» ʟɪsᴛ ᴏғ ᴄᴜʀʀᴇɴᴛʟʏ ᴀᴄᴛɪᴠᴇ ᴠɪᴅᴇᴏ ᴄʜᴀᴛs :</b>\n\n{text}",
            disable_web_page_preview=True,
        )


# 3. SHORT STATS (Active Count)
@Client.on_message(filters.command(["ac", "av"]))
async def start(client: Client, message: Message):
    bot_id = client.me.id
    user_id = message.from_user.id
    
    clone_data = await clonebotdb.find_one({"bot_id": bot_id})
    if not clone_data:
        return
        
    owner_id = clone_data.get("user_id")

    if user_id != owner_id and user_id not in SUDOERS:
        return await message.reply_text("❌ **Only the Clone Owner can view this.**")

    # Fetch Lists
    active_audio = await get_active_chats()
    active_video = await get_active_video_chats()
    my_served_chats = await get_my_served_chats(bot_id)

    # Pure Filter Logic
    my_audio_count = 0
    for chat in active_audio:
        if chat in my_served_chats:
            my_audio_count += 1
            
    my_video_count = 0
    for chat in active_video:
        if chat in my_served_chats:
            my_video_count += 1

    await message.reply_text(
        f"✫ <b><u>{client.me.first_name} Active Chats</u></b> :\n\n"
        f"ᴠᴏɪᴄᴇ : {my_audio_count}\n"
        f"ᴠɪᴅᴇᴏ : {my_video_count}",
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton('✯ ᴄʟᴏsᴇ ✯', callback_data=f"close", style=enums.ButtonStyle.DANGER)]])
    )
