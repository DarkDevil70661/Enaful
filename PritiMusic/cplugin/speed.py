from pyrogram import filters, Client
from pyrogram.types import Message, CallbackQuery

from PritiMusic import app
from PritiMusic.core.call import Lucky
from PritiMusic.misc import db

# ✅ IMPORT FIX: Clone Owner & Optimized Admin Checks
from PritiMusic.cplugin.admins import AdminRightsCheck, ActualAdminCB

from PritiMusic.utils.database import is_active_chat
from PritiMusic.utils.decorators.language import languageCB
from PritiMusic.utils.inline import close_markup, speed_markup
from config import BANNED_USERS

# To prevent spamming speed change requests
checker = []

@Client.on_message(
    filters.command(["cspeed", "speed", "cslow", "slow", "playback", "cplayback"])
    & filters.group
    & ~BANNED_USERS
)
@AdminRightsCheck
async def playback(client: Client, message: Message, _, chat_id):
    # Fetch Bot Name
    cname = (await client.get_me()).mention
    
    playing = db.get(chat_id)
    if not playing:
        return await message.reply_text(_["queue_2"])
        
    duration_seconds = int(playing[0]["seconds"])
    if duration_seconds == 0:
        return await message.reply_text(_["admin_27"])
        
    file_path = playing[0]["file"]
    # Speed Change only works for downloaded files (Not live streams/links)
    if "downloads" not in file_path:
        return await message.reply_text(_["admin_27"])
        
    upl = speed_markup(_, chat_id)
    return await message.reply_text(
        text=_["admin_28"].format(cname),
        reply_markup=upl,
    )


@Client.on_callback_query(filters.regex("SpeedUP") & ~BANNED_USERS)
@languageCB
@ActualAdminCB  # ✅ FIX: Handles Clone Owner, Sudoers & Group Admins
async def speed_play_callback(client: Client, callback_query: CallbackQuery, _):
    callback_data = callback_query.data.strip()
    callback_request = callback_data.split(None, 1)[1]
    chat, speed = callback_request.split("|")
    chat_id = int(chat)
    
    if not await is_active_chat(chat_id):
        return await callback_query.answer(_["general_5"], show_alert=True)
    
    playing = db.get(chat_id)
    if not playing:
        return await callback_query.answer(_["queue_2"], show_alert=True)
        
    duration_seconds = int(playing[0]["seconds"])
    if duration_seconds == 0:
        return await callback_query.answer(_["admin_27"], show_alert=True)
        
    file_path = playing[0]["file"]
    if "downloads" not in file_path:
        return await callback_query.answer(_["admin_27"], show_alert=True)
        
    checkspeed = playing[0].get("speed")
    if checkspeed:
        if str(checkspeed) == str(speed):
            if str(speed) == str("1.0"):
                return await callback_query.answer(_["admin_29"], show_alert=True)
    else:
        if str(speed) == str("1.0"):
            return await callback_query.answer(_["admin_29"], show_alert=True)
            
    # Race Condition Check
    if chat_id in checker:
        return await callback_query.answer(_["admin_30"], show_alert=True)
    else:
        checker.append(chat_id)
    
    try:
        await callback_query.answer(_["admin_31"])
    except:
        pass
        
    mystic = await callback_query.message.reply_text(
        text=_["admin_32"].format(callback_query.from_user.mention),
    )
    
    try:
        await Lucky.speedup_stream(
            chat_id,
            file_path,
            speed,
            playing,
        )
    except Exception as e:
        if chat_id in checker:
            checker.remove(chat_id)
        return await mystic.edit_text(
            text=_["admin_33"],
            reply_markup=close_markup(_),
        )
        
    if chat_id in checker:
        checker.remove(chat_id)
        
    await mystic.edit_text(
        text=_["admin_34"].format(speed, callback_query.from_user.mention),
        reply_markup=close_markup(_),
    )
