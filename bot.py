import random
import json
import asyncio
import os
import threading
import aiohttp
from http.server import BaseHTTPRequestHandler, HTTPServer
from datetime import datetime, timezone
import discord
from discord.ext import commands, tasks

# ==========================================
# 🕵️‍♂️ HEADLESS BOT: SMART MAP SCANNER ENGINE
# ==========================================
DUMMY_SESSION_TOKEN = "[INSERT_YOUR_TOKEN_HERE]"  # <- LDPlayer से निकाला हुआ टोकन यहाँ डलेगा
ENEMY_GUILDS = ["AAA", "XYZ", "BAD"]  # जिन गिल्ड्स पर नज़र रखनी है उनके टैग्स
MIN_MIGHT_ALERT = 50000000  # 50 Million पावर से ऊपर वालों का ही अलर्ट आएगा

# 🌙 हर दिन सोने और जगने का समय रैंडम तय करने वाला फंक्शन (100% Anti-Detection)
def should_bot_sleep():
    current_hour = datetime.now(timezone.utc).hour
    
    # रात 10 से रात 1 बजे के बीच कभी भी सोना शुरू करेगा (हर दिन अलग समय)
    random_sleep_start = random.randint(22, 1) 
    # सुबह 5 से 8 बजे के बीच कभी भी उठेगा (हर दिन अलग समय)
    random_wake_up = random.randint(5, 8)     

    if random_sleep_start <= current_hour or current_hour <= random_wake_up:
        return True # इस दौरान बॉट सोएगा
    return False

@tasks.loop(minutes=3)
async def smart_map_scanner():
    if DUMMY_SESSION_TOKEN == "[INSERT_YOUR_TOKEN_HERE]":
        # जब तक टोकन नहीं डलेगा, बॉट शांति से बैठा रहेगा
        return

    # 1. Human-like Random Sleep Check (यहाँ रैंडम स्लीप चेक हो रहा है)
    if should_bot_sleep():
        print("💤 Bot is sleeping like a human today to avoid detection...")
        return

    # 2. Human-like Delay (रोबोटिक स्पीड से बचने के लिए रैंडम ब्रेक)
    human_delay = random.uniform(3.5, 7.8)
    await asyncio.sleep(human_delay)

    # 3. Tracker Logic (जब पैकेट स्निफिंग/API कनेक्ट होगी)
    try:
        # यहाँ मैप डेटा फेच करके शील्ड चेक होगी और Discord पर alert भेजा जाएगा
        pass
    except Exception as e:
        print(f"Scanner Error: {e}")

# ==========================================
# 🌐 Render 24/7 Keep Alive Web Server
# ==========================================
class DummyHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/plain')
        self.end_headers()
        self.wfile.write(b"Lords Mobile Tracker Bot is online 24/7!")

    def do_HEAD(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/plain')
        self.end_headers()

def keep_alive():
    port = int(os.environ.get("PORT", 8080))
    server = HTTPServer(('0.0.0.0', port), DummyHandler)
    threading.Thread(target=server.serve_forever, daemon=True).start()

# ==========================================
# 🤖 Discord Bot Setup
# ==========================================
intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True
bot = commands.Bot(command_prefix='!', intents=intents)
bot.remove_command('help')

@bot.event
async def on_ready():
    print(f'✅ Tracker Bot ({bot.user}) ऑनलाइन आ गया है!')
    await bot.change_presence(status=discord.Status.online, activity=discord.Game(name="Scanning Map..."))
    
    if not smart_map_scanner.is_running():
        smart_map_scanner.start()

# 🛡️ Shield Timer Command
@bot.command(name="shield")
async def shield(ctx, hours: int):
    if hours <= 0:
        await ctx.send("❌ भाई, सही टाइम बताओ! जैसे: `!shield 8`")
        return
    total_seconds = hours * 3600
    warning_seconds = total_seconds - 900 
    await ctx.send(f"🛡️ {ctx.author.mention}, **{hours} घंटे** की शील्ड सेट कर दी गई है। 15 मिनट पहले अलर्ट आ जाएगा!")
    
    if warning_seconds > 0:
        await asyncio.sleep(warning_seconds)
        try:
            await ctx.author.send(f"🚨 **चेतावनी:** भाई! तुम्हारी शील्ड में सिर्फ **15 मिनट** बचे हैं!")
        except discord.Forbidden:
            await ctx.send(f"🚨 {ctx.author.mention}, तुम्हारी शील्ड 15 मिनट में खत्म होने वाली है!")
        await asyncio.sleep(900)
    else:
        await asyncio.sleep(total_seconds)
    try:
        await ctx.author.send(f"⚠️ **अलर्ट:** शील्ड **खत्म हो चुकी है!** 🏰")
    except discord.Forbidden:
        await ctx.send(f"⚠️ {ctx.author.mention}, तुम्हारी शील्ड **खत्म हो चुकी है!** 🏰")

# ==========================================
# 🏃 Run Bot
# ==========================================
keep_alive()
token = os.environ.get("DISCORD_TOKEN")
if token:
    bot.run(token)
else:
    print("❌ Error: DISCORD_TOKEN environment variable not found")
