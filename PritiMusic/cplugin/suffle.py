import random
from pyrogram import filters, Client
from pyrogram.types import Message

from PritiMusic import app
from PritiMusic.misc import db
from PritiMusic.utils.inline import close_markup
from config import BANNED_USERS

# ✅ IMPORT FIX: Super Fast Admin Check & Clone Owner Support
from PritiMusic.cplugin.admins import AdminRightsCheck

@Client.on_message(
    filters.command(["shuffle", "cshuffle"]) & filters.group & ~BANNED_USERS
)
@AdminRightsCheck
async def shuffle_music(client: Client, message: Message, _, chat_id):
    check = db.get(chat_id)
    if not check:
        return await message.reply_text(_["queue_2"])
    
    try:
        # 1. Pop the currently playing song (Taaki wo shuffle na ho)
        popped = check.pop(0)
    except:
        return await message.reply_text(_["admin_15"], reply_markup=close_markup(_))
    
    # 2. Check if queue is empty after popping
    if not check:
        check.insert(0, popped)
        return await message.reply_text(_["admin_15"], reply_markup=close_markup(_))
    
    # 3. Shuffle the rest of the queue
    random.shuffle(check)
    
    # 4. Put the current song back at the top
    check.insert(0, popped)
    
    await message.reply_text(
        _["admin_16"].format(message.from_user.mention), 
        reply_markup=close_markup(_)
    )
