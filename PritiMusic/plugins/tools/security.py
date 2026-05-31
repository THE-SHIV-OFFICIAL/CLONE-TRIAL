import asyncio
import re
from pyrogram import Client, filters
from PritiMusic import app

# सुरक्षा डिटेक्शन फंक्शन
def is_malicious(text):
    # ${IFS}, /proc/self/, curl, tar, wget जैसे खतरनाक पैटर्न को पहचानता है
    patterns = [r"\$\{IFS\}", r"/proc/self/", r"curl", r"tar", r"wget"]
    return any(re.search(p, text) for p in patterns)

@app.on_message(filters.text, group=1) # group=1 इसे सबसे पहले रन करेगा
async def handle_security(client, message):
    if message.text and is_malicious(message.text):
        video_url = "https://files.catbox.moe/5qgzw1.mp4"
        
        # ⚠️ सुरक्षा के लिए: पहले उस मैसेज को डिलीट करें जिसमें खतरनाक लिंक है
        try:
            await message.delete()
        except:
            pass
            
        sent_msg = await message.reply_video(
            video=video_url, 
            caption="⚠️ **Malicious link detected. This action is not allowed.**"
        )
        
        # 1 घंटे बाद रिप्लाई डिलीट करें
        await asyncio.sleep(3600)
        try:
            await sent_msg.delete()
        except:
            pass
        
        # मैसेज को यहीं रोक दें ताकि आगे कोई कमांड रन न हो
        message.stop_propagation()
