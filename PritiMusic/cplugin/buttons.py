import math
import random
from pyrogram import enums
from pyrogram.types import InlineKeyboardButton
from PritiMusic.utils.formatters import time_to_seconds
import config

# 🎨 Premium colored-button styles for every player panel in the clone bot.
STYLES = [
    enums.ButtonStyle.PRIMARY,
    enums.ButtonStyle.SUCCESS,
    enums.ButtonStyle.DANGER,
]

def _styles():
    """Fresh random (alone, group) style pair for each panel render."""
    alone = random.choice(STYLES)
    group = random.choice([s for s in STYLES if s != alone])
    return alone, group

def track_markup(_, videoid, user_id, channel, fplay):
    alone, group = _styles()
    buttons = [
        [
            InlineKeyboardButton(
                text=_["P_B_1"],
                callback_data=f"MusicStream {videoid}|{user_id}|a|{channel}|{fplay}",
                style=group,
            ),
            InlineKeyboardButton(
                text=_["P_B_2"],
                callback_data=f"MusicStream {videoid}|{user_id}|v|{channel}|{fplay}",
                style=group,
            ),
        ],
        [
            InlineKeyboardButton(
                text=_["CLOSE_BUTTON"],
                callback_data=f"forceclose {videoid}|{user_id}",
                style=alone,
            )
        ],
    ]
    return buttons

def stream_markup_timer(_, chat_id, played, dur):
    alone, group = _styles()
    played_sec = time_to_seconds(played)
    duration_sec = time_to_seconds(dur)
    percentage = (played_sec / duration_sec) * 100 if duration_sec else 0
    umm = math.floor(percentage)
    if 0 < umm <= 10: bar = "◉—————————"
    elif 10 < umm < 20: bar = "—◉————————"
    elif 20 <= umm < 30: bar = "——◉———————"
    elif 30 <= umm < 40: bar = "———◉——————"
    elif 40 <= umm < 50: bar = "————◉—————"
    elif 50 <= umm < 60: bar = "—————◉————"
    elif 60 <= umm < 70: bar = "——————◉———"
    elif 70 <= umm < 80: bar = "———————◉——"
    elif 80 <= umm < 95: bar = "————————◉—"
    else: bar = "—————————◉"
    buttons = [
        [InlineKeyboardButton(text=f"{played} {bar} {dur}", callback_data="GetTimer", style=alone)],
        [
            InlineKeyboardButton(text="▷", callback_data=f"ADMIN Resume|{chat_id}", style=group),
            InlineKeyboardButton(text="II", callback_data=f"ADMIN Pause|{chat_id}", style=group),
            InlineKeyboardButton(text="↻", callback_data=f"ADMIN Replay|{chat_id}", style=group),
            InlineKeyboardButton(text="‣‣I", callback_data=f"ADMIN Skip|{chat_id}", style=group),
            InlineKeyboardButton(text="▢", callback_data=f"ADMIN Stop|{chat_id}", style=group),
        ],
        [InlineKeyboardButton(text=_["CLOSE_BUTTON"], callback_data="close", style=alone)]
    ]
    return buttons

def stream_markup(_, chat_id):
    alone, group = _styles()
    buttons = [
        [
            InlineKeyboardButton(text="▷", callback_data=f"ADMIN Resume|{chat_id}", style=group),
            InlineKeyboardButton(text="II", callback_data=f"ADMIN Pause|{chat_id}", style=group),
            InlineKeyboardButton(text="↻", callback_data=f"ADMIN Replay|{chat_id}", style=group),
            InlineKeyboardButton(text="‣‣I", callback_data=f"ADMIN Skip|{chat_id}", style=group),
            InlineKeyboardButton(text="▢", callback_data=f"ADMIN Stop|{chat_id}", style=group),
        ],
        [InlineKeyboardButton(text=_["CLOSE_BUTTON"], callback_data="close", style=alone)]
    ]
    return buttons

def playlist_markup(_, videoid, user_id, ptype, channel, fplay):
    alone, group = _styles()
    buttons = [
        [
            InlineKeyboardButton(text=_["P_B_1"], callback_data=f"LuckyPlaylists {videoid}|{user_id}|{ptype}|a|{channel}|{fplay}", style=group),
            InlineKeyboardButton(text=_["P_B_2"], callback_data=f"LuckyPlaylists {videoid}|{user_id}|{ptype}|v|{channel}|{fplay}", style=group),
        ],
        [InlineKeyboardButton(text=_["CLOSE_BUTTON"], callback_data=f"forceclose {videoid}|{user_id}", style=alone)],
    ]
    return buttons

def livestream_markup(_, videoid, user_id, mode, channel, fplay):
    alone, group = _styles()
    buttons = [
        [InlineKeyboardButton(text=_["P_B_3"], callback_data=f"LiveStream {videoid}|{user_id}|{mode}|{channel}|{fplay}", style=alone)],
        [InlineKeyboardButton(text=_["CLOSE_BUTTON"], callback_data=f"forceclose {videoid}|{user_id}", style=group)],
    ]
    return buttons

def slider_markup(_, videoid, user_id, query, query_type, channel, fplay):
    alone, group = _styles()
    query = f"{query[:20]}"
    buttons = [
        [
            InlineKeyboardButton(text=_["P_B_1"], callback_data=f"MusicStream {videoid}|{user_id}|a|{channel}|{fplay}", style=group),
            InlineKeyboardButton(text=_["P_B_2"], callback_data=f"MusicStream {videoid}|{user_id}|v|{channel}|{fplay}", style=group),
        ],
        [
            InlineKeyboardButton(text="◁", callback_data=f"slider B|{query_type}|{query}|{user_id}|{channel}|{fplay}", style=group),
            InlineKeyboardButton(text=_["CLOSE_BUTTON"], callback_data=f"forceclose {query}|{user_id}", style=alone),
            InlineKeyboardButton(text="▷", callback_data=f"slider F|{query_type}|{query}|{user_id}|{channel}|{fplay}", style=group),
        ],
    ]
    return buttons

def telegram_markup(_, chat_id):
    alone, group = _styles()
    buttons = [
        [
            InlineKeyboardButton(text="Next", callback_data=f"PanelMarkup None|{chat_id}", style=group),
            InlineKeyboardButton(text=_["CLOSEMENU_BUTTON"], callback_data="close", style=alone),
        ],
    ]
    return buttons

def queue_markup(_, videoid, chat_id, bot_username):
    alone, group = _styles()
    buttons = [
        [InlineKeyboardButton(text=_["S_B_3"], url=f"https://t.me/{bot_username}?startgroup=true", style=alone)],
        [
            InlineKeyboardButton(text="II ᴘᴀᴜsᴇ", callback_data=f"ADMIN Pause|{chat_id}", style=group),
            InlineKeyboardButton(text="▢ sᴛᴏᴘ", callback_data=f"ADMIN Stop|{chat_id}", style=group),
            InlineKeyboardButton(text="sᴋɪᴘ ‣‣I", callback_data=f"ADMIN Skip|{chat_id}", style=group),
        ],
        [
            InlineKeyboardButton(text="▷ ʀᴇsᴜᴍᴇ", callback_data=f"ADMIN Resume|{chat_id}", style=group),
            InlineKeyboardButton(text="ʀᴇᴘʟᴀʏ ↺", callback_data=f"ADMIN Replay|{chat_id}", style=group),
        ],
        [InlineKeyboardButton(text="ᴍᴏʀᴇ", callback_data=f"PanelMarkup None|{chat_id}", style=alone)],
    ]
    return buttons

def stream_markup2(_, chat_id, bot_username):
    alone, group = _styles()
    buttons = [
        [InlineKeyboardButton(text=_["S_B_3"], url=f"https://t.me/{bot_username}?startgroup=true", style=alone)],
        [
            InlineKeyboardButton(text="▷", callback_data=f"ADMIN Resume|{chat_id}", style=group),
            InlineKeyboardButton(text="II", callback_data=f"ADMIN Pause|{chat_id}", style=group),
            InlineKeyboardButton(text="↻", callback_data=f"ADMIN Replay|{chat_id}", style=group),
            InlineKeyboardButton(text="‣‣I", callback_data=f"ADMIN Skip|{chat_id}", style=group),
            InlineKeyboardButton(text="▢", callback_data=f"ADMIN Stop|{chat_id}", style=group),
        ],
        [InlineKeyboardButton(text=_["CLOSEMENU_BUTTON"], callback_data="close", style=alone)],
    ]
    return buttons

def stream_markup_timer2(_, chat_id, played, dur):
    alone, group = _styles()
    played_sec = time_to_seconds(played)
    duration_sec = time_to_seconds(dur)
    percentage = (played_sec / duration_sec) * 100 if duration_sec else 0
    umm = math.floor(percentage)
    if 0 < umm <= 40: bar = "◉——————————"
    elif 10 < umm < 20: bar = "—◉—————————"
    elif 20 < umm < 30: bar = "——◉————————"
    elif 30 <= umm < 40: bar = "———◉———————"
    elif 40 <= umm < 50: bar = "————◉——————"
    elif 50 <= umm < 60: bar = "——————◉————"
    elif 50 <= umm < 70: bar = "———————◉———"
    else: bar = "——————————◉"
    buttons = [
        [InlineKeyboardButton(text=f"{played} {bar} {dur}", callback_data="GetTimer", style=alone)],
        [
            InlineKeyboardButton(text="▷", callback_data=f"ADMIN Resume|{chat_id}", style=group),
            InlineKeyboardButton(text="II", callback_data=f"ADMIN Pause|{chat_id}", style=group),
            InlineKeyboardButton(text="↻", callback_data=f"ADMIN Replay|{chat_id}", style=group),
            InlineKeyboardButton(text="‣‣I", callback_data=f"ADMIN Skip|{chat_id}", style=group),
            InlineKeyboardButton(text="▢", callback_data=f"ADMIN Stop|{chat_id}", style=group),
        ],
        [InlineKeyboardButton(text=_["CLOSEMENU_BUTTON"], callback_data="close", style=alone)],
    ]
    return buttons

def panel_markup_1(_, videoid, chat_id, bot_username):
    alone, group = _styles()
    buttons = [
        [InlineKeyboardButton(text=_["S_B_3"], url=f"https://t.me/{bot_username}?startgroup=true", style=alone)],
        [
            InlineKeyboardButton(text="sᴜғғʟᴇ", callback_data=f"ADMIN Shuffle|{chat_id}", style=group),
            InlineKeyboardButton(text="ʟᴏᴏᴘ ↺", callback_data=f"ADMIN Loop|{chat_id}", style=group),
        ],
        [
            InlineKeyboardButton(text="◁ 10 sᴇᴄ", callback_data=f"ADMIN 1|{chat_id}", style=group),
            InlineKeyboardButton(text="10 sᴇᴄ ▷", callback_data=f"ADMIN 2|{chat_id}", style=group),
        ],
        [
            InlineKeyboardButton(text="ʜᴏᴍᴇ", callback_data=f"Pages Back|2|{videoid}|{chat_id}", style=alone),
            InlineKeyboardButton(text="ɴᴇxᴛ", callback_data=f"Pages Forw|2|{videoid}|{chat_id}", style=alone),
        ],
    ]
    return buttons

def panel_markup_2(_, videoid, chat_id, bot_username):
    alone, group = _styles()
    buttons = [
        [InlineKeyboardButton(text=_["S_B_3"], url=f"https://t.me/{bot_username}?startgroup=true", style=alone)],
        [
            InlineKeyboardButton(text="🕒 0.5x", callback_data=f"SpeedUP {chat_id}|0.5", style=group),
            InlineKeyboardButton(text="🕓 0.75x", callback_data=f"SpeedUP {chat_id}|0.75", style=group),
            InlineKeyboardButton(text="🕤 1.0x", callback_data=f"SpeedUP {chat_id}|1.0", style=group),
        ],
        [
            InlineKeyboardButton(text="🕤 1.5x", callback_data=f"SpeedUP {chat_id}|1.5", style=group),
            InlineKeyboardButton(text="🕛 2.0x", callback_data=f"SpeedUP {chat_id}|2.0", style=group),
        ],
        [InlineKeyboardButton(text="ʙᴀᴄᴋ", callback_data=f"Pages Back|1|{videoid}|{chat_id}", style=alone)],
    ]
    return buttons

def panel_markup_3(_, videoid, chat_id):
    alone, group = _styles()
    buttons = [
        [
            InlineKeyboardButton(text="🕒 0.5x", callback_data=f"SpeedUP {chat_id}|0.5", style=group),
            InlineKeyboardButton(text="🕓 0.75x", callback_data=f"SpeedUP {chat_id}|0.75", style=group),
            InlineKeyboardButton(text="🕤 1.0x", callback_data=f"SpeedUP {chat_id}|1.0", style=group),
        ],
        [
            InlineKeyboardButton(text="🕤 1.5x", callback_data=f"SpeedUP {chat_id}|1.5", style=group),
            InlineKeyboardButton(text="🕛 2.0x", callback_data=f"SpeedUP {chat_id}|2.0", style=group),
        ],
        [InlineKeyboardButton(text="ʙᴀᴄᴋ", callback_data=f"Pages Back|2|{videoid}|{chat_id}", style=alone)],
    ]
    return buttons

def panel_markup_4(_, vidid, chat_id, played, dur):
    alone, group = _styles()
    played_sec = time_to_seconds(played)
    duration_sec = time_to_seconds(dur)
    percentage = (played_sec / duration_sec) * 100 if duration_sec else 0
    umm = math.floor(percentage)
    if 0 < umm <= 40: bar = "◉——————————"
    elif 10 < umm < 20: bar = "—◉—————————"
    elif 20 < umm < 30: bar = "——◉————————"
    elif 30 <= umm < 40: bar = "———◉———————"
    elif 40 <= umm < 50: bar = "————◉——————"
    elif 50 <= umm < 60: bar = "——————◉————"
    elif 50 <= umm < 70: bar = "———————◉———"
    else: bar = "——————————◉"
    buttons = [
        [InlineKeyboardButton(text=f"{played} {bar} {dur}", callback_data="GetTimer", style=alone)],
        [
            InlineKeyboardButton(text="II ᴘᴀᴜsᴇ", callback_data=f"ADMIN Pause|{chat_id}", style=group),
            InlineKeyboardButton(text="▢ sᴛᴏᴘ ▢", callback_data=f"ADMIN Stop|{chat_id}", style=group),
            InlineKeyboardButton(text="sᴋɪᴘ ‣‣I", callback_data=f"ADMIN Skip|{chat_id}", style=group),
        ],
        [
            InlineKeyboardButton(text="▷ ʀᴇsᴜᴍᴇ", callback_data=f"ADMIN Resume|{chat_id}", style=group),
            InlineKeyboardButton(text="ʀᴇᴘʟᴀʏ ↺", callback_data=f"ADMIN Replay|{chat_id}", style=group),
        ],
        [InlineKeyboardButton(text="ʜᴏᴍᴇ", callback_data=f"MainMarkup {vidid}|{chat_id}", style=alone)],
    ]
    return buttons

def panel_markup_5(_, videoid, chat_id, bot_username):
    alone, group = _styles()
    buttons = [
        [InlineKeyboardButton(text=_["S_B_3"], url=f"https:t.me/{bot_username}?startgroup=true", style=alone)],
        [
            InlineKeyboardButton(text="ᴘᴀᴜsᴇ", callback_data=f"ADMIN Pause|{chat_id}", style=group),
            InlineKeyboardButton(text="sᴛᴏᴘ", callback_data=f"ADMIN Stop|{chat_id}", style=group),
            InlineKeyboardButton(text="sᴋɪᴘ", callback_data=f"ADMIN Skip|{chat_id}", style=group),
        ],
        [
            InlineKeyboardButton(text="ʀᴇsᴜᴍᴇ", callback_data=f"ADMIN Resume|{chat_id}", style=group),
            InlineKeyboardButton(text="ʀᴇᴘʟᴀʏ", callback_data=f"ADMIN Replay|{chat_id}", style=group),
        ],
        [
            InlineKeyboardButton(text="ʜᴏᴍᴇ", callback_data=f"MainMarkup {videoid}|{chat_id}", style=alone),
            InlineKeyboardButton(text="ɴᴇxᴛ", callback_data=f"Pages Forw|1|{videoid}|{chat_id}", style=alone),
        ],
    ]
    return buttons

def panel_markup_clone(_, vidid, chat_id):
    alone, group = _styles()
    buttons = [
        [
            InlineKeyboardButton(text="▷", callback_data=f"ADMIN Resume|{chat_id}", style=group),
            InlineKeyboardButton(text="II", callback_data=f"ADMIN Pause|{chat_id}", style=group),
            InlineKeyboardButton(text="‣‣I", callback_data=f"ADMIN Skip|{chat_id}", style=group),
            InlineKeyboardButton(text="▢", callback_data=f"ADMIN Stop|{chat_id}", style=group),
        ],
        [InlineKeyboardButton(text=_["CLOSE_BUTTON"], callback_data="close", style=alone)]
    ]
    return buttons
