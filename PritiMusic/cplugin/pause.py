from pyrogram import filters, Client
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton

from PritiMusic import app
from PritiMusic.core.call import Lucky
from PritiMusic.utils.database import music_off
from config import BANNED_USERS

# ✅ IMPORT NEW ADMIN CHECKER
from PritiMusic.cplugin.utils.decorators.admins import AdminRightsCheck

@Client.on_message(filters.command(["pause", "cpause"]) & filters.group & ~BANNED_USERS)
@AdminRightsCheck 
async def pause_admin(cli, message: Message, _, chat_id):
    
    # 1. Database mein music off mark karein
    await music_off(chat_id)
    
    # 2. Call module ka use karke stream pause karein
    # Note: Agar aapka Lucky module 'Lucky.pause_stream(chat_id)' support karta hai toh ye sahi hai
    await Lucky.pause_stream(chat_id)

    # 3. Inline Buttons setup
    buttons = [
        [
            InlineKeyboardButton(
                text="ʀᴇsᴜᴍᴇ ▷", callback_data=f"ADMIN Resume|{chat_id}"
            ),
            InlineKeyboardButton(
                text="ʀᴇᴘʟᴀʏ ↺", callback_data=f"ADMIN Replay|{chat_id}"
            ),
        ],
        [ 
            InlineKeyboardButton(
                text="✯ CLONE NOW ✯", url="https://t.me/clone_MUSICrobot"
            )
        ],
    ]

    # 4. Reply message
    await message.reply_text(
        _["admin_2"].format(message.from_user.mention),
        reply_markup=InlineKeyboardMarkup(buttons),
    )
