from pyrogram import Client, filters
from pyrogram.enums import ParseMode
from pyrogram.types import Message
from config import BANNED_USERS

@Client.on_message(filters.command("id") & ~BANNED_USERS)
async def getid(client: Client, message: Message):
    chat = message.chat
    your_id = message.from_user.id
    message_id = message.id
    reply = message.reply_to_message

    # 1. Basic Info
    text = f"**[ᴍᴇssᴀɢᴇ ɪᴅ:]({message.link})** `{message_id}`\n"
    text += f"**[ʏᴏᴜʀ ɪᴅ:](tg://user?id={your_id})** `{your_id}`\n"

    # 2. Chat ID Logic
    if len(message.command) == 2:
        # Agar user ne specific username diya hai (/id @username)
        try:
            split = message.text.split(None, 1)[1].strip()
            user = await client.get_users(split)
            text += f"**[ᴜsᴇʀ ɪᴅ:](tg://user?id={user.id})** `{user.id}`\n"
        except Exception:
            return await message.reply_text("❌ **User/Chat not found.**", quote=True)

    text += f"**[ᴄʜᴀᴛ ɪᴅ:](https://t.me/{chat.username})** `{chat.id}`\n\n" if chat.username else f"**[ᴄʜᴀᴛ ɪᴅ:]** `{chat.id}`\n\n"

    # 3. Reply Logic
    if reply:
        # A. Replied User
        if reply.from_user:
            text += f"**[ʀᴇᴘʟɪᴇᴅ ᴍᴇssᴀɢᴇ ɪᴅ:]({reply.link})** `{reply.id}`\n"
            text += f"**[ʀᴇᴘʟɪᴇᴅ ᴜsᴇʀ ɪᴅ:](tg://user?id={reply.from_user.id})** `{reply.from_user.id}`\n\n"

        # B. Forwarded from User/Bot
        if reply.forward_from:
            text += f"**[ғᴏʀᴡᴀʀᴅᴇᴅ ᴜsᴇʀ ɪᴅ:](tg://user?id={reply.forward_from.id})** `{reply.forward_from.id}`\n\n"

        # C. Forwarded from Channel/Chat
        if reply.forward_from_chat:
            text += f"**[ғᴏʀᴡᴀʀᴅᴇᴅ ᴄʜᴀᴛ ɪᴅ:]** `{reply.forward_from_chat.id}`\n"
            if reply.forward_from_chat.username:
                text += f"**[ғᴏʀᴡᴀʀᴅᴇᴅ ᴄʜᴀᴛ:]** @{reply.forward_from_chat.username}\n\n"
            else:
                text += "\n"

        # D. Anonymous Sender / Channel Post
        if reply.sender_chat:
            text += f"**[sᴇɴᴅᴇʀ ᴄʜᴀᴛ ɪᴅ:]** `{reply.sender_chat.id}`\n"

    # 4. Send Response
    await message.reply_text(
        text,
        disable_web_page_preview=True,
        parse_mode=ParseMode.DEFAULT,
    )
