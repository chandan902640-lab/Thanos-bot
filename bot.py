import os
import json
import random
import threading
import time
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
# 🤖 Telegram Bot Setup (AI REMOVED)
# ==========================================
BOT_TOKEN = os.environ.get("TELEGRAM_TOKEN")
bot = telebot.TeleBot(BOT_TOKEN)

# Auto-Checker Configuration
TARGET_CHAT_ID = "8569573547" 
SEEN_UPDATES_FILE = "seen_updates.json"

def load_seen_updates():
    if not os.path.exists(SEEN_UPDATES_FILE):
        with open(SEEN_UPDATES_FILE, "w") as f:
            json.dump([], f)
        return []
    try:
        with open(SEEN_UPDATES_FILE, "r") as f:
            return json.load(f)
    except:
        return []

def save_seen_update(update_id):
    seen = load_seen_updates()
    if update_id not in seen:
        seen.append(update_id)
        with open(SEEN_UPDATES_FILE, "w") as f:
            json.dump(seen, f, indent=4)

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
# 🐲 FULL 18 Monsters Data
# ==========================================
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
    "18": ("Hardrox", "https://raw.githubusercontent.com/chandan902640-lab/Thanos-bot/main/Hardrox.png", "https://raw.githubusercontent.com/chandan902640-lab/Thanos-bot/main/18.png")
}

# ==========================================
# 👑 Main Control Panel 
# ==========================================
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
# 💬 MAGIC HANDLER: Any Text Opens Menu
# ==========================================
@bot.message_handler(func=lambda m: True)
def chat_all(message):
    send_panel(message)

# ==========================================
# 🖱️ Button Clicks (Callback Logic)
# ==========================================
@bot.callback_query_handler(func=lambda call: True)
def handle_query(call):
    cid = call.message.chat.id
    mid = call.message.message_id
    uid = call.from_user.id
    
    try:
        # --- 1. MAIN MENUS ---
        if call.data == "menu_bank":
            markup = InlineKeyboardMarkup()
            markup.row(InlineKeyboardButton("💡 Tips", callback_data="bank_tips"), InlineKeyboardButton("📌 General", callback_data="bank_gen"))
            markup.row(InlineKeyboardButton("🔍 Search", callback_data="bank_search"), InlineKeyboardButton("⚖️ Balance", callback_data="bank_bal"))
            markup.row(InlineKeyboardButton("💰 Resource", callback_data="bank_res"))
            bot.edit_message_text("🏦 **Guild Bank Commands:**\nकिस तरह की बैंक कमांड्स देखनी हैं?", cid, mid, reply_markup=markup, parse_mode='Markdown')
            
        elif call.data == "menu_monster":
            markup = InlineKeyboardMarkup()
            markup.row(InlineKeyboardButton("1. Queen Bee", callback_data="mon_1"), InlineKeyboardButton("2. Saberfang", callback_data="mon_2"))
            markup.row(InlineKeyboardButton("3. Gryphon", callback_data="mon_3"), InlineKeyboardButton("4. Mecha Trojan", callback_data="mon_4"))
            markup.row(InlineKeyboardButton("5. Jade Wyrm", callback_data="mon_5"), InlineKeyboardButton("6. Bon Appeti", callback_data="mon_6"))
            markup.row(InlineKeyboardButton("7. Gargantua", callback_data="mon_7"), InlineKeyboardButton("8. Frostwing", callback_data="mon_8"))
            markup.row(InlineKeyboardButton("9. Hell Drider", callback_data="mon_9"), InlineKeyboardButton("10. Snow Beast", callback_data="mon_10"))
            markup.row(InlineKeyboardButton("11. Tidal Titan", callback_data="mon_11"), InlineKeyboardButton("12. Terrorthorn", callback_data="mon_12"))
            markup.row(InlineKeyboardButton("13. Noceros", callback_data="mon_13"), InlineKeyboardButton("14. Mega Maggot", callback_data="mon_14"))
            markup.row(InlineKeyboardButton("15. Blackwing", callback_data="mon_15"), InlineKeyboardButton("16. Voodoo Shaman", callback_data="mon_16"))
            markup.row(InlineKeyboardButton("17. Grim Reaper", callback_data="mon_17"), InlineKeyboardButton("18. Hardrox", callback_data="mon_18"))
            bot.edit_message_text("🐲 **Monster Hunt:**\nजिस मॉन्स्टर की टीम देखनी है, उस पर क्लिक करें:", cid, mid, reply_markup=markup, parse_mode='Markdown')
            
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

        # --- 2. MONSTERS HANDLERS ---
        elif call.data.startswith("mon_"):
            mon_id = call.data.split("_")[1]
            name, m_url, s_url = MONSTERS[mon_id]
            bot.answer_callback_query(call.id, f"{name} की टीम ढूँढ रहा हूँ...")
            bot.send_photo(cid, photo=requests.get(m_url).content, caption=f"👾 **Monster: {name}**")
            bot.send_photo(cid, photo=requests.get(s_url).content, caption=f"⚔️ **Recommended Hero Setup for {name}**")

        # --- 3. GEAR HANDLERS ---
        elif call.data == "gear_mix":
            bot.answer_callback_query(call.id, "Mix ATK Load ho raha hai...")
            bot.send_photo(cid, photo=requests.get("https://raw.githubusercontent.com/chandan902640-lab/Thanos-bot/main/mixatk.jpg").content, caption="🛡️ Best Mix ATK Gear Setup")
        elif call.data == "gear_inf":
            bot.answer_callback_query(call.id, "Infantry ATK Load ho raha hai...")
            bot.send_photo(cid, photo=requests.get("https://raw.githubusercontent.com/chandan902640-lab/Thanos-bot/main/infatk.png").content, caption="⚔️ Best Infantry ATK Gear Setup")
        elif call.data == "gear_rng":
            bot.answer_callback_query(call.id, "Ranged ATK Load ho raha hai...")
            bot.send_photo(cid, photo=requests.get("https://raw.githubusercontent.com/chandan902640-lab/Thanos-bot/main/rangeatk.jpg").content, caption="🏹 Best Ranged ATK Gear Setup")
        elif call.data == "gear_cav":
            bot.answer_callback_query(call.id, "Cavalry ATK Load ho raha hai...")
            bot.send_photo(cid, photo=requests.get("https://raw.githubusercontent.com/chandan902640-lab/Thanos-bot/main/cavatk.png").content, caption="🐎 Best Cavalry ATK Gear Setup")

        # --- 4. BANK COMMANDS ---
        elif call.data == "bank_tips":
            bot.send_message(cid, "💡 **BANK TIPS & TRICKS:**\n\nUse underscore ('!setacc Player_1').\nHero Stages: Bank will not respond during long hero stages.")
        elif call.data == "bank_gen":
            text1 = "📌 **GENERAL COMMANDS (Part 1):**\n\n!payransom ➡️ Paid\n!clearboard ➡️ Deleted\n!stats ➡️ Report gifts\n!gryphon ➡️ Gryphon skill"
            bot.send_message(cid, text1)
        elif call.data == "bank_search":
            bot.send_message(cid, "🔍 **SEARCH COMMANDS:**\n\n!findtile [type] [level]\n!findmonster [name] [lvl]")
        elif call.data == "bank_bal":
            bot.send_message(cid, "⚖️ **BALANCE COMMANDS:**\n\n!bal ➡️ Personal RSS\n!adminbal ➡️ Bank RSS")
        elif call.data == "bank_res":
            bot.send_message(cid, "💰 **RESOURCE COMMANDS:**\n\n![type] [amount]\n!rss [F] [S] [W] [O] [G]")

        # --- 5. ECONOMY ---
        elif call.data == "eco_bal":
            bal = get_balance(uid)
            bot.answer_callback_query(call.id, f"🏦 आपके खाते में {bal} Coins हैं!", show_alert=True)
        elif call.data == "eco_daily":
            now = datetime.now()
            if uid in daily_cooldowns and (now - daily_cooldowns[uid]).total_seconds() < 86400:
                bot.answer_callback_query(call.id, f"⏳ आज का इनाम ले चुके हो!", show_alert=True)
            else:
                add_money(uid, 2000)
                daily_cooldowns[uid] = now
                bot.answer_callback_query(call.id, "🎁 2000 Coins जुड़ गए!", show_alert=True)
        elif call.data == "eco_slots":
            bal = get_balance(uid)
            if bal < 100:
                bot.answer_callback_query(call.id, "❌ बैलेंस कम है!", show_alert=True)
                return
            emojis = ["🍎", "💎", "🍒", "🔔", "⭐"]
            s1, s2, s3 = random.choice(emojis), random.choice(emojis), random.choice(emojis)
            if s1 == s2 == s3:
                add_money(uid, 1000)
                bot.send_message(cid, f"🎰 | {s1} | {s2} | {s3} |\n🚨 **JACKPOT! +1000 Coins**")
            elif s1 == s2 or s2 == s3 or s1 == s3:
                add_money(uid, 200)
                bot.send_message(cid, f"🎰 | {s1} | {s2} | {s3} |\n✨ **Win! +200 Coins**")
            else:
                add_money(uid, -100)
                bot.send_message(cid, f"🎰 | {s1} | {s2} | {s3} |\n❌ **Loss! -100 Coins**")

    except Exception as e:
        print(f"Error: {e}")
        bot.send_message(cid, "⚠️ कुछ गड़बड़ हुई है।")

# ==========================================
# 🔄 Multi-Source Scanner & Auto-Checker Loop
# ==========================================
def auto_checker_loop():
    time.sleep(5)  # Bot online hone ka wait
    try:
        # Multi-source historical testing items with designated event images
        sample_scans = [
            ("🎁 **Lords Mobile Old Code Found:** LORDS25K", "https://raw.githubusercontent.com/chandan902640-lab/Thanos-bot/main/mixatk.jpg"),
            ("🎉 **Event Tracked:** Lords Mobile Guild Fest Rewards & Setup", "https://raw.githubusercontent.com/chandan902640-lab/Thanos-bot/main/1.png")
        ]
        
        seen = load_seen_updates()
        
        for text_msg, img_url in sample_scans:
            if text_msg not in seen:
                bot.send_photo(TARGET_CHAT_ID, photo=requests.get(img_url).content, caption=text_msg, parse_mode='Markdown')
                save_seen_update(text_msg)
                time.sleep(3)
                
        print("✅ Multi-source scan completed successfully!")
    except Exception as e:
        print(f"Multi-Source Error: {e}")

    while True:
        try:
            # Yahan aage real web scraping ya API tracking logic aayega
            pass
        except Exception as e:
            print(f"Auto Checker Error: {e}")
            
        time.sleep(600)

# ==========================================
# 🏃 Server Start
# ==========================================
if __name__ == "__main__":
    print("✅ Thanos Telegram Bot is Fully Active with ALL Features!")
    keep_alive()
    
    threading.Thread(target=auto_checker_loop, daemon=True).start()
    
    bot.infinity_polling()
