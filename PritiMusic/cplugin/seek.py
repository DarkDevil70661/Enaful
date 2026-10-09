from pyrogram import filters, Client
from pyrogram.types import Message

from PritiMusic import YouTube
from PritiMusic.core.call import Lucky
from PritiMusic.misc import db
from PritiMusic.utils.formatters import seconds_to_min
from PritiMusic.utils.inline import close_markup
from config import BANNED_USERS

# ✅ IMPORT FIX: Optimized Admin Check & Clone Owner Support
from PritiMusic.cplugin.admins import AdminRightsCheck

@Client.on_message(
    filters.command(["seek", "cseek", "seekback", "cseekback"])
    & filters.group
    & ~BANNED_USERS
)
@AdminRightsCheck
async def seek_comm(client, message: Message, _, chat_id):
    if len(message.command) == 1:
        return await message.reply_text(_["admin_20"])
    
    query = message.text.split(None, 1)[1].strip()
    if not query.isnumeric():
        return await message.reply_text(_["admin_21"])
    
    playing = db.get(chat_id)
    if not playing:
        return await message.reply_text(_["queue_2"])
    
    duration_seconds = int(playing[0]["seconds"])
    if duration_seconds == 0:
        return await message.reply_text(_["admin_22"])
    
    file_path = playing[0]["file"]
    duration_played = int(playing[0]["played"])
    duration_to_skip = int(query)
    duration = playing[0]["dur"]
    
    # Check Command Type (Forward vs Backward)
    cmd = message.command[0].lower()
    
    if cmd.endswith("back"):
        if (duration_played - duration_to_skip) <= 10:
            return await message.reply_text(
                text=_["admin_23"].format(seconds_to_min(duration_played), duration),
                reply_markup=close_markup(_),
            )
        to_seek = duration_played - duration_to_skip
    else:
        if (duration_played + duration_to_skip) >= duration_seconds:
             return await message.reply_text(
                text=_["admin_23"].format(seconds_to_min(duration_played), duration),
                reply_markup=close_markup(_),
            )
        to_seek = duration_played + duration_to_skip
        
    mystic = await message.reply_text(_["admin_24"])
    
    # Handle Video Link Refresh (Needed for YouTube streams)
    if "vid_" in file_path:
        try:
            n, file_path = await YouTube.video(playing[0]["vidid"], True)
            if n == 0:
                return await mystic.edit_text(_["admin_22"])
        except:
            return await mystic.edit_text(_["admin_22"])
            
    check = (playing[0]).get("speed_path")
    if check:
        file_path = check
        
    if "index_" in file_path:
        file_path = playing[0]["vidid"]
        
    try:
        await Lucky.seek_stream(
            chat_id,
            file_path,
            seconds_to_min(to_seek),
            duration,
            playing[0]["streamtype"],
        )
    except:
        return await mystic.edit_text(_["admin_26"], reply_markup=close_markup(_))
        
    # Update Played Duration in DB
    if cmd.endswith("back"):
        db[chat_id][0]["played"] -= duration_to_skip
    else:
        db[chat_id][0]["played"] += duration_to_skip
        
    await mystic.edit_text(
        text=_["admin_25"].format(seconds_to_min(to_seek), message.from_user.mention),
        reply_markup=close_markup(_),
    )
