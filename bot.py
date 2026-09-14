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

# 🔵 नीले रंग के बटन वाला हेल्प मेनू
class HelpButtonView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="🤖 Bot Commands & Info", style=discord.ButtonStyle.primary, emoji="📋")
    async def help_callback(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message(
            "✨ **Thanos Bot की सभी कमांड्स और फीचर्स:**\n\n"
            "🛡️ `/shield [घंटे]` - गेम के लिए शील्ड टाइमर सेट करता है (जैसे `/shield 1`)।\n"
            "🗑️ `/clearall` - इस चैनल के सारे मैसेज एक साथ डिलीट करने के लिए (बटन के साथ)।\n"
            "📋 `/helpmenu` - यह हेल्प मेनू दोबारा मंगाने के लिए।\n"
            "💬 `Hi / Hello` - बॉट से बातचीत करने के लिए।\n"
            "🧹 **Auto-Cleanup** - हर 4 घंटे में पुराने मैसेज अपने आप साफ़ होते हैं!",
            ephemeral=True
        )

@bot.command()
async def helpmenu(ctx):
    view = HelpButtonView()
    await ctx.send("👇 नीचे दिए गए **नीले बटन** पर क्लिक करके देखें कि कौन सी कमांड क्या करती है!", view=view)

# ⚠️ चैट डिलीट करने के लिए कंफर्मेशन बटन व्यू (सिर्फ कमांड चलाने वाला ही क्लिक कर पाएगा)
class ClearConfirmView(discord.ui.View):
    def __init__(self, ctx):
        super().__init__(timeout=60)
        self.ctx = ctx

    @discord.ui.button(label="✅ Confirm (OK) - Delete All", style=discord.ButtonStyle.danger)
    async def confirm_callback(self, interaction: discord.Interaction, button: discord.ui.Button):
        # जाँच करें कि क्या बटन दबाने वाला वही व्यक्ति है जिसने कमांड चलाई थी
        if interaction.user != self.ctx.author:
            await interaction.response.send_message("❌ आप इस बटन का उपयोग नहीं कर सकते!", ephemeral=True)
            return
        
        await interaction.response.send_message("🧹 चैनल के मैसेज साफ किए जा रहे हैं...", ephemeral=True)
        try:
            deleted = await self.ctx.channel.purge(limit=1000)
            print(f"🧹 {self.ctx.channel.name} से {len(deleted)} मैसेज डिलीट किए गए।")
        except Exception as e:
            await self.ctx.send(f"❌ एरर आ गया: {e}", delete_after=5)

    @discord.ui.button(label="❌ Cancel", style=discord.ButtonStyle.secondary)
    async def cancel_callback(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user != self.ctx.author:
            await interaction.response.send_message("❌ आप इस बटन का उपयोग नहीं कर सकते!", ephemeral=True)
            return
        await interaction.response.edit_message(content="❌ चैट डिलीट करने का प्रोसेस रद्द कर दिया गया है।", view=None)

# 🗑️ नया कमांड: /clearall
@bot.command()
async def clearall(ctx):
    # सुरक्षा जाँच: इसे सिर्फ एडमिन या बॉट का मालिक ही चला सकता है
    if not ctx.author.guild_permissions.administrator:
        await ctx.send("❌ आपके पास इस कमांड को चलाने की परमिशन नहीं है!", delete_after=5)
        return
    
    view = ClearConfirmView(ctx)
    await ctx.send("⚠️ **चेतावनी:** क्या आप इस चैनल के सारे मैसेज डिलीट करना चाहते हैं? पुष्टि करने के लिए नीचे दिए गए **Confirm (OK)** बटन पर क्लिक करें:", view=view)

# स्मार्ट चैट फीचर
@bot.event
async def on_message(message):
    if message.author == bot.user:
        return

    words = message.content.lower().split()
    if not words:
        await bot.process_commands(message)
        return

    if any(w in words for w in ["hi", "hii", "hello", "hey", "namaste"]):
        await message.channel.send(f"Hello / नमस्ते {message.author.mention}! 👋 बताइए भाई, आज क्या मदद चाहिए? (कमांड देखने के लिए `/helpmenu` टाइप करें)")

    elif any(w in words for w in ["kaise", "haal", "how"]):
        await message.channel.send(f"मैं एकदम फर्स्ट क्लास हूँ {message.author.mention}! 🤖 आप सुनाओ, Lords Mobile कैसा चल रहा है?")

    elif any(w in words for w in ["code", "command", "commands"]):
        await message.channel.send(f"💻 भाई, सभी कमांड्स देखने के लिए `/helpmenu` टाइप करें!")

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
