import os
import re
import random
import aiofiles
import aiohttp
import colorsys
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
        draw = ImageDraw.Draw(background, "RGBA")

        # Card Background
        draw.rounded_rectangle((40, 40, 1880, 940), radius=60, fill=(10, 25, 40, 140), outline=(0, 200, 255, 180), width=6)
        
        # --- NEW: RAIN EFFECT ---
        for _ in range(300):
            rx = random.randint(0, 1920)
            ry = random.randint(0, 1080)
            length = random.randint(10, 30)
            # Slanted white lines with variable transparency
            draw.line([(rx, ry), (rx + 5, ry + length)], 
                      fill=(255, 255, 255, random.randint(20, 70)), 
                      width=2)
        
        try:
            f1 = ImageFont.truetype("PritiMusic/assets/font.ttf", 65)
            f2 = ImageFont.truetype("PritiMusic/assets/font2.ttf", 45)
            br = ImageFont.truetype("PritiMusic/assets/font2.ttf", 55)
        except:
            f1 = f2 = br = ImageFont.load_default()

        # YouTube Thumbnail & User Profile
        yt_img = circle(bg.resize((500, 500)))
        background.paste(yt_img, (80, 200), yt_img)
        
        u_photo = await download_user_photo(user_id)
        if u_photo:
            u_img = circle(Image.open(u_photo).resize((450, 450)))
            background.paste(u_img, (1350, 215), u_img)

        # Texts
        draw.text((650, 300), (title[:22] + "...") if len(title) > 22 else title, fill="white", font=f1)
        draw.text((650, 400), f"Artist: {channel}", fill=(220, 220, 220), font=f2)
        draw.text((650, 460), f"Views: {views}", fill=(190, 190, 190), font=f2)
        draw.text((650, 520), f"Duration: {duration}", fill=(190, 190, 190), font=f2)

        # --- RAINBOW NEON AUDIO WAVE ---
        center_y = 750
        num_bars = 90
        bar_width = 6   
        spacing = 15
        start_x = 350
        
        for i in range(num_bars):
            h = random.randint(40, 80) if i % 5 == 0 else random.randint(10, 45)
            x1 = start_x + (i * spacing)
            x2 = x1 + bar_width
            if x2 > 1800: break
                
            hue = 0.60 + (i / num_bars) * 0.75
            if hue > 1.0: hue -= 1.0
            r, g, b = [int(c * 255) for c in colorsys.hsv_to_rgb(hue, 1.0, 1.0)]
            
            draw.rounded_rectangle((x1 - 8, center_y - h - 8, x2 + 8, center_y + h + 8), radius=8, fill=(r, g, b, 15))
            draw.rounded_rectangle((x1 - 4, center_y - h - 4, x2 + 4, center_y + h + 4), radius=6, fill=(r, g, b, 45))
            draw.rounded_rectangle((x1 - 1, center_y - h - 1, x2 + 1, center_y + h + 1), radius=4, fill=(r, g, b, 120))
            draw.rounded_rectangle((x1 + 2, center_y - h, x2 - 2, center_y + h), radius=2, fill=(255, 255, 255, 255))

        # Play Button icon
        draw.ellipse((930, 830, 990, 890), outline="white", width=4)
        draw.rectangle((950, 845, 960, 875), fill="white")
        draw.rectangle((965, 845, 975, 875), fill="white")

        # Footer Texts
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
