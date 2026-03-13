import telebot
from telebot import types
import sqlite3
import os
from flask import Flask
from threading import Thread

# ১. Render এর Environment Variable থেকে টোকেন ও আইডি পড়ার সিস্টেম
API_TOKEN = os.environ.get('BOT_TOKEN')
ADMIN_ID = int(os.environ.get('ADMIN_ID', 0))
ADMIN_USERNAME = os.environ.get('ADMIN_USERNAME', 'anikhasanjihad')

bot = telebot.TeleBot(API_TOKEN)

# --- ফ্রি হোস্টিং এর জন্য Flask ওয়েব সার্ভার (বটকে জাগিয়ে রাখতে) ---
app = Flask('')

@app.route('/')
def home():
    return "NexFlix Bot is Online!"

def run():
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    t = Thread(target=run)
    t.start()
# ---------------------------------------------------------

# ডাটাবেস সেটআপ
def init_db():
    conn = sqlite3.connect('nexflix.db')
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS movies 
                      (name TEXT, url TEXT, poster TEXT)''')
    conn.commit()
    conn.close()

# এডমিন মুভি এড করবে: /add
@bot.message_handler(commands=['add'])
def add_movie(message):
    if message.from_user.id == ADMIN_ID:
        msg = bot.reply_to(message, "✅ মুভি অ্যাড ফরম্যাট:\n`নাম | পোস্ট লিঙ্ক | পোস্টার লিঙ্ক`", parse_mode="Markdown")
        bot.register_next_step_handler(msg, save_movie)
    else:
        bot.reply_to(message, "❌ আপনি অ্যাডমিন নন।")

def save_movie(message):
    try:
        data = message.text.split('|')
        name = data[0].strip()
        url = data[1].strip()
        poster = data[2].strip()
        
        conn = sqlite3.connect('nexflix.db')
        cursor = conn.cursor()
        cursor.execute("INSERT INTO movies VALUES (?, ?, ?)", (name, url, poster))
        conn.commit()
        conn.close()
        bot.reply_to(message, f"🎯 সেভ হয়েছে: {name}")
    except:
        bot.reply_to(message, "❌ ফরম্যাট ভুল! নাম | লিঙ্ক | পোস্টার এভাবে দিন।")

# গ্রুপে মুভি সার্চ করা
@bot.message_handler(func=lambda message: True)
def search_movie(message):
    query = message.text.strip().lower()
    if len(query) < 2: return

    conn = sqlite3.connect('nexflix.db')
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM movies WHERE name LIKE ?", ('%' + query + '%',))
    results = cursor.fetchall()
    conn.close()

    if results:
        for name, url, poster in results:
            markup = types.InlineKeyboardMarkup()
            markup.add(types.InlineKeyboardButton("🎬 View & Download Movie", url=url))
            try:
                bot.send_photo(message.chat.id, poster, caption=f"🍿 *Movie Found:* {name}", parse_mode="Markdown", reply_markup=markup)
            except:
                bot.send_message(message.chat.id, f"🍿 *Movie:* {name}", parse_mode="Markdown", reply_markup=markup)
    else:
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("📝 Request to Admin", url=f"https://t.me/{ADMIN_USERNAME}"))
        bot.reply_to(message, "❌ এই মুভিটি আমাদের সাইটে নেই। অ্যাডমিনকে জানান।", reply_markup=markup)

if __name__ == "__main__":
    init_db()
    keep_alive() # ওয়েব সার্ভার চালু করবে
    print("NexFlix Bot is Running...")
    bot.infinity_polling()
    
