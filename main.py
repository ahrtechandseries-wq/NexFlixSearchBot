import telebot
from telebot import types
import sqlite3
import os
from flask import Flask
from threading import Thread
import threading
import time

# আপনার তথ্য
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

# --- Database Setup ---
def init_db():
    conn = sqlite3.connect('nexflix.db')
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS movies 
                      (name TEXT, url TEXT, poster TEXT)''')
    conn.commit()
    conn.close()

# --- Auto Delete Function ---
def delete_message_after_time(chat_id, message_id, delay):
    time.sleep(delay)
    try:
        bot.delete_message(chat_id, message_id)
    except Exception as e:
        print(f"Error deleting message: {e}")

# --- Commands ---
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

@bot.message_handler(commands=['backup'])
def backup_database(message):
    if message.from_user.id == ADMIN_ID:
        try:
            with open('nexflix.db', 'rb') as f:
                bot.send_document(message.chat.id, f, caption="📂 NexFlix Database Backup")
        except Exception as e:
            bot.reply_to(message, f"❌ সমস্যা: {e}")

@bot.message_handler(commands=['help'])
def help_command(message):
    help_text = (
        "❓ **How to Use NexFlix Bot:**\n\n"
        "1️⃣ Just send the movie or series name.\n"
        "2️⃣ Result will be deleted after 5 minutes for safety."
    )
    bot.reply_to(message, help_text, parse_mode="Markdown")

@bot.message_handler(commands=['website'])
def website_command(message):
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("🌐 Visit NexFlix Website", url="https://rnexflix.top"))
    bot.send_message(message.chat.id, "Click below to visit official website:", reply_markup=markup)

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
        bot.reply_to(message, "❌ ভুল ফরম্যাট! আবার চেষ্টা করুন।")

# --- Search & Auto Delete ---
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
                # পোস্টারসহ মেসেজ পাঠানো
                sent_msg = bot.send_photo(message.chat.id, poster, caption=f"🍿 *Found:* {name}\n\n⚠️ This message will be deleted in 5 mins.", parse_mode="Markdown", reply_markup=markup)
            except:
                # পোস্টার না থাকলে শুধু টেক্সট পাঠানো
                sent_msg = bot.send_message(message.chat.id, f"🍿 *Movie:* {name}\n\n⚠️ This message will be deleted in 5 mins.", parse_mode="Markdown", reply_markup=markup)
            
            # ৫ মিনিট পর ডিলিট করার জন্য থ্রেড চালু করা
            threading.Thread(target=delete_message_after_time, args=(message.chat.id, sent_msg.message_id, 300)).start()
    else:
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("📝 Request to Admin", url=f"https://t.me/+-Bo6KSNJWf9iNjQ1"))
        bot.reply_to(message, "❌ মুভিটি ডাটাবেসে নেই। রিকোয়েস্ট করুন।", reply_markup=markup)

if __name__ == "__main__":
    init_db()
    keep_alive()
    print("Bot is Live...")
    bot.infinity_polling()
