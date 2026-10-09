import asyncio
import os
import random
from datetime import datetime, timedelta
from typing import Union

from pyrogram import Client
from pyrogram.types import InlineKeyboardMarkup
from pyrogram.enums import ParseMode

from pytgcalls import PyTgCalls
from pytgcalls.exceptions import NoActiveGroupCall
from ntgcalls import TelegramServerError
from pytgcalls.types import Update, StreamEnded, GroupCallParticipant, AudioQuality, VideoQuality, MediaStream, ChatUpdate
from pytgcalls import filters as fl

import config
from PritiMusic import LOGGER, YouTube, app
from PritiMusic.misc import db
from PritiMusic.utils.database import (
    add_active_chat,
    add_active_video_chat,
    get_lang,
    get_loop,
    group_assistant,
    is_autoend,
    music_on,
    remove_active_chat,
    remove_active_video_chat,
    set_loop,
)
from PritiMusic.utils.exceptions import AssistantErr
from PritiMusic.utils.formatters import check_duration, seconds_to_min, speed_converter
from PritiMusic.utils.inline.play import stream_markup, telegram_markup
from PritiMusic.utils.stream.autoclear import auto_clean
from strings import get_string
from PritiMusic.utils.thumbnails import get_thumb

autoend = {}
counter = {}

# ✅ Helper for Random Image (From Second Code)
def get_random_img(img_list):
    if img_list:
        if isinstance(img_list, list):
            return random.choice(img_list)
        return img_list
    return "https://telegra.ph/file/2e3d368e77c449c287430.jpg" # Fallback

async def _clear_(chat_id):
    db[chat_id] = []
    await remove_active_video_chat(chat_id)
    await remove_active_chat(chat_id)


class Call(PyTgCalls):
    def __init__(self):
        self.userbot1 = Client(
            name="LuckyAss1",
            api_id=config.API_ID,
            api_hash=config.API_HASH,
            session_string=str(config.STRING1),
        )
        self.one = PyTgCalls(
            self.userbot1,
            cache_duration=100,
        )
        
        self.custom_assistants = {} 
        self.active_clients = {} 

    # ✅ Second Code Logic structure
    async def get_active_clients(self, chat_id):
        clients = []
        if chat_id in self.active_clients:
            val = self.active_clients[chat_id]
            if isinstance(val, list):
                clients.extend(val)
            else:
                clients.append(val)
        
        if not clients:
            try:
                main_ass = await group_assistant(self, chat_id)
                clients.append(main_ass)
            except:
                clients.append(self.one)
        
        return list(set(clients))

    async def pause_stream(self, chat_id: int, assistant_type=None):
        assistants = await self.get_active_clients(chat_id)
        for assistant in assistants:
            try:
                await assistant.pause(chat_id)
            except:
                pass

    async def resume_stream(self, chat_id: int, assistant_type=None):
        assistants = await self.get_active_clients(chat_id)
        for assistant in assistants:
            try:
                await assistant.resume(chat_id)
            except:
                pass

    async def stop_stream(self, chat_id: int, assistant_type=None):
        try:
            await _clear_(chat_id)
        except:
            pass
            
        if chat_id in self.active_clients:
            for assistant in self.active_clients[chat_id]:
                try:
                    await assistant.leave_call(chat_id)
                except:
                    pass
            del self.active_clients[chat_id]

        try:
            assistant = await group_assistant(self, chat_id)
            await assistant.leave_call(chat_id)
        except:
            pass
            
        try:
            await self.one.leave_call(chat_id)
        except:
            pass

    async def stop_stream_force(self, chat_id: int):
        try:
            await _clear_(chat_id)
        except:
            pass

        if chat_id in self.active_clients:
            for assistant in self.active_clients[chat_id]:
                try:
                    await assistant.leave_call(chat_id)
                except:
                    pass
            del self.active_clients[chat_id]
            
        try:
            assistant = await group_assistant(self, chat_id)
            await assistant.leave_call(chat_id)
        except:
            pass
            
        try:
            await self.one.leave_call(chat_id)
        except:
            pass

    async def speedup_stream(self, chat_id: int, file_path, speed, playing):
        assistants = await self.get_active_clients(chat_id)
        assistant = assistants[0] if assistants else self.one
        
        if str(speed) != str("1.0"):
            base = os.path.basename(file_path)
            chatdir = os.path.join(os.getcwd(), "playback", str(speed))
            if not os.path.isdir(chatdir):
                os.makedirs(chatdir)
            out = os.path.join(chatdir, base)
            if not os.path.isfile(out):
                if str(speed) == str("0.5"):
                    vs = 2.0
                elif str(speed) == str("0.75"):
                    vs = 1.35
                elif str(speed) == str("1.5"):
                    vs = 0.68
                elif str(speed) == str("2.0"):
                    vs = 0.5
                else:
                    vs = 1.0
                proc = await asyncio.create_subprocess_shell(
                    cmd=(
                        f"ffmpeg -i {file_path} -filter:v setpts={vs}*PTS -filter:a atempo={speed} -c:a libopus -b:a 192k -vbr on -compression_level 10 {out}"
                    ),
                    stdin=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                )
                await proc.communicate()
            else:
                pass
        else:
            out = file_path
        dur = await asyncio.get_event_loop().run_in_executor(None, check_duration, out)
        dur = int(dur)
        played, con_seconds = speed_converter(playing[0]["played"], speed)
        duration = seconds_to_min(dur)
        
        # ✅ First Code Video Logic
        stream = (
            MediaStream(
                out, 
                audio_parameters=AudioQuality.HIGH, 
                video_parameters=VideoQuality.FHD_1080p, 
                ffmpeg_parameters=f"-ss {played} -to {duration}"
            ) if playing[0]["streamtype"] == "video" else 
            MediaStream(
                out, 
                audio_parameters=AudioQuality.HIGH, 
                ffmpeg_parameters=f"-ss {played} -to {duration}", 
                video_flags=MediaStream.Flags.IGNORE
            )
        )
        
        if str(db[chat_id][0]["file"]) == str(file_path):
            for assistant in assistants:
                try:
                    await assistant.play(chat_id, stream)
                except:
                    pass
        else:
            raise AssistantErr("Umm")
        if str(db[chat_id][0]["file"]) == str(file_path):
            exis = (playing[0]).get("old_dur")
            if not exis:
                db[chat_id][0]["old_dur"] = db[chat_id][0]["dur"]
                db[chat_id][0]["old_second"] = db[chat_id][0]["seconds"]
            db[chat_id][0]["played"] = con_seconds
            db[chat_id][0]["dur"] = duration
            db[chat_id][0]["seconds"] = dur
            db[chat_id][0]["speed_path"] = out
            db[chat_id][0]["speed"] = speed

    async def skip_stream(
        self,
        chat_id: int,
        link: str,
        video: Union[bool, str] = None,
        image: Union[bool, str] = None,
        assistant_type=None 
    ):
        assistants = await self.get_active_clients(chat_id)
        if video:
            stream = MediaStream(link, audio_parameters=AudioQuality.HIGH, video_parameters=VideoQuality.FHD_1080p)
        else:
            stream = MediaStream(link, audio_parameters=AudioQuality.HIGH, video_flags=MediaStream.Flags.IGNORE)
            
        for assistant in assistants:
            try:
                await assistant.play(chat_id, stream)
            except Exception as e:
                pass

    async def seek_stream(self, chat_id, file_path, to_seek, duration, mode):
        assistants = await self.get_active_clients(chat_id)
        stream = (
            MediaStream(
                file_path, 
                audio_parameters=AudioQuality.HIGH, 
                video_parameters=VideoQuality.FHD_1080p, 
                ffmpeg_parameters=f"-ss {to_seek} -to {duration}"
            ) if mode == "video" else 
            MediaStream(
                file_path, 
                audio_parameters=AudioQuality.HIGH, 
                video_flags=MediaStream.Flags.IGNORE, 
                ffmpeg_parameters=f"-ss {to_seek} -to {duration}"
            )
        )
        for assistant in assistants:
            try:
                await assistant.play(chat_id, stream)
            except:
                pass

    async def stream_call(self, link):
        assistant = await group_assistant(self, config.LOGGER_ID)
        await assistant.play(config.LOGGER_ID, MediaStream(link, audio_parameters=AudioQuality.HIGH))
        await asyncio.sleep(0.2)
        await assistant.leave_call(config.LOGGER_ID)

    async def join_call(
        self,
        chat_id: int,
        original_chat_id: int,
        link,
        video: Union[bool, str] = None,
        image: Union[bool, str] = None,
        userbot=None,
    ):
        assistant_to_join = None
        
        if userbot:
            # ✅ FIX: Removed FORCE_JOIN_LINKS completely from here to save the session string.
            # ✅ FIX: Prevent Double instance of default bot
            if hasattr(self, "userbot1") and userbot.me.id == self.userbot1.me.id:
                assistant_to_join = self.one
            else:
                user_id = userbot.me.id
                if user_id in self.custom_assistants:
                    assistant_to_join = self.custom_assistants[user_id]
                else:
                    assistant_to_join = PyTgCalls(
                        userbot,
                        cache_duration=100
                    )
                    await assistant_to_join.start()
                    
                    @assistant_to_join.on_update(fl.stream_end())
                    async def stream_end_handler(client: PyTgCalls, update: StreamEnded):
                        await self.change_stream(client, update.chat_id)

                    @assistant_to_join.on_update(fl.chat_update(ChatUpdate.Status.KICKED | ChatUpdate.Status.LEFT_GROUP | ChatUpdate.Status.CLOSED_VOICE_CHAT))
                    async def stream_services_handler(client, update: Update):
                        await self.stop_stream(update.chat_id)
                    
                    self.custom_assistants[user_id] = assistant_to_join

        else:
            assistant_to_join = await group_assistant(self, chat_id)
        
        if chat_id not in self.active_clients:
            self.active_clients[chat_id] = []
        
        if assistant_to_join not in self.active_clients[chat_id]:
            self.active_clients[chat_id].append(assistant_to_join)
        
        language = await get_lang(chat_id)
        _ = get_string(language)
        if video:
            stream = MediaStream(link, audio_parameters=AudioQuality.HIGH, video_parameters=VideoQuality.FHD_1080p)
        else:
            stream = MediaStream(link, audio_parameters=AudioQuality.HIGH, video_flags=MediaStream.Flags.IGNORE)
            
        try:
            await assistant_to_join.play(chat_id, stream)
        except NoActiveGroupCall:
            await asyncio.sleep(0.5)
            try:
                await assistant_to_join.play(chat_id, stream)
            except:
                raise AssistantErr(_["call_8"])
        except TelegramServerError:
            raise AssistantErr(_["call_10"])
        except Exception as e:
            raise AssistantErr(str(e))
            
        await add_active_chat(chat_id)
        await music_on(chat_id)
        if video:
            await add_active_video_chat(chat_id)
        if await is_autoend():
            counter[chat_id] = {}
            try:
                participants = await assistant_to_join.get_participants(chat_id)
                if participants:
                    users = len(participants)
                    if users == 1:
                        autoend[chat_id] = datetime.now() + timedelta(minutes=1)
            except:
                pass

    async def change_stream(self, client, chat_id):
        check = db.get(chat_id)
        popped = None
        loop = await get_loop(chat_id)
        try:
            if loop == 0:
                popped = check.pop(0)
            else:
                loop = loop - 1
                await set_loop(chat_id, loop)
            await auto_clean(popped)
            if not check:
                await self.stop_stream(chat_id)
                return
        except:
            try:
                await self.stop_stream(chat_id)
                return
            except:
                return
        else:
            queued = check[0]["file"]
            language = await get_lang(chat_id)
            _ = get_string(language)
            title = (check[0]["title"]).title()
            user = check[0]["by"]
            original_chat_id = check[0]["chat_id"]
            streamtype = check[0]["streamtype"]
            videoid = check[0]["vidid"]
            
            chat_client = check[0].get("client")
            if not chat_client:
                chat_client = app

            db[chat_id][0]["played"] = 0
            exis = (check[0]).get("old_dur")
            if exis:
                db[chat_id][0]["dur"] = exis
                db[chat_id][0]["seconds"] = check[0]["old_second"]
                db[chat_id][0]["speed_path"] = None
                db[chat_id][0]["speed"] = 1.0
            video = True if str(streamtype) == "video" else False
            if "live_" in queued:
                n, link = await YouTube.video(videoid, True)
                if n == 0:
                    return await chat_client.send_message(original_chat_id, text=_["call_6"])
                if video:
                    stream = MediaStream(link, audio_parameters=AudioQuality.HIGH, video_parameters=VideoQuality.FHD_1080p)
                else:
                    stream = MediaStream(link, audio_parameters=AudioQuality.HIGH, video_flags=MediaStream.Flags.IGNORE)
                try:
                    await client.play(chat_id, stream)
                except Exception:
                    return await chat_client.send_message(original_chat_id, text=_["call_6"])
                button = telegram_markup(_, chat_id)
                img = get_random_img(config.STREAM_IMG_URL)
                run = await chat_client.send_photo(
                    chat_id=original_chat_id,
                    photo=img,
                    caption=_["stream_1"].format(f"https://t.me/{app.username}?start=info_{videoid}", title[:23], check[0]["dur"], user),
                    reply_markup=InlineKeyboardMarkup(button),
                    has_spoiler=True
                )
                db[chat_id][0]["mystic"] = run
                db[chat_id][0]["markup"] = "tg"
            elif "vid_" in queued:
                mystic = await chat_client.send_message(original_chat_id, _["call_7"])
                try:
                    file_path, direct = await YouTube.download(videoid, mystic, videoid=True, video=True if str(streamtype) == "video" else False)
                except:
                    try:
                        file_path, direct = await YouTube.download(videoid, mystic, videoid=True, video=True if str(streamtype) == "video" else False)
                    except:
                        return await mystic.edit_text(_["call_6"], disable_web_page_preview=True)
                if video:
                    stream = MediaStream(file_path, audio_parameters=AudioQuality.HIGH, video_parameters=VideoQuality.FHD_1080p)
                else:
                    stream = MediaStream(file_path, audio_parameters=AudioQuality.HIGH, video_flags=MediaStream.Flags.IGNORE)
                try:
                    await client.play(chat_id, stream)
                except:
                    return await chat_client.send_message(original_chat_id, text=_["call_6"])
                img = await get_thumb(videoid)
                if not img: img = get_random_img(config.PLAYLIST_IMG_URL)
                button = stream_markup(_, chat_id)
                await mystic.delete()
                run = await chat_client.send_photo(
                    chat_id=original_chat_id,
                    photo=img,
                    caption=_["stream_1"].format(f"https://t.me/{app.username}?start=info_{videoid}", title[:23], check[0]["dur"], user),
                    reply_markup=InlineKeyboardMarkup(button),
                    has_spoiler=True
                )
                db[chat_id][0]["mystic"] = run
                db[chat_id][0]["markup"] = "stream"
            elif "index_" in queued:
                stream = (
                    MediaStream(videoid, audio_parameters=AudioQuality.HIGH, video_parameters=VideoQuality.FHD_1080p) if str(streamtype) == "video" 
                    else MediaStream(videoid, audio_parameters=AudioQuality.HIGH, video_flags=MediaStream.Flags.IGNORE)
                )
                try:
                    await client.play(chat_id, stream)
                except:
                    return await chat_client.send_message(original_chat_id, text=_["call_6"])
                button = telegram_markup(_, chat_id)
                run = await chat_client.send_photo(
                    chat_id=original_chat_id,
                    photo=get_random_img(config.STREAM_IMG_URL),
                    caption=_["stream_2"].format(user),
                    reply_markup=InlineKeyboardMarkup(button),
                    has_spoiler=True
                )
                db[chat_id][0]["mystic"] = run
                db[chat_id][0]["markup"] = "tg"
            else:
                if video:
                    stream = MediaStream(queued, audio_parameters=AudioQuality.HIGH, video_parameters=VideoQuality.FHD_1080p)
                else:
                    stream = MediaStream(queued, audio_parameters=AudioQuality.HIGH, video_flags=MediaStream.Flags.IGNORE)
                try:
                    await client.play(chat_id, stream)
                except:
                    return await chat_client.send_message(original_chat_id, text=_["call_6"])
                if videoid == "telegram":
                    button = telegram_markup(_, chat_id)
                    tg_img = get_random_img(config.TELEGRAM_AUDIO_URL) if str(streamtype) == "audio" else get_random_img(config.TELEGRAM_VIDEO_URL)
                    run = await chat_client.send_photo(
                        chat_id=original_chat_id,
                        photo=tg_img,
                        caption=_["stream_1"].format(config.SUPPORT_CHAT, title[:23], check[0]["dur"], user),
                        reply_markup=InlineKeyboardMarkup(button),
                        has_spoiler=True
                    )
                    db[chat_id][0]["mystic"] = run
                    db[chat_id][0]["markup"] = "tg"
                elif videoid == "soundcloud":
                    button = telegram_markup(_, chat_id)
                    run = await chat_client.send_photo(
                        chat_id=original_chat_id,
                        photo=get_random_img(config.SOUNCLOUD_IMG_URL),
                        caption=_["stream_1"].format(config.SUPPORT_CHAT, title[:23], check[0]["dur"], user),
                        reply_markup=InlineKeyboardMarkup(button),
                        has_spoiler=True
                    )
                    db[chat_id][0]["mystic"] = run
                    db[chat_id][0]["markup"] = "tg"
                else:
                    img = await get_thumb(videoid)
                    if not img: img = get_random_img(config.PLAYLIST_IMG_URL)
                    button = stream_markup(_, chat_id)
                    run = await chat_client.send_photo(
                        chat_id=original_chat_id,
                        photo=img,
                        caption=_["stream_1"].format(f"https://t.me/{app.username}?start=info_{videoid}", title[:23], check[0]["dur"], user),
                        reply_markup=InlineKeyboardMarkup(button),
                        has_spoiler=True
                    )
                    db[chat_id][0]["mystic"] = run
                    db[chat_id][0]["markup"] = "stream"

    async def ping(self):
        pings = []
        if config.STRING1:
            pings.append(self.one.ping)
        return str(round(sum(pings) / len(pings), 3)) if pings else "0"

    async def start(self):
        LOGGER(__name__).info("Starting PyTgCalls Client...\n")
        if config.STRING1:
            await self.one.start()

    async def decorators(self):
        @self.one.on_update(fl.chat_update(ChatUpdate.Status.KICKED | ChatUpdate.Status.LEFT_GROUP | ChatUpdate.Status.CLOSED_VOICE_CHAT))
        async def stream_services_handler(client, update: Update):
            await self.stop_stream(update.chat_id)

        @self.one.on_update(fl.stream_end())
        async def stream_end_handler1(client: PyTgCalls, update: StreamEnded):
            await self.change_stream(client, update.chat_id)

Lucky = Call()
