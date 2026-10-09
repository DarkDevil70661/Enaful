from pyrogram import filters, Client
from pyrogram.types import Message

from PritiMusic.core.call import Lucky
from PritiMusic.utils.database import set_loop
from PritiMusic.utils.inline import close_markup
from config import BANNED_USERS
from PritiMusic.misc import db

# ✅ IMPORT FIX: Super Fast Admin Check & Clone Owner Support
from PritiMusic.cplugin.admins import AdminRightsCheck

@Client.on_message(
    filters.command(
        ["end", "stop", "cend", "cstop"],
        prefixes=["/", "!", "%", ",", "", ".", "@", "#"],
    )
    & filters.group
    & ~BANNED_USERS
)
@AdminRightsCheck
async def stop_music(client: Client, message: Message, _, chat_id):
    if len(message.command) != 1:
        return
    
    # 1. Stop Stream Instantly
    await Lucky.stop_stream(chat_id)
    
    # 2. Reset Loop Status
    await set_loop(chat_id, 0)
    
    # 3. Force Clear Queue
    if chat_id in db:
        db[chat_id] = []
        
    # 4. Send Confirmation
    await message.reply_text(
        _["admin_5"].format(message.from_user.mention), 
        reply_markup=close_markup(_)
    )
