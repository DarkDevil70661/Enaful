from pyrogram import filters, Client
from pyrogram.types import InlineKeyboardMarkup, Message

from PritiMusic import app
from PritiMusic.utils.database import get_playmode, get_playtype, is_nonadmin_chat
from PritiMusic.utils.decorators.language import language
from PritiMusic.utils.inline.settings import playmode_users_markup
from config import BANNED_USERS


@Client.on_message(
    filters.command(
        ["playmode", "mode"], 
        prefixes=["/", "!", "%", ",", "", ".", "@", "#"]
    )
    & filters.group
    & ~BANNED_USERS
)
@language
async def playmode_settings(client, message: Message, _):
    # 1. Play Mode Check (Direct Link vs Inline)
    playmode = await get_playmode(message.chat.id)
    Direct = True if playmode == "Direct" else None
    
    # 2. Admin Rights Check (Auth Users vs Everyone)
    is_non_admin = await is_nonadmin_chat(message.chat.id)
    Group = True if not is_non_admin else None
    
    # 3. Play Type Check (Admins vs Everyone)
    playty = await get_playtype(message.chat.id)
    Playtype = None if playty == "Everyone" else True
    
    # 4. Generate Buttons
    buttons = playmode_users_markup(_, Direct, Group, Playtype)
    
    # 5. Send Response
    await message.reply_text(
        _["play_22"].format(message.chat.title),
        reply_markup=InlineKeyboardMarkup(buttons),
    )
