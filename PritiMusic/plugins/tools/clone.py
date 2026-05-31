import logging
import asyncio
import random
from datetime import datetime
from pyrogram import Client, filters
import pyrogram.errors
from PritiMusic import app
from PritiMusic.utils.database import get_assistant, clonebotdb
from PritiMusic.utils.database.clonedb import has_user_cloned_any_bot
from PritiMusic.utils.decorators.language import language
from PritiMusic.misc import SUDOERS
from config import API_ID, API_HASH, OWNER_ID, SUPPORT_CHANNEL, START_IMG_URL

# --- GLOBAL VARIABLES ---
CLONES = set()
ACTIVE_CLONES = {}
CLONE_LIMIT = 500
FOOTER = (
    "\n\n━━━━━━━━━━━━━━━━━━\n"
    "✨ **Start customizing your bot now!**\n"
    "📢 Join: @betabot_hub"
)

# --- HELPER FUNCTIONS ---
def get_random_start_img():
    return random.choice(START_IMG_URL) if isinstance(START_IMG_URL, list) else START_IMG_URL or "https://telegra.ph/file/2e3d368e77c449c287430.jpg"

# --- CLONE COMMAND ---
@app.on_message(filters.command("clone"))
@language
async def clone_txt(client, message, _):
    # Limit Check
    count = await clonebotdb.count_documents({})
    if count >= CLONE_LIMIT and message.from_user.id != OWNER_ID:
        return await message.reply_photo(photo=get_random_start_img(), caption="**⚠️ ᴄʟᴏɴᴇ ʟɪᴍɪᴛ ʀᴇᴀᴄʜᴇᴅ**" + FOOTER)

    # Already Cloned Check
    if await has_user_cloned_any_bot(message.from_user.id) and message.from_user.id != OWNER_ID:
        return await message.reply_text(_["C_B_H_0"])
    
    if len(message.command) < 2:
        return await message.reply_text("Usage: /clone <BOT_TOKEN>")

    bot_token = message.text.split(None, 1)[1].strip()
    mi = await message.reply_text("🔄 **Initializing...**")
        
    try:
        # Start Clone Client
        ai = Client(f"Clone_{bot_token[:10]}", API_ID, API_HASH, bot_token=bot_token, in_memory=True)
        await ai.start()
        bot = await ai.get_me()
        
        # Assistant session export
        userbot = await get_assistant(message.chat.id)
        session_string = await userbot.export_session_string() 

        # Unblock Logic (Fix for YouBlockedUser)
        try:
            await userbot.send_message(bot.username, "/start")
        except pyrogram.errors.exceptions.bad_request_400.YouBlockedUser:
            await userbot.unblock_user(bot.username)
            await asyncio.sleep(1)
            await userbot.send_message(bot.username, "/start")

        # Database Sync
        await clonebotdb.insert_one({
            "bot_id": bot.id, 
            "name": bot.first_name, 
            "token": bot_token, 
            "username": bot.username, 
            "user_id": message.from_user.id,
            "session_string": session_string, 
            "Date": datetime.now().strftime("%d-%m-%Y")
        })
        
        ACTIVE_CLONES[bot.id] = ai
        CLONES.add(bot.id)
        
        await mi.edit_text(f"✅ **Clone Successful:** @{bot.username}" + FOOTER)
    except Exception as e:
        logging.exception("Error in clone_txt")
        await mi.edit_text(f"⚠️ **Error:** `{e}`")

# --- RESTART BOTS (CRITICAL) ---
async def restart_bots():
    """यह फंक्शन बॉट स्टार्ट होते ही सभी क्लोन बॉट्स को फिर से लोड करता है."""
    async for bot_data in clonebotdb.find():
        token = bot_data.get("token")
        bot_id = bot_data.get("bot_id")
        session_string = bot_data.get("session_string")
        
        try:
            ai = Client(f"Clone_{token[:10]}", API_ID, API_HASH, bot_token=token, in_memory=True)
            await ai.start()
            
            # Re-attach Assistant if exists
            if session_string:
                try:
                    ass = Client(f"Ass_{bot_id}", API_ID, API_HASH, session_string=session_string, in_memory=True)
                    await ass.start()
                    ai.assistant = ass
                except: pass
            
            ACTIVE_CLONES[bot_id] = ai
            CLONES.add(bot_id)
            logging.info(f"✅ Restarted Clone: {bot_id}")
        except Exception as e:
            logging.error(f"Failed to restart clone {bot_id}: {e}")

# --- DELETE CLONE ---
@app.on_message(filters.command(["delclone", "removeclone"]) & SUDOERS)
async def delete_cloned_bot(client, message):
    query = " ".join(message.command[1:]).replace("@", "")
    cloned_bot = await clonebotdb.find_one({"$or": [{"token": query}, {"username": query}]})
    if cloned_bot:
        if cloned_bot["bot_id"] in ACTIVE_CLONES:
            try:
                await ACTIVE_CLONES[cloned_bot["bot_id"]].stop()
                del ACTIVE_CLONES[cloned_bot["bot_id"]]
            except: pass
        await clonebotdb.delete_one({"_id": cloned_bot["_id"]})
        await message.reply_text("🗑️ **Bot Removed Successfully.**" + FOOTER)
    else:
        await message.reply_text("❌ **Bot not found.**")
