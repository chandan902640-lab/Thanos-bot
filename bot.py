import asyncio
import os
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from datetime import datetime, timedelta, timezone
import discord
from discord.ext import commands, tasks

# यह डमी सर्वर है ताकि Render को लगे कि यह एक वेबसाइट है
class DummyHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/plain')
        self.end_headers()
        self.wfile.write(b"Bot is running 24/7")

def keep_alive():
    port = int(os.environ.get("PORT", 8080))
    server = HTTPServer(('0.0.0.0', port), DummyHandler)
    threading.Thread(target=server.serve_forever, daemon=True).start()

intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True
bot = commands.Bot(command_prefix='/', intents=intents)

# हर 4 घंटे में पुराने मैसेज डिलीट करने वाला लूप
@tasks.loop(hours=4)
async def auto_clear_chat():
    for guild in bot.guilds:
        for channel in guild.text_channels:
            try:
                now = datetime.now(timezone.utc)
                deleted = await channel.purge(limit=100, check=lambda m: (now - m.created_at) > timedelta(hours=4))
                if len(deleted) > 0:
                    print(f"🧹 {channel.name} से {len(deleted)} पुराने मैसेज डिलीट कर दिए गए।")
            except Exception as e:
                print(f"Error in {channel.name}: {e}")

@bot.event
async def on_ready():
    print(f'✅ {bot.user} ऑनलाइन आ गया है!')
    await bot.change_presence(activity=discord.Game(name="Lords Mobile"))
    if not auto_clear_chat.is_running():
        auto_clear_chat.start()

# 🌍 मल्टी-लैंग्वेज चैट फीचर (हिंदी और अंग्रेजी दोनों के लिए)
@bot.event
async def on_message(message):
    if message.author == bot.user:
        return

    msg = message.content.lower()

    # अगर कोई हेलो या नमस्ते कहे
    if any(word in msg for in ["hi", "hii", "hello", "hey", "namaste"]):
        await message.channel.send(f"Hello / नमस्ते {message.author.mention}! 👋 How can I help you today? / बोलिए, कैसे मदद कर सकता हूँ?")

    # अगर कोई हालचाल पूछे (English या Hindi में)
    elif any(word in msg for word in ["kaise ho", "how are you", "kya haal"]):
        await message.channel.send(f"I'm doing great {message.author.mention}! 🤖 मैं एकदम मस्त हूँ। Lords Mobile कैसा चल रहा है?")

    await bot.process_commands(message)

@bot.command()
async def shield(ctx, hours: int):
    await ctx.send(f"🛡️ {ctx.author.mention}, मैंने {hours} घंटे का शील्ड टाइमर सेट कर दिया है।")
    await asyncio.sleep(hours * 3600) 
    await ctx.send(f"⚠️ {ctx.author.mention}, आपका शील्ड खत्म होने वाला है! तुरंत गेम चेक करें।")

# डमी वेबसाइट चालू करें और फिर बॉट रन करें
keep_alive()
token = os.environ.get("DISCORD_TOKEN")
bot.run(token)
