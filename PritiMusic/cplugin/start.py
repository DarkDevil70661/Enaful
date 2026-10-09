import time
import random
import asyncio
import logging
from pyrogram import filters, Client, enums
from pyrogram.enums import ChatType, ParseMode
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup, Message, InputMediaPhoto, InputMediaVideo
from py_yt import VideosSearch

import config
from PritiMusic import app
from PritiMusic.misc import _boot_, SUDOERS
from PritiMusic.plugins.sudo.sudoers import sudoers_list
from PritiMusic.utils.formatters import get_readable_time

# Config Imports
from config import BANNED_USERS, OWNER_ID, START_IMG_URL

# Module Imports
from PritiMusic.utils.decorators.language import LanguageStart, languageCB
from PritiMusic.utils.database.clonedb import get_owner_id_from_db
from PritiMusic.utils.database import add_served_user_clone, add_served_chat_clone
from PritiMusic.utils.database import clonebotdb

# Extra Import for Transfer Logic
from PritiMusic.core.mongo import mongodb
cloneownerdb = mongodb.cloneownerdb

# Initialize logging
LOG = logging.getLogger(__name__)

# Fallback Effect IDs
DEFAULT_EFFECT_IDS = [
    "5104841245755180586", # 🔥
    "5107584321108051014", # 👍
    "5046509860389126442", # 🎉
    "5044134455711629726", # ❤️
]

# 🎨 Premium colored-button styles (random PRIMARY/SUCCESS/DANGER look per render)
STYLES = [
    enums.ButtonStyle.PRIMARY,
    enums.ButtonStyle.SUCCESS,
    enums.ButtonStyle.DANGER,
]

# =====================================================================
# INTERNAL BUTTON HELPERS
# =====================================================================

def make_start_panel(bot_username, owner_url, 
                     txt_add, txt_support, txt_channel, txt_owner, txt_help, 
                     support_chat, support_channel,
                     custom_btn=None, btn_pos="TOP"):

    alone_style = random.choice(STYLES)
    group_style = random.choice([s for s in STYLES if s != alone_style])

    buttons = []

    # 1. Add to Group
    if txt_add != "HIDDEN":
        buttons.append([InlineKeyboardButton(text=txt_add, url=f"https://t.me/{bot_username}?startgroup=true", style=group_style)])

    # 2. Help Button
    if txt_help != "HIDDEN":
        buttons.append([InlineKeyboardButton(text=txt_help, callback_data="settings_back_helper", style=group_style)])

    # 3. Support & Channel (Row)
    row_support = []
    if txt_support != "HIDDEN":
        row_support.append(InlineKeyboardButton(text=txt_support, url=support_chat, style=group_style))
    if txt_channel != "HIDDEN":
        row_support.append(InlineKeyboardButton(text=txt_channel, url=support_channel, style=group_style))
    if row_support:
        buttons.append(row_support)

    # 4. Owner Button
    if txt_owner != "HIDDEN":
        buttons.append([InlineKeyboardButton(text=txt_owner, url=owner_url, style=alone_style)])

    # --- Custom Button Logic ---
    if custom_btn and custom_btn.get("text"):
        c_btn = InlineKeyboardButton(text=custom_btn["text"], url=custom_btn["url"], style=alone_style)

        if btn_pos in ["UP", "TOP"]:
            buttons.insert(0, [c_btn])
        elif btn_pos in ["DOWN", "BOTTOM"]:
            buttons.append([c_btn])
        elif btn_pos in ["MID", "MIDDLE"]:
            if len(buttons) >= 1:
                buttons.insert(1, [c_btn])
            else:
                buttons.append([c_btn])
        elif btn_pos == "LEFT":
            if buttons and isinstance(buttons[0], list):
                buttons[0].insert(0, c_btn)
            else:
                buttons.insert(0, [c_btn])
        elif btn_pos == "RIGHT":
            if buttons and isinstance(buttons[0], list):
                buttons[0].append(c_btn)
            else:
                buttons.insert(0, [c_btn])
        else:
            buttons.insert(0, [c_btn])

    return InlineKeyboardMarkup(buttons)


def make_gp_panel(bot_username, txt_add, txt_support, support_chat):
    alone_style = random.choice(STYLES)
    group_style = random.choice([s for s in STYLES if s != alone_style])

    buttons = [
        [
            InlineKeyboardButton(text=txt_add, url=f"https://t.me/{bot_username}?startgroup=true", style=group_style),
            InlineKeyboardButton(text=txt_support, url=support_chat, style=alone_style),
        ]
    ]
    return InlineKeyboardMarkup(buttons)

# =====================================================================
# Database Helpers
# =====================================================================

# ⚡ Speed: one Mongo round-trip per /start instead of ~15 (owner id, support
# links, every start_* field and every custom button label all live on the
# same clonebotdb document, keyed by bot_id — so fetch it once and reuse it).
async def get_bot_settings(bot_id):
    return await clonebotdb.find_one({"bot_id": bot_id}) or {}

def get_start_image(d):
    return d.get("start_image")

def get_start_caption(d):
    return d.get("start_caption")

def get_start_button(d):
    return d.get("start_button")

def get_start_btn_pos(d):
    return d.get("start_btn_pos", "TOP")

def get_start_video(d):
    return d.get("start_video")

def get_start_sticker(d):
    return d.get("start_sticker")

def get_start_animation(d):
    return d.get("start_animation")

def get_start_reaction(d):
    return d.get("start_reaction")

def get_start_effect(d):
    return d.get("start_effect")

def get_custom_btn_text(d, key, default_text):
    return d.get(f"btn_{key}", default_text)

# ✅ Helper to Add Random Content (Fix for NoneType error)
async def add_start_content(bot_id, key, value):
    d = await clonebotdb.find_one({"bot_id": bot_id}) or {}
    current = d.get(key)
    
    if current:
        if isinstance(current, dict):
            current = f"{current['text']} - {current['url']}" 
        
        # Avoid duplicates
        if value in current:
            return False 
        final_value = f"{current}|||{value}"
    else:
        final_value = value
        
    await clonebotdb.update_one({"bot_id": bot_id}, {"$set": {key: final_value}}, upsert=True)
    return True

# --- General Helpers ---

def get_random_start_image():
    if START_IMG_URL:
        if isinstance(START_IMG_URL, list):
            return random.choice(START_IMG_URL)
        return START_IMG_URL
    return "https://telegra.ph/file/2e3d368e77c449c287430.jpg"

def format_link(val):
    if not val:
        return "https://t.me/Telegram" 
    if "https://" in val or "http://" in val:
        return val
    return f"https://t.me/{val}"

def get_mention_html(user_id, name):
    return f'<a href="tg://user?id={user_id}">{name}</a>'

# ✅ Check Owner / Sudo Logic
async def check_owner(client, message):
    user_id = message.from_user.id
    if user_id in SUDOERS:
        return True
    
    bot_id = client.me.id
    owner_id = await get_owner_id_from_db(bot_id)
    if user_id == owner_id:
        return True
    return False

# =====================================================================
# START COMMAND (PRIVATE)
# =====================================================================

@Client.on_message(filters.command("start") & filters.private & ~BANNED_USERS)
@LanguageStart
async def start_pm(client, message: Message, _):
    a = await client.get_me()
    bot_id = a.id

    # ⚡ One query gets everything: owner id, support links, buttons, media,
    # caption, reaction and effect all live on this single document.
    settings, _served = await asyncio.gather(
        get_bot_settings(bot_id),
        add_served_user_clone(message.from_user.id, bot_id),
    )

    # 1. Loading Animation
    raw_sticker = get_start_sticker(settings)
    raw_animation = get_start_animation(settings)

    custom_sticker = random.choice(raw_sticker.split("|||")) if raw_sticker else None
    custom_animation = random.choice(raw_animation.split("|||")) if raw_animation else None
    
    loading = None

    if custom_sticker:
        try:
            loading = await message.reply_sticker(custom_sticker)
            await asyncio.sleep(1)
        except:
            pass
    elif custom_animation:
        try:
            loading = await message.reply_animation(custom_animation)
            await asyncio.sleep(1)
        except:
             pass
    else:
        anim_frames = ["<b>ʟᴏᴀᴅɪɴɢ</b>", "<b>ʟᴏᴀᴅɪɴɢ.</b>", "<b>ʟᴏᴀᴅɪɴɢ..</b>", "<b>ʟᴏᴀᴅɪɴɢ...</b>"]
        try:
            loading = await message.reply_text(anim_frames[0])
            for frame in anim_frames[1:]:
                await asyncio.sleep(0.15)
                try:
                    await loading.edit_text(frame, parse_mode=ParseMode.HTML)
                except:
                    pass
        except:
            pass

    # Pull the rest straight out of the single fetched document (no extra DB calls)
    C_BOT_OWNER_ID = settings.get("user_id")
    raw_support = settings.get("support", "No support chat set.")
    raw_channel = settings.get("channel", "No channel set.")
    txt_add = get_custom_btn_text(settings, "add", _["S_B_3"])
    txt_support = get_custom_btn_text(settings, "support", _["S_B_9"])
    txt_channel = get_custom_btn_text(settings, "channel", _["S_B_6"])
    txt_owner = get_custom_btn_text(settings, "owner", _["C_B_2"])
    txt_help = get_custom_btn_text(settings, "help", _["S_B_4"])
    raw_custom_btn = get_start_button(settings)
    btn_pos = get_start_btn_pos(settings)
    raw_video = get_start_video(settings)
    raw_img = get_start_image(settings)
    raw_caption = get_start_caption(settings)
    raw_reaction = get_start_reaction(settings)
    raw_effect = get_start_effect(settings)

    C_SUPPORT_CHAT = format_link(raw_support)
    C_SUPPORT_CHANNEL = format_link(raw_channel)
    OWNER_URL = f"tg://openmessage?user_id={C_BOT_OWNER_ID}"

    # 1. Reaction Logic
    if raw_reaction:
        reaction_emoji = random.choice(raw_reaction.split("|||"))
    else:
        reaction_emoji = random.choice(["🔥", "❤️", "🥰", "😍", "👍", "⚡", "🎉"])
    
    try:
        await message.react(reaction_emoji)
    except:
        pass

    try:
        if loading: await loading.delete()
    except:
        pass

    # Inline Arguments Logic
    if len(message.text.split()) > 1:
        arg = message.text.split(None, 1)[1]
        
        if arg.startswith("help"):
            keyboard = InlineKeyboardMarkup([[InlineKeyboardButton(_["S_B_9"], url=C_SUPPORT_CHAT)]])
            return await message.reply_photo(
                photo=get_random_start_image(),
                caption=_["help_1"].format(C_SUPPORT_CHAT),
                reply_markup=keyboard,
                has_spoiler=True
            )
        if arg.startswith("sud"):
            return await sudoers_list(client=client, message=message, _=_)
        if arg.startswith("inf"):
            m = await message.reply_text("🔎")
            q = arg.replace("info_", "", 1)
            try:
                results = await VideosSearch(f"https://www.youtube.com/watch?v={q}", limit=1).next()
                result = results["result"][0]
                thumbnail = result["thumbnails"][0]["url"].split("?")[0]
                caption = _["start_6"].format(result["title"], result["duration"], result["viewCount"]["short"], result["publishedTime"], result["channel"]["link"], result["channel"]["name"], a.mention)
                key = InlineKeyboardMarkup([[InlineKeyboardButton(_["S_B_8"], url=result["link"]), InlineKeyboardButton(_["S_B_9"], url=C_SUPPORT_CHAT)]])
                await m.delete()
                return await message.reply_photo(photo=thumbnail, caption=caption, reply_markup=key, has_spoiler=True)
            except Exception as e:
                LOG.error(e)
                return await m.edit_text("❌ Error fetching info.")

    # Custom Button Data Logic
    custom_button_data = None
    if raw_custom_btn:
        if isinstance(raw_custom_btn, dict):
            custom_button_data = raw_custom_btn
        elif isinstance(raw_custom_btn, str):
            chosen_str = random.choice(raw_custom_btn.split("|||"))
            if "-" in chosen_str:
                txt, url = chosen_str.split("-", 1)
                custom_button_data = {"text": txt.strip(), "url": url.strip()}
    
    markup = make_start_panel(a.username, OWNER_URL,
                              txt_add, txt_support, txt_channel, txt_owner, txt_help,
                              C_SUPPORT_CHAT, C_SUPPORT_CHANNEL,
                              custom_button_data, btn_pos)

    # Media & Caption Logic
    start_video = random.choice(raw_video.split("|||")) if raw_video else None
    start_img = random.choice(raw_img.split("|||")) if raw_img else None
    custom_caption = random.choice(raw_caption.split("|||")) if raw_caption else None
    
    user_mention = get_mention_html(message.from_user.id, message.from_user.first_name)
    bot_mention = get_mention_html(a.id, a.first_name)
    
    if custom_caption:
        try:
            caption = custom_caption.format(
                name=user_mention,
                firstname=message.from_user.first_name,
                botname=bot_mention,
                username=a.username
            )
        except:
            caption = custom_caption
    else:
        formatted_text = (
            f"<b>нєу ʙᴀʙʏ {user_mention}, 🥀 ❞</b>\n\n"
            f"<b>๏ ᴛʜɪs ɪs {bot_mention} 🎵 : ғᴀsᴛ & ᴘᴏᴡᴇʀғᴜʟ ᴛɢ ᴍᴜsɪᴄ ʙᴏᴛ.</b>\n"
            f"<b>๏ sᴍᴏᴏᴛʜ ʙᴇᴀᴛs • sᴛᴀʙʟᴇ & sᴇᴀᴍʟᴇss ᴍᴜsɪᴄ ғʟᴏᴡ.</b>\n"
            f"<b>๏ ɴᴇᴡ ᴠᴇʀsɪᴏɴ ᴡɪᴛʜ sᴜᴘᴇʀ ғᴀsᴛ ʏᴏᴜᴛᴜʙᴇ ᴀᴘɪ ʙᴀsᴇᴅ.</b>\n"
            f"<b>•── ⋅ ⋅ ⋅ ────── ⋅  ⋅ ────── ⋅ ⋅ ⋅ ──•</b>\n"
            f"<b>๏ ᴄʟɪᴄᴋ ᴏɴ ᴛʜᴇ ʜᴇʟᴩ ʙᴜᴛᴛᴏɴ ᴛᴏ ɢᴇᴛ ɪɴғᴏʀᴍᴀᴛɪᴏɴ ᴀʙᴏᴜᴛ ᴍʏ ᴍᴏᴅᴜʟᴇs ᴀɴᴅ ᴄᴏᴍᴍᴀɴᴅs.</b>"
        )
        caption = f"<blockquote expandable>{formatted_text}</blockquote>"
        

    # 2. Effect Logic
    if raw_effect:
        effect = random.choice(raw_effect.split("|||"))
    else:
        # Check if config has effect IDs, else use fallback
        try:
            EFFECT_ID = config.EFFECT_ID
        except:
            EFFECT_ID = DEFAULT_EFFECT_IDS
        effect = random.choice(EFFECT_ID)
    
    try:
        effect = int(effect)
    except:
        effect = None

    if start_video:
        try:
            return await message.reply_video(start_video, caption=caption, reply_markup=markup, message_effect_id=effect, has_spoiler=True, parse_mode=ParseMode.HTML)
        except:
            pass
    
    photo = start_img if start_img else get_random_start_image()
    await message.reply_photo(photo, caption=caption, reply_markup=markup, message_effect_id=effect, has_spoiler=True, parse_mode=ParseMode.HTML)


# =====================================================================
# START COMMAND (GROUP)
# =====================================================================

@Client.on_message(filters.command("start") & filters.group & ~BANNED_USERS)
@LanguageStart
async def start_gp(client, message: Message, _):
    a = await client.get_me()
    bot_id = a.id
    uptime = get_readable_time(int(time.time() - _boot_))

    # ⚡ Single query instead of five
    settings = await get_bot_settings(bot_id)
    raw_support = settings.get("support", "No support chat set.")
    txt_add = get_custom_btn_text(settings, "add", _["S_B_1"])
    txt_support = get_custom_btn_text(settings, "support", _["S_B_2"])
    raw_video = get_start_video(settings)
    raw_img = get_start_image(settings)

    C_SUPPORT_CHAT = format_link(raw_support)
    markup = make_gp_panel(a.username, txt_add, txt_support, C_SUPPORT_CHAT)
    caption = _["start_1"].format(a.mention, uptime)
    
    start_video = random.choice(raw_video.split("|||")) if raw_video else None
    start_img = random.choice(raw_img.split("|||")) if raw_img else None
    
    if start_video:
        try:
            return await message.reply_video(start_video, caption=caption, reply_markup=markup, has_spoiler=True)
        except:
            pass
    
    photo = start_img if start_img else get_random_start_image()
    await message.reply_photo(photo, caption=caption, reply_markup=markup, has_spoiler=True)
    await add_served_chat_clone(message.chat.id, a.id)


# =====================================================================
# CALLBACKS
# =====================================================================

@Client.on_callback_query(filters.regex("settingsback_home") & ~BANNED_USERS)
@languageCB
async def home_back_handler(client, CallbackQuery, _):
    a = await client.get_me()
    bot_id = a.id

    # ⚡ Single query instead of fourteen
    settings = await get_bot_settings(bot_id)
    C_BOT_OWNER_ID = settings.get("user_id")
    raw_support = settings.get("support", "No support chat set.")
    raw_channel = settings.get("channel", "No channel set.")
    txt_add = get_custom_btn_text(settings, "add", _["S_B_3"])
    txt_support = get_custom_btn_text(settings, "support", _["S_B_9"])
    txt_channel = get_custom_btn_text(settings, "channel", _["S_B_6"])
    txt_owner = get_custom_btn_text(settings, "owner", _["C_B_2"])
    txt_help = get_custom_btn_text(settings, "help", _["S_B_4"])
    raw_custom_btn = get_start_button(settings)
    btn_pos = get_start_btn_pos(settings)
    raw_video = get_start_video(settings)
    raw_img = get_start_image(settings)
    raw_caption = get_start_caption(settings)
    raw_effect = get_start_effect(settings)

    C_SUPPORT_CHAT = format_link(raw_support)
    C_SUPPORT_CHANNEL = format_link(raw_channel)
    OWNER_URL = f"tg://openmessage?user_id={C_BOT_OWNER_ID}"

    custom_button_data = None
    if raw_custom_btn:
        if isinstance(raw_custom_btn, dict):
            custom_button_data = raw_custom_btn
        elif isinstance(raw_custom_btn, str):
            chosen_str = random.choice(raw_custom_btn.split("|||"))
            if "-" in chosen_str:
                txt, url = chosen_str.split("-", 1)
                custom_button_data = {"text": txt.strip(), "url": url.strip()}
    
    markup = make_start_panel(a.username, OWNER_URL,
                              txt_add, txt_support, txt_channel, txt_owner, txt_help,
                              C_SUPPORT_CHAT, C_SUPPORT_CHANNEL,
                              custom_button_data, btn_pos)

    start_video = random.choice(raw_video.split("|||")) if raw_video else None
    start_img = random.choice(raw_img.split("|||")) if raw_img else None
    custom_caption = random.choice(raw_caption.split("|||")) if raw_caption else None
    
    user_mention = get_mention_html(CallbackQuery.from_user.id, CallbackQuery.from_user.first_name)
    bot_mention = get_mention_html(a.id, a.first_name)
    
    if custom_caption:
        try:
            caption = custom_caption.format(name=user_mention, firstname=CallbackQuery.from_user.first_name, botname=bot_mention, username=a.username)
        except:
            caption = custom_caption
    else:
        formatted_text = (
            f"<b>нєу ʙᴀʙʏ {user_mention}, 🥀 ❞</b>\n\n"
            f"<b>๏ ᴛʜɪs ɪs {bot_mention} 🎵 : ғᴀsᴛ & ᴘᴏᴡᴇʀғᴜʟ ᴛɢ ᴍᴜsɪᴄ ʙᴏᴛ.</b>\n"
            f"<b>๏ sᴍᴏᴏᴛʜ ʙᴇᴀᴛs • sᴛᴀʙʟᴇ & sᴇᴀᴍʟᴇss ᴍᴜsɪᴄ ғʟᴏᴡ.</b>\n"
            f"<b>๏ ɴᴇᴡ ᴠᴇʀsɪᴏɴ ᴡɪᴛʜ sᴜᴘᴇʀ ғᴀsᴛ ʏᴏᴜᴛᴜʙᴇ ᴀᴘɪ ʙᴀsᴇᴅ.</b>\n"
            f"<b>•── ⋅ ⋅ ⋅ ────── ⋅  ⋅ ────── ⋅ ⋅ ⋅ ──•</b>\n"
            f"<b>๏ ᴄʟɪᴄᴋ ᴏɴ ᴛʜᴇ ʜᴇʟᴩ ʙᴜᴛᴛᴏɴ ᴛᴏ ɢᴇᴛ ɪɴғᴏʀᴍᴀᴛɪᴏɴ ᴀʙᴏᴜᴛ ᴍʏ ᴍᴏᴅᴜʟᴇs ᴀɴᴅ ᴄᴏᴍᴍᴀɴᴅs.</b>"
        )
        caption = f"<blockquote expandable>{formatted_text}</blockquote>"

    if raw_effect:
        effect = random.choice(raw_effect.split("|||"))
    else:
        try:
            EFFECT_ID = config.EFFECT_ID
        except:
            EFFECT_ID = DEFAULT_EFFECT_IDS
        effect = random.choice(EFFECT_ID)
    
    try:
        effect = int(effect)
    except:
        effect = None

    try:
        if start_video:
            await CallbackQuery.edit_message_media(media=InputMediaVideo(media=start_video, caption=caption), reply_markup=markup)
        else:
            photo = start_img if start_img else get_random_start_image()
            await CallbackQuery.edit_message_media(media=InputMediaPhoto(media=photo, caption=caption), reply_markup=markup)
    except Exception as e:
        try:
            await CallbackQuery.message.delete()
        except:
            pass
        if start_video:
            await CallbackQuery.message.reply_video(start_video, caption=caption, reply_markup=markup, message_effect_id=effect, has_spoiler=True, parse_mode=ParseMode.HTML)
        else:
            photo = start_img if start_img else get_random_start_image()
            await CallbackQuery.message.reply_photo(photo, caption=caption, reply_markup=markup, message_effect_id=effect, has_spoiler=True, parse_mode=ParseMode.HTML)


# =====================================================================
# SETTINGS & MANAGEMENT (Secure)
# =====================================================================

@Client.on_message(filters.command(["transfer", "transferowner"]) & ~BANNED_USERS)
async def transfer_owner(client, message):
    if not await check_owner(client, message):
         return await message.reply_text("❌ **Only Bot Owner can use this.**")

    bot_id = (await client.get_me()).id
    user = message.from_user

    new_owner = None
    if message.reply_to_message:
        new_owner = message.reply_to_message.from_user
    elif len(message.command) > 1:
        try:
            new_owner = await client.get_users(message.command[1])
        except:
            return await message.reply_text("❌ User not found!")
    else:
        return await message.reply_text("❌ Reply to a user or type `/transfer @username`.")

    if new_owner.is_bot:
        return await message.reply_text("❌ Bot cannot be owner.")
    if new_owner.id == user.id:
        return await message.reply_text("❌ You are already the owner.")

    await clonebotdb.update_one({"bot_id": bot_id}, {"$set": {"user_id": new_owner.id}})
    await cloneownerdb.update_one({"bot_id": bot_id}, {"$set": {"user_id": new_owner.id}}, upsert=True)

    await message.reply_text(f"✅ **Ownership Transferred!**\n👑 New Owner: {new_owner.mention}")


@Client.on_message(filters.command("viewstartsettings") & ~BANNED_USERS)
async def view_start_settings(client, message):
    if not await check_owner(client, message): return
    bot_id = (await client.get_me()).id
    settings = await get_bot_settings(bot_id)
    pos = get_start_btn_pos(settings)
    await message.reply_text(f"⚙️ **Settings Viewed**\nButton Position: `{pos}`")


@Client.on_message(filters.command("resetstartsetting") & ~BANNED_USERS)
async def reset_start_settings(client, message):
    if not await check_owner(client, message): return
    bot_id = (await client.get_me()).id
    await clonebotdb.update_one({"bot_id": bot_id}, {"$unset": {
        "start_image": "", "start_video": "", "start_sticker": "", 
        "start_animation": "", "start_caption": "", "start_button": "", 
        "start_btn_pos": "", "start_reaction": "", "start_effect": ""
    }})
    await message.reply_text("🔄 All Start Settings Reset!")


@Client.on_message(filters.command(["setstartreaction", "addstartreaction"]) & ~BANNED_USERS)
async def set_start_reaction_cmd(client, message):
    if not await check_owner(client, message): return
    bot_id = (await client.get_me()).id
    if len(message.command) < 2:
        return await message.reply_text("❌ **Usage:** `/setstartreaction 🔥`")
    
    emoji = message.command[1]
    await add_start_content(bot_id, "start_reaction", emoji)
    await message.reply_text(f"✅ Added: {emoji}")


@Client.on_message(filters.command(["delstartreaction", "resetstartreaction"]) & ~BANNED_USERS)
async def del_start_reaction_cmd(client, message):
    if not await check_owner(client, message): return
    bot_id = (await client.get_me()).id
    await clonebotdb.update_one({"bot_id": bot_id}, {"$unset": {"start_reaction": ""}})
    await message.reply_text("✅ Start Reaction Reset!")


@Client.on_message(filters.command(["setstarteffect", "addstarteffect"]) & ~BANNED_USERS)
async def set_start_effect_cmd(client, message):
    if not await check_owner(client, message): return
    bot_id = (await client.get_me()).id
    if len(message.command) < 2:
        return await message.reply_text("❌ **Usage:** `/setstarteffect 🔥`\nSupported: 🔥, 👍, 👎, ❤️, 🎉, 💩")
    
    EFFECT_MAP = {
        "🔥": "5104841245755180586",
        "👍": "5107584321108051014",
        "👎": "5104858069142078462",
        "❤️": "5044134455711629726",
        "🎉": "5046509860389126442",
        "💩": "5046589136895476101"
    }
    
    arg = message.command[1]
    effect_id = EFFECT_MAP.get(arg, arg) 
    await add_start_content(bot_id, "start_effect", effect_id)
    await message.reply_text(f"✅ Start Effect Added!")


@Client.on_message(filters.command(["delstarteffect", "resetstarteffect"]) & ~BANNED_USERS)
async def del_start_effect_cmd(client, message):
    if not await check_owner(client, message): return
    bot_id = (await client.get_me()).id
    await clonebotdb.update_one({"bot_id": bot_id}, {"$unset": {"start_effect": ""}})
    await message.reply_text("✅ Start Effect Reset!")


@Client.on_message(filters.command(["setstartimg", "addstartimg"]) & ~BANNED_USERS)
async def set_start_image_cmd(client, message):
    if not await check_owner(client, message): return
    bot_id = (await client.get_me()).id
    if message.reply_to_message and message.reply_to_message.photo:
        await add_start_content(bot_id, "start_image", message.reply_to_message.photo.file_id)
        await message.reply_text("✅ Image Added!")
    else:
        await message.reply_text("Reply to a photo.")

@Client.on_message(filters.command(["delstartimg", "resetstartimg"]) & ~BANNED_USERS)
async def del_start_image_cmd(client, message):
    if not await check_owner(client, message): return
    bot_id = (await client.get_me()).id
    await clonebotdb.update_one({"bot_id": bot_id}, {"$unset": {"start_image": ""}})
    await message.reply_text("✅ Images Reset!")


@Client.on_message(filters.command(["setstartvideo", "addstartvideo"]) & ~BANNED_USERS)
async def set_start_video_cmd(client, message):
    if not await check_owner(client, message): return
    bot_id = (await client.get_me()).id
    if message.reply_to_message and message.reply_to_message.video:
        await add_start_content(bot_id, "start_video", message.reply_to_message.video.file_id)
        await message.reply_text("✅ Video Added!")
    else:
        await message.reply_text("Reply to a video.")

@Client.on_message(filters.command(["delstartvideo", "resetstartvideo"]) & ~BANNED_USERS)
async def del_start_video_cmd(client, message):
    if not await check_owner(client, message): return
    bot_id = (await client.get_me()).id
    await clonebotdb.update_one({"bot_id": bot_id}, {"$unset": {"start_video": ""}})
    await message.reply_text("✅ Videos Reset!")


@Client.on_message(filters.command(["setstartsticker", "addstartsticker"]) & ~BANNED_USERS)
async def set_start_sticker_cmd(client, message):
    if not await check_owner(client, message): return
    bot_id = (await client.get_me()).id
    if message.reply_to_message and message.reply_to_message.sticker:
        await add_start_content(bot_id, "start_sticker", message.reply_to_message.sticker.file_id)
        await message.reply_text("✅ Sticker Added!")
    else:
        await message.reply_text("Reply to a sticker.")

@Client.on_message(filters.command(["delstartsticker", "resetstartsticker"]) & ~BANNED_USERS)
async def del_start_sticker_cmd(client, message):
    if not await check_owner(client, message): return
    bot_id = (await client.get_me()).id
    await clonebotdb.update_one({"bot_id": bot_id}, {"$unset": {"start_sticker": ""}})
    await message.reply_text("✅ Stickers Reset!")


@Client.on_message(filters.command(["setstartanimation", "addstartanimation"]) & ~BANNED_USERS)
async def set_start_animation_cmd(client, message):
    if not await check_owner(client, message): return
    bot_id = (await client.get_me()).id
    if message.reply_to_message and message.reply_to_message.animation:
        await add_start_content(bot_id, "start_animation", message.reply_to_message.animation.file_id)
        await message.reply_text("✅ Animation Added!")
    else:
        await message.reply_text("Reply to a GIF.")

@Client.on_message(filters.command(["delstartanimation", "resetstartanimation"]) & ~BANNED_USERS)
async def del_start_animation_cmd(client, message):
    if not await check_owner(client, message): return
    bot_id = (await client.get_me()).id
    await clonebotdb.update_one({"bot_id": bot_id}, {"$unset": {"start_animation": ""}})
    await message.reply_text("✅ Animations Reset!")


@Client.on_message(filters.command(["setstartcaption", "addstartcaption"]) & ~BANNED_USERS)
async def set_start_caption_cmd(client, message):
    if not await check_owner(client, message): return
    bot_id = (await client.get_me()).id
    if message.reply_to_message:
        text = message.reply_to_message.text.html if message.reply_to_message.text else message.reply_to_message.caption.html
        await add_start_content(bot_id, "start_caption", text)
        await message.reply_text("✅ Caption Added!")
    else:
        await message.reply_text("Reply to a text.")

@Client.on_message(filters.command(["delstartcaption", "resetstartcaption"]) & ~BANNED_USERS)
async def del_start_caption_cmd(client, message):
    if not await check_owner(client, message): return
    bot_id = (await client.get_me()).id
    await clonebotdb.update_one({"bot_id": bot_id}, {"$unset": {"start_caption": ""}})
    await message.reply_text("✅ Captions Reset!")


@Client.on_message(filters.command(["setstartbutton", "addstartbutton"]) & ~BANNED_USERS)
async def set_start_button_cmd(client, message):
    if not await check_owner(client, message): return
    bot_id = (await client.get_me()).id
    data = message.text.split(None, 1)[1] if len(message.command) > 1 else None
    
    if not data or "-" not in data: 
        return await message.reply_text("Format: `/addstartbutton Text - URL`")
    
    txt, url = data.split("-", 1)
    btn_str = f"{txt.strip()} - {url.strip()}"
    
    await add_start_content(bot_id, "start_button", btn_str)
    await message.reply_text("✅ Button Added!")

@Client.on_message(filters.command(["delstartbutton", "resetstartbutton"]) & ~BANNED_USERS)
async def del_start_button_cmd(client, message):
    if not await check_owner(client, message): return
    bot_id = (await client.get_me()).id
    await clonebotdb.update_one({"bot_id": bot_id}, {"$unset": {"start_button": ""}})
    await message.reply_text("✅ Buttons Reset!")


@Client.on_message(filters.command("setbtnpos") & ~BANNED_USERS)
async def set_btn_pos_cmd(client, message):
    if not await check_owner(client, message): return
    bot_id = (await client.get_me()).id
    if len(message.command) < 2:
        return await message.reply_text("Usage: `/setbtnpos [UP/DOWN/MID]`")
    
    raw_pos = message.command[1].upper()
    valid_pos = ["UP", "TOP", "DOWN", "BOTTOM", "MID", "MIDDLE"]
    
    if raw_pos in valid_pos:
        if raw_pos == "TOP": raw_pos = "UP"
        if raw_pos == "BOTTOM": raw_pos = "DOWN"
        if raw_pos == "MIDDLE": raw_pos = "MID"
        
        await clonebotdb.update_one({"bot_id": bot_id}, {"$set": {"start_btn_pos": raw_pos}}, upsert=True)
        await message.reply_text(f"✅ Position Set: **{raw_pos}**")
    else:
        await message.reply_text("❌ Invalid! Use: UP, DOWN, MID")
