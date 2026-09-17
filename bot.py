import asyncio
import os
import threading
import aiohttp
import re  
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

# 🛠️ AI फंक्शन
async def get_ai_response(prompt):
    if not GEMINI_KEY:
        return "⚠️ Gemini API Key सेट नहीं है!"
        
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
                return (
                    "**🛑WELCOME-THANOS BOT🛑**\n\n"
                    "✨ **Hello / नमस्ते Everyone / दोस्तों!**\n"
                    "Thanos Bot is online and ready to help your guild! / गिल्ड की मदद के लिए बॉट तैयार है! 🤖🔥\n\n"
                    "💡 **Type in chat to see commands / कमांड्स देखने के लिए चैट में लिखें:**\n"
                    "`hi` or / `hello`\n\n"
                    "⚠️ **Need Help?** Mention Admin or ask here! / कोई दिक्कत हो तो एडमिन को टैग करें!"
                )

# 📝 बॉट की डायरी (Saved Codes)
CODES_FILE = "saved_codes.txt"

def load_saved_codes():
    if not os.path.exists(CODES_FILE):
        return []
    with open(CODES_FILE, "r") as f:
        return f.read().splitlines()

def save_new_code(code):
    with open(CODES_FILE, "a") as f:
        f.write(code + "\n")

# 📝 पैच नोट्स की डायरी (Saved Patches)
PATCH_FILE = "saved_patches.txt"

def load_saved_patches():
    if not os.path.exists(PATCH_FILE):
        return set()
    with open(PATCH_FILE, "r") as f:
        return set(line.strip() for line in f if line.strip())

def save_patch_id(post_id):
    with open(PATCH_FILE, "a") as f:
        f.write(f"{post_id}\n")

# 🤖 Discord Bot सेटअप
intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True
intents.presences = True
bot = commands.Bot(command_prefix='/', intents=intents)
bot.remove_command('help')

# 🧹 हर 30 मिनट में चेक करेगा और 24 घंटे पुराने मैसेज अपने आप डिलीट कर देगा
@tasks.loop(minutes=30)
async def auto_clear_chat():
    for guild in bot.guilds:
        for channel in guild.text_channels:
            try:
                now = datetime.now(timezone.utc)
                deleted = await channel.purge(limit=200, check=lambda m: (now - m.created_at) > timedelta(hours=24))
                if len(deleted) > 0:
                    print(f"🧹 {channel.name} से {len(deleted)} पुराने मैसेज डिलीट किए गए।")
            except Exception:
                pass

# 🕵️ रिडीम कोड ढूँढने वाला ऑटोमैटिक जासूस
@tasks.loop(minutes=30)
async def code_scraper():
    url = "https://www.reddit.com/r/lordsmobile/new.json?limit=10"
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Bot'}

    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(url, headers=headers) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    saved_codes = load_saved_codes()
                    
                    for post in data['data']['children']:
                        title = post['data']['title'].upper()
                        text = post['data'].get('selftext', '').upper()
                        full_content = title + " " + text
                        
                        if "CODE" in full_content or "REDEEM" in full_content:
                            possible_codes = re.findall(r'\b[A-Z0-9]{8,12}\b', full_content)
                            
                            for p_code in possible_codes:
                                if p_code not in saved_codes and not p_code.isnumeric():
                                    save_new_code(p_code)
                                    
                                    for guild in bot.guilds:
                                        for channel in guild.text_channels:
                                            if channel.permissions_for(guild.me).send_messages:
                                                try:
                                                    await channel.send(
                                                        f"🚨 **New Lords Mobile Code Found!** 🚨\n"
                                                        f"🎁 **Code:** `{p_code}`\n"
                                                        f"🔗 *Redeem here:* <https://lordsmobile.igg.com/project/gifts/>"
                                                    )
                                                except Exception:
                                                    pass 
        except Exception as e:
            print(f"Scraper Error: {e}")

# 🚨 ऑफिशियल पैच नोट्स और बैनर स्क्रैपर
@tasks.loop(hours=1)
async def patch_notes_scraper():
    url = "https://www.reddit.com/r/lordsmobile/new.json?limit=10"
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Bot'}

    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(url, headers=headers) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    saved_patches = load_saved_patches()
                    
                    for post in data['data']['children']:
                        p_data = post['data']
                        post_id = p_data['id']
                        title = p_data['title']
                        text = p_data.get('selftext', '')
                        full_content = (title + " " + text).lower()
                        
                        if any(keyword in full_content for keyword in ["update", "patch", "maintenance", "notes", "event"]):
                            if post_id not in saved_patches:
                                save_patch_id(post_id)
                                
                                image_url = p_data.get('url', None)
                                post_permalink = f"https://www.reddit.com{p_data.get('permalink', '')}"
                                
                                embed = discord.Embed(
                                    title="🚨 New Lords Mobile Update & Patch Notes!",
                                    description=f"**{title}**\n\n🔗 [Read full post on Reddit]({post_permalink})",
                                    color=discord.Color.gold()
                                )
                                
                                if image_url and any(image_url.endswith(ext) for ext in ['.jpg', '.png', '.jpeg']):
                                    embed.set_image(url=image_url)
                                
                                for guild in bot.guilds:
                                    for channel in guild.text_channels:
                                        if channel.permissions_for(guild.me).send_messages:
                                            try:
                                                await channel.send(embed=embed)
                                            except Exception:
                                                pass
                                break 
        except Exception as e:
            print(f"Patch Scraper Error: {e}")

@bot.event
async def on_ready():
    print(f'✅ {bot.user} ऑनलाइन आ गया है!')
    await bot.change_presence(status=discord.Status.online, activity=discord.Game(name="Lords Mobile"))
    
    bot.add_view(MainGreetingView())
    bot.add_view(HelpButtonView())
    bot.add_view(MonsterView())
    bot.add_view(BankCategoryView())
    bot.add_view(GearCategoryView())

    if not auto_clear_chat.is_running():
        auto_clear_chat.start()
        
    if not code_scraper.is_running():
        code_scraper.start()
        print("🕵️ Code Scraper चालू हो गया है!")

    if not patch_notes_scraper.is_running():
        patch_notes_scraper.start()
        print("🚨 Patch Notes Scraper चालू हो गया है!")

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
            "🗑️ **`/clearall`** - चैनल के सारे मैसेज डिलीट करने के लिए (एडमिन के लिए)।"
        )

# ⚠️ चैट डिलीट कंफर्मेशन
class ClearConfirmView(discord.ui.View):
    def __init__(self, author):
        super().__init__(timeout=60)
        self.author = author

    @discord.ui.button(label="✅ Confirm - Clear My Chat", style=discord.ButtonStyle.danger)
    async def confirm_callback(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user != self.author:
            await interaction.response.send_message("❌ आप इसे यूज़ नहीं कर सकते! अपना बटन खुद दबाएं।")
            return
        
        await interaction.response.send_message("🧹 आपकी चैट तुरंत साफ हो रही...")
        
        try:
            if interaction.guild is None:
                async for msg in interaction.channel.history(limit=100):
                    if msg.author == interaction.client.user:
                        try:
                            await msg.delete()
                        except:
                            pass
            else:
                await interaction.channel.purge(limit=500)
        except Exception:
            pass

    @discord.ui.button(label="❌ Cancel", style=discord.ButtonStyle.secondary)
    async def cancel_callback(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user != self.author:
            await interaction.response.send_message("❌ नो परमिशन!")
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
        
        await interaction.response.send_message(embeds=[embed1, embed2])

class MonsterView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(MonsterSelect())

# 🟢 गियर मेनू
class GearCategoryView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Mix ATK", style=discord.ButtonStyle.primary, emoji="🛡️", custom_id="gear_mix_btn")
    async def mix_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        embed = discord.Embed(title="🛡️ Best Mix ATK Gear Setup", color=discord.Color.gold())
        embed.set_image(url="https://raw.githubusercontent.com/chandan902640-lab/Thanos-bot/main/mixatk.jpg")
        await interaction.response.send_message(embed=embed)

    @discord.ui.button(label="Infantry ATK", style=discord.ButtonStyle.secondary, emoji="⚔️", custom_id="gear_inf_btn")
    async def inf_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        embed = discord.Embed(title="⚔️ Best Infantry ATK Gear Setup", color=discord.Color.blue())
        embed.set_image(url="https://raw.githubusercontent.com/chandan902640-lab/Thanos-bot/main/infatk.png")
        await interaction.response.send_message(embed=embed)

    @discord.ui.button(label="Ranged ATK", style=discord.ButtonStyle.success, emoji="🏹", custom_id="gear_range_btn")
    async def range_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        embed = discord.Embed(title="🏹 Best Ranged ATK Gear Setup", color=discord.Color.green())
        embed.set_image(url="https://raw.githubusercontent.com/chandan902640-lab/Thanos-bot/main/rangeatk.jpg")
        await interaction.response.send_message(embed=embed)

    @discord.ui.button(label="Cavalry ATK", style=discord.ButtonStyle.danger, emoji="🐎", custom_id="gear_cav_btn")
    async def cav_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        embed = discord.Embed(title="🐎 Best Cavalry ATK Gear Setup", color=discord.Color.red())
        embed.set_image(url="https://raw.githubusercontent.com/chandan902640-lab/Thanos-bot/main/cavatk.png")
        await interaction.response.send_message(embed=embed)

# 🟡 बैंक मेनू
class BankCategoryView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Tips", style=discord.ButtonStyle.secondary, emoji="💡", custom_id="bank_tips_btn")
    async def tips_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        text = "**💡 BANK TIPS & TRICKS:**\n\nUse underscore ('!setacc Player_1').\nHero Stages: Bank will not respond during long hero stages."
        await interaction.response.send_message(text)

    @discord.ui.button(label="General", style=discord.ButtonStyle.success, emoji="📌", custom_id="bank_general_btn")
    async def general_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        text1 = (
            "**📌 GENERAL COMMANDS:**\n\n"
            "**📋 ALL BANK COMMANDS (Part 1):**\n\n"
            "`!payransom` ➡️ The ransom for the accounts leader is paid\n"
            "`!clearboard` ➡️ All quests are deleted\n"
            "`!ess` ➡️ Mails the status of transmutation lab\n"
            "`!stats` ➡️ Report of all Guild Gifts for yourself\n"
            "`!stats all` ➡️ Summary of your guilds purchase/monsters\n"
            "`!pstats [Player]` ➡️ Report of the Guild Gift stats for a player\n"
            "`!gryphon` ➡️ Uses the Gryphon familiar skill\n"
            "`!reguser` ➡️ Bind your ID for using commands\n"
            "`!unreguser` ➡️ Unbind your ID\n"
            "`!pos` ➡️ Reports the exact location of the Bank\n"
            "`!shield` ➡️ Report of when the Bank shield drops\n"
            "`!shield deploy` ➡️ Shield is activated on the bank\n"
            "`!relocate [X] [Y]` ➡️ Relocates the bank to X Y\n"
            "`!relocate rand` ➡️ Relocate the bank to a random position\n"
            "`!relocatekvk [K]` ➡️ Randomly relocates into the target kingdom\n"
            "`!migrate [K][X][Y]` ➡️ Migrate to target Kingdom\n"
            "`!recall` ➡️ Recall all troops to your castle\n"
            "`!buildspam [amt] [delay]` ➡️ The bank will spam helps\n"
            "`!buildspam stop` ➡️ Cancel build in progress\n"
            "`!hunt [x] [y]` ➡️ Hunts the specified monster\n"
            "`!hunt [on/off]` ➡️ Disable or enable hunting\n"
            "`!addtitle [player] [title]` ➡️ The bank will give a title\n"
            "`!deltitle [title]` ➡️ The bank will remove the title\n"
        )
        
        text2 = (
            "**📋 ALL BANK COMMANDS (Part 2):**\n\n"
            "`!whitelist [player] [Rank]` ➡️ Accepts a player and sets Rank\n"
            "`!blacklist [player]` ➡️ Rejects a player\n"
            "`!unlistwhite [player]` ➡️ Removes player from whitelist\n"
            "`!unlistblack [player]` ➡️ Removes player from blacklist\n"
            "`!purge` ➡️ The Guild Chat will be cleared\n"
            "`!abort` ➡️ All queued RSS will be canceled\n"
            "`!yell [msg]` ➡️ Writes a message to the guild chat\n"
            "`!quest` ➡️ Mails player the guild fest status\n"
            "`!guild [tag]` ➡️ Leaves guild and joins a new one\n"
            "`!camp [x] [y]` ➡️ Sends a camp to x/y\n"
            "`!setgather [on/off]` ➡️ Disable or enable gathering\n"
            "`!snowbeast` ➡️ Snowbeast familiars skill is activated\n"
            "`!stop [time]` ➡️ Account will go offline for x seconds\n"
            "`!reloadacc` ➡️ Resets the account\n"
            "`!members` ➡️ Member information is refreshed\n"
            "`!busrank` ➡️ Promotes members who completed hunting\n"
            "`!resetstats` ➡️ The gift stats have been reset\n"
            "`!joingvg` ➡️ Join Guild Expedition\n"
            "`!leavegvg` ➡️ Leave Guild Expedition\n"
            "`!joinca` ➡️ Joins the Chaos Arena Event\n"
            "`!leaveca` ➡️ Leaves the Chaos Arena Event\n"
            "`!joinda` ➡️ Joins Dragon Arena for your guild\n"
            "`!leaveda` ➡️ Leaves Dragon Arena for your guild\n"
        )
        
        await interaction.response.send_message(text1)
        await interaction.followup.send(text2)

    @discord.ui.button(label="Search", style=discord.ButtonStyle.primary, emoji="🔍", custom_id="bank_search_btn")
    async def search_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        text = (
            "**🔍 SEARCH COMMANDS:**\n\n"
            "`!findtile [type] [level]` ➡️ Search for specific resource tiles around the bank\n"
            "`!findtile any [level]` ➡️ Search for any resource tiles around the bank\n"
            "`!findtilelocal [type] [lvl]` ➡️ Search for resource tiles around your castle\n"
            "`!findmonster [name] [lvl]` ➡️ Search for a specific monster around the bank\n"
            "`!findmonster any [lvl]` ➡️ Search for any monster around the bank\n"
            "`!findmonsterlocal [name] [lvl]` ➡️ Search for a monster around your castle\n"
            "`!findnest [level]` ➡️ Search for a Darknest around the bank\n"
            "`!findnestlocal [level]` ➡️ Search for a Darknest around your castle\n\n"
            "*(Note: The bank will send all search results directly to your in-game mail!)*"
        )
        await interaction.response.send_message(text)
        
    @discord.ui.button(label="Balance", style=discord.ButtonStyle.secondary, emoji="⚖️", custom_id="bank_balance_btn")
    async def balance_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        text = (
            "**⚖️ BALANCE COMMANDS:**\n\n"
            "`!bal` ➡️ Checks your personal RSS balance\n"
            "`!adminbal` ➡️ Checks the RSS balance of the Bank\n"
            "`!adminbal [player]` ➡️ Checks the balance of a specific player\n"
            "`!adminbag` ➡️ Checks the RSS balance of the Bank's bag\n"
            "`!setbal [player] [type] [amt]` ➡️ Manually sets the RSS balance for an account\n"
            "`!setacc [player]` ➡️ Credits all your sent balance to another account\n"
            "`!transfer [player] [type] [amt]` ➡️ Transfers your balance to another player\n"
            "`!setrsslimit [type] [amt]` ➡️ Sets a minimum RSS limit the bank won't go below\n"
        )
        await interaction.response.send_message(text)

    @discord.ui.button(label="Resource", style=discord.ButtonStyle.danger, emoji="💰", custom_id="bank_resource_btn")
    async def resource_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        text = (
            "**💰 RESOURCE COMMANDS:**\n\n"
            "`![type] [amount]` ➡️ Sends one specific RSS (e.g., `!food 5M`)\n"
            "`!rss [F] [S] [W] [O] [G]` ➡️ Sends all types of RSS (e.g., `!rss 5M 5M 5M 5M 0`)\n"
            "`!donate[type] [player] [amt]` ➡️ Sends specific RSS to a player (e.g., `!donatefood Shark 5M`)\n"
            "`!admin[type] [player] [amt]` ➡️ Admin command to send specific RSS to a player\n"
            "`!adminrss [F] [S] [W] [O] [G] [player]` ➡️ Admin sends all types of RSS to a player\n"
        )
        await interaction.response.send_message(text)
         
# 🟢 मुख्य मेनू (बटन्स के सही कलर्स के साथ)
class MainGreetingView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    # 1. Guild Bank (Primary - Blue)
    @discord.ui.button(label="Guild Bank Commands", style=discord.ButtonStyle.primary, emoji="🏦", custom_id="main_bank_btn")
    async def open_bank_menu_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        view = BankCategoryView()
        await interaction.response.send_message("👇 **किस तरह की बैंक कमांड्स देखनी हैं?**", view=view)

    # 2. Monster Hunt (Success - Green)
    @discord.ui.button(label="🏹 Monster Hunt", style=discord.ButtonStyle.success, emoji="🐲", custom_id="main_monster_btn")
    async def monster_hunt_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        view = MonsterView()
        await interaction.response.send_message("👇 **नीचे दिए गए ड्रॉपडाउन से अपना मॉन्स्टर चुनें:**", view=view)

    # 3. Best Gear Setups (Secondary - Grey)
    @discord.ui.button(label="⚙️ Best Gear Setups", style=discord.ButtonStyle.secondary, emoji="🛡️", custom_id="main_gear_btn")
    async def gear_setup_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        view = GearCategoryView()
        await interaction.response.send_message("👇 **कौन सा गियर सेटअप देखना है? नीचे से चुनें:**", view=view)

    # 4. Bot Commands (Primary - Blue)
    @discord.ui.button(label="Bot Commands", style=discord.ButtonStyle.primary, emoji="🤖", custom_id="main_botcmd_btn")
    async def bot_commands_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        text = (
            "✨ **THANOS BOT COMMANDS & FEATURES / बॉट की कमांड्स और फीचर्स:**\n\n"
            "🏦 **Guild Bank Menu:** ➔Access bank commands instantly. ➔ बैंक कमांड्स का आसान मेनू。\n"
            "🐲 **Monster Hunt:** View ➔18 monster hero setups. ➔ 18 मॉन्स्टर्स के हीरो सेटअप देखें。\n"
            "🛡️ **`/shield [hours]`** -➔ Shield timer with alerts. ➔ /शील्ड टाइमर और अलर्ट。\n"
            "🎁 **Auto Redeem Codes:** ➔Bot will automatically send new redeem codes. ➔ नया रिडीम कोड आने पर बॉट आपको ऑटोमैटिक रिडीम कोड भेजेगा。\n"
            "🚨 **Event & Patch Notes:**➔ Bot will automatically send event pages. ➔ नया इवेंट आने पर बॉट आपको ऑटोमैटिक इवेंट पेज भेजेगा。\n"
            "🗑️ **`/clearall` / Clear Chat:** ➔Clean up chat messages. ➔/ चैट साफ़ करें।"
        )
        await interaction.response.send_message(text)

    # 5. Clear My Chat (Danger - Red)
    @discord.ui.button(label="Clear My Chat", style=discord.ButtonStyle.danger, emoji="🗑️", custom_id="main_clearchat_btn")
    async def clear_chat_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        view = ClearConfirmView(interaction.user)
        await interaction.response.send_message("⚠️ **चेतावनी:** क्या आप अपने और बॉट के मैसेज डिलीट करना चाहते हैं?", view=view)

# 🗑️ क्लियर कमांड 
@bot.command()
async def clearall(ctx):
    view = ClearConfirmView(ctx.author)
    await ctx.send("⚠️ **चेतावनी:** क्या आप अपने और बॉट के मैसेज डिलीट करना चाहते हैं?", view=view)

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
            f"👇 **Click buttons below for Bot Commands & Guild Bank / बॉट कमांड्स और बैंक के लिए नीचे बटन दबाएं:**", 
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
            
            if "WELCOME-THANOS BOT" in ai_text:
                embed = discord.Embed(color=0x00ffff) 
                embed.set_image(url="https://raw.githubusercontent.com/chandan902640-lab/Thanos-bot/main/bothii.png")
                await message.channel.send(full_response, embed=embed)
            else:
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
    print("❌ Error: DISCORD_TOKEN environment variable not found")
