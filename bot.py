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
            "🧠 **Gemini AI Chat:** बॉट को टैग करके (`@Thanos Bot`) इससे कुछ भी सवाल पूछ सकते हैं!\n"
            "🐲 **`/monster [नाम]`** - किसी भी मॉन्स्टर के F2P और P2P हीरोज पता करें (उदा. `/monster hardrox`)\n"
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
            await interaction.channel.send(f"❌ एरर आ गया: {e}", delete_after=5)

    @discord.ui.button(label="❌ Cancel", style=discord.ButtonStyle.secondary)
    async def cancel_callback(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user != self.author:
            await interaction.response.send_message("❌ आप इस बटन का उपयोग नहीं कर सकते!", ephemeral=True)
            return
        await interaction.response.edit_message(content="❌ चैट डिलीट करने का प्रोसेस रद्द कर दिया गया है。", view=None)

# 🟡 अंदर खुलने वाला 5 बटन का मेनू (Bank Categories)
class BankCategoryView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Tips", style=discord.ButtonStyle.secondary, emoji="📝")
    async def tips_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        text = "**💡 BANK TIPS & TRICKS:**\n\n• **Space in name?** Use underscore (`!setacc Player_1`) OR quotes (`!setacc \"Player 1\"`).\n• **Authorized users:** Balances are non-deductible (Unlimited). They cannot use Donate.\n• **R4 Access:** By default, R4+ have similar access to Authorized users.\n• **Hero Stages:** Bank will not respond during long hero stages. Set custom chapter, 3☆, and use Sweep x10."
        await interaction.response.send_message(text, ephemeral=True)

    @discord.ui.button(label="General", style=discord.ButtonStyle.success, emoji="📌")
    async def general_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        text = "**📌 GENERAL COMMANDS:**\n`!pos` - Bank location | `!shield` / `!shield deploy` - Shield bank\n`!relocate [X] [Y]` / `!relocate rand` / `!migrate [K][X][Y]` - Relocate bank\n`!buildspam [amount] [delay]` / `!buildspam stop` - Spam GF helps\n`!hunt [x] [y]` / `!hunt [on/off]` - Monster hunting\n`!payransom` - Pay leader ransom | `!clearboard` - Clear GF board\n`!stats` / `!stats all` / `!pstats [name]` - Gift statistics\n`!gryphon` / `!snowbeast` - Familiar skills\n`!whitelist [name] [Rank]` / `!blacklist [name]` - Manage members\n`!addtitle [name] [title]` / `!deltitle [title]` - Manage titles\n`!purge` - Clear chat | `!abort` - Abort RSS shipments\n`!yell [msg]` - Write in chat | `!quest` - GF status | `!guild [tag]` - Change guild\n`!recall` - Recall troops | `!camp [x] [y]` - Send camp\n`!setgather [on/off]` - Gathering | `!stop [time]` - Offline\n`!reloadacc` / `!members` / `!resetstats` - Refresh & Reset\n**Events:** `!joingvg`, `!joinca`, `!joinda`"
        await interaction.response.send_message(text, ephemeral=True)

    @discord.ui.button(label="Search", style=discord.ButtonStyle.primary, emoji="🔍")
    async def search_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        text = "**🔍 SEARCH COMMANDS**\n*(Tip: Write `chat` at the end to post result in guild. Radius: ~70 tiles)*\n\n**Tiles:**\n`!findtile [type] [level]` - e.g. `!findtile food 4`\n`!findtile any [level]` - Find any tile\n`!findtilelocal [type] [level]` - Find tile around YOU\n\n**Monsters:**\n`!findmonster [name] [level]` - e.g. `!findmonster hardrox 2`\n`!findmonster any [level]` - Find any monster\n`!findmonsterlocal [name] [level]` - Find monster around YOU\n\n**Darknests:**\n`!findnest [level]` - Find darknest near bank\n`!findnestlocal [level]` - Find darknest near YOU"
        await interaction.response.send_message(text, ephemeral=True)

    @discord.ui.button(label="Balance", style=discord.ButtonStyle.secondary, emoji="⚖️")
    async def balance_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        text = "**⚖️ BALANCE COMMANDS:**\n`!bal` - Checks your balance sent to the bank\n`!adminbal [player]` - Check player's balance (e.g. `!adminbal Shark`)\n`!adminbal` / `!adminbag` - Checks Bank's RSS balance / Bag balance\n`!setbal [player] [type] [amount]` - Manually sets RSS balance\n`!setacc [player]` - Credit your sent RSS to another account\n`!transfer [player] [type] [amount]` - Transfer balance to another player\n`!setrsslimit [type] [amount]` - Sets a limit bank won't go below"
        await interaction.response.send_message(text, ephemeral=True)

    @discord.ui.button(label="Resource", style=discord.ButtonStyle.danger, emoji="🌾")
    async def resource_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        text = "**🌾 RESOURCE COMMANDS:**\n`![type] [amount]` - Sends specific RSS (e.g. `!food 5M`)\n`!rss [F] [S] [W] [O] [G]` - Sends all RSS (e.g. `!rss 5M 5M 5M 5M 0`)\n`!donate[type] [player] [amount]` - Sends RSS to specific player (e.g. `!donatefood Shark 5M`)\n`!admin[type] [player] [amount]` - Admin sends RSS to player\n`!adminrss [F] [S] [W] [O] [G] [player]` - Admin sends all types of RSS to player"
        await interaction.response.send_message(text, ephemeral=True)

# 🟢 मुख्य 3 बटन वाला मेनू (जो hii लिखने पर आएगा)
class MainGreetingView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Guild Bank Commands", style=discord.ButtonStyle.success, emoji="🏦")
    async def open_bank_menu_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        view = BankCategoryView()
        await interaction.response.send_message("👇 **किस तरह की बैंक कमांड्स देखनी हैं? नीचे से कैटेगरी चुनें:**", view=view, ephemeral=True)

    # 🎮 नया बटन: प्लेयर्स को कमांड्स बताने के लिए
    @discord.ui.button(label="Bot Commands", style=discord.ButtonStyle.primary, emoji="🤖")
    async def bot_commands_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        text = (
            "✨ **THANOS BOT COMMANDS LIST:**\n\n"
            "🐲 **`/monster [नाम]`**\n"
            "किसी भी मॉन्स्टर के F2P और P2P हीरोज पता करें।\n"
            "👉 *ऐसे लिखें:* `/monster hardrox`\n\n"
            "🛡️ **`/shield [घंटे]`**\n"
            "एडवांस शील्ड टाइमर सेट करें (खत्म होने से 15 मिनट पहले आपको मैसेज आ जाएगा!)।\n"
            "👉 *ऐसे लिखें:* `/shield 24` या `/shield 8`\n\n"
            "🧠 **AI Chat**\n"
            "बॉट को टैग करके (`@Thanos Bot`) गेम या दुनिया का कोई भी सवाल पूछें!"
        )
        await interaction.response.send_message(text, ephemeral=True)

    @discord.ui.button(label="Clear Chat", style=discord.ButtonStyle.danger, emoji="🗑️")
    async def clear_chat_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message("❌ आपके पास मैसेज डिलीट करने की परमिशन नहीं है!", ephemeral=True)
            return
        view = ClearConfirmView(interaction.user)
        await interaction.response.send_message("⚠️ **चेतावनी:** क्या आप इस चैनल के सारे मैसेज डिलीट करना चाहते हैं? पुष्टि करने के लिए **Confirm** बटन पर क्लिक करें:", view=view, ephemeral=True)


@bot.command()
async def clearall(ctx):
    if not ctx.author.guild_permissions.administrator:
        await ctx.send("❌ आपके पास इस कमांड को चलाने की परमिशन नहीं है!", delete_after=5)
        return
    view = ClearConfirmView(ctx.author)
    await ctx.send("⚠️ **चेतावनी:** क्या आप इस चैनल के सारे मैसेज डिलीट करना चाहते हैं? पुष्टि करने के लिए नीचे दिए गए **Confirm (OK)** बटन पर क्लिक करें:", view=view)


# 🐲 नया फीचर 1: मॉन्स्टर कमांड (Gemini AI के साथ)
@bot.command()
async def monster(ctx, *, monster_name: str = None):
    if not monster_name:
        await ctx.send("⚠️ भाई, किसी मॉन्स्टर का नाम तो बताओ! (जैसे: `/monster hardrox` या `/monster snow beast`)")
        return

    if not ai_client:
        await ctx.send("⚠️ Gemini API Key सेट नहीं है भाई!")
        return

    prompt = f"Lords Mobile game में '{monster_name}' monster को मारने के लिए Best F2P (Free to play) और P2P (Pay to play) heroes की लिस्ट बताओ. जवाब हिंदी और इंग्लिश मिक्स (Hinglish) में एकदम साफ़ बुलेट पॉइंट्स में देना."

    async with ctx.typing():
        try:
            response = ai_client.models.generate_content(
                model='gemini-3.6-flash',
                contents=prompt,
            )
            await ctx.send(f"👾 **{monster_name.title()}** को मारने के बेस्ट हीरोज:\n{response.text}")
        except Exception as e:
            await ctx.send(f"❌ कुछ गड़बड़ हो गई: {e}")


# 🛡️ नया फीचर 2: एडवांस शील्ड कमांड (15 मिनट पहले DM अलर्ट के साथ)
@bot.command()
async def shield(ctx, hours: int):
    if hours <= 0:
        await ctx.send("❌ भाई, सही टाइम बताओ! (जैसे 4, 8, 24)")
        return

    total_seconds = hours * 3600
    warning_seconds = total_seconds - 900 # 15 मिनट (900 सेकंड) पहले का टाइम

    await ctx.send(f"🛡️ {ctx.author.mention}, मैंने **{hours} घंटे** का शील्ड टाइमर सेट कर दिया है। खत्म होने से ठीक 15 मिनट पहले मैं तुम्हें **प्राइवेट मैसेज (DM)** में अलर्ट कर दूंगा! ⏰")

    if warning_seconds > 0:
        await asyncio.sleep(warning_seconds)
        
        # 15 मिनट पहले का अलर्ट (DM में भेजने की कोशिश)
        try:
            await ctx.author.send(f"🚨 **चेतावनी:** भाई! तुम्हारी **{hours} घंटे** वाली Lords Mobile शील्ड खत्म होने में सिर्फ **15 मिनट** बचे हैं! जल्दी गेम खोलो वरना कोई अटैक कर देगा! ⚔️")
        except discord.Forbidden:
            # अगर यूज़र के DM बंद हुए, तो चैनल में ही टैग करके बता देगा
            await ctx.send(f"🚨 {ctx.author.mention}, तुम्हारी शील्ड 15 मिनट में खत्म होने वाली है! (तुम्हारे DM बंद हैं, इसलिए यहाँ बता रहा हूँ)")
            
        await asyncio.sleep(900)
    else:
        await asyncio.sleep(total_seconds)

    # शील्ड खत्म होने का फाइनल अलर्ट
    try:
        await ctx.author.send(f"⚠️ **अलर्ट:** भाई! तुम्हारी शील्ड **खत्म हो चुकी है!** तुरंत गेम चेक करो! 🏰")
    except discord.Forbidden:
        await ctx.send(f"⚠️ {ctx.author.mention}, तुम्हारी शील्ड **खत्म हो चुकी है!** तुरंत गेम चेक करो! 🏰")


@bot.event
async def on_message(message):
    if message.author == bot.user:
        return

    is_mentioned = bot.user in message.mentions or f"<@{bot.user.id}>" in message.content or f"<@!{bot.user.id}>" in message.content

    if is_mentioned:
        if not ai_client:
            await message.channel.send("⚠️ Gemini API Key सेट नहीं है भाई! कृपया Render में `GEMINI_API_KEY` जोड़ें।")
            return

        prompt = message.content.replace(f'<@!{bot.user.id}>', '').replace(f'<@{bot.user.id}>', '').strip()
        
        if prompt:
            async with message.channel.typing():
                try:
                    response = ai_client.models.generate_content(
                        model='gemini-3.6-flash',
                        contents=prompt,
                    )
                    
                    full_response = f"{message.author.mention} \n{response.text}"
                    
                    for i in range(0, len(full_response), 1900):
                        await message.channel.send(full_response[i:i+1900])
                        
                except Exception as e:
                    await message.channel.send(f"❌ कुछ गड़बड़ हो गई: {e}")
        else:
            await message.channel.send(f"हाँ भाई {message.author.mention}! बताइए, मुझसे क्या पूछना चाहते हैं?")
        return

    words = message.content.lower().split()
    if words:
        if any(w in words for w in ["hi", "hii", "hello", "hey", "namaste"]):
            view = MainGreetingView()
            await message.channel.send(
                f"Hello / नमस्ते {message.author.mention}! 👋 \n"
                f"👇 **बॉट की सभी कमांड्स (Monster, Shield आदि)** और **Guild Bank** के लिए नीचे बटन दबाएं:", 
                view=view
            )
        elif any(w in words for w in ["code", "command", "commands"]):
            await message.channel.send(f"💻 भाई, सभी कमांड्स देखने के लिए `/helpmenu` टाइप करें या `hii` लिखकर **🤖 Bot Commands** बटन दबाएं!")

    await bot.process_commands(message)

keep_alive()
token = os.environ.get("DISCORD_TOKEN")
bot.run(token)
