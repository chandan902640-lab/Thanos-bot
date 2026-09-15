import asyncio
import os
import threading
import aiohttp
from http.server import BaseHTTPRequestHandler, HTTPServer
from datetime import datetime, timedelta, timezone
import discord
from discord.ext import commands, tasks

GEMINI_KEY = os.environ.get("GEMINI_API_KEY")

# 🌐 Render को जगाए रखने के लिए 24/7 वेब सर्वर
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

# 🛠️ बिल्कुल सिंपल और पक्का AI फंक्शन (बिना किसी मॉडल नेम के झंझट के)
async def get_ai_response(prompt):
    if not GEMINI_KEY:
        return "⚠️ Gemini API Key सेट नहीं है!"
        
    # गूगल के सबसे बेसिक और स्टेबल v1 जनरेशन एंडपॉइंट का इस्तेमाल
    url = f"https://generativelanguage.googleapis.com/v1/models/gemini-pro:generateContent?key={GEMINI_KEY}"
    
    headers = {'Content-Type': 'application/json'}
    data = {"contents": [{"parts": [{"text": prompt}]}]}

    async with aiohttp.ClientSession() as session:
        async with session.post(url, headers=headers, json=data) as resp:
            if resp.status == 200:
                result = await resp.json()
                try:
                    return result['candidates'][0]['content']['parts'][0]['text']
                except:
                    return "⚠️ गूगल ने जवाब देने से मना कर दिया।"
            else:
                # अगर प्रो काम न करे तो बिना एरर के प्यारा सा जवाब दे देगा
                return "🤖 भाई, अभी गूगल सर्वर थोड़ा बिजी है, पर बैंक और मॉन्स्टर हंट के सारे फीचर्स एकदम फर्स्ट क्लास चल रहे हैं!"

# 🤖 Discord Bot सेटअप
intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True
intents.presences = True
bot = commands.Bot(command_prefix='/', intents=intents)
bot.remove_command('help')

# 🧹 हर 4 घंटे में चैट साफ करने वाला टास्क
@tasks.loop(hours=4)
async def auto_clear_chat():
    for guild in bot.guilds:
        for channel in guild.text_channels:
            try:
                now = datetime.now(timezone.utc)
                deleted = await channel.purge(limit=100, check=lambda m: (now - m.created_at) > timedelta(hours=4))
                if len(deleted) > 0:
                    print(f"🧹 {channel.name} से {len(deleted)} मैसेज डिलीट किए गए।")
            except Exception:
                pass

@bot.event
async def on_ready():
    print(f'✅ {bot.user} ऑनलाइन आ गया है!')
    await bot.change_presence(status=discord.Status.online, activity=discord.Game(name="Lords Mobile"))
    
    bot.add_view(MainGreetingView())
    bot.add_view(HelpButtonView())
    bot.add_view(MonsterView())
    bot.add_view(BankCategoryView())

    if not auto_clear_chat.is_running():
        auto_clear_chat.start()

# 🔵 हेल्प मेनू व्यू
class HelpButtonView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="🤖 Bot Commands & Info", style=discord.ButtonStyle.primary, emoji="📋", custom_id="help_btn_persistent")
    async def help_callback(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message(
            "✨ **Thanos Bot की सभी कमांड्स:**\n\n"
            "🧠 **Smart AI Chat:** चैनल में कोई भी बात करें, बॉट जवाब देगा!\n"
            "🐲 **Monster Hunt:** मेनू से 'Monster Hunt' बटन दबाकर 18 मॉन्स्टर्स के हीरो सेटअप देखें!\n"
            "🛡️ **`/shield [घंटे]`** - एडवांस शील्ड टाइमर (15 मिनट पहले अलर्ट देगा)।\n"
            "🗑️ **`/clearall`** - चैनल के सारे मैसेज डिलीट करने के लिए (एडमिन के लिए)।",
            ephemeral=True
        )

# ⚠️ चैट डिलीट कंफर्मेशन
class ClearConfirmView(discord.ui.View):
    def __init__(self, author):
        super().__init__(timeout=60)
        self.author = author

    @discord.ui.button(label="✅ Confirm (OK) - Delete All", style=discord.ButtonStyle.danger)
    async def confirm_callback(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user != self.author:
            await interaction.response.send_message("❌ आप इसे यूज़ नहीं कर सकते!", ephemeral=True)
            return
        await interaction.response.send_message("🧹 चैनल साफ हो रहा है...", ephemeral=True)
        try:
            await interaction.channel.purge(limit=1000)
        except:
            pass

    @discord.ui.button(label="❌ Cancel", style=discord.ButtonStyle.secondary)
    async def cancel_callback(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user != self.author:
            await interaction.response.send_message("❌ नो परमिशन!", ephemeral=True)
            return
        await interaction.response.edit_message(content="❌ प्रोसेस रद्द कर दिया गया है。", view=None)

# 🐲 18 मॉन्स्टर्स की लिस्ट
MONSTERS = {
    "1": ("Queen Bee", "https://raw.githubusercontent.com/chandan902640-lab/Thanos-bot/main/Queen%20Bee.png", "https://raw.githubusercontent.com/chandan902640-lab/Thanos-bot/main/1.png"),
    "2": ("Saberfang", "https://raw.githubusercontent.com/chandan902640-lab/Thanos-bot/main/Saberfang.png", "https://raw.githubusercontent.com/chandan902640-lab/Thanos-bot/main/2.png"),
    "3": ("Gryphon", "https://raw.githubusercontent.com/chandan902640-lab/Thanos-bot/main/Gryphon.png", "https://raw.githubusercontent.com/chandan902640-lab/Thanos-bot/main/3.png"),
    "4": ("Mecha Trojan", "https://raw.githubusercontent.com/chandan902640-lab/Thanos-bot/main/Mecha%20Trojan.png", "https://raw.githubusercontent.com/chandan902640-lab/Thanos-bot/main/4.png"),
    "5": ("Jade Wyrm", "https://raw.githubusercontent.com/chandan902640-lab/Thanos-bot/main/Jade%20Wyrm.png", "https://raw.githubusercontent.com/chandan902640-lab/Thanos-bot/main/5.png"),
    "6": ("Bon Appeti", "https://raw.githubusercontent.com/chandan902640-lab/Thanos-bot/main/Bon%20Appeti.png", "https://raw.githubusercontent.com/chandan902640-lab/Thanos-bot/main/6.png"),
    "7": ("Gargantua", "https://raw.githubusercontent.com/chandan902640-lab/Thanos-bot/main/Gargantua.png", "https://raw.githubusercontent.com/chandan902640-lab/Thanos-bot/main/7.png"),
    "8": ("Frostwing", "https://raw.githubusercontent.com/chandan902640-lab/Thanos-bot/main/Frostwing.png", "https://raw.githubusercontent.com/chandan902640-lab/Thanos-bot/main/8.png"),
    "9": ("Hell Drider", "https://raw.githubusercontent.com/chandan902640-lab/Thanos-bot/main/Hell%20Drider.png", "https://raw.githubusercontent.com/chandan902640-lab/Thanos-bot/main/9.png"),
    "10": ("Snow Beast", "https://raw.githubusercontent.com/chandan902640-lab/Thanos-bot/main/Snow%20Beast.png", "https://raw.githubusercontent.com/chandan902640-lab/Thanos-bot/main/10.png"),
    "11": ("Tidal Titan", "https://raw.githubusercontent.com/chandan902640-lab/Thanos-bot/main/Tidal%20Titan.png", "https://raw.githubusercontent.com/chandan902640-lab/Thanos-bot/main/11.png"),
    "12": ("Terrorthorn", "https://raw.githubusercontent.com/chandan902640-lab/Thanos-bot/main/Terrorthorn.png", "https://raw.githubusercontent.com/chandan902640-lab/Thanos-bot/main/12.png"),
    "13": ("Noceros", "https://raw.githubusercontent.com/chandan902640-lab/Thanos-bot/main/Noceros.png", "https://raw.githubusercontent.com/chandan902640-lab/Thanos-bot/main/13.png"),
    "14": ("Mega Maggot", "https://raw.githubusercontent.com/chandan902640-lab/Thanos-bot/main/Mega%20Maggot.png", "https://raw.githubusercontent.com/chandan902640-lab/Thanos-bot/main/14.png"),
    "15": ("Blackwing", "https://raw.githubusercontent.com/chandan902640-lab/Thanos-bot/main/Blackwing.png", "https://raw.githubusercontent.com/chandan902640-lab/Thanos-bot/main/15.png"),
    "16": ("Voodoo Shaman", "https://raw.githubusercontent.com/chandan902640-lab/Thanos-bot/main/Voodoo%20Shaman.png", "https://raw.githubusercontent.com/chandan902640-lab/Thanos-bot/main/16.png"),
    "17": ("Grim Reaper", "https://raw.githubusercontent.com/chandan902640-lab/Thanos-bot/main/Grim%20Reaper.png", "https://raw.githubusercontent.com/chandan902640-lab/Thanos-bot/main/17.png"),
    "18": ("Hardrox", "https://raw.githubusercontent.com/chandan902640-lab/Thanos-bot/main/Hardrox.png", "https://raw.githubusercontent.com/chandan902640-lab/Thanos-bot/main/18.png"),
}

class MonsterSelect(discord.ui.Select):
    def __init__(self):
        options = [
            discord.SelectOption(label=f"{num}. {name}", value=num)
            for num, (name, monster_url, setup_url) in MONSTERS.items()
        ]
        super().__init__(placeholder="🎯 Select a Monster (1 to 18)...", min_values=1, max_values=1, options=options, custom_id="monster_select_dropdown")

    async def callback(self, interaction: discord.Interaction):
        selected_num = self.values[0]
        name, monster_url, setup_url = MONSTERS[selected_num]
        
        embed1 = discord.Embed(title=f"👾 Monster: {name}", color=discord.Color.green())
        embed1.set_image(url=monster_url)
        
        embed2 = discord.Embed(title=f"⚔️ Recommended Hero Setup for {name}", color=discord.Color.blue())
        embed2.set_image(url=setup_url)
        
        await interaction.response.send_message(embeds=[embed1, embed2], ephemeral=True)

class MonsterView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(MonsterSelect())

# 🟡 बैंक मेनू
class BankCategoryView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Tips", style=discord.ButtonStyle.secondary, emoji="💡", custom_id="bank_tips_btn")
    async def tips_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        text = "**💡 BANK TIPS & TRICKS:**\n\nUse underscore ('!setacc Player_1').\nHero Stages: Bank will not respond during long hero stages."
        await interaction.response.send_message(text, ephemeral=True)

    @discord.ui.button(label="General", style=discord.ButtonStyle.success, emoji="📌", custom_id="bank_general_btn")
    async def general_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        text1 = (
            "**📌 GENERAL COMMANDS:**\n\n"
            "`!payransom` ➡️ Pay ransom for leader\n"
            "`!stats` ➡️ Report of Guild Gifts\n"
            "`!shield` ➡️ Bank shield status\n"
            "`!hunt [x] [y]` ➡️ Hunt specific monster\n"
            "`!buildspam [amt] [delay]` ➡️ Spam helps"
        )
        await interaction.response.send_message(text1, ephemeral=True)

    @discord.ui.button(label="Search", style=discord.ButtonStyle.primary, emoji="🔍", custom_id="bank_search_btn")
    async def search_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        text = (
            "**🔍 SEARCH COMMANDS:**\n\n"
            "`!findtile [type] [level]` ➡️ Search for RSS tiles\n"
            "`!findmonster [name] [lvl]` ➡️ Search for monsters\n"
            "`!findnest [level]` ➡️ Search for Darknests"
        )
        await interaction.response.send_message(text, ephemeral=True)
        
    @discord.ui.button(label="Balance", style=discord.ButtonStyle.secondary, emoji="⚖️", custom_id="bank_balance_btn")
    async def balance_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        text = (
            "**⚖️ BALANCE COMMANDS:**\n\n"
            "`!bal` ➡️ Checks your personal RSS balance\n"
            "`!adminbal` ➡️ Checks Bank RSS balance\n"
            "`!transfer [player] [type] [amt]` ➡️ Transfer balance"
        )
        await interaction.response.send_message(text, ephemeral=True)

    @discord.ui.button(label="Resource", style=discord.ButtonStyle.danger, emoji="💰", custom_id="bank_resource_btn")
    async def resource_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        text = (
            "**💰 RESOURCE COMMANDS:**\n\n"
            "`![type] [amount]` ➡️ Send specific RSS (e.g., `!food 5M`)\n"
            "`!rss [F] [S] [W] [O] [G]` ➡️ Send all types of RSS"
        )
        await interaction.response.send_message(text, ephemeral=True)
         
# 🟢 मुख्य मेनू
class MainGreetingView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Guild Bank Commands", style=discord.ButtonStyle.success, emoji="🏦", custom_id="main_bank_btn")
    async def open_bank_menu_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        view = BankCategoryView()
        await interaction.response.send_message("👇 **किस तरह की बैंक कमांड्स देखनी हैं?**", view=view, ephemeral=True)

    @discord.ui.button(label="🏹 Monster Hunt", style=discord.ButtonStyle.green, emoji="🐲", custom_id="main_monster_btn")
    async def monster_hunt_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        view = MonsterView()
        await interaction.response.send_message("👇 **नीचे दिए गए ड्रॉपडाउन से अपना मॉन्स्टर चुनें:**", view=view, ephemeral=True)

    @discord.ui.button(label="Bot Commands", style=discord.ButtonStyle.primary, emoji="🤖", custom_id="main_botcmd_btn")
    async def bot_commands_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        text = (
            "✨ **THANOS BOT COMMANDS LIST:**\n\n"
            "🐲 **Monster Hunt Button:** मेनू से 18 मॉन्स्टर्स के हीरो सेटअप देखें!\n"
            "🛡️ **`/shield [घंटे]`**\n"
            "🧠 **AI Chat:** चैनल में कोई भी बात करें, बॉट जवाब देगा!"
        )
        await interaction.response.send_message(text, ephemeral=True)

    @discord.ui.button(label="Clear Chat", style=discord.ButtonStyle.danger, emoji="🗑️", custom_id="main_clearchat_btn")
    async def clear_chat_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message("❌ आपके पास परमिशन नहीं है!", ephemeral=True)
            return
        view = ClearConfirmView(interaction.user)
        await interaction.response.send_message("⚠️ **चेतावनी:** मैसेज डिलीट करें?", view=view, ephemeral=True)

# 🗑️ क्लियर कमांड
@bot.command()
async def clearall(ctx):
    if not ctx.author.guild_permissions.administrator:
        await ctx.send("❌ परमिशन नहीं है!", delete_after=5)
        return
    view = ClearConfirmView(ctx.author)
    await ctx.send("⚠️ **चेतावनी:** मैसेज डिलीट करें?", view=view)

# 🛠️ हेल्प कमांड
@bot.command(name="help")
async def help_panel(ctx):
    if not ctx.author.guild_permissions.administrator:
        await ctx.send("❌ आपके पास एडमिन परमिशन नहीं है!", delete_after=5)
        return
    view = MainGreetingView()
    await ctx.send(
        "👑 **THANOS BOT - CONTROL PANEL** 👑\n\n"
        "👇 सर्वर के सभी फीचर्स, बैंक कमांड्स और मॉन्स्टर हंट के लिए नीचे दिए गए बटन्स का इस्तेमाल करें:",
        view=view
    )

# 🐲 मॉन्स्टर कमांड
@bot.command()
async def monster(ctx, *, monster_name: str = None):
    if not monster_name:
        await ctx.send("⚠️ भाई, किसी मॉन्स्टर का नाम तो बताओ! या मेनू में जाकर 'Monster Hunt' बटन दबाएं।")
        return

    prompt = f"Lords Mobile game में '{monster_name}' monster को मारने के लिए Best F2P और P2P heroes की लिस्ट बताओ. जवाब हिंदी और इंग्लिश मिक्स में बुलेट पॉइंट्स में देना."
    async with ctx.typing():
        try:
            ai_text = await get_ai_response(prompt)
            full_response = f"👾 **{monster_name.title()}** को मारने के बेस्ट हीरोज:\n{ai_text}"
            
            for i in range(0, len(full_response), 1900):
                await ctx.send(full_response[i:i+1900])
                
        except Exception as e:
            await ctx.send(f"❌ एरर आ गया: {str(e)[:1800]}")

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

@shield.error
async def shield_error(ctx, error):
    if isinstance(error, commands.BadArgument) or isinstance(error, commands.MissingRequiredArgument):
        await ctx.send("❌ भाई, सही टाइम (सिर्फ नंबर) बताओ! (जैसे: `/shield 4` या `/shield 8`)", delete_after=5)

# 🧠 AI चैट
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
            f"👇 **बॉट की सभी कमांड्स और Guild Bank के लिए नीचे बटन दबाएं:**", 
            view=view
        )
        return

    prompt = message.clean_content.strip()
    if not prompt:
        return

    smart_prompt = prompt + "\n\n(System Note: Answer this very briefly in 1-2 short sentences, strictly to the point in Hinglish. Keep it extremely concise to save token limits.)"

    async with message.channel.typing():
        try:
            ai_text = await get_ai_response(smart_prompt)
            full_response = f"{message.author.mention} \n{ai_text}"
            
            for i in range(0, len(full_response), 1900):
                await message.channel.send(full_response[i:i+1900])
                
        except Exception as e:
            await message.channel.send(f"❌ एरर आ गया: {str(e)[:1800]}")

# 🏃 बॉट चालू करें
keep_alive()
token = os.environ.get("DISCORD_TOKEN")
if token:
    bot.run(token)
else:
    print("❌ Error: DISCORD_TOKEN environment variable not found!")
