import random
from pyrogram import filters, Client
from pyrogram.types import InlineKeyboardMarkup, Message

import config
from PritiMusic import YouTube, app
from PritiMusic.core.call import Lucky
from PritiMusic.misc import db
from PritiMusic.utils.database import get_loop

# ✅ IMPORT FIX: Admin Check from cplugin
from PritiMusic.cplugin.admins import AdminRightsCheck
from PritiMusic.utils.inline import close_markup, stream_markup, stream_markup2
from PritiMusic.utils.stream.autoclear import auto_clean
from PritiMusic.utils.thumbnails import get_thumb
from config import BANNED_USERS
from PritiMusic.utils.database.clonedb import get_cloned_support_chat

# --- HELPER: Random Image ---
def get_random_img(img_list):
    if img_list:
        if isinstance(img_list, list):
            return random.choice(img_list)
        return img_list
    return "https://telegra.ph/file/2e3d368e77c449c287430.jpg"


@Client.on_message(
    filters.command(["skip", "cskip", "next", "cnext"], prefixes=["/", "!", "%", ",", ".", "@", "#"])
    & filters.group
    & ~BANNED_USERS
)
@AdminRightsCheck
async def skip(cli, message: Message, _, chat_id):
    # 1. Fetch Bot Info safely
    me = await cli.get_me()
    bot_username = me.username
    
    # 2. Fetch Support Chat
    C_BOT_SUPPORT_CHAT = await get_cloned_support_chat(me.id)
    if C_BOT_SUPPORT_CHAT:
         C_SUPPORT_CHAT = C_BOT_SUPPORT_CHAT if "https://" in C_BOT_SUPPORT_CHAT else f"https://t.me/{C_BOT_SUPPORT_CHAT}"
    else:
         C_SUPPORT_CHAT = config.SUPPORT_CHAT

    # 3. Check Loop Status
    loop = await get_loop(chat_id)
    if loop != 0:
        return await message.reply_text(_["admin_8"])

    # 4. Handle Specific Skip Count (e.g., /skip 3)
    check = db.get(chat_id)
    if len(message.command) > 1:
        if not check:
            return await message.reply_text(_["queue_2"])
            
        state = message.text.split(None, 1)[1].strip()
        if state.isnumeric():
            state = int(state)
            count = len(check)
            
            if count > 2:
                count = int(count - 1)
                if 1 <= state <= count:
                    for x in range(state):
                        popped = None
                        try:
                            popped = check.pop(0)
                        except:
                            return await message.reply_text(_["admin_12"])
                        if popped:
                            await auto_clean(popped)
                        
                        # Stop if queue empty
                        if not check:
                            try:
                                await message.reply_text(
                                    text=_["admin_6"].format(
                                        message.from_user.mention, message.chat.title
                                    ),
                                    reply_markup=close_markup(_),
                                )
                                await Lucky.stop_stream(chat_id)
                            except:
                                pass
                            return
                else:
                    return await message.reply_text(_["admin_11"].format(count))
            else:
                return await message.reply_text(_["admin_10"])
        else:
            return await message.reply_text(_["admin_9"])
            
    # 5. Handle Normal Skip (Next Track)
    else:
        if not check:
             return await message.reply_text(_["queue_2"])
             
        popped = None
        try:
            popped = check.pop(0)
            if popped:
                await auto_clean(popped)
            if not check:
                await message.reply_text(
                    text=_["admin_6"].format(
                        message.from_user.mention, message.chat.title
                    ),
                    reply_markup=close_markup(_),
                )
                try:
                    return await Lucky.stop_stream(chat_id)
                except:
                    return
        except:
            try:
                await message.reply_text(
                    text=_["admin_6"].format(
                        message.from_user.mention, message.chat.title
                    ),
                    reply_markup=close_markup(_),
                )
                return await Lucky.stop_stream(chat_id)
            except:
                return

    # 6. Play Next Track
    queued = check[0]["file"]
    title = (check[0]["title"]).title()
    user = check[0]["by"]
    streamtype = check[0]["streamtype"]
    videoid = check[0]["vidid"]
    status = True if str(streamtype) == "video" else None
    
    # Reset Play Duration
    db[chat_id][0]["played"] = 0
    exis = (check[0]).get("old_dur")
    if exis:
        db[chat_id][0]["dur"] = exis
        db[chat_id][0]["seconds"] = check[0]["old_second"]
        db[chat_id][0]["speed_path"] = None
        db[chat_id][0]["speed"] = 1.0

    # --- STREAMING LOGIC ---
    
    # A. YouTube Live
    if "live_" in queued:
        n, link = await YouTube.video(videoid, True)
        if n == 0:
            return await message.reply_text(_["admin_7"].format(title))
        try:
            image = await YouTube.thumbnail(videoid, True)
        except:
            image = None
        try:
            await Lucky.skip_stream(chat_id, link, video=status, image=image)
        except:
            return await message.reply_text(_["call_6"])
            
        button = stream_markup2(_, chat_id)
        img = await get_thumb(videoid)
        run = await message.reply_photo(
            photo=img,
            caption=_["stream_1"].format(
                f"https://t.me/{bot_username}?start=info_{videoid}",
                title[:23],
                check[0]["dur"],
                user,
            ),
            reply_markup=InlineKeyboardMarkup(button),
        )
        db[chat_id][0]["mystic"] = run
        db[chat_id][0]["markup"] = "tg"

    # B. YouTube Video
    elif "vid_" in queued:
        mystic = await message.reply_text(_["call_7"], disable_web_page_preview=True)
        try:
            file_path, direct = await YouTube.download(
                videoid,
                mystic,
                videoid=True,
                video=status,
            )
        except:
            return await mystic.edit_text(_["call_6"])
        try:
            image = await YouTube.thumbnail(videoid, True)
        except:
            image = None
        try:
            await Lucky.skip_stream(chat_id, file_path, video=status, image=image)
        except:
            return await mystic.edit_text(_["call_6"])
            
        button = stream_markup(_, chat_id)
        img = await get_thumb(videoid)
        run = await message.reply_photo(
            photo=img,
            caption=_["stream_1"].format(
                f"https://t.me/{bot_username}?start=info_{videoid}",
                title[:23],
                check[0]["dur"],
                user,
            ),
            reply_markup=InlineKeyboardMarkup(button),
        )
        db[chat_id][0]["mystic"] = run
        db[chat_id][0]["markup"] = "stream"
        await mystic.delete()

    # C. Index Link / M3U8
    elif "index_" in queued:
        try:
            await Lucky.skip_stream(chat_id, videoid, video=status)
        except:
            return await message.reply_text(_["call_6"])
            
        button = stream_markup2(_, chat_id)
        run = await message.reply_photo(
            photo=get_random_img(config.STREAM_IMG_URL),
            caption=_["stream_2"].format(user),
            reply_markup=InlineKeyboardMarkup(button),
        )
        db[chat_id][0]["mystic"] = run
        db[chat_id][0]["markup"] = "tg"

    # D. Telegram Audio/Video & SoundCloud
    else:
        if videoid == "telegram":
            image = None
        elif videoid == "soundcloud":
            image = None
        else:
            try:
                image = await YouTube.thumbnail(videoid, True)
            except:
                image = None
                
        try:
            await Lucky.skip_stream(chat_id, queued, video=status, image=image)
        except:
            return await message.reply_text(_["call_6"])
            
        if videoid == "telegram":
            button = stream_markup2(_, chat_id)
            tg_img = get_random_img(config.TELEGRAM_AUDIO_URL) if str(streamtype) == "audio" else get_random_img(config.TELEGRAM_VIDEO_URL)
            run = await message.reply_photo(
                photo=tg_img,
                caption=_["stream_1"].format(
                    C_SUPPORT_CHAT, title[:23], check[0]["dur"], user
                ),
                reply_markup=InlineKeyboardMarkup(button),
            )
            db[chat_id][0]["mystic"] = run
            db[chat_id][0]["markup"] = "tg"
            
        elif videoid == "soundcloud":
            button = stream_markup2(_, chat_id)
            run = await message.reply_photo(
                photo=get_random_img(config.SOUNCLOUD_IMG_URL),
                caption=_["stream_1"].format(
                    C_SUPPORT_CHAT, title[:23], check[0]["dur"], user
                ),
                reply_markup=InlineKeyboardMarkup(button),
            )
            db[chat_id][0]["mystic"] = run
            db[chat_id][0]["markup"] = "tg"
            
        else:
            button = stream_markup(_, chat_id)
            img = await get_thumb(videoid)
            run = await message.reply_photo(
                photo=img,
                caption=_["stream_1"].format(
                    f"https://t.me/{bot_username}?start=info_{videoid}",
                    title[:23],
                    check[0]["dur"],
                    user,
                ),
                reply_markup=InlineKeyboardMarkup(button),
            )
            db[chat_id][0]["mystic"] = run
            db[chat_id][0]["markup"] = "stream"
