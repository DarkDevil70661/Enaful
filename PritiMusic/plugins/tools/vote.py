import asyncio
from pyrogram import Client, filters
from pyrogram.types import Message
from pyrogram.errors import FloodWait, AuthKeyUnregistered

from PritiMusic import app
from PritiMusic.utils.database import clonebotdb
from config import API_ID, API_HASH
from PritiMusic.misc import SUDOERS

# --- COMMAND: /vote [Name] [Delay] ---
@app.on_message(filters.command(["vote", "poll", "massvote"]) & SUDOERS)
async def custom_delay_vote(client: Client, message: Message):
    if not message.reply_to_message:
        if len(message.command) < 2:
            return await message.reply_text(
                "❌ **Usage:**\n"
                "1. Reply: `/vote [Name] [Delay]`\n"
                "2. Link: `/vote [Link] [Name] [Delay]`\n\n"
                "**Example:** `/vote Keshav 2` (Keshav par 2s delay ke sath)"
            )
    
    status_msg = await message.reply_text("🔄 **Analyzing Command...**")
    
    chat_u = None
    msg_id = None
    vote_name = ""
    delay_time = 0

    args = message.command[1:]

    try:
        if message.reply_to_message:
            # --- Case A: Reply ---
            chat_u = message.chat.username if message.chat.username else message.chat.id
            msg_id = message.reply_to_message.id
            
            if not args:
                return await status_msg.edit_text("❌ **Kisko vote karna hai uska naam batao!**")

            # Check agar aakhiri word number hai (Delay ke liye)
            if args[-1].isdigit():
                delay_time = int(args[-1])
                vote_name = " ".join(args[:-1]).lower()
            else:
                vote_name = " ".join(args).lower()

        else:
            # --- Case B: Link ---
            link = args[0]
            
            # Link Logic
            if "t.me/" in link:
                parts = link.split("/")
                if "c" in parts: # Private Link
                    chat_u = int("-100" + parts[-2])
                    msg_id = int(parts[-1])
                else: # Public Link
                    chat_u = parts[-2]
                    msg_id = int(parts[-1])
            else:
                return await status_msg.edit_text("❌ **Invalid Link.**")

            # Option Name & Delay Parse
            if len(args) > 1:
                if args[-1].isdigit() and len(args) > 2:
                    delay_time = int(args[-1])
                    vote_name = " ".join(args[1:-1]).lower()
                else:
                    vote_name = " ".join(args[1:]).lower()
            
            if not vote_name:
                return await status_msg.edit_text("❌ **Kisko vote karna hai uska naam batao!**")

    except Exception as e:
        return await status_msg.edit_text(f"❌ **Error:** `{e}`")

    # 3. FETCH SESSIONS
    sessions = []
    async for bot in clonebotdb.find({"session_string": {"$exists": True}}):
        if bot.get("session_string"):
            sessions.append(bot["session_string"])
    
    from config import STRING1, STRING2, STRING3, STRING4, STRING5
    for s in [STRING1, STRING2, STRING3, STRING4, STRING5]:
        if s:
            sessions.append(s)

    sessions = list(set(sessions))

    if not sessions:
        return await status_msg.edit_text("❌ **No Assistants found!**")

    # Update Status
    await status_msg.edit_text(
        f"🚀 **Auto Vote Mode (By Name)**\n"
        f"🎯 **Target:** `{chat_u}`\n"
        f"🗣️ **Voting For:** `{vote_name.title()}`\n"
        f"💣 **Total IDs:** {len(sessions)}\n"
        f"⏳ **Delay:** `{delay_time} sec` per vote"
    )

    # 4. WORKER FUNCTION (Dono type ke polls support karega)
    async def vote_worker(session):
        async with Client(
            "voter", 
            api_id=API_ID, 
            api_hash=API_HASH, 
            session_string=session, 
            in_memory=True, 
            no_updates=True
        ) as acc:
            try:
                if isinstance(chat_u, str) and not chat_u.startswith("-100"):
                    try:
                        await acc.join_chat(chat_u)
                        await asyncio.sleep(2)
                    except:
                        pass 
                
                # Target message fetch karo
                target_msg = await acc.get_messages(chat_u, msg_id)
                if not target_msg:
                    return False

                # --- METHOD 1: NORMAL TELEGRAM POLL ---
                if target_msg.poll:
                    opt_idx = -1
                    for i, opt in enumerate(target_msg.poll.options):
                        if vote_name in opt.text.lower():
                            opt_idx = i
                            break
                    
                    if opt_idx != -1:
                        await acc.vote_poll(chat_u, msg_id, [opt_idx])
                        return True
                    else:
                        return False # Naam nahi mila poll mein
                
                # --- METHOD 2: INLINE BOT BUTTONS (Jaise Advance_poll_bot) ---
                elif target_msg.reply_markup and target_msg.reply_markup.inline_keyboard:
                    target_btn = None
                    for row in target_msg.reply_markup.inline_keyboard:
                        for btn in row:
                            if vote_name in btn.text.lower():
                                target_btn = btn
                                break
                        if target_btn:
                            break
                            
                    if target_btn:
                        await acc.request_callback_answer(
                            chat_id=chat_u,
                            message_id=msg_id,
                            callback_data=target_btn.callback_data
                        )
                        return True
                    else:
                        return False # Naam nahi mila buttons mein

                return False
                
            except FloodWait as e:
                return False
            except AuthKeyUnregistered:
                return False
            except Exception as e:
                return False

    # 5. EXECUTION LOOP
    successful = 0
    failed = 0
    total = len(sessions)
    
    for i, session in enumerate(sessions):
        is_done = await vote_worker(session)
        
        if is_done:
            successful += 1
        else:
            failed += 1
        
        if i % 5 == 0:
            await status_msg.edit_text(
                f"🔄 **Voting for `{vote_name.title()}`...** ({i+1}/{total})\n"
                f"✅ Done: {successful} | ❌ Fail: {failed}\n"
                f"⏳ **Delay:** {delay_time}s..."
            )
        
        if delay_time > 0 and i < total - 1:
            await asyncio.sleep(delay_time)

    # 6. Final Report
    await status_msg.edit_text(
        f"🏁 **Vote Completed!**\n\n"
        f"🗣️ **Name:** `{vote_name.title()}`\n"
        f"✅ **Successful:** {successful}\n"
        f"❌ **Failed:** {failed}\n"
        f"⏳ **Speed:** {delay_time}s/vote"
    )
