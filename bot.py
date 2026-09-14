import discord
from discord.ext import commands
import asyncio
import os
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

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
bot = commands.Bot(command_prefix='!', intents=intents)

@bot.event
async def on_ready():
    print(f'✅ {bot.user} ऑनलाइन आ गया है!')

@bot.command()
async def shield(ctx, hours: int):
    await ctx.send(f"🛡️ {ctx.author.mention}, मैंने {hours} घंटे का शील्ड टाइमर सेट कर दिया है।")
    await asyncio.sleep(hours * 3600) 
    await ctx.send(f"⚠️ {ctx.author.mention}, आपका शील्ड खत्म होने वाला है! तुरंत गेम चेक करें।")

# डमी वेबसाइट चालू करें और फिर बॉट रन करें
keep_alive()
token = os.environ.get("DISCORD_TOKEN")
bot.run(token)
