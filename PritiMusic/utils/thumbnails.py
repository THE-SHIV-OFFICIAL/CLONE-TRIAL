import os
import re
import random
import aiofiles
import aiohttp
from PIL import (Image, ImageDraw, ImageFilter, ImageFont, ImageOps)
from py_yt import VideosSearch
from PritiMusic import app

def circle(img):
    img = img.convert("RGBA")
    size = min(img.size)
    img = ImageOps.fit(img, (size, size), centering=(0.5, 0.5))
    mask = Image.new("L", (size, size), 0)
    ImageDraw.Draw(mask).ellipse((0, 0, size, size), fill=255)
    output = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    output.paste(img, (0, 0), mask)
    return output

def draw_text_with_glow(draw, position, text, font, fill, glow_fill):
    x, y = position
    for dx, dy in [(-3, 0), (3, 0), (0, -3), (0, 3)]:
        draw.text((x + dx, y + dy), text, font=font, fill=glow_fill)
    draw.text((x, y), text, font=font, fill=fill)

async def download_user_photo(user_id):
    try:
        async for photo in app.get_chat_photos(user_id, limit=1):
            return await app.download_media(photo.file_id, file_name=f"cache/{user_id}.jpg")
    except: return None
    return None

async def get_thumb(videoid, user_id, user_name):
    os.makedirs("cache", exist_ok=True)
    final_path = f"cache/{videoid}_{user_id}.png"
    if os.path.exists(final_path): return final_path

    try:
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

        bg = Image.open(f"cache/temp_{videoid}.jpg").convert("RGBA").resize((1920, 1080))
        background = bg.filter(ImageFilter.GaussianBlur(25)).point(lambda p: p * 0.35)
        draw = ImageDraw.Draw(background)

        draw.rounded_rectangle((40, 40, 1880, 940), radius=60, fill=(0, 0, 0, 80), outline=(132, 224, 240, 150), width=6)
        
        try:
            f1 = ImageFont.truetype("PritiMusic/assets/font.ttf", 65)
            f2 = ImageFont.truetype("PritiMusic/assets/font2.ttf", 45)
            br = ImageFont.truetype("PritiMusic/assets/font2.ttf", 55)
        except:
            f1 = f2 = br = ImageFont.load_default()

        yt_img = circle(bg.resize((500, 500)))
        background.paste(yt_img, (80, 200))
        
        u_photo = await download_user_photo(user_id)
        if u_photo:
            u_img = circle(Image.open(u_photo).resize((450, 450)))
            background.paste(u_img, (1350, 215))

        draw.text((650, 300), (title[:22] + "...") if len(title) > 22 else title, fill="white", font=f1)
        draw.text((650, 400), f"Artist: {channel}", fill=(220, 220, 220), font=f2)
        
        # बदलाव 1: Duration को Views के नीचे कर दिया गया है
        draw.text((650, 460), f"Views: {views}", fill=(190, 190, 190), font=f2)
        draw.text((650, 520), f"Duration: {duration}", fill=(190, 190, 190), font=f2)

        # बदलाव 2 & 3: Wave को बीच से (Up-Down) और अलग-अलग कलर का किया गया है
        center_y = 750 # वेव की सेंटर लाइन
        for i in range(40):
            h = random.randint(10, 60) # वेव की ऊँचाई (ऊपर और नीचे)
            r = random.randint(100, 255)
            g = random.randint(100, 255)
            b = random.randint(150, 255)
            # सेंटर से 'h' पिक्सल ऊपर और 'h' पिक्सल नीचे ड्रा होगा
            draw.rounded_rectangle((140 + i*40, center_y - h, 170 + i*40, center_y + h), radius=10, fill=(r, g, b))

        draw.ellipse((930, 830, 990, 890), outline="white", width=4)
        draw.rectangle((950, 845, 960, 875), fill="white")
        draw.rectangle((965, 845, 975, 875), fill="white")

        draw_text_with_glow(draw, (80, 975), "BETA BOT HUB", br, (132, 224, 240), (0, 255, 255, 100))
        draw_text_with_glow(draw, (1480, 975), "THE SHIV", br, (255, 60, 160), (255, 0, 170, 100))

        background.convert("RGB").save(final_path, "PNG")
        return final_path
    except Exception as e:
        print(f"Thumbnail Error: {e}")
        return None
    finally:
        if os.path.exists(f"cache/temp_{videoid}.jpg"): os.remove(f"cache/temp_{videoid}.jpg")
        if 'u_photo' in locals() and u_photo and os.path.exists(u_photo): os.remove(u_photo)
