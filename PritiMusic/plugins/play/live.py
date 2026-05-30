from pyrogram import filters
from PritiMusic import YouTube, app
from PritiMusic.utils.channelplay import get_channeplayCB
from PritiMusic.utils.decorators.language import languageCB
from PritiMusic.utils.stream.stream import stream
from config import BANNED_USERS

@app.on_callback_query(filters.regex("LiveStream") & ~BANNED_USERS)
@languageCB
async def play_live_stream(client, CallbackQuery, _):
    callback_data = CallbackQuery.data.strip()
    callback_request = callback_data.split(None, 1)[1]
    vidid, user_id, mode, cplay, fplay = callback_request.split("|")
    
    if CallbackQuery.from_user.id != int(user_id):
        try:
            return await CallbackQuery.answer(_["playcb_1"], show_alert=True)
        except:
            return

    try:
        chat_id, channel = await get_channeplayCB(_, cplay, CallbackQuery)
    except:
        return

    video = True if mode == "v" else None
    user_name = CallbackQuery.from_user.first_name
    
    # Safely delete message to avoid flood errors
    try:
        await CallbackQuery.message.delete()
    except:
        pass

    try:
        await CallbackQuery.answer()
    except:
        pass

    mystic = await CallbackQuery.message.reply_text(
        _["play_2"].format(channel) if channel else _["play_1"]
    )
    
    try:
        details, track_id = await YouTube.track(vidid, True)
    except Exception as e:
        return await mystic.edit_text(_["play_3"])
    
    ffplay = True if fplay == "f" else None
    
    # Check if stream is actually live (duration is None/0 for live streams)
    if not details["duration_min"]:
        try:
            await stream(
                _,
                mystic,
                user_id,
                details,
                chat_id,
                user_name,
                CallbackQuery.message.chat.id,
                video,
                streamtype="live",
                forceplay=ffplay,
            )
        except Exception as e:
            ex_type = type(e).__name__
            err = e if ex_type == "AssistantErr" else _["general_2"].format(ex_type)
            return await mystic.edit_text(err)
    else:
        return await mystic.edit_text("» ɴᴏᴛ ᴀ ʟɪᴠᴇ sᴛʀᴇᴀᴍ.")
    
    # Clean up the processing message
    try:
        await mystic.delete()
    except:
        pass
