from PritiMusic.core.mongo import mongodb

# ==========================================
# MONGODB COLLECTIONS
# ==========================================
cloneownerdb = mongodb.cloneownerdb
clonebotnamedb = mongodb.clonebotnamedb
chatsdbc = mongodb.chatsc
usersdbc = mongodb.tgusersdbc
clonebotdb = mongodb.clonebotdb
clone_custom_db = mongodb.clone_custom_settings

# ==========================================
# SAFETY UTILS
# ==========================================
def to_int(bot_id):
    """Ensures bot_id is always an integer for consistent DB queries."""
    try:
        return int(bot_id)
    except (ValueError, TypeError):
        return bot_id

# ==========================================
# GLOBAL CLONE MANAGEMENT
# ==========================================

def get_all_clones():
    return clonebotdb.find()

async def save_clonebot_owner(bot_id, user_id):
    await cloneownerdb.update_one(
        {"bot_id": to_int(bot_id)},
        {"$set": {"user_id": user_id}},
        upsert=True
    )

async def get_owner_id_from_db(bot_id):
    bot_data = await clonebotdb.find_one({"bot_id": to_int(bot_id)})
    return bot_data.get("user_id") if bot_data else None

async def has_user_cloned_any_bot(user_id: int) -> bool:
    return bool(await clonebotdb.find_one({"user_id": user_id}))

# ==========================================
# CUSTOMIZATION (PLAY/SEARCH)
# ==========================================

async def set_clone_search_type(bot_id, type_name, content):
    await clone_custom_db.update_one(
        {"bot_id": to_int(bot_id)},
        {"$set": {type_name: content}},
        upsert=True
    )

async def get_clone_search_type(bot_id, type_name):
    data = await clone_custom_db.find_one({"bot_id": to_int(bot_id)})
    return data.get(type_name) if data else None

async def get_clone_search_settings(bot_id):
    data = await clone_custom_db.find_one({"bot_id": to_int(bot_id)})
    if not data:
        return None, None
    
    # Priority: Video > Photo > Animation > Sticker > Text
    for p_type in ["video", "photo", "animation", "sticker", "text"]:
        val = data.get(p_type)
        if val:
            return p_type, val
    return None, None

async def delete_clone_search_type(bot_id):
    await clone_custom_db.update_one(
        {"bot_id": to_int(bot_id)},
        {"$unset": {
            "video": "", "photo": "", "animation": "",
            "sticker": "", "text": ""
        }}
    )

# ==========================================
# STREAM CAPTION
# ==========================================

async def set_clone_stream_caption(bot_id, caption):
    await clone_custom_db.update_one(
        {"bot_id": to_int(bot_id)},
        {"$set": {"stream_caption": caption}},
        upsert=True
    )

async def get_clone_stream_caption(bot_id):
    data = await clone_custom_db.find_one({"bot_id": to_int(bot_id)})
    return data.get("stream_caption") if data else None

async def delete_clone_stream_caption(bot_id):
    await clone_custom_db.update_one(
        {"bot_id": to_int(bot_id)},
        {"$unset": {"stream_caption": ""}}
    )

# ==========================================
# BROADCAST HELPERS
# ==========================================

async def get_served_chats_clone(bot_id):
    return [chat async for chat in chatsdbc.find({"bot_id": to_int(bot_id)})]

async def get_served_users_clone(bot_id):
    return [user async for user in usersdbc.find({"bot_id": to_int(bot_id)})]
