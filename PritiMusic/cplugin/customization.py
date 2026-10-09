from pyrogram import Client, filters
from pyrogram.types import Message
from PritiMusic.misc import SUDOERS
from PritiMusic.utils.database.clonedb import (
    set_clone_search_type, 
    get_clone_search_type,
    set_clone_stream_caption,
    delete_clone_search_type,
    delete_clone_stream_caption,
    clonebotdb
)

# --- HELPER: Check Permissions ---
async def check_auth(client, message):
    """
    Check if user is Clone Owner OR Main Bot Sudoer.
    """
    user_id = message.from_user.id
    bot_id = client.me.id
    
    # 1. Allow Sudoers
    if user_id in SUDOERS:
        return True
        
    # 2. Allow Clone Owner
    clone_data = await clonebotdb.find_one({"bot_id": bot_id})
    if clone_data and clone_data.get("user_id") == user_id:
        return True
        
    await message.reply_text("❌ **Only the Clone Owner or Sudoers can change these settings.**")
    return False

# --- HELPER: Add to Random List ---
async def add_to_random_list(bot_id, type_key, new_value):
    """
    Appends value to the list separated by |||
    """
    current_data = await get_clone_search_type(bot_id, type_key)
    
    if current_data:
        # Avoid duplicates
        if new_value in current_data:
            return False 
        final_value = f"{current_data}|||{new_value}"
    else:
        final_value = new_value
    
    await set_clone_search_type(bot_id, type_key, final_value)
    return True

# ==========================================
#              SETTING COMMANDS
# ==========================================

# --- 1. TEXT ---
@Client.on_message(filters.command(["setplaytext", "addplaytext"]))
async def set_play_text(client: Client, message: Message):
    if not await check_auth(client, message):
        return

    if len(message.command) < 2:
        return await message.reply_text("Usage: `/setplaytext <Your Text>`")
    
    text = message.text.split(None, 1)[1]
    bot_id = client.me.id
    
    await add_to_random_list(bot_id, "text", text)
    await message.reply_text(f"✅ **Added to Random List:**\n\n`{text}`")

# --- 2. STICKER ---
@Client.on_message(filters.command(["setplaysticker", "addplaysticker"]))
async def set_play_sticker(client: Client, message: Message):
    if not await check_auth(client, message):
        return

    if not message.reply_to_message or not message.reply_to_message.sticker:
        return await message.reply_text("Usage: **Reply to a Sticker** with `/setplaysticker`")
    
    file_id = message.reply_to_message.sticker.file_id
    bot_id = client.me.id
    
    await add_to_random_list(bot_id, "sticker", file_id)
    await message.reply_text("✅ **Sticker Added to Random List!**")

# --- 3. ANIMATION (GIF) ---
@Client.on_message(filters.command(["setplayanimation", "addplayanimation"]))
async def set_play_gif(client: Client, message: Message):
    if not await check_auth(client, message):
        return

    if not message.reply_to_message or not message.reply_to_message.animation:
        return await message.reply_text("Usage: **Reply to a GIF** with `/setplayanimation`")
    
    file_id = message.reply_to_message.animation.file_id
    bot_id = client.me.id
    
    await add_to_random_list(bot_id, "animation", file_id)
    
    # Auto-Hide Text (Set invisible char if text is empty to ensure caption logic works)
    current_text = await get_clone_search_type(bot_id, "text")
    if not current_text:
        await set_clone_search_type(bot_id, "text", "⠀")
        
    await message.reply_text("✅ **GIF Added to Random List!**")

# --- 4. VIDEO (MP4) ---
@Client.on_message(filters.command(["setplayvideo", "addplayvideo"]))
async def set_play_video(client: Client, message: Message):
    if not await check_auth(client, message):
        return

    if not message.reply_to_message or not message.reply_to_message.video:
        return await message.reply_text("Usage: **Reply to a Video** with `/setplayvideo`")
    
    file_id = message.reply_to_message.video.file_id
    bot_id = client.me.id
    
    await add_to_random_list(bot_id, "video", file_id)
    
    current_text = await get_clone_search_type(bot_id, "text")
    if not current_text:
        await set_clone_search_type(bot_id, "text", "⠀")
    
    await message.reply_text("✅ **Video Added to Random List!**")

# --- 5. PHOTO (IMAGE) ---
@Client.on_message(filters.command(["setplayphoto", "addplayphoto"]))
async def set_play_photo(client: Client, message: Message):
    if not await check_auth(client, message):
        return

    if not message.reply_to_message or not message.reply_to_message.photo:
        return await message.reply_text("Usage: **Reply to a Photo** with `/setplayphoto`")
    
    file_id = message.reply_to_message.photo.file_id
    bot_id = client.me.id
    
    await add_to_random_list(bot_id, "photo", file_id)
    
    current_text = await get_clone_search_type(bot_id, "text")
    if not current_text:
        await set_clone_search_type(bot_id, "text", "⠀")
    
    await message.reply_text("✅ **Photo Added to Random List!**")

# --- 6. CAPTION SETTING ---
@Client.on_message(filters.command("setstreamtext"))
async def set_stream_text(client: Client, message: Message):
    if not await check_auth(client, message):
        return

    if len(message.command) < 2:
        return await message.reply_text(
            "**Usage:** `/setstreamtext <Your Caption>`\n\n"
            "**Available Variables:**\n"
            "`{0}` : Song Name\n"
            "`{1}` : Duration\n"
            "`{2}` : Requested By Link\n\n"
            "**Example:**\n"
            "`/setstreamtext 🎸 Playing: {0} | ⏳ Time: {1}`"
        )
    
    text = message.text.split(None, 1)[1]
    bot_id = client.me.id
    
    await set_clone_stream_caption(bot_id, text)
    await message.reply_text(f"✅ **Stream Caption Updated:**\n\n`{text}`")

# ==========================================
#              DELETE / RESET COMMANDS
# ==========================================

@Client.on_message(filters.command(["delplay", "resetplay", "delplaymode"]))
async def delete_play_mode(client: Client, message: Message):
    if not await check_auth(client, message):
        return
        
    bot_id = client.me.id
    await delete_clone_search_type(bot_id)
    await message.reply_text("🗑️ **Search Mode Reset!**\nAll saved random lists cleared.")

@Client.on_message(filters.command(["delstreamtext", "resetstreamtext"]))
async def delete_stream_text_cmd(client: Client, message: Message):
    if not await check_auth(client, message):
        return
        
    bot_id = client.me.id
    try:
        await delete_clone_stream_caption(bot_id)
    except:
        pass
    await message.reply_text("🗑️ **Stream Caption Reset!**")
