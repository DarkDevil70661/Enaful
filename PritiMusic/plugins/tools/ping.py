import random  # <--- YEH IMPORT JARURI HAI
from datetime import datetime

from pyrogram import filters
from pyrogram.types import Message
from config import *
from PritiMusic import app
from PritiMusic.core.call import Lucky
from PritiMusic.utils import bot_sys_stats
from PritiMusic.utils.decorators.language import language
from PritiMusic.utils.inline import supp_markup
from config import BANNED_USERS
from config import PING_IMG_URL


@app.on_message(filters.command("ping", prefixes=["/", "!", "%", ",", "", ".", "@", "#"]) & ~BANNED_USERS)
@language
async def ping_com(client, message: Message, _):
    start = datetime.now()
    
    # --- FIX START ---
    # Agar PING_IMG_URL list hai (split laga hai), toh random choose karo
    # Agar single string hai, toh waisa hi rahne do
    if isinstance(PING_IMG_URL, list):
        response_img = random.choice(PING_IMG_URL)
    else:
        response_img = PING_IMG_URL
    # --- FIX END ---

    response = await message.reply_photo(
        photo=response_img, # <--- Yahan fixed variable use kiya
        caption=_["ping_1"].format(app.mention),
    )
    
    pytgping = await Lucky.ping()
    UP, CPU, RAM, DISK = await bot_sys_stats()
    resp = (datetime.now() - start).microseconds / 1000
    
    await response.edit_text(
        _["ping_2"].format(resp, app.mention, UP, RAM, CPU, DISK, pytgping),
        reply_markup=supp_markup(_),
    )