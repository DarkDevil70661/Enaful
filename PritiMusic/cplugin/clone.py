import random
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup, Message
from PritiMusic.utils.decorators.language import language
from config import START_IMG_URL, BOT_LINK

def get_random_start_img():
    if START_IMG_URL:
        if isinstance(START_IMG_URL, list):
            return random.choice(START_IMG_URL)
        return START_IMG_URL
    return "https://telegra.ph/file/2e3d368e77c449c287430.jpg"

@Client.on_message(filters.command("clone"))
@language
async def ping_clone(client: Client, message: Message, _):
    await message.reply_photo(
        photo=get_random_start_img(),
        caption=_["NO_CLONE_MSG"],
        reply_markup=InlineKeyboardMarkup(
            [
                [InlineKeyboardButton("ɢᴏ ᴀɴᴅ ᴄʟᴏɴᴇ", url=BOT_LINK)]
            ]
        ),
        has_spoiler=True
    )