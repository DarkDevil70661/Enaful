import asyncio
import random
from pyrogram import Client, filters
from pyrogram.types import Message
from pyrogram.raw import functions, types
from PritiMusic import app
from PritiMusic.misc import SUDOERS
from PritiMusic.utils.database import clonebotdb
from config import API_ID, API_HASH

# ✅ PROOF LOGIC:
# Report ke sath hum pichle 3-5 messages ki IDs bhejenge taaki Admin dekh sake.

SPAM_COMMENTS = [
    "User is flooding the chat with spam.",
    "Repeatedly posting unwanted ads.",
    "Automated bot behavior detected.",
    "Bulk messaging violation.",
    "Spamming links and scams."
]

VIOLENCE_COMMENTS = [
    "Promoting violence and terrorism.",
    "Threatening real-world harm.",
    "Sharing gore and graphic violence.",
    "Hate speech inciting violence.",
    "Dangerous organization support."
]

PORN_COMMENTS = [
    "Posting explicit sexual content.",
    "Sharing pornography in public.",
    "Violating nudity policies.",
    "Soliciting sexual acts.",
    "NSFW content without warning."
]

CHILD_ABUSE_COMMENTS = [
    "Child exploitation content.",
    "Illegal material involving minors.",
    "Sharing CSAM content.",
    "Promoting harm to children.",
    "Severe policy violation (Child Safety)."
]

FAKE_COMMENTS = [
    "Impersonating official staff.",
    "Fake account for scamming.",
    "Identity theft detected.",
    "Fraudulent profile.",
    "Pretending to be someone else."
]

REPORT_CATEGORIES = [
    {"type": types.InputReportReasonSpam(), "msgs": SPAM_COMMENTS},
    {"type": types.InputReportReasonViolence(), "msgs": VIOLENCE_COMMENTS},
    {"type": types.InputReportReasonPornography(), "msgs": PORN_COMMENTS},
    {"type": types.InputReportReasonChildAbuse(), "msgs": CHILD_ABUSE_COMMENTS},
    {"type": types.InputReportReasonFake(), "msgs": FAKE_COMMENTS}
]

@app.on_message(filters.command(["greport", "massreport"]) & SUDOERS)
async def global_report(client: Client, message: Message):
    if len(message.command) < 2:
        return await message.reply_text(
            "⚠️ **Proof-Based Report Tool**\n\n"
            "**Usage:** `/greport [Username/Link]`\n\n"
            "ℹ️ **New Logic:** Ye tool Target ke **Last 5 Messages** ko scan karega aur Report ke saath **Attach (Proof)** karke bhejega."
        )

    target = message.command[1]
    msg = await message.reply_text("🔄 **Gathering Evidence (Saboot)...**")

    # Fetch Sessions
    sessions = []
    async for bot in clonebotdb.find({"session_string": {"$exists": True}}):
        if bot.get("session_string"):
            sessions.append(bot["session_string"])

    if not sessions:
        return await msg.edit_text("❌ **No Clones Connected!**")

    await msg.edit_text(f"🚀 **Target:** `{target}`\n💣 **Clones:** {len(sessions)}\n🕵️ **Evidence Mode: ON**")

    # Worker Function with Evidence
    async def report_worker(session, category_data):
        async with Client(
            "reporter", 
            api_id=API_ID, 
            api_hash=API_HASH, 
            session_string=session, 
            in_memory=True, 
            no_updates=True
        ) as acc:
            try:
                # 1. Resolve Peer
                peer = await acc.resolve_peer(target)
                
                # 2. ✅ GET PROOF (Fetch Last 3-5 Messages)
                message_ids = []
                try:
                    # History fetch karo
                    async for m in acc.get_chat_history(target, limit=5):
                        message_ids.append(m.id)
                except:
                    # Agar history nahi mili (Private Profile), toh bina IDs ke report karo
                    message_ids = []

                # 3. Select Random Official Comment
                comment = random.choice(category_data["msgs"])
                
                # 4. REPORT WITH PROOF (IDs attach karo)
                await acc.invoke(
                    functions.account.ReportPeer(
                        peer=peer,
                        id=message_ids,  # <--- YAHAN HAI SABOOT
                        reason=category_data["type"],
                        message=comment
                    )
                )
                return True, category_data["type"]
            except Exception:
                return False, None

    # Execution Loop
    successful = 0
    failed = 0
    BATCH_SIZE = 8
    
    for i in range(0, len(sessions), BATCH_SIZE):
        batch = sessions[i:i + BATCH_SIZE]
        tasks = []
        
        for idx, session in enumerate(batch):
            cat_index = (i + idx) % len(REPORT_CATEGORIES)
            category_data = REPORT_CATEGORIES[cat_index]
            tasks.append(report_worker(session, category_data))
        
        results = await asyncio.gather(*tasks)
        
        for success, _ in results:
            if success:
                successful += 1
            else:
                failed += 1
        
        if i % 10 == 0:
            try:
                await msg.edit_text(
                    f"🔄 **Reporting with Proof...**\n"
                    f"✅ Done: {successful}\n"
                    f"❌ Failed: {failed}"
                )
            except:
                pass

    await msg.edit_text(
        f"🏁 **Proof-Based Report Completed!**\n\n"
        f"🎯 **Target:** `{target}`\n"
        f"✅ **Reports Sent:** {successful}\n"
        f"❌ **Failed:** {failed}\n\n"
        f"📝 **Note:** Har Report ke saath Last 5 Messages ka reference attach kiya gaya hai. Action fast hoga."
    )
