import os
import random
import logging
from typing import Union
from pyrogram.types import InlineKeyboardMarkup
import config
from PritiMusic import Carbon, YouTube, app
from PritiMusic.core.call import Lucky
from PritiMusic.misc import db
from PritiMusic.utils.database import is_active_chat
from PritiMusic.utils.exceptions import AssistantErr
from PritiMusic.utils.inline import aq_markup, close_markup, stream_markup
from PritiMusic.utils.stream.queue import put_queue
from PritiMusic.utils.pastebin import LuckyBin
from PritiMusic.utils.thumbnails import get_thumb 

# Helper to safely get Random Image
def get_random_img(img_list):
    if img_list:
        return random.choice(img_list) if isinstance(img_list, list) else img_list
    return "https://telegra.ph/file/2e3d368e77c449c287430.jpg"

# Helper to safely update the queue
def safe_update_mystic(chat_id, run_msg, markup_type):
    if chat_id in db and isinstance(db[chat_id], list) and len(db[chat_id]) > 0:
        db[chat_id][0]["mystic"] = run_msg
        db[chat_id][0]["markup"] = markup_type
    else:
        logging.warning(f"Queue empty for {chat_id}, skipping mystic update.")

async def stream(_, mystic, user_id, result, chat_id, user_name, original_chat_id, video=None, streamtype=None, spotify=None, forceplay=None):
    if not result: return
    if forceplay: await Lucky.force_stop_stream(chat_id)

    if streamtype == "playlist":
        msg = f"{_['play_19']}\n\n"
        count = 0
        for search in result:
            if count == config.PLAYLIST_FETCH_LIMIT: continue
            try:
                title, duration_min, duration_sec, thumbnail, vidid = await YouTube.details(search, not spotify)
            except: continue
            if str(duration_min) == "None" or duration_sec > config.DURATION_LIMIT: continue
            
            if await is_active_chat(chat_id):
                await put_queue(chat_id, original_chat_id, f"vid_{vidid}", title, duration_min, user_name, vidid, user_id, "video" if video else "audio")
                count += 1
                msg += f"{count}. {title[:70]}\n\n"
            else:
                if not forceplay: db[chat_id] = []
                file_path, direct = await YouTube.download(vidid, mystic, video=video, videoid=True)
                await Lucky.join_call(chat_id, original_chat_id, file_path, video=video, image=thumbnail)
                await put_queue(chat_id, original_chat_id, file_path if direct else f"vid_{vidid}", title, duration_min, user_name, vidid, user_id, "video" if video else "audio", forceplay=forceplay)
                
                img = await get_thumb(vidid, user_id, app) or get_random_img(config.PLAYLIST_IMG_URL)
                run = await app.send_photo(original_chat_id, photo=img, caption=_["stream_1"].format(f"https://t.me/{app.username}?start=info_{vidid}", title[:23], duration_min, user_name), reply_markup=InlineKeyboardMarkup(stream_markup(_, chat_id)))
                safe_update_mystic(chat_id, run, "stream")
        
        if count == 0: return
        link = await LuckyBin(msg)
        return await app.send_photo(original_chat_id, photo=await Carbon.generate(msg[:500], random.randint(100, 10000000)), caption=_["play_21"].format(len(db.get(chat_id))-1, link), reply_markup=close_markup(_))

    elif streamtype in ["youtube", "live"]:
        vidid = result["vidid"]
        title = result["title"].title()
        thumbnail = result["thumb"]
        status = True if video else None
        
        if await is_active_chat(chat_id):
            await put_queue(chat_id, original_chat_id, f"vid_{vidid}" if streamtype == "youtube" else f"live_{vidid}", title, result["duration_min"], user_name, vidid, user_id, "video" if video else "audio")
            await app.send_message(chat_id=original_chat_id, text=_["queue_4"].format(len(db.get(chat_id))-1, title[:27], result["duration_min"], user_name), reply_markup=InlineKeyboardMarkup(aq_markup(_, chat_id)))
        else:
            if not forceplay: db[chat_id] = []
            file_path = (await YouTube.video(result["link"]))[1] if streamtype == "live" else (await YouTube.download(vidid, mystic, videoid=True, video=status))[0]
            await Lucky.join_call(chat_id, original_chat_id, file_path, video=status, image=thumbnail)
            await put_queue(chat_id, original_chat_id, f"vid_{vidid}" if streamtype == "youtube" else f"live_{vidid}", title, result["duration_min"], user_name, vidid, user_id, "video" if video else "audio", forceplay=forceplay)
            
            img = await get_thumb(vidid, user_id, app) or get_random_img(config.PLAYLIST_IMG_URL)
            run = await app.send_photo(original_chat_id, photo=img, caption=_["stream_1"].format(f"https://t.me/{app.username}?start=info_{vidid}", title[:23], result["duration_min"], user_name), reply_markup=InlineKeyboardMarkup(stream_markup(_, chat_id)))
            safe_update_mystic(chat_id, run, "stream" if streamtype == "youtube" else "tg")
