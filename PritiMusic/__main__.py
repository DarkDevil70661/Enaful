
import asyncio
import importlib

from pyrogram import idle
from pytgcalls.exceptions import NoActiveGroupCall

import config
from PritiMusic import LOGGER, app, userbot
from PritiMusic.core.call import Lucky
from PritiMusic.misc import sudo
from PritiMusic.plugins import ALL_MODULES
from PritiMusic.utils.database import get_banned_users, get_gbanned
from config import BANNED_USERS
from PritiMusic.plugins.tools.clone import restart_bots


async def init():
    if not config.STRING1:
        LOGGER(__name__).error("String Session not filled, please Provide a valid session.")
        exit()
    await sudo()
    try:
        users = await get_gbanned()
        for user_id in users:
            BANNED_USERS.add(user_id)
        users = await get_banned_users()
        for user_id in users:
            BANNED_USERS.add(user_id)
    except:
        pass
    await app.start()
    for all_module in ALL_MODULES:
        importlib.import_module("PritiMusic.plugins" + all_module)
    LOGGER("PritiMusic.plugins").info("𝐀𝐥𝐥 𝐅𝐞𝐚𝐭𝐮𝐫𝐞𝐬 𝐋𝐨𝐚𝐝𝐞𝐝 𝐁𝐚𝐛𝐲🥳...")
    await userbot.start()
    await Lucky.start()
    try:
        await Lucky.stream_call("https://te.legra.ph/file/29f784eb49d230ab62e9e.mp4")
    except NoActiveGroupCall:
        # ⚠️ Not fatal: log-group voice chat isn't live yet. Previously this
        # called exit() here, which killed the whole process (main bot +
        # every clone) on Railway and triggered an auto-restart loop just
        # because one voice chat check failed. Just warn and keep going.
        LOGGER("PritiMusic").warning(
            "𝗡𝗼 𝗮𝗰𝘁𝗶𝘃𝗲 𝘃𝗼𝗶𝗰𝗲 𝗰𝗵𝗮𝘁 𝗶𝗻 𝗹𝗼𝗴 𝗴𝗿𝗼𝘂𝗽/𝗰𝗵𝗮𝗻𝗻𝗲𝗹 — 𝗰𝗼𝗻𝘁𝗶𝗻𝘂𝗶𝗻𝗴 𝗮𝗻𝘆𝘄𝗮𝘆."
        )
    except:
        pass
    await Lucky.decorators()
    await restart_bots()
    LOGGER("PritiMusic").info(
        "╔═════ஜ۩۞۩ஜ════╗\n  ☠︎︎𝗠𝗔𝗗𝗘 𝗕𝗬 𝗣𝗿𝗼𝗕𝗼t𝘀☠︎︎\n╚═════ஜ۩۞۩ஜ════╝"
    )
    await idle()
    await app.stop()
    await userbot.stop()
    LOGGER("PritiMusic").info("𝗦𝗧𝗢𝗣 𝗠𝗨𝗦𝗜𝗖🎻 𝗕𝗢𝗧..")


if __name__ == "__main__":
    asyncio.get_event_loop().run_until_complete(init())
