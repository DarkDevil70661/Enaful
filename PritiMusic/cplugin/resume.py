from pyrogram import filters, Client
from pyrogram.types import Message, InlineKeyboardButton, InlineKeyboardMarkup

from PritiMusic import app
from PritiMusic.core.call import Lucky
from PritiMusic.utils.database import is_music_playing, music_on
from config import BANNED_USERS

# ✅ IMPORT FIX: Super Fast Admin Check & Clone Owner Support
from PritiMusic.cplugin.admins import AdminRightsCheck

@Client.on_message(
    filters.command(["resume", "cresume"]) & filters.group & ~BANNED_USERS
)
@AdminRightsCheck
async def resume_command(client, message: Message, _, chat_id):
    # 1. Check if already playing
    if await is_music_playing(chat_id):
        return await message.reply_text(_["admin_3"])
    
    # 2. Update Database & Resume Stream
    await music_on(chat_id)
    await Lucky.resume_stream(chat_id)
    
    # 3. Control Buttons
    buttons_resume = [
        [
            InlineKeyboardButton(text="sᴋɪᴘ", callback_data=f"ADMIN Skip|{chat_id}"),
            InlineKeyboardButton(text="sᴛᴏᴘ", callback_data=f"ADMIN Stop|{chat_id}"),
        ],
        [
            InlineKeyboardButton(
                text="ᴘᴀᴜsᴇ",
                callback_data=f"ADMIN Pause|{chat_id}",
            ),
        ],
    ]
    
    # 4. Send Response
    await message.reply_text(
        _["admin_4"].format(message.from_user.mention),
        reply_markup=InlineKeyboardMarkup(buttons_resume),
    )
