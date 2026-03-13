import telebot
from telebot import types
import sqlite3
import os
from flask import Flask
from threading import Thread

# সরাসরি এখানে আপনার তথ্য বসিয়ে দিলাম যেন ভেরিয়েবলের ঝামেলা না থাকে
API_TOKEN = '8591858459:AAESL_0xlUvBMKEyUi3e9P5p5r2XUVKriF8'
ADMIN_ID = 7414830213
ADMIN_USERNAME = "anikhasanjihad"

bot = telebot.TeleBot(API_TOKEN)

# --- Flask Server (Always On) ---
app = Flask('')
@app.route('/')
def home():
    return "NexFlix Bot is Online!"

def run():
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    t = Thread(target=run)
    t.start()
# -------------------------------

def init_db():
    conn = sqlite3.connect('nexflix.db')
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS movies 
                      (name TEXT, url TEXT, poster TEXT)''')
    conn.commit()
    conn.close()

@bot.message_handler(commands=['start'])
def start(message):
    bot.reply_to(message, "NexFlix Bot-এ স্বাগতম! মুভির নাম লিখে সার্চ দিন।")

@bot.message_handler(commands=['add'])
def add_movie(message):
    if message.from_user.id == ADMIN_ID:
        msg = bot.reply_to(message, "✅ ফরম্যাট: `নাম | লিঙ্ক | পোস্টার`", parse_mode="Markdown")
        bot.register_next_step_handler(msg, save_movie)
    else:
        bot.reply_to(message, "❌ আপনি অ্যাডমিন নন।")

def save_movie(message):
    try:
        data = message.text.split('|')
        conn = sqlite3.connect('nexflix.db')
        cursor = conn.cursor()
        cursor.execute("INSERT INTO movies VALUES (?, ?, ?)", (data[0].strip(), data[1].strip(), data[2].strip()))
        conn.commit()
        conn.close()
        bot.reply_to(message, "🎯 মুভি সেভ হয়েছে!")
    except:
        bot.reply_to(message, "❌ ভুল ফরম্যাট!")

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
            markup.add(types.InlineKeyboardButton("🎬 Download Now", url=url))
            try:
                bot.send_photo(message.chat.id, poster, caption=f"🍿 *Found:* {name}", parse_mode="Markdown", reply_markup=markup)
            except:
                bot.send_message(message.chat.id, f"🍿 *Movie:* {name}", parse_mode="Markdown", reply_markup=markup)
    else:
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("📝 Request to Admin", url=f"https://t.me/+-Bo6KSNJWf9iNjQ1"))
        bot.reply_to(message, "❌ মুভিটি নেই। রিকোয়েস্ট করুন।", reply_markup=markup)

if __name__ == "__main__":
    init_db()
    keep_alive()
    print("Bot is Live...")
    bot.infinity_polling()
