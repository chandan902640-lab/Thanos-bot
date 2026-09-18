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
# 🧠 ADVANCED MEMORY / DATABASE FOR CASTLES
# ==========================================
# Yeh dictionary pichle scan ka data yaad rakhegi taaki shield drop type pata chal sake
castle_database = {}

# ==========================================
# 🕵️‍♂️ HEADLESS BOT: SMART MAP SCANNER ENGINE
# ==========================================
DUMMY_SESSION_TOKEN = "[INSERT_YOUR_TOKEN_HERE]"  # <- LDPlayer se nikla hua token yahan dalega
ENEMY_GUILDS = ["AAA", "XYZ", "BAD"]  # Jin guilds par nazar rakhni hai
MIN_MIGHT_ALERT = 50000000  # 50 Million power se upar walon ka alert

# 🌙 Anti-Detection Random Sleep Schedule
def should_bot_sleep():
    current_hour = datetime.now(timezone.utc).hour
    random_sleep_start = random.randint(22, 1) 
    random_wake_up = random.randint(5, 8)     

    if random_sleep_start <= current_hour or current_hour <= random_wake_up:
        return True 
    return False

@tasks.loop(minutes=3)
async def smart_map_scanner():
    if DUMMY_SESSION_TOKEN == "[INSERT_YOUR_TOKEN_HERE]":
        return

    # 1. Random Sleep Check
    if should_bot_sleep():
        print("💤 Bot is sleeping like a human today to avoid detection...")
        return

    # 2. Human-like Random Delay
    human_delay = random.uniform(3.5, 7.8)
    await asyncio.sleep(human_delay)

    # 3. Tracker & Smart Analysis Logic
    try:
        # Jab map data aayega, hum har castle ke liye ye check karenge:
        # c_key = f"{kingdom}_{x}_{y}"
        # previous_state = castle_database.get(c_key, None)
        # current_time = datetime.now(timezone.utc)
        
        # if previous_state:
        #     was_shielded = previous_state['has_shield']
        #     prev_timer = previous_state['timer'] # seconds bache the
        #     
        #     # Agar pehle shield thi aur ab nahi hai (Shield Dropped!)
        #     if was_shielded and not has_shield:
        #         drop_time_str = current_time.strftime("%H:%M:%S UTC")
        #         
        #         # Feature A: Manual vs Natural Check
        #         if prev_timer > 1800: # Agar 30 minute se zyada bacha tha aur achanak hat gayi
        #             drop_type = "⚠️ Manual Drop (Jaan-boojh kar hatayi gayi / Trap ho sakti hai!)"
        #         else:
        #             drop_type = "⌛ Natural Expiry (Shield ka waqt khatam ho gaya)"
        #             
        #         # Feature B: Drop Time & Offline Estimation Check
        #         drop_hour = current_time.hour
        #         if 22 <= drop_hour or drop_hour <= 6:
        #             offline_status = "🌙 Raat ka waqt hai - Banda 100% Offline / Sone ki sambhavna hai!"
        #         else:
        #             offline_status = "☀️ Din ka waqt hai - Active ho sakta hai (Scout zaroor karein!)"
        #             
        #         # Yahan Discord channel par alert bhejne ka code aayega jisme ye sab details hongi!
        
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
    print(f'✅ Tracker Bot ({bot.user}) online aa gaya hai!')
    await bot.change_presence(status=discord.Status.online, activity=discord.Game(name="Scanning Map..."))
    
    if not smart_map_scanner.is_running():
        smart_map_scanner.start()

# 🛡️ Shield Timer Command
@bot.command(name="shield")
async def shield(ctx, hours: int):
    if hours <= 0:
        await ctx.send("❌ Bhai, sahi time batao! Jaise: `!shield 8`")
        return
    total_seconds = hours * 3600
    warning_seconds = total_seconds - 900 
    await ctx.send(f"🛡️ {ctx.author.mention}, **{hours} ghante** ki shield set kar di gayi hai. 15 minute pehle alert aa jayega!")
    
    if warning_seconds > 0:
        await asyncio.sleep(warning_seconds)
        try:
            await ctx.author.send(f"🚨 **Cheतावनी:** Bhai! Tumhari shield mein sirf **15 minute** bache hain!")
        except discord.Forbidden:
            await ctx.send(f"🚨 {ctx.author.mention}, tumhari shield 15 minute mein khatam hone wali hai!")
        await asyncio.sleep(900)
    else:
        await asyncio.sleep(total_seconds)
    try:
        await ctx.author.send(f"⚠️ **Alert:** Shield **khatam ho chuki hai!** 🏰")
    except discord.Forbidden:
        await ctx.send(f"⚠️ {ctx.author.mention}, tumhari shield **khatam ho chuki hai!** 🏰")

# ==========================================
# 🏃 Run Bot
# ==========================================
keep_alive()
token = os.environ.get("DISCORD_TOKEN")
if token:
    bot.run(token)
else:
    print("❌ Error: DISCORD_TOKEN environment variable not found")
