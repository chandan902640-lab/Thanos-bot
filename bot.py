import asyncio
import os
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from datetime import datetime, timedelta, timezone
import discord
from discord.ext import commands, tasks
from google import genai

# Gemini AI सेटअप
GEMINI_KEY = os.environ.get("GEMINI_API_KEY")
if GEMINI_KEY:
    ai_client = genai.Client(api_key=GEMINI_KEY)
else:
    ai_client = None

# Render और UptimeRobot के लिए 24/7 वेब सर्वर
class DummyHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/plain')
        self.end_headers()
        self.wfile.write(b"Thanos Bot is online and running 24/7!")

    def do_HEAD(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/plain')
        self.end_headers()

def keep_alive():
    port = int(os.environ.get("PORT", 8080))
    server = HTTPServer(('0.0.0.0', port), DummyHandler)
    threading.Thread(target=server.serve_forever, daemon=True).start()

intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True
intents.presences = True
bot = commands.Bot(command_prefix='/', intents=intents)

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
    await bot.change_presence(status=discord.Status.online, activity=discord.Game(name="Lords Mobile"))
    if not auto_clear_chat.is_running():
        auto_clear_chat.start()

# 🔵 हेल्प मेनू व्यू
class HelpButtonView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="🤖 Bot Commands & Info", style=discord.ButtonStyle.primary, emoji="📋")
    async def help_callback(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message(
            "✨ **Thanos Bot की सभी कमांड्स और फीचर्स:**\n\n"
            "🧠 **Smart AI Chat:** चैनल में कोई भी सवाल पूछें, बॉट अपने आप जवाब देगा (बिना टैग किए)!\n"
            "🐲 **`/monster [नाम]`** - किसी भी मॉन्स्टर के F2P और P2P हीरोज पता करें।\n"
            "🛡️ **`/shield [घंटे]`** - एडवांस शील्ड टाइमर (15 मिनट पहले प्राइवेट DM में अलर्ट देगा)।\n"
            "🗑️ **`/clearall`** - चैनल के सारे मैसेज डिलीट करने के लिए (सिर्फ एडमिन के लिए)।\n"
            "📋 **`/helpmenu`** - यह हेल्प मेनू मंगाने के लिए।\n"
            "🧹 **Auto-Cleanup:** हर 4 घंटे में पुराने मैसेज अपने आप साफ़ होते हैं!",
            ephemeral=True
        )

@bot.command()
async def helpmenu(ctx):
    view = HelpButtonView()
    await ctx.send("👇 नीचे दिए गए **नीले बटन** पर क्लिक करके देखें कि कौन सी कमांड क्या करती है!", view=view)

# ⚠️ चैट डिलीट करने के लिए कंफर्मेशन बटन व्यू
class ClearConfirmView(discord.ui.View):
    def __init__(self, author):
        super().__init__(timeout=60)
        self.author = author

    @discord.ui.button(label="✅ Confirm (OK) - Delete All", style=discord.ButtonStyle.danger)
    async def confirm_callback(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user != self.author:
            await interaction.response.send_message("❌ आप इस बटन का उपयोग नहीं कर सकते!", ephemeral=True)
            return
        await interaction.response.send_message("🧹 चैनल के मैसेज साफ किए जा रहे हैं...", ephemeral=True)
        try:
            deleted = await interaction.channel.purge(limit=1000)
            print(f"🧹 {interaction.channel.name} से {len(deleted)} मैसेज डिलीट किए गए।")
        except Exception as e:
            await interaction.channel.send(f"❌ एरर आ गया: {str(e)[:1800]}", delete_after=5)

    @discord.ui.button(label="❌ Cancel", style=discord.ButtonStyle.secondary)
    async def cancel_callback(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user != self.author:
            await interaction.response.send_message("❌ आप इस बटन का उपयोग नहीं कर सकते!", ephemeral=True)
            return
        await interaction.response.edit_message(content="❌ चैट डिलीट करने का प्रोसेस रद्द कर दिया गया है。", view=None)

# 🟡 बैंक मेनू
class BankCategoryView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Tips", style=discord.ButtonStyle.secondary, emoji="📝")
    async def tips_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        text = "**💡 BANK TIPS & TRICKS:**\n\n• Use underscore (`!setacc Player_1`).\n• Hero Stages: Bank will not respond during long hero stages."
        await interaction.response.send_message(text, ephemeral=True)

    @discord.ui.button(label="General", style=discord.ButtonStyle.success, emoji="📌")
    async def general_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        text = "**📌 GENERAL COMMANDS:**\n"`!payransom` ➡️ The ransom for the accounts leader is paid\n"
        "`!payransom` ➡️ The ransom for the accounts leader is paid\n"
        await interaction.response.send_message(text, ephemeral=True)

    @discord.ui.button(label="Search", style=discord.ButtonStyle.primary, emoji="🔍")
    async def search_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        text = "**🔍 SEARCH COMMANDS:**\nTiles: `!findtile food 4`\nMonsters: `!findmonster hardrox 2`\nDarknests: `!findnest 5`"
        await interaction.response.send_message(text, ephemeral=True)

    @discord.ui.button(label="Balance", style=discord.ButtonStyle.secondary, emoji="⚖️")
    async def balance_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        text = "**⚖️ BALANCE COMMANDS:**\n`!bal`, `!adminbal`, `!setbal`, `!transfer`"
        await interaction.response.send_message(text, ephemeral=True)

    @discord.ui.button(label="Resource", style=discord.ButtonStyle.danger, emoji="🌾")
    async def resource_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        text = "**🌾 RESOURCE COMMANDS:**\n`!food 5M`, `!rss 5M 5M 5M 5M 0`, `!donatefood Shark 5M`"
        await interaction.response.send_message(text, ephemeral=True)

# 🟢 मुख्य मेनू
class MainGreetingView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Guild Bank Commands", style=discord.ButtonStyle.success, emoji="🏦")
    async def open_bank_menu_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        view = BankCategoryView()
        await interaction.response.send_message("👇 **किस तरह की बैंक कमांड्स देखनी हैं?**", view=view, ephemeral=True)

    @discord.ui.button(label="Bot Commands", style=discord.ButtonStyle.primary, emoji="🤖")
    async def bot_commands_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        text = (
            "✨ **THANOS BOT COMMANDS LIST:**\n\n"
            "🐲 **`/monster [नाम]`**\n"
            "🛡️ **`/shield [घंटे]`**\n"
            "🧠 **AI Chat:** अब चैनल में कोई भी सवाल पूछें, बॉट तुरंत जवाब देगा!"
        )
        await interaction.response.send_message(text, ephemeral=True)

    @discord.ui.button(label="Clear Chat", style=discord.ButtonStyle.danger, emoji="🗑️")
    async def clear_chat_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message("❌ आपके पास परमिशन नहीं है!", ephemeral=True)
            return
        view = ClearConfirmView(interaction.user)
        await interaction.response.send_message("⚠️ **चेतावनी:** मैसेज डिलीट करें?", view=view, ephemeral=True)

@bot.command()
async def clearall(ctx):
    if not ctx.author.guild_permissions.administrator:
        await ctx.send("❌ परमिशन नहीं है!", delete_after=5)
        return
    view = ClearConfirmView(ctx.author)
    await ctx.send("⚠️ **चेतावनी:** मैसेज डिलीट करें?", view=view)

# 🐲 मॉन्स्टर कमांड
@bot.command()
async def monster(ctx, *, monster_name: str = None):
    if not monster_name:
        await ctx.send("⚠️ भाई, किसी मॉन्स्टर का नाम तो बताओ!")
        return
    if not ai_client:
        await ctx.send("⚠️ Gemini API Key सेट नहीं है!")
        return

    prompt = f"Lords Mobile game में '{monster_name}' monster को मारने के लिए Best F2P और P2P heroes की लिस्ट बताओ. जवाब हिंदी और इंग्लिश मिक्स में बुलेट पॉइंट्स में देना."
    async with ctx.typing():
        try:
            response = ai_client.models.generate_content(
                model='gemini-3.6-flash',
                contents=prompt,
            )
            full_response = f"👾 **{monster_name.title()}** को मारने के बेस्ट हीरोज:\n{response.text}"
            
            for i in range(0, len(full_response), 1900):
                await ctx.send(full_response[i:i+1900])
                
        except Exception as e:
            error_msg = str(e)[:1800]
            await ctx.send(f"❌ गूगल सर्वर एरर या बिजी: {error_msg}")

# 🛡️ शील्ड कमांड
@bot.command()
async def shield(ctx, hours: int):
    if hours <= 0:
        await ctx.send("❌ भाई, सही टाइम बताओ! (जैसे 4, 8, 24)")
        return
    total_seconds = hours * 3600
    warning_seconds = total_seconds - 900 
    await ctx.send(f"🛡️ {ctx.author.mention}, मैंने **{hours} घंटे** का शील्ड टाइमर सेट कर दिया है। 15 मिनट पहले अलर्ट आ जाएगा! ⏰")

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


# 🧠 AI चैट (SMART FILTER - लिमिट बचाएगा और छोटा जवाब देगा)
@bot.event
async def on_message(message):
    if message.author.bot:
        return

    await bot.process_commands(message)

    if message.content.startswith('/') or message.content.startswith('!'):
        return

    msg_lower = message.content.lower().strip()
    if not msg_lower:
        return

    words = msg_lower.split()
    if len(words) <= 2 and any(w in words for w in ["hi", "hii", "hello", "hey", "namaste"]):
        view = MainGreetingView()
        await message.channel.send(
            f"Hello / नमस्ते {message.author.mention}! 👋 \n"
            f"👇 **बॉट की सभी कमांड्स और Guild Bank** के लिए नीचे बटन दबाएं:", 
            view=view
        )
        return

    # --- SMART FILTER: सिर्फ तभी रिप्लाई करेगा जब सवाल हो या नाम लिया जाए ---
    question_keywords = ["kya", "kaise", "kyu", "kyon", "batao", "kaun", "kab", "kaha", "how", "what", "why", "where", "help"]
    
    # चेक करेगा कि मैसेज में कोई सवाल वाला शब्द है, या '?' है, या बॉट का नाम है
    is_question = any(word in words for word in question_keywords) or "?" in msg_lower
    is_mentioned = "thanos" in msg_lower or "thanod" in msg_lower or bot.user in message.mentions

    # अगर न सवाल है, न नाम लिया है, तो बॉट चुपचाप मैसेज को इग्नोर कर देगा (API लिमिट बचेगी!)
    if not (is_question or is_mentioned):
        return

    if not ai_client:
        await message.channel.send("⚠️ Gemini API Key सेट नहीं है!")
        return

    prompt = message.clean_content.strip()
    for word in ["@Thanos bot", "@Thanos Bot", "Thanos bot", "thanos bot", "thanod bot", "Thanos", "thanos", "thanod"]:
        prompt = prompt.replace(word, "").strip()

    if not prompt:
        await message.channel.send(f"हाँ भाई {message.author.mention}! बताइए, मुझसे क्या पूछना चाहते हैं?")
        return

    # AI को हिडन कमांड: जवाब छोटा और सटीक दो!
    smart_prompt = prompt + "\n\n(System Note: Answer this very briefly and strictly to the point in Hinglish. Do not write long paragraphs. Give only necessary information.)"

    async with message.channel.typing():
        try:
            response = ai_client.models.generate_content(
                model='gemini-3.6-flash',
                contents=smart_prompt,
            )
            full_response = f"{message.author.mention} \n{response.text}"
            
            for i in range(0, len(full_response), 1900):
                await message.channel.send(full_response[i:i+1900])
                
        except Exception as e:
            error_msg = str(e)[:1800]
            await message.channel.send(f"❌ गूगल सर्वर बिजी है, 1 मिनट बाद पूछें: {error_msg}")

# बॉट चालू करें
keep_alive()
token = os.environ.get("DISCORD_TOKEN")
if token:
    bot.run(token)
else:
    print("❌ Error: DISCORD_TOKEN environment variable not found!")
