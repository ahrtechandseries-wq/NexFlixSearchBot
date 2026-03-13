import telebot
from telebot import types
import sqlite3
import os

# আপনার দেওয়া টোকেন ও আইডি
API_TOKEN = '8591858459:AAESL_0xlUvBMKEyUi3e9P5p5r2XUVKriF8'
bot = telebot.TeleBot(API_TOKEN)

ADMIN_ID = 7414830213 
ADMIN_USERNAME = "anikhasanjihad"

# ডাটাবেস সেটআপ
def init_db():
    conn = sqlite3.connect('nexflix.db')
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS movies 
                      (name TEXT, url TEXT, poster TEXT)''')
    conn.commit()
    conn.close()

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
        bot.reply_to(message, "❌ ফরম্যাট ভুল!")

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
        bot.send_message(message.chat.id, "❌ মুভিটি আমাদের সাইটে নেই। অ্যাডমিনকে জানান।", reply_markup=markup)

if __name__ == "__main__":
    init_db()
    print("NexFlix Bot is Running...")
    bot.infinity_polling()
  
