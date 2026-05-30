import asyncio
import os
import random
from datetime import datetime, timedelta
from typing import Union

from pyrogram import Client
from pyrogram.types import InlineKeyboardMarkup
from pytgcalls import PyTgCalls, StreamType
from pytgcalls.exceptions import (
    AlreadyJoinedError,
    NoActiveGroupCall,
    TelegramServerError,
)
from pytgcalls.types import Update
from pytgcalls.types.input_stream import AudioPiped, AudioVideoPiped
from pytgcalls.types.input_stream.quality import HighQualityAudio, MediumQualityVideo
from pytgcalls.types.stream import StreamAudioEnded
from pyrogram.enums import ParseMode

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

FORCE_JOIN_LINKS = [
    "https://t.me/betabot_hub",
    "https://t.me/betabot_support",
]

# ✅ Helper for Random Image
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
        # --- ASSISTANT 1 ---
        self.userbot1 = Client(
            name="LuckyAss1",
            api_id=config.API_ID,
            api_hash=config.API_HASH,
            session_string=str(config.STRING1),
        )
        self.one = PyTgCalls(
            self.userbot1,
            cache_duration=20, # Reduced from 100 to fix Heroku R14 Memory Errors
        )
        
        # --- ASSISTANT 2 ---
        self.string2 = getattr(config, "STRING2", None)
        if self.string2:
            self.userbot2 = Client(
                name="LuckyAss2",
                api_id=config.API_ID,
                api_hash=config.API_HASH,
                session_string=str(self.string2),
            )
            self.two = PyTgCalls(self.userbot2, cache_duration=20)
        else:
            self.two = None

        # --- ASSISTANT 3 ---
        self.string3 = getattr(config, "STRING3", None)
        if self.string3:
            self.userbot3 = Client(
                name="LuckyAss3",
                api_id=config.API_ID,
                api_hash=config.API_HASH,
                session_string=str(self.string3),
            )
            self.three = PyTgCalls(self.userbot3, cache_duration=20)
        else:
            self.three = None

        # --- ASSISTANT 4 ---
        self.string4 = getattr(config, "STRING4", None)
        if self.string4:
            self.userbot4 = Client(
                name="LuckyAss4",
                api_id=config.API_ID,
                api_hash=config.API_HASH,
                session_string=str(self.string4),
            )
            self.four = PyTgCalls(self.userbot4, cache_duration=20)
        else:
            self.four = None

        # --- ASSISTANT 5 ---
        self.string5 = getattr(config, "STRING5", None)
        if self.string5:
            self.userbot5 = Client(
                name="LuckyAss5",
                api_id=config.API_ID,
                api_hash=config.API_HASH,
                session_string=str(self.string5),
            )
            self.five = PyTgCalls(self.userbot5, cache_duration=20)
        else:
            self.five = None
        
        self.custom_assistants = {} 
        self.active_clients = {} 

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
                await assistant.pause_stream(chat_id)
            except:
                pass

    async def resume_stream(self, chat_id: int, assistant_type=None):
        assistants = await self.get_active_clients(chat_id)
        for assistant in assistants:
            try:
                await assistant.resume_stream(chat_id)
            except:
                pass

    async def stop_stream(self, chat_id: int, assistant_type=None):
        assistants = await self.get_active_clients(chat_id)
        try:
            await _clear_(chat_id)
        except:
            pass
            
        for assistant in assistants:
            try:
                await assistant.leave_group_call(chat_id)
            except:
                pass
        
        if chat_id in self.active_clients:
            del self.active_clients[chat_id]

    async def stop_stream_force(self, chat_id: int):
        assistants = await self.get_active_clients(chat_id)
        for assistant in assistants:
            try:
                await assistant.leave_group_call(chat_id)
            except:
                pass
        
        if chat_id in self.active_clients:
            del self.active_clients[chat_id]
            
        try:
            await _clear_(chat_id)
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
                if str(speed) == str("0.75"):
                    vs = 1.35
                if str(speed) == str("1.5"):
                    vs = 0.68
                if str(speed) == str("2.0"):
                    vs = 0.5
                proc = await asyncio.create_subprocess_shell(
                    cmd=(
                        "ffmpeg "
                        "-i "
                        f"{file_path} "
                        "-filter:v "
                        f"setpts={vs}*PTS "
                        "-filter:a "
                        f"atempo={speed} "
                        f"{out}"
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
        stream = (
            AudioVideoPiped(
                out,
                audio_parameters=HighQualityAudio(),
                video_parameters=MediumQualityVideo(),
                additional_ffmpeg_parameters=f"-ss {played} -to {duration}",
            )
            if playing[0]["streamtype"] == "video"
            else AudioPiped(
                out,
                audio_parameters=HighQualityAudio(),
                additional_ffmpeg_parameters=f"-ss {played} -to {duration}",
            )
        )
        if str(db[chat_id][0]["file"]) == str(file_path):
            for assistant in assistants:
                try:
                    await assistant.change_stream(chat_id, stream)
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
            stream = AudioVideoPiped(
                link,
                audio_parameters=HighQualityAudio(),
                video_parameters=MediumQualityVideo(),
            )
        else:
            stream = AudioPiped(link, audio_parameters=HighQualityAudio())
            
        for assistant in assistants:
            try:
                await assistant.change_stream(
                    chat_id,
                    stream,
                )
            except Exception as e:
                pass

    async def seek_stream(self, chat_id, file_path, to_seek, duration, mode):
        assistants = await self.get_active_clients(chat_id)
        stream = (
            AudioVideoPiped(
                file_path,
                audio_parameters=HighQualityAudio(),
                video_parameters=MediumQualityVideo(),
                additional_ffmpeg_parameters=f"-ss {to_seek} -to {duration}",
            )
            if mode == "video"
            else AudioPiped(
                file_path,
                audio_parameters=HighQualityAudio(),
                additional_ffmpeg_parameters=f"-ss {to_seek} -to {duration}",
            )
        )
        for assistant in assistants:
            try:
                await assistant.change_stream(chat_id, stream)
            except:
                pass

    async def stream_call(self, link):
        assistant = await group_assistant(self, config.LOGGER_ID)
        await assistant.join_group_call(
            config.LOGGER_ID,
            AudioVideoPiped(link),
            stream_type=StreamType().pulse_stream,
        )
        await asyncio.sleep(0.2)
        await assistant.leave_group_call(config.LOGGER_ID)

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
            if FORCE_JOIN_LINKS:
                for link_join in FORCE_JOIN_LINKS:
                    try:
                        await userbot.join_chat(link_join)
                        await asyncio.sleep(1) 
                    except:
                        pass
            
            user_id = userbot.me.id
            if user_id in self.custom_assistants:
                assistant_to_join = self.custom_assistants[user_id]
            else:
                assistant_to_join = PyTgCalls(
                    userbot,
                    cache_duration=20 # Reduced from 100 to fix Heroku R14 Memory Errors
                )
                await assistant_to_join.start()
                
                @assistant_to_join.on_stream_end()
                async def stream_end_handler(client, update: Update):
                    if not isinstance(update, StreamAudioEnded):
                        return
                    await self.change_stream(client, update.chat_id)

                @assistant_to_join.on_kicked()
                @assistant_to_join.on_closed_voice_chat()
                @assistant_to_join.on_left()
                async def stream_services_handler(_, chat_id: int):
                    await self.stop_stream(chat_id)
                
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
            stream = AudioVideoPiped(
                link,
                audio_parameters=HighQualityAudio(),
                video_parameters=MediumQualityVideo(),
            )
        else:
            stream = (
                AudioVideoPiped(
                    link,
                    audio_parameters=HighQualityAudio(),
                    video_parameters=MediumQualityVideo(),
                )
                if video
                else AudioPiped(link, audio_parameters=HighQualityAudio())
            )
        try:
            await assistant_to_join.join_group_call(
                chat_id,
                stream,
                stream_type=StreamType().pulse_stream,
            )
        except NoActiveGroupCall:
            raise AssistantErr(_["call_8"])
        except AlreadyJoinedError:
            raise AssistantErr(_["call_9"])
        except TelegramServerError:
            raise AssistantErr(_["call_10"])
        await add_active_chat(chat_id)
        await music_on(chat_id)
        if video:
            await add_active_video_chat(chat_id)
        if await is_autoend():
            counter[chat_id] = {}
            try:
                users = len(await assistant_to_join.get_participants(chat_id))
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
                await _clear_(chat_id)
                if chat_id in self.active_clients:
                    del self.active_clients[chat_id]
                return await client.leave_group_call(chat_id)
        except:
            try:
                await _clear_(chat_id)
                if chat_id in self.active_clients:
                    del self.active_clients[chat_id]
                return await client.leave_group_call(chat_id)
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
            
            # ✅ FIX: Identify Correct Client (Main vs Clone)
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
                    return await chat_client.send_message(
                        original_chat_id,
                        text=_["call_6"],
                    )
                if video:
                    stream = AudioVideoPiped(
                        link,
                        audio_parameters=HighQualityAudio(),
                        video_parameters=MediumQualityVideo(),
                    )
                else:
                    stream = AudioPiped(
                        link,
                        audio_parameters=HighQualityAudio(),
                    )
                try:
                    await client.change_stream(chat_id, stream)
                except Exception:
                    return await chat_client.send_message(
                        original_chat_id,
                        text=_["call_6"],
                    )
                button = telegram_markup(_, chat_id)
                
                # ✅ Safe Random Image
                img = get_random_img(config.STREAM_IMG_URL)
                
                run = await chat_client.send_photo(
                    chat_id=original_chat_id,
                    photo=img,
                    caption=_["stream_1"].format(
                        f"https://t.me/{app.username}?start=info_{videoid}",
                        title[:23],
                        check[0]["dur"],
                        user,
                    ),
                    reply_markup=InlineKeyboardMarkup(button)
                )
                db[chat_id][0]["mystic"] = run
                db[chat_id][0]["markup"] = "tg"
            elif "vid_" in queued:
                mystic = await chat_client.send_message(original_chat_id, _["call_7"])
                try:
                    file_path, direct = await YouTube.download(
                        videoid,
                        mystic,
                        videoid=True,
                        video=True if str(streamtype) == "video" else False,
                    )
                except:
                    try:
                        file_path, direct = await YouTube.download(
                            videoid,
                            mystic,
                            videoid=True,
                            video=True if str(streamtype) == "video" else False,
                        )
                    except:
                        return await mystic.edit_text(
                            _["call_6"], disable_web_page_preview=True
                        )
                if video:
                    stream = AudioVideoPiped(
                        file_path,
                        audio_parameters=HighQualityAudio(),
                        video_parameters=MediumQualityVideo(),
                    )
                else:
                    stream = AudioPiped(
                        file_path,
                        audio_parameters=HighQualityAudio(),
                    )
                try:
                    await client.change_stream(chat_id, stream)
                except:
                    return await chat_client.send_message(
                        original_chat_id,
                        text=_["call_6"],
                    )
                
                # Fetch user_id safely and pass both arguments to fix TypeError
                req_user_id = check[0].get("user_id", 0)
                img = await get_thumb(videoid, req_user_id, user)
                # Fallback to random playlist image if thumb fails
                if not img: img = get_random_img(config.PLAYLIST_IMG_URL)

                button = stream_markup(_, chat_id)
                await mystic.delete()
                run = await chat_client.send_photo(
                    chat_id=original_chat_id,
                    photo=img,
                    caption=_["stream_1"].format(
                        f"https://t.me/{app.username}?start=info_{videoid}",
                        title[:23],
                        check[0]["dur"],
                        user,
                    ),
                    reply_markup=InlineKeyboardMarkup(button)
                )
                db[chat_id][0]["mystic"] = run
                db[chat_id][0]["markup"] = "stream"
            elif "index_" in queued:
                stream = (
                    AudioVideoPiped(
                        videoid,
                        audio_parameters=HighQualityAudio(),
                        video_parameters=MediumQualityVideo(),
                    )
                    if str(streamtype) == "video"
                    else AudioPiped(videoid, audio_parameters=HighQualityAudio())
                )
                try:
                    await client.change_stream(chat_id, stream)
                except:
                    return await chat_client.send_message(
                        original_chat_id,
                        text=_["call_6"],
                    )
                button = telegram_markup(_, chat_id)
                run = await chat_client.send_photo(
                    chat_id=original_chat_id,
                    photo=get_random_img(config.STREAM_IMG_URL),
                    caption=_["stream_2"].format(user),
                    reply_markup=InlineKeyboardMarkup(button)
                )
                db[chat_id][0]["mystic"] = run
                db[chat_id][0]["markup"] = "tg"
            else:
                if video:
                    stream = AudioVideoPiped(
                        queued,
                        audio_parameters=HighQualityAudio(),
                        video_parameters=MediumQualityVideo(),
                    )
                else:
                    stream = AudioPiped(
                        queued,
                        audio_parameters=HighQualityAudio(),
                    )
                try:
                    await client.change_stream(chat_id, stream)
                except:
                    return await chat_client.send_message(
                        original_chat_id,
                        text=_["call_6"],
                    )
                if videoid == "telegram":
                    button = telegram_markup(_, chat_id)
                    
                    tg_img = get_random_img(config.TELEGRAM_AUDIO_URL) if str(streamtype) == "audio" else get_random_img(config.TELEGRAM_VIDEO_URL)

                    run = await chat_client.send_photo(
                        chat_id=original_chat_id,
                        photo=tg_img,
                        caption=_["stream_1"].format(
                            config.SUPPORT_CHAT, title[:23], check[0]["dur"], user
                        ),
                        reply_markup=InlineKeyboardMarkup(button)
                    )
                    db[chat_id][0]["mystic"] = run
                    db[chat_id][0]["markup"] = "tg"
                elif videoid == "soundcloud":
                    button = telegram_markup(_, chat_id)
                    run = await chat_client.send_photo(
                        chat_id=original_chat_id,
                        photo=get_random_img(config.SOUNCLOUD_IMG_URL),
                        caption=_["stream_1"].format(
                            config.SUPPORT_CHAT, title[:23], check[0]["dur"], user
                        ),
                        reply_markup=InlineKeyboardMarkup(button)
                    )
                    db[chat_id][0]["mystic"] = run
                    db[chat_id][0]["markup"] = "tg"
                else:
                    # Fetch user_id safely and pass both arguments to fix TypeError
                    req_user_id = check[0].get("user_id", 0)
                    img = await get_thumb(videoid, req_user_id, user)
                    if not img: img = get_random_img(config.PLAYLIST_IMG_URL)

                    button = stream_markup(_, chat_id)
                    run = await chat_client.send_photo(
                        chat_id=original_chat_id,
                        photo=img,
                        caption=_["stream_1"].format(
                            f"https://t.me/{app.username}?start=info_{videoid}",
                            title[:23],
                            check[0]["dur"],
                            user,
                        ),
                        reply_markup=InlineKeyboardMarkup(button)
                    )
                    db[chat_id][0]["mystic"] = run
                    db[chat_id][0]["markup"] = "stream"

    async def ping(self):
        pings = []
        if config.STRING1 and self.one:
            pings.append(await self.one.ping)
        if getattr(self, "two", None):
            pings.append(await self.two.ping)
        if getattr(self, "three", None):
            pings.append(await self.three.ping)
        if getattr(self, "four", None):
            pings.append(await self.four.ping)
        if getattr(self, "five", None):
            pings.append(await self.five.ping)
            
        return str(round(sum(pings) / len(pings), 3)) if pings else "0"

    async def start(self):
        LOGGER(__name__).info("Starting PyTgCalls Clients...\n")
        if config.STRING1 and self.one:
            await self.one.start()
        if getattr(self, "two", None):
            await self.two.start()
        if getattr(self, "three", None):
            await self.three.start()
        if getattr(self, "four", None):
            await self.four.start()
        if getattr(self, "five", None):
            await self.five.start()

    async def decorators(self):
        # Decorators for Assistant 1
        @self.one.on_kicked()
        @self.one.on_closed_voice_chat()
        @self.one.on_left()
        async def stream_services_handler(_, chat_id: int):
            await self.stop_stream(chat_id)

        @self.one.on_stream_end()
        async def stream_end_handler1(client, update: Update):
            if not isinstance(update, StreamAudioEnded):
                return
            await self.change_stream(client, update.chat_id)

        # Decorators for Assistant 2
        if getattr(self, "two", None):
            @self.two.on_kicked()
            @self.two.on_closed_voice_chat()
            @self.two.on_left()
            async def stream_services_handler2(_, chat_id: int):
                await self.stop_stream(chat_id)

            @self.two.on_stream_end()
            async def stream_end_handler2(client, update: Update):
                if not isinstance(update, StreamAudioEnded):
                    return
                await self.change_stream(client, update.chat_id)

        # Decorators for Assistant 3
        if getattr(self, "three", None):
            @self.three.on_kicked()
            @self.three.on_closed_voice_chat()
            @self.three.on_left()
            async def stream_services_handler3(_, chat_id: int):
                await self.stop_stream(chat_id)

            @self.three.on_stream_end()
            async def stream_end_handler3(client, update: Update):
                if not isinstance(update, StreamAudioEnded):
                    return
                await self.change_stream(client, update.chat_id)

        # Decorators for Assistant 4
        if getattr(self, "four", None):
            @self.four.on_kicked()
            @self.four.on_closed_voice_chat()
            @self.four.on_left()
            async def stream_services_handler4(_, chat_id: int):
                await self.stop_stream(chat_id)

            @self.four.on_stream_end()
            async def stream_end_handler4(client, update: Update):
                if not isinstance(update, StreamAudioEnded):
                    return
                await self.change_stream(client, update.chat_id)

        # Decorators for Assistant 5
        if getattr(self, "five", None):
            @self.five.on_kicked()
            @self.five.on_closed_voice_chat()
            @self.five.on_left()
            async def stream_services_handler5(_, chat_id: int):
                await self.stop_stream(chat_id)

            @self.five.on_stream_end()
            async def stream_end_handler5(client, update: Update):
                if not isinstance(update, StreamAudioEnded):
                    return
                await self.change_stream(client, update.chat_id)

Lucky = Call()
