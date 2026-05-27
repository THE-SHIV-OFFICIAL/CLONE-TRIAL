import os
import re
import random
import aiofiles
import aiohttp
from PIL import (Image, ImageDraw, ImageEnhance, ImageFilter, ImageFont, ImageOps)
from py_yt import VideosSearch
from PritiMusic import app
from PritiMusic.utils.database import clonebotdb

# Helper: Circular crop
def circle(img):
    img = img.convert("RGBA")
    size = min(img.size)
    img = ImageOps.fit(img, (size, size), centering=(0.5, 0.5))
    mask = Image.new("L", (size, size), 0)
    ImageDraw.Draw(mask).ellipse((0, 0, size, size), fill=255)
    output = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    output.paste(img, (0, 0), mask)
    return output

# Helper: Text Truncator
def clear(text, max_length=38):
    text = text.strip()
    return text[:max_length].rstrip() + "..." if len(text) > max_length else text

# Helper: Download user profile
async def download_user_photo(user_id):
    try:
        async for photo in app.get_chat_photos(user_id, limit=1):
            return await app.download_media(photo.file_id, file_name=f"cache/{user_id}.jpg")
    except: return None
    return None

async def get_thumb(videoid, user_id, client):
    # 1. Fetch Bot & Owner
    me = await client.get_me()
    bot_name = me.first_name.upper()
    bot_id = me.id
    owner_name = "OWNER"
    try:
        bot_data = await clonebotdb.find_one({"bot_id": bot_id})
        if bot_data:
            owner = await client.get_users(bot_data.get("user_id"))
            owner_name = owner.first_name.upper()
    except: owner_name = "ADMIN"

    # 2. Setup Files
    os.makedirs("cache", exist_ok=True)
    filename = f"cache/{videoid}_{bot_id}.png"
    if os.path.isfile(filename): return filename

    # 3. Download YT Data
    results = VideosSearch(f"https://www.youtube.com/watch?v={videoid}", limit=1)
    data = await results.next()
    result = data["result"][0]
    title = re.sub(r"\W+", " ", result["title"]).title()
    duration = result.get("duration", "00:00")
    views = result.get("viewCount", {}).get("short", "Unknown")
    channel = result.get("channel", {}).get("name", "Unknown Artist")
    
    async with aiohttp.ClientSession() as session:
        async with session.get(result["thumbnails"][0]["url"].split("?")[0]) as resp:
            f = await aiofiles.open(f"cache/temp_{videoid}.jpg", mode="wb")
            await f.write(await resp.read())
            await f.close()

    # 4. Drawing Logic
    bg = Image.open(f"cache/temp_{videoid}.jpg").convert("RGBA").resize((1920, 1080))
    background = bg.filter(ImageFilter.GaussianBlur(25)).point(lambda p: p * 0.4)
    draw = ImageDraw.Draw(background)

    # UI Glass Box
    draw.rounded_rectangle((40, 40, 1880, 940), radius=60, fill=(0, 0, 0, 100), outline=(132, 224, 240, 200), width=6)
    
    f1 = ImageFont.truetype("PritiMusic/assets/font.ttf", 65)
    f2 = ImageFont.truetype("PritiMusic/assets/font2.ttf", 45)
    br = ImageFont.truetype("PritiMusic/assets/font2.ttf", 50)

    # Paste Images (YT & User)
    yt_img = circle(bg.resize((500, 500)))
    background.paste(yt_img, (80, 250))
    
    u_photo = await download_user_photo(user_id)
    if u_photo:
        u_img = circle(Image.open(u_photo).resize((450, 450)))
        background.paste(u_img, (1350, 250))

    # Text & Waveform
    draw.text((650, 300), clear(title), fill="white", font=f1)
    draw.text((650, 400), f"Artist: {channel}", fill=(200, 200, 200), font=f2)
    draw.text((650, 460), f"Views: {views} | Duration: {duration}", fill=(150, 150, 150), font=f2)
    
    # Branding
    draw.text((100, 100), f"BOT: {bot_name}", fill="yellow", font=br)
    draw.text((1400, 100), f"OWNER: {owner_name}", fill="cyan", font=br)

    # Waveform
    for i in range(45):
        h = random.randint(30, 120)
        draw.rounded_rectangle((700 + i*25, 750, 720 + i*25, 750 + h), radius=5, fill=(219, 133, 166))

    background.convert("RGB").save(filename)
    os.remove(f"cache/temp_{videoid}.jpg")
    if u_photo and os.path.exists(u_photo): os.remove(u_photo)
    return filename
