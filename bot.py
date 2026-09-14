import asyncio
import os
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from datetime import datetime, timedelta, timezone
import discord
from discord.ext import commands, tasks
import google.generativeai as genai

# Gemini AI सेटअप
GEMINI_KEY = os.environ.get("GEMINI_API_KEY")
if GEMINI_KEY:
    genai.configure(api_key=GEMINI_KEY)
    ai_model = genai.GenerativeModel('gemini-pro')
else:
    ai_model = None

# यह डमी वेबसाइट है ताकि Render इसे 24/7 ऑनलाइन रख सके
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
intents.presences = True  # 🟢 ऑनलाइन स्टेटस दिखाने के लिए
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
    await bot.change_presence(
        status=discord.Status.online,
        activity=discord.Game(name="Lords Mobile")
    )
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
            "🧠 **Gemini AI Chat:** बॉट को टैग करके (`@Thanos Bot`) इससे कुछ भी सवाल पूछ सकते हैं!\n"
            "🛡️ `/shield [घंटे]` - गेम के लिए शील्ड टाइमर सेट करता है।\n"
            "🗑️ `/clearall` - चैनल के सारे मैसेज डिलीट करने के लिए (बटन के साथ)।\n"
            "📋 `/helpmenu` - हेल्प मेनू मंगाने के लिए।\n"
            "🧹 **Auto-Cleanup** - हर 4 घंटे में पुराने मैसेज अपने आप साफ़ होते हैं!",
            ephemeral=True
        )

@bot.command()
async def helpmenu(ctx):
    view = HelpButtonView()
    await ctx.send("👇 नीचे दिए गए **नीले बटन** पर क्लिक करके देखें कि कौन सी कमांड क्या करती है!", view=view)

# ⚠️ चैट डिलीट करने के लिए कंफर्मेशन बटन व्यू
class ClearConfirmView(discord.ui.View):
    def __init__(self, ctx):
        super().__init__(timeout=60)
        self.ctx = ctx

    @discord.ui.button(label="✅ Confirm (OK) - Delete All", style=discord.ButtonStyle.danger)
    async def confirm_callback(self, interaction: discord.Interaction, button: discord.ui.Button):
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

@bot.command()
async def clearall(ctx):
    if not ctx.author.guild_permissions.administrator:
        await ctx.send("❌ आपके पास इस कमांड को चलाने की परमिशन नहीं है!", delete_after=5)
        return
    
    view = ClearConfirmView(ctx)
    await ctx.send("⚠️ **चेतावनी:** क्या आप इस चैनल के सारे मैसेज डिलीट करना चाहते हैं? पुष्टि करने के लिए नीचे दिए गए **Confirm (OK)** बटन पर क्लिक करें:", view=view)

# 🧠 Gemini AI चैट और मजबूत मेंशन चेक फीचर
@bot.event
async def on_message(message):
    if message.author == bot.user:
        return

    # बॉट को टैग किया गया है या नहीं, इसे चेक करने का पक्का तरीका
    is_mentioned = bot.user in message.mentions or f"<@{bot.user.id}>" in message.content or f"<@!{bot.user.id}>" in message.content

    if is_mentioned:
        if not ai_model:
            await message.channel.send("⚠️ Gemini API Key सेट नहीं है भाई! कृपया Render में `GEMINI_API_KEY` जोड़ें।")
            return

        # मैसेज से बॉट का टैग हटाकर सिर्फ सवाल निकालें
        prompt = message.content.replace(f'<@!{bot.user.id}>', '').replace(f'<@{bot.user.id}>', '').strip()
        
        if prompt:
            async with message.channel.typing():
                try:
                    response = ai_model.generate_content(prompt)
                    await message.channel.send(f"{message.author.mention} \n{response.text}")
                except Exception as e:
                    await message.channel.send(f"❌ कुछ गड़बड़ हो गई: {e}")
        else:
            await message.channel.send(f"हाँ भाई {message.author.mention}! बताइए, मुझसे क्या पूछना चाहते हैं?")
        return

    # सामान्य बातचीत के लिए
    words = message.content.lower().split()
    if words:
        if any(w in words for w in ["hi", "hii", "hello", "hey", "namaste"]):
            await message.channel.send(f"Hello / नमस्ते {message.author.mention}! 👋 मुझे कुछ भी पूछने के लिए मुझे टैग करें (जैसे `@Thanos Bot सवाल`)।")
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
