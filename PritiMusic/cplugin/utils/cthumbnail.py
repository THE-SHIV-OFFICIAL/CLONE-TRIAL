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
def clear(text, max_length=25):
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
    # RGBA added here for transparent effects like rain
    draw = ImageDraw.Draw(background, "RGBA") 

    # UI Glass Box
    draw.rounded_rectangle((40, 40, 1880, 940), radius=60, fill=(0, 0, 0, 100), outline=(132, 224, 240, 200), width=6)
    
    # --- NEW: Rain Effect Inside the Card ---
    for _ in range(200): # 200 raindrops
        rx = random.randint(60, 1860) # Keeping inside card bounds
        ry = random.randint(60, 920)
        length = random.randint(15, 40)
        angle_offset = random.randint(-5, 5) # Slight diagonal fall
        opacity = random.randint(30, 100) # Semi-transparent white
        draw.line((rx, ry, rx + angle_offset, ry + length), fill=(255, 255, 255, opacity), width=random.randint(1, 2))

    try:
        f1 = ImageFont.truetype("PritiMusic/assets/font.ttf", 65)
        f2 = ImageFont.truetype("PritiMusic/assets/font2.ttf", 45)
        br = ImageFont.truetype("PritiMusic/assets/font2.ttf", 50)
    except:
        f1 = f2 = br = ImageFont.load_default()

    # Paste Images (Mask pass kiya gaya hai taki background rain clear rahe)
    yt_img = circle(bg.resize((500, 500)))
    background.paste(yt_img, (80, 250), yt_img) 
    
    u_photo = await download_user_photo(user_id)
    if u_photo:
        u_img = circle(Image.open(u_photo).resize((450, 450)))
        background.paste(u_img, (1350, 250), u_img)

    # Fetch User Name
    try:
        user_info = await client.get_users(user_id)
        user_name = user_info.first_name
    except: user_name = "User"

    # Text Placement
    draw.text((650, 300), clear(title, 25), fill="white", font=f1)
    draw.text((650, 400), f"Artist: {channel}", fill=(200, 200, 200), font=f2)
    draw.text((650, 470), f"Views: {views}", fill=(150, 150, 150), font=f2)
    draw.text((650, 530), f"Duration: {duration}", fill=(150, 150, 150), font=f2)
    
    # Branding & Request
    draw.text((100, 100), f"BOT: {bot_name}", fill="yellow", font=br)
    draw.text((1400, 100), f"OWNER: {owner_name}", fill="cyan", font=br)
    draw.text((1350, 880), f"Requested by: {user_name}", fill="white", font=f2)

    # --- UPDATED: Thinner and More Attractive Audio Wave ---
    center_y = 750
    num_bars = 80  # More bars for smooth effect
    bar_width = 8  # Thinner bars
    spacing = 14   # Gap between bars
    start_x = 650  # Aligned with the text
    
    for i in range(num_bars):
        if i % 5 == 0:
            h = random.randint(40, 80)
        else:
            h = random.randint(10, 45)
            
        r = random.randint(150, 255)
        g = random.randint(100, 200)
        b = random.randint(200, 255) 
        
        x1 = start_x + (i * spacing)
        x2 = x1 + bar_width
        
        if x2 > 1300: # Stop before overlapping the user profile picture
            break
            
        draw.rounded_rectangle((x1, center_y - h, x2, center_y + h), radius=4, fill=(r, g, b, 200))

    background.convert("RGB").save(filename)
    os.remove(f"cache/temp_{videoid}.jpg")
    if u_photo and os.path.exists(u_photo): os.remove(u_photo)
    return filename
