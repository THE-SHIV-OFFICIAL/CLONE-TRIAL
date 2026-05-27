import os
import re
import random
import math
import aiofiles
import aiohttp
from PIL import (Image, ImageDraw, ImageEnhance, ImageFilter, ImageFont, ImageOps)
from unidecode import unidecode
from py_yt import VideosSearch

from PritiMusic import app
from config import YOUTUBE_IMG_URL

# Helper: Circular crop for images
def circle(img):
    img = img.convert("RGBA")
    size = min(img.size)
    img = ImageOps.fit(img, (size, size), centering=(0.5, 0.5))
    mask = Image.new("L", (size, size), 0)
    ImageDraw.Draw(mask).ellipse((0, 0, size, size), fill=255)
    output = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    output.paste(img, (0, 0), mask)
    return output

# Helper: Glow effect for text
def draw_text_with_glow(draw, position, text, font, fill, glow_fill):
    x, y = position
    for dx, dy in [(-3, 0), (3, 0), (0, -3), (0, 3)]:
        draw.text((x + dx, y + dy), text, font=font, fill=glow_fill)
    draw.text((x, y), text, font=font, fill=fill)

# Helper: Download user profile photo
async def download_user_photo(user_id):
    try:
        async for photo in app.get_chat_photos(user_id, limit=1):
            return await app.download_media(photo.file_id, file_name=f"cache/{user_id}.jpg")
    except: return None
    return None

# --- Main Thumbnail Function ---
async def get_thumb(videoid, user_id, user_name):
    os.makedirs("cache", exist_ok=True)
    final_path = f"cache/{videoid}_{user_id}.png"
    
    # Fetch YT Data
    results = VideosSearch(f"https://www.youtube.com/watch?v={videoid}", limit=1)
    data = await results.next()
    result = data["result"][0]
    title = re.sub(r"\W+", " ", result["title"]).title()
    duration = result.get("duration", "00:00")
    views = result.get("viewCount", {}).get("short", "Unknown")
    channel = result.get("channel", {}).get("name", "Unknown Artist")
    
    # Download Thumbnail
    async with aiohttp.ClientSession() as session:
        async with session.get(result["thumbnails"][0]["url"].split("?")[0]) as resp:
            f = await aiofiles.open(f"cache/temp_{videoid}.jpg", mode="wb")
            await f.write(await resp.read())
            await f.close()

    # Image Processing
    bg = Image.open(f"cache/temp_{videoid}.jpg").convert("RGBA").resize((1920, 1080))
    background = bg.filter(ImageFilter.GaussianBlur(25)).point(lambda p: p * 0.35)
    draw = ImageDraw.Draw(background)

    # UI Glass Box
    draw.rounded_rectangle((40, 40, 1880, 940), radius=60, fill=(0, 0, 0, 80), outline=(132, 224, 240, 150), width=6)
    
    # Fonts loading
    f1 = ImageFont.truetype("PritiMusic/assets/font.ttf", 65)
    f2 = ImageFont.truetype("PritiMusic/assets/font2.ttf", 45)
    br = ImageFont.truetype("PritiMusic/assets/font2.ttf", 55)

    # Left Thumbnail & User Photo
    yt_img = circle(bg.resize((500, 500)))
    background.paste(yt_img, (80, 200))
    
    u_photo = await download_user_photo(user_id)
    if u_photo:
        u_img = circle(Image.open(u_photo).resize((450, 450)))
        background.paste(u_img, (1350, 215))

    # Text
    draw.text((650, 300), title[:38] + "...", fill="white", font=f1)
    draw.text((650, 400), f"Artist: {channel}", fill=(220, 220, 220), font=f2)
    draw.text((650, 460), f"Views: {views} | Duration: {duration}", fill=(190, 190, 190), font=f2)

    # Waveform drawing
    for i in range(40):
        h = random.randint(20, 100)
        draw.rounded_rectangle((140 + i*40, 750, 170 + i*40, 750 + h), radius=10, fill=(219, 133, 166))

    # Pause Button
    draw.ellipse((930, 830, 990, 890), outline="white", width=4)
    draw.rectangle((950, 845, 960, 875), fill="white")
    draw.rectangle((965, 845, 975, 875), fill="white")

    # Footer Branding
    draw_text_with_glow(draw, (80, 975), "BETA BOT HUB", br, (132, 224, 240), (0, 255, 255, 100))
    draw_text_with_glow(draw, (1480, 975), f"👑 {user_name[:15]}", br, (255, 60, 160), (255, 0, 170, 100))

    # Save final
    background.convert("RGB").save(final_path, "PNG")
    os.remove(f"cache/temp_{videoid}.jpg")
    if u_photo and os.path.exists(u_photo): os.remove(u_photo)
    return final_path
