import re
import logging
import asyncio
import requests
from datetime import datetime, timedelta
from pyrogram import Client, filters
import pyrogram.errors
from pyrogram.errors import (AccessTokenExpired, AccessTokenInvalid, FloodWait)
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from PritiMusic import app
from PritiMusic.utils.database import get_assistant, clonebotdb
from PritiMusic.utils.database.clonedb import has_user_cloned_any_bot, get_owner_id_from_db
from PritiMusic.utils.decorators.language import language
from PritiMusic.misc import SUDOERS
from config import API_ID, API_HASH, OWNER_ID, OWNER_USERNAME, CLONE_LOGGER, SUPPORT_CHAT, SUPPORT_CHANNEL, START_IMG_URL

# Branding Footer
FOOTER = (
    "\n\n━━━━━━━━━━━━━━━━━━\n"
    "✨ **Start customizing your bot now!**\n"
    "📢 Join: @betabot_hub\n"
    "💬 Support: @betabot_support"
)

CLONES = set()
ACTIVE_CLONES = {}
CLONE_LIMIT = 500
BOT_LINK = "https://t.me/clone_MUSICrobot"

C_BOT_COMMANDS = [
    {"command": "/start", "description": "sᴛᴀʀᴛs ᴛʜᴇ ᴍᴜsɪᴄ ʙᴏᴛ"},
    {"command": "/play", "description": "sᴛᴀʀᴛs sᴛʀᴇᴀᴍɪɴɢ"},
    {"command": "/ping", "description": "sʏsᴛᴇᴍ sᴛᴀᴛs"}
]

def get_random_start_img():
    return random.choice(START_IMG_URL) if isinstance(START_IMG_URL, list) else START_IMG_URL or "https://telegra.ph/file/2e3d368e77c449c287430.jpg"

@app.on_message(filters.command("clone"))
@language
async def clone_txt(client, message, _):
    count = await clonebotdb.count_documents({})
    if count >= CLONE_LIMIT and message.from_user.id != OWNER_ID:
        return await message.reply_photo(photo=get_random_start_img(), caption="**⚠️ ᴄʟᴏɴᴇ ʟɪᴍɪᴛ ʀᴇᴀᴄʜᴇᴅ**" + FOOTER)

    userbot = await get_assistant(message.chat.id)
    if await has_user_cloned_any_bot(message.from_user.id) and message.from_user.id != OWNER_ID:
        return await message.reply_text(_["C_B_H_0"])
    
    if len(message.command) < 2:
        return await message.reply_text("Usage: /clone <BOT_TOKEN>")

    bot_token = message.text.split(None, 1)[1].strip()
    mi = await message.reply_text("🔄 **Initializing...**")
        
    try:
        ai = Client(bot_token, API_ID, API_HASH, bot_token=bot_token, in_memory=True)
        await ai.start()
        bot = await ai.get_me()
        
        # Unblock Logic
        try:
            await userbot.send_message(bot.username, "/start")
        except pyrogram.errors.exceptions.bad_request_400.YouBlockedUser:
            await userbot.unblock_user(bot.username)
            await asyncio.sleep(1)
            await userbot.send_message(bot.username, "/start")

        # Database Sync
        await clonebotdb.insert_one({
            "bot_id": bot.id, "name": bot.first_name, "token": bot_token, 
            "username": bot.username, "user_id": message.from_user.id,
            "Date": datetime.now().strftime("%d-%m-%Y")
        })
        
        ACTIVE_CLONES[bot.id] = ai
        CLONES.add(bot.id)
        
        await mi.edit_text(f"✅ **Clone Successful:** @{bot.username}" + FOOTER)
    except Exception as e:
        await mi.edit_text(f"⚠️ **Error:** `{e}`" + FOOTER)

# 

@app.on_message(filters.command(["delclone", "removeclone"]) & SUDOERS)
async def delete_cloned_bot(client, message):
    query = " ".join(message.command[1:]).replace("@", "")
    cloned_bot = await clonebotdb.find_one({"$or": [{"token": query}, {"username": query}]})
    
    if cloned_bot:
        if cloned_bot["bot_id"] in ACTIVE_CLONES:
            await ACTIVE_CLONES[cloned_bot["bot_id"]].stop()
            del ACTIVE_CLONES[cloned_bot["bot_id"]]
            
        await clonebotdb.delete_one({"_id": cloned_bot["_id"]})
        await message.reply_text("🗑️ **Bot Removed Successfully.**" + FOOTER)
    else:
        await message.reply_text("❌ **Bot not found in database.**")

# Helper to maintain active instances
async def restart_bots():
    async for bot_data in clonebotdb.find():
        try:
            ai = Client(bot_data["token"], API_ID, API_HASH, bot_token=bot_data["token"], in_memory=True)
            await ai.start()
            ACTIVE_CLONES[bot_data["bot_id"]] = ai
        except: continue
