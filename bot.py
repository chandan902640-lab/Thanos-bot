import os
import json
import random
import threading
import requests
import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from http.server import BaseHTTPRequestHandler, HTTPServer
from datetime import datetime

# ==========================================
# 🌐 24/7 Render Server Setup
# ==========================================
class DummyHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/plain')
        self.end_headers()
        self.wfile.write(b"Telegram Thanos Bot is online and running 24/7!")
    def do_HEAD(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/plain')
        self.end_headers()

def keep_alive():
    port = int(os.environ.get("PORT", 8080))
    server = HTTPServer(('0.0.0.0', port), DummyHandler)
    threading.Thread(target=server.serve_forever, daemon=True).start()

# ==========================================
# 🤖 Telegram Bot & API Setup
# ==========================================
BOT_TOKEN = os.environ.get("TELEGRAM_TOKEN")
GEMINI_KEY = os.environ.get("GEMINI_API_KEY")
bot = telebot.TeleBot(BOT_TOKEN)

# ==========================================
# 💎 Economy System (Bank)
# ==========================================
ECONOMY_FILE = "economy.json"
daily_cooldowns = {}

def load_economy():
    if not os.path.exists(ECONOMY_FILE):
        with open(ECONOMY_FILE, "w") as f:
            json.dump({}, f)
        return {}
    try:
        with open(ECONOMY_FILE, "r") as f:
            return json.load(f)
    except:
        return {}

def save_economy(data):
    with open(ECONOMY_FILE, "w") as f:
        json.dump(data, f, indent=4)

def get_balance(user_id):
    data = load_economy()
    return data.get(str(user_id), 0)

def add_money(user_id, amount):
    data = load_economy()
    user_id = str(user_id)
    data[user_id] = data.get(user_id, 0) + amount
    if data[user_id] < 0:
        data[user_id] = 0
    save_economy(data)

# ==========================================
# 🧠 AI Function (Gemini)
# ==========================================
def get_ai_response(prompt):
    if not GEMINI_KEY:
        return "⚠️ Gemini API Key सेट नहीं है!"
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={GEMINI_KEY}"
    headers = {'Content-Type': 'application/json'}
    data = {"contents": [{"parts": [{"text": prompt}]}]}
    try:
        response = requests.post(url, headers=headers, json=data)
        if response.status_code == 200:
            return response.json()['candidates'][0]['content']['parts'][0]['text']
        else:
            return "⚠️ गूगल AI अभी व्यस्त है।"
    except Exception as e:
        return f"⚠️ Error: {e}"

# ==========================================
# 👑 Main Control Panel (!99 or Start)
# ==========================================
@bot.message_handler(commands=['start', '99', 'menu'])
def send_panel(message):
    markup = InlineKeyboardMarkup()
    markup.row(
        InlineKeyboardButton("🏦 Guild Bank", callback_data="menu_bank"),
        InlineKeyboardButton("🐲 Monster Hunt", callback_data="menu_monster")
    )
    markup.row(
        InlineKeyboardButton("⚙️ Best Gear", callback_data="menu_gear"),
        InlineKeyboardButton("💰 Economy & Games", callback_data="menu_economy")
    )
    
    welcome_text = (
        "👑 **THANOS BOT - CONTROL PANEL** 👑\n\n"
        f"Hello {message.from_user.first_name}!\n"
        "👇 IGG/Lords Mobile के सभी फीचर्स के लिए नीचे दिए गए बटन्स का इस्तेमाल करें:"
    )
    bot.send_message(message.chat.id, welcome_text, reply_markup=markup, parse_mode='Markdown')

# ==========================================
# 🖱️ Button Clicks (Callback Logic)
# ==========================================
@bot.callback_query_handler(func=lambda call: True)
def handle_query(call):
    cid = call.message.chat.id
    mid = call.message.message_id
    uid = call.from_user.id
    
    # --- 1. MAIN MENUS ---
    if call.data == "menu_bank":
        markup = InlineKeyboardMarkup()
        markup.row(InlineKeyboardButton("💡 Tips", callback_data="bank_tips"), InlineKeyboardButton("📌 General", callback_data="bank_gen"))
        markup.row(InlineKeyboardButton("🔍 Search", callback_data="bank_search"), InlineKeyboardButton("⚖️ Balance", callback_data="bank_bal"))
        markup.row(InlineKeyboardButton("💰 Resource", callback_data="bank_res"))
        bot.edit_message_text("🏦 **Guild Bank Commands:**\nकिस तरह की बैंक कमांड्स देखनी हैं?", cid, mid, reply_markup=markup, parse_mode='Markdown')
        
    elif call.data == "menu_monster":
        bot.send_message(cid, "🐲 **Monster Hunt:**\nकिसी भी मॉन्स्टर की बेस्ट टीम जानने के लिए टाइप करें:\n`/monster [मॉन्स्टर का नाम]`\n*(उदाहरण: `/monster Queen Bee`)*", parse_mode='Markdown')
        
    elif call.data == "menu_gear":
        markup = InlineKeyboardMarkup()
        markup.row(InlineKeyboardButton("🛡️ Mix ATK", callback_data="gear_mix"), InlineKeyboardButton("⚔️ Infantry", callback_data="gear_inf"))
        markup.row(InlineKeyboardButton("🏹 Ranged", callback_data="gear_rng"), InlineKeyboardButton("🐎 Cavalry", callback_data="gear_cav"))
        bot.edit_message_text("⚙️ **Best Gear Setups:**\nकौन सा गियर सेटअप देखना है? नीचे से चुनें:", cid, mid, reply_markup=markup, parse_mode='Markdown')
        
    elif call.data == "menu_economy":
        markup = InlineKeyboardMarkup()
        markup.row(InlineKeyboardButton("💰 Balance", callback_data="eco_bal"), InlineKeyboardButton("🎁 Daily 2000", callback_data="eco_daily"))
        markup.row(InlineKeyboardButton("🎰 Slots (Bet 100)", callback_data="eco_slots"))
        bot.edit_message_text("🪙 **Economy & Games:**\nपैसे कमाएं, बैलेंस चेक करें और गेम्स खेलें!", cid, mid, reply_markup=markup, parse_mode='Markdown')

    # --- 2. GEAR HANDLERS (Photo Sender) ---
    elif call.data == "gear_mix":
        bot.send_photo(cid, "https://raw.githubusercontent.com/chandan902640-lab/Thanos-bot/main/mixatk.jpg", caption="🛡️ Best Mix ATK Gear Setup")
    elif call.data == "gear_inf":
        bot.send_photo(cid, "https://raw.githubusercontent.com/chandan902640-lab/Thanos-bot/main/infatk.png", caption="⚔️ Best Infantry ATK Gear Setup")
    elif call.data == "gear_rng":
        bot.send_photo(cid, "https://raw.githubusercontent.com/chandan902640-lab/Thanos-bot/main/rangeatk.jpg", caption="🏹 Best Ranged ATK Gear Setup")
    elif call.data == "gear_cav":
        bot.send_photo(cid, "https://raw.githubusercontent.com/chandan902640-lab/Thanos-bot/main/cavatk.png", caption="🐎 Best Cavalry ATK Gear Setup")

    # --- 3. FULL BANK COMMANDS HANDLERS ---
    elif call.data == "bank_tips":
        text = "💡 BANK TIPS & TRICKS:\n\nUse underscore ('!setacc Player_1').\nHero Stages: Bank will not respond during long hero stages."
        bot.send_message(cid, text)

    elif call.data == "bank_gen":
        text1 = (
            "📌 GENERAL COMMANDS (Part 1):\n\n"
            "!payransom ➡️ The ransom for the accounts leader is paid\n"
            "!clearboard ➡️ All quests are deleted\n"
            "!ess ➡️ Mails the status of transmutation lab\n"
            "!stats ➡️ Report of all Guild Gifts for yourself\n"
            "!stats all ➡️ Summary of your guilds purchase/monsters\n"
            "!pstats [Player] ➡️ Report of the Guild Gift stats for a player\n"
            "!gryphon ➡️ Uses the Gryphon familiar skill\n"
            "!reguser ➡️ Bind your ID for using commands\n"
            "!unreguser ➡️ Unbind your ID\n"
            "!pos ➡️ Reports the exact location of the Bank\n"
            "!shield ➡️ Report of when the Bank shield drops\n"
            "!shield deploy ➡️ Shield is activated on the bank\n"
            "!relocate [X] [Y] ➡️ Relocates the bank to X Y\n"
            "!relocate rand ➡️ Relocate the bank to a random position\n"
            "!relocatekvk [K] ➡️ Randomly relocates into the target kingdom\n"
            "!migrate [K][X][Y] ➡️ Migrate to target Kingdom\n"
            "!recall ➡️ Recall all troops to your castle\n"
            "!buildspam [amt] [delay] ➡️ The bank will spam helps\n"
            "!buildspam stop ➡️ Cancel build in progress\n"
            "!hunt [x] [y] ➡️ Hunts the specified monster\n"
            "!hunt [on/off] ➡️ Disable or enable hunting\n"
            "!addtitle [player] [title] ➡️ The bank will give a title\n"
            "!deltitle [title] ➡️ The bank will remove the title\n"
        )
        text2 = (
            "📌 GENERAL COMMANDS (Part 2):\n\n"
            "!whitelist [player] [Rank] ➡️ Accepts a player and sets Rank\n"
            "!blacklist [player] ➡️ Rejects a player\n"
            "!unlistwhite [player] ➡️ Removes player from whitelist\n"
            "!unlistblack [player] ➡️ Removes player from blacklist\n"
            "!purge ➡️ The Guild Chat will be cleared\n"
            "!abort ➡️ All queued RSS will be canceled\n"
            "!yell [msg] ➡️ Writes a message to the guild chat\n"
            "!quest ➡️ Mails player the guild fest status\n"
            "!guild [tag] ➡️ Leaves guild and joins a new one\n"
            "!camp [x] [y] ➡️ Sends a camp to x/y\n"
            "!setgather [on/off] ➡️ Disable or enable gathering\n"
            "!snowbeast ➡️ Snowbeast familiars skill is activated\n"
            "!stop [time] ➡️ Account will go offline for x seconds\n"
            "!reloadacc ➡️ Resets the account\n"
            "!members ➡️ Member information is refreshed\n"
            "!busrank ➡️ Promotes members who completed hunting\n"
            "!resetstats ➡️ The gift stats have been reset\n"
            "!joingvg ➡️ Join Guild Expedition\n"
            "!leavegvg ➡️ Leave Guild Expedition\n"
            "!joinca ➡️ Joins the Chaos Arena Event\n"
            "!leaveca ➡️ Leaves the Chaos Arena Event\n"
            "!joinda ➡️ Joins Dragon Arena for your guild\n"
            "!leaveda ➡️ Leaves Dragon Arena for your guild\n"
        )
        bot.send_message(cid, text1)
        bot.send_message(cid, text2)

    elif call.data == "bank_search":
        text = (
            "🔍 SEARCH COMMANDS:\n\n"
            "!findtile [type] [level] ➡️ Search for specific resource tiles around the bank\n"
            "!findtile any [level] ➡️ Search for any resource tiles around the bank\n"
            "!findtilelocal [type] [lvl] ➡️ Search for resource tiles around your castle\n"
            "!findmonster [name] [lvl] ➡️ Search for a specific monster around the bank\n"
            "!findmonster any [lvl] ➡️ Search for any monster around the bank\n"
            "!findmonsterlocal [name] [lvl] ➡️ Search for a monster around your castle\n"
            "!findnest [level] ➡️ Search for a Darknest around the bank\n"
            "!findnestlocal [level] ➡️ Search for a Darknest around your castle\n\n"
            "*(Note: The bank will send all search results directly to your in-game mail!)*"
        )
        bot.send_message(cid, text)
        
    elif call.data == "bank_bal":
        text = (
            "⚖️ BALANCE COMMANDS:\n\n"
            "!bal ➡️ Checks your personal RSS balance\n"
            "!adminbal ➡️ Checks the RSS balance of the Bank\n"
            "!adminbal [player] ➡️ Checks the balance of a specific player\n"
            "!adminbag ➡️ Checks the RSS balance of the Bank's bag\n"
            "!setbal [player] [type] [amt] ➡️ Manually sets the RSS balance for an account\n"
            "!setacc [player] ➡️ Credits all your sent balance to another account\n"
            "!transfer [player] [type] [amt] ➡️ Transfers your balance to another player\n"
            "!setrsslimit [type] [amt] ➡️ Sets a minimum RSS limit the bank won't go below\n"
        )
        bot.send_message(cid, text)
        
    elif call.data == "bank_res":
        text = (
            "💰 RESOURCE COMMANDS:\n\n"
            "![type] [amount] ➡️ Sends one specific RSS (e.g., !food 5M)\n"
            "!rss [F] [S] [W] [O] [G] ➡️ Sends all types of RSS (e.g., !rss 5M 5M 5M 5M 0)\n"
            "!donate[type] [player] [amt] ➡️ Sends specific RSS to a player (e.g., !donatefood Shark 5M)\n"
            "!admin[type] [player] [amt] ➡️ Admin command to send specific RSS to a player\n"
            "!adminrss [F] [S] [W] [O] [G] [player] ➡️ Admin sends all types of RSS to a player\n"
        )
        bot.send_message(cid, text)

    # --- 4. ECONOMY & GAMES HANDLERS ---
    elif call.data == "eco_bal":
        bal = get_balance(uid)
        bot.answer_callback_query(call.id, f"🏦 आपके खाते में {bal} Coins हैं!", show_alert=True)
        
    elif call.data == "eco_daily":
        now = datetime.now()
        if uid in daily_cooldowns and (now - daily_cooldowns[uid]).total_seconds() < 86400:
            hours = int((86400 - (now - daily_cooldowns[uid]).total_seconds()) // 3600)
            bot.answer_callback_query(call.id, f"⏳ आज का इनाम ले चुके हो! {hours} घंटे बाद आना।", show_alert=True)
        else:
            add_money(uid, 2000)
            daily_cooldowns[uid] = now
            bot.answer_callback_query(call.id, "🎁 बधाई हो! आपके खाते में 2000 Coins जुड़ गए हैं।", show_alert=True)
            
    elif call.data == "eco_slots":
        bal = get_balance(uid)
        if bal < 100:
            bot.answer_callback_query(call.id, "❌ पैसे नहीं हैं! आपका बैलेंस 100 से कम है।", show_alert=True)
            return
            
        emojis = ["🍎", "💎", "🍒", "🔔", "⭐"]
        s1, s2, s3 = random.choice(emojis), random.choice(emojis), random.choice(emojis)
        
        if s1 == s2 == s3:
            add_money(uid, 1000)
            bot.send_message(cid, f"🎰 **SLOTS MACHINE** 🎰\n| {s1} | {s2} | {s3} |\n🚨 **MEGA JACKPOT!** आप 1000 Coins जीत गए!")
        elif s1 == s2 or s2 == s3 or s1 == s3:
            add_money(uid, 200)
            bot.send_message(cid, f"🎰 **SLOTS MACHINE** 🎰\n| {s1} | {s2} | {s3} |\n✨ **Small Win!** आप 200 Coins जीत गए!")
        else:
            add_money(uid, -100)
            bot.send_message(cid, f"🎰 **SLOTS MACHINE** 🎰\n| {s1} | {s2} | {s3} |\n❌ मशीन रुक गई और आपके 100 Coins डूब गए!")

# ==========================================
# 🐲 Monster AI Command
# ==========================================
@bot.message_handler(commands=['monster'])
def monster_command(message):
    text = message.text.replace('/monster', '').strip()
    if not text:
        bot.reply_to(message, "⚠️ भाई, किसी मॉन्स्टर का नाम तो बताओ! जैसे: `/monster Queen Bee`")
        return
        
    bot.reply_to(message, f"⏳ **{text}** की बेस्ट टीम ढूँढ रहा हूँ, थोड़ा इंतज़ार करें...")
    prompt = f"Lords Mobile game में '{text}' monster को मारने के लिए Best F2P और P2P heroes की लिस्ट बताओ. जवाब हिंदी और इंग्लिश मिक्स में बुलेट पॉइंट्स में देना."
    ai_reply = get_ai_response(prompt)
    bot.send_message(message.chat.id, f"👾 **{text.title()}** को मारने के बेस्ट हीरोज:\n\n{ai_reply}")

# ==========================================
# 💬 Normal AI Chat (Smart Reply)
# ==========================================
@bot.message_handler(func=lambda m: True)
def chat_ai(message):
    text = message.text.lower()
    if text in ['hi', 'hello', 'hey']:
        send_panel(message)
    else:
        bot.send_chat_action(message.chat.id, 'typing')
        prompt = f"Act like a helpful Lords Mobile Bot named Thanos. Reply in Hinglish. User says: {message.text}"
        ai_reply = get_ai_response(prompt)
        bot.reply_to(message, ai_reply)

# ==========================================
# 🏃 Server Start
# ==========================================
if __name__ == "__main__":
    print("✅ Thanos Telegram Bot is Fully Active with All Commands!")
    keep_alive()
    bot.infinity_polling()
