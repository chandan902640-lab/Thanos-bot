import os
import threading
import requests
import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from http.server import BaseHTTPRequestHandler, HTTPServer

# 🌐 Render को जगाए रखने के लिए 24/7 वेब सर्वर (Same as before)
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

# 🤖 Telegram Bot Setup
BOT_TOKEN = os.environ.get("TELEGRAM_TOKEN")
GEMINI_KEY = os.environ.get("GEMINI_API_KEY")

if not BOT_TOKEN:
    print("❌ Error: TELEGRAM_TOKEN nahi mila!")
    exit()

bot = telebot.TeleBot(BOT_TOKEN)

# 🛠️ AI फंक्शन (Telegram ke liye Synchronous banaya gaya hai)
def get_ai_response(prompt):
    if not GEMINI_KEY:
        return "⚠️ Gemini API Key सेट नहीं है!"
        
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={GEMINI_KEY}"
    headers = {'Content-Type': 'application/json'}
    data = {"contents": [{"parts": [{"text": prompt}]}]}

    try:
        response = requests.post(url, headers=headers, json=data)
        if response.status_code == 200:
            result = response.json()
            return result['candidates'][0]['content']['parts'][0]['text']
        else:
            return "⚠️ गूगल AI अभी व्यस्त है या आपका मैसेज समझ नहीं पाया।"
    except Exception as e:
        return f"⚠️ Error: {e}"

# 👑 99 कमांड (कंट्रोल पैनल - Telegram Buttons ke sath)
@bot.message_handler(commands=['start', '99', 'menu'])
def send_panel(message):
    markup = InlineKeyboardMarkup()
    # Telegram Buttons Row 1
    markup.row(
        InlineKeyboardButton("🏦 Guild Bank", callback_data="menu_bank"),
        InlineKeyboardButton("🐲 Monster Hunt", callback_data="menu_monster")
    )
    # Telegram Buttons Row 2
    markup.row(
        InlineKeyboardButton("⚙️ Best Gear", callback_data="menu_gear"),
        InlineKeyboardButton("💰 Economy & Shop", callback_data="menu_economy")
    )
    
    welcome_text = (
        "👑 **THANOS BOT - CONTROL PANEL** 👑\n\n"
        f"Hello {message.from_user.first_name}!\n"
        "👇 IGG/Lords Mobile के सभी फीचर्स और मेनू के लिए नीचे दिए गए बटन्स का इस्तेमाल करें:"
    )
    bot.send_message(message.chat.id, welcome_text, reply_markup=markup, parse_mode='Markdown')

# 🖱️ Button Clicks (Callbacks) Handle karna
@bot.callback_query_handler(func=lambda call: True)
def handle_query(call):
    if call.data == "menu_bank":
        bot.answer_callback_query(call.id, "🏦 Guild Bank Menu Opening...")
        bot.send_message(call.message.chat.id, "🏦 **Guild Bank Commands:**\n`!payransom`, `!shield`, `!bal` aadi jald hi add ki jayengi!")
        
    elif call.data == "menu_monster":
        bot.answer_callback_query(call.id, "🐲 Monster Hunt Opening...")
        bot.send_message(call.message.chat.id, "🐲 **Monster Hunt:**\nKiski details chahiye? Type karein: `/monster Queen Bee`")
        
    elif call.data == "menu_gear":
        bot.answer_callback_query(call.id, "⚙️ Gear Setup Opening...")
        bot.send_message(call.message.chat.id, "🛡️ **Gear Setups:** Mix ATK, Infantry, Cavalry aadi jald hi aayenge!")
        
    elif call.data == "menu_economy":
        bot.answer_callback_query(call.id, "💰 Economy Opening...")
        bot.send_message(call.message.chat.id, "🪙 **Economy:** Type `/bal` to check balance (Work in progress)!")

# 🐲 Monster AI Command
@bot.message_handler(commands=['monster'])
def monster_command(message):
    # '/monster Queen Bee' me se 'Queen Bee' nikalna
    text = message.text.replace('/monster', '').strip()
    if not text:
        bot.reply_to(message, "⚠️ भाई, किसी मॉन्स्टर का नाम तो बताओ! जैसे: `/monster Queen Bee`")
        return
        
    bot.reply_to(message, f"⏳ **{text}** की बेस्ट टीम ढूँढ रहा हूँ, थोड़ा इंतज़ार करें...")
    
    prompt = f"Lords Mobile game में '{text}' monster को मारने के लिए Best F2P और P2P heroes की लिस्ट बताओ. जवाब हिंदी और इंग्लिश मिक्स में बुलेट पॉइंट्स में देना."
    ai_reply = get_ai_response(prompt)
    bot.send_message(message.chat.id, f"👾 **{text.title()}** को मारने के बेस्ट हीरोज:\n\n{ai_reply}")

# 💬 Normal AI Chat (Hi, Hello ya normal sawal)
@bot.message_handler(func=lambda m: True)
def chat_ai(message):
    text = message.text.lower()
    if text in ['hi', 'hello', 'hey']:
        send_panel(message)
    else:
        # Agar koi normal sawal puche toh AI se jawab do
        bot.send_chat_action(message.chat.id, 'typing')
        prompt = f"Act like a helpful Lords Mobile Bot named Thanos. Reply in Hinglish. User says: {message.text}"
        ai_reply = get_ai_response(prompt)
        bot.reply_to(message, ai_reply)

# 🏃 बॉट चालू करें
if __name__ == "__main__":
    print("✅ Thanos Telegram Bot Start Ho Gaya Hai!")
    keep_alive()
    bot.infinity_polling()
