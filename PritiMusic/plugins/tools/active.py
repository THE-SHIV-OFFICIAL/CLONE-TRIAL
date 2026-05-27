"""
Active Chats Plugin for PritiMusic
🤞 𝐏ᴏᴡєʀєᴅ 𝐁ʏ ➛ BETA BOTS.🙂❤️
"""

from pyrogram import filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from unidecode import unidecode

from PritiMusic import app
from PritiMusic.misc import SUDOERS
from PritiMusic.utils.database import (
    get_active_chats,
    get_active_video_chats,
)
from PritiMusic.utils.database.clonedb import get_served_chats_clone, clonebotdb

POWERED_BY = "🤞 **𝐏ᴏᴡєʀєᴅ 𝐁ʏ ➛ BETA BOTS.🙂❤️**"

# --- HELPER ---
async def get_chat_link(chat_id: int) -> str:
    try:
        chat = await app.get_chat(chat_id)
        if chat.username:
            return f"https://t.me/{chat.username}"
        return f"https://t.me/c/{str(chat_id)[4:]}/1"
    except:
        return f"https://t.me/c/{str(chat_id)[4:]}/1"

# --- MAIN BOT COMMANDS ---

@app.on_message(filters.command(["activevc", "vc", "activevoice"]) & SUDOERS)
async def active_voice_chats(_, message: Message):
    mystic = await message.reply_text("🔄 **Fetching active voice chats...**")
    served_chats = await get_active_chats()
    if not served_chats:
        return await mystic.edit_text(f"📭 **No active voice chats.**\n\n{POWERED_BY}")
    
    text, j = "🎤 **Active Voice Chats:**\n\n", 0
    for chat_id in served_chats:
        try:
            chat = await app.get_chat(chat_id)
            link = await get_chat_link(chat_id)
            text += f"**{j + 1}.** [{unidecode(chat.title)[:25]}]({link}) `[{chat_id}]`\n"
            j += 1
        except: continue
    await mystic.edit_text(f"{text}\n{POWERED_BY}", disable_web_page_preview=True)

@app.on_message(filters.command(["activevideo", "av", "activev"]) & SUDOERS)
async def active_video_chats(_, message: Message):
    mystic = await message.reply_text("🔄 **Fetching active video chats...**")
    served_chats = await get_active_video_chats()
    if not served_chats:
        return await mystic.edit_text(f"📭 **No active video chats.**\n\n{POWERED_BY}")
    
    text, j = "📹 **Active Video Chats:**\n\n", 0
    for chat_id in served_chats:
        try:
            chat = await app.get_chat(chat_id)
            link = await get_chat_link(chat_id)
            text += f"**{j + 1}.** [{unidecode(chat.title)[:25]}]({link}) `[{chat_id}]`\n"
            j += 1
        except: continue
    await mystic.edit_text(f"{text}\n{POWERED_BY}", disable_web_page_preview=True)

# --- CLONE COMMANDS ---

@app.on_message(filters.command(["cvc"]) & SUDOERS)
async def clone_vc_stats(_, message: Message):
    all_clones = await clonebotdb.find({}).to_list(length=None)
    text = "🌐 **Clones Active Voice Calls:**\n\n"
    active_chats = await get_active_chats()
    
    for clone in all_clones:
        bot_id = clone["bot_id"]
        served = await get_served_chats_clone(bot_id)
        ids = [int(c["chat_id"]) for c in served]
        active_in_this = [cid for cid in active_chats if cid in ids]
        
        if active_in_this:
            text += f"🤖 **Bot ID:** `{bot_id}`\n"
            for cid in active_in_this:
                chat = await app.get_chat(cid)
                text += f" └ 🔗 [{unidecode(chat.title)[:20]}]({await get_chat_link(cid)})\n"
    await message.reply_text(f"{text}\n{POWERED_BY}", disable_web_page_preview=True)

@app.on_message(filters.command(["cvvc"]) & SUDOERS)
async def clone_vvc_stats(_, message: Message):
    all_clones = await clonebotdb.find({}).to_list(length=None)
    text = "🌐 **Clones Active Video Calls:**\n\n"
    active_video = await get_active_video_chats()
    
    for clone in all_clones:
        bot_id = clone["bot_id"]
        served = await get_served_chats_clone(bot_id)
        ids = [int(c["chat_id"]) for c in served]
        active_in_this = [cid for cid in active_video if cid in ids]
        
        if active_in_this:
            text += f"🤖 **Bot ID:** `{bot_id}`\n"
            for cid in active_in_this:
                chat = await app.get_chat(cid)
                text += f" └ 🔗 [{unidecode(chat.title)[:20]}]({await get_chat_link(cid)})\n"
    await message.reply_text(f"{text}\n{POWERED_BY}", disable_web_page_preview=True)

# --- ASTATS & CALLBACKS ---

@app.on_message(filters.command(["astats"]) & SUDOERS)
async def astats(_, message: Message):
    v = len(await get_active_chats())
    vv = len(await get_active_video_chats())
    await message.reply_text(
        f"📊 **PritiMusic Stats**\n\n🎤 VC: `{v}` | 📹 VVC: `{vv}`\n\n{POWERED_BY}",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🎤 VC", callback_data="activevc_cb"), InlineKeyboardButton("📹 VVC", callback_data="activev_cb")],
            [InlineKeyboardButton("🤖 Clone VC", callback_data="cvc_cb"), InlineKeyboardButton("🤖 Clone VVC", callback_data="cvvc_cb")],
            [InlineKeyboardButton("❌ Close", callback_data="close")]
        ])
    )

@app.on_callback_query(filters.regex("activevc_cb") & SUDOERS)
async def cb_vc(c, q): await active_voice_chats(c, q.message)
@app.on_callback_query(filters.regex("activev_cb") & SUDOERS)
async def cb_vvc(c, q): await active_video_chats(c, q.message)
@app.on_callback_query(filters.regex("cvc_cb") & SUDOERS)
async def cb_cvc(c, q): await clone_vc_stats(c, q.message)
@app.on_callback_query(filters.regex("cvvc_cb") & SUDOERS)
async def cb_cvvc(c, q): await clone_vvc_stats(c, q.message)
@app.on_callback_query(filters.regex("close") & SUDOERS)
async def cb_close(_, q): await q.message.delete()
