import telebot
from telebot import types
import sqlite3
import threading
import time
import os

# --- কনফিগারেশন ---
# আপনার নতুন টোকেনটি এখানে বসিয়েছি
API_TOKEN = '8591858459:AAGfJ8RcGIn0DW70Ei7Vb1fTAu1tdZvvI8s'
ADMIN_ID = 7414830213
CHANNEL_ID = -1002347717460 

# লিঙ্ক দুটি আলাদা করা হয়েছে
FORCE_SUB_LINK = 'https://t.me/+ow2Xg3aefO1hNzBl'      # জয়েন লিঙ্ক
REQUEST_ADMIN_LINK = 'https://t.me/+-Bo6KSNJWf9iNjQ1'  # রিকোয়েস্ট লিঙ্ক

bot = telebot.TeleBot(API_TOKEN)

# --- ডাটাবেস সেটআপ ---
def init_db():
    conn = sqlite3.connect('nexflix.db')
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS movies (name TEXT, url TEXT, poster TEXT)''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS users (user_id INTEGER UNIQUE)''')
    conn.commit()
    conn.close()

# ৫ মিনিট পর মেসেজ ডিলিট করার ফাংশন
def delete_message_after_time(chat_id, message_id, delay):
    time.sleep(delay)
    try:
        bot.delete_message(chat_id, message_id)
    except:
        pass

# সাবস্ক্রিপশন চেক করার ফাংশন
def is_subscribed(user_id):
    try:
        status = bot.get_chat_member(CHANNEL_ID, user_id).status
        return status in ['member', 'administrator', 'creator']
    except:
        return True 

# --- কমান্ড হ্যান্ডলার ---

@bot.message_handler(commands=['start'])
def start(message):
    conn = sqlite3.connect('nexflix.db')
    cursor = conn.cursor()
    cursor.execute("INSERT OR IGNORE INTO users VALUES (?)", (message.from_user.id,))
    conn.commit()
    conn.close()
    bot.reply_to(message, "👋 NexFlix Bot-এ স্বাগতম!\n\nমুভির নাম লিখে সার্চ দিন।")

# ব্যাকআপ কমান্ড
@bot.message_handler(commands=['backup'])
def send_backup(message):
    if message.from_user.id == ADMIN_ID:
        try:
            with open('nexflix.db', 'rb') as doc:
                bot.send_document(message.chat.id, doc, caption="📂 লেটেস্ট ডাটাবেস।\nGitHub-এ আপলোড দিন।")
        except:
            bot.reply_to(message, "❌ ফাইলটি পাওয়া যায়নি!")

# ব্রডকাস্ট কমান্ড
@bot.message_handler(commands=['broadcast'])
def broadcast(message):
    if message.from_user.id == ADMIN_ID:
        msg = bot.reply_to(message, "📢 ব্রডকাস্ট মেসেজটি লিখুন:")
        bot.register_next_step_handler(msg, send_broadcast_logic)

def send_broadcast_logic(message):
    conn = sqlite3.connect('nexflix.db')
    cursor = conn.cursor()
    cursor.execute("SELECT user_id FROM users")
    users = cursor.fetchall()
    conn.close()
    count = 0
    for user in users:
        try:
            bot.send_message(user[0], message.text)
            count += 1
        except: continue
    bot.reply_to(message, f"✅ {count} জন ইউজারকে পাঠানো হয়েছে।")

# মুভি অ্যাড করার কমান্ড
@bot.message_handler(commands=['add'])
def add_movie_start(message):
    if message.from_user.id == ADMIN_ID:
        msg = bot.reply_to(message, "📝 মুভির নাম দিন:")
        bot.register_next_step_handler(msg, process_movie_name)

def process_movie_name(message):
    movie_name = message.text
    msg = bot.reply_to(message, f"🔗 '{movie_name}' এর লিঙ্ক দিন:")
    bot.register_next_step_handler(msg, process_movie_url, movie_name)

def process_movie_url(message, movie_name):
    movie_url = message.text
    msg = bot.reply_to(message, "🖼 মুভির পোস্টার লিঙ্ক দিন:")
    bot.register_next_step_handler(msg, process_movie_final, movie_name, movie_url)

def process_movie_final(message, movie_name, movie_url):
    movie_poster = message.text
    conn = sqlite3.connect('nexflix.db')
    cursor = conn.cursor()
    cursor.execute("INSERT INTO movies VALUES (?, ?, ?)", (movie_name, movie_url, movie_poster))
    conn.commit()
    conn.close()
    bot.reply_to(message, f"✅ '{movie_name}' সেভ হয়েছে!\n⚠️ /backup নিয়ে GitHub-এ আপলোড দিন।")

# --- মুভি সার্চ হ্যান্ডলার ---
@bot.message_handler(func=lambda message: True)
def handle_search(message):
    if not is_subscribed(message.from_user.id):
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("📢 Join Channel", url=FORCE_SUB_LINK))
        bot.reply_to(message, "❌ আমাদের চ্যানেলে জয়েন না থাকলে মুভি পাবেন না!", reply_markup=markup)
        return

    query = message.text.strip().lower()
    conn = sqlite3.connect('nexflix.db')
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM movies WHERE name LIKE ?", ('%' + query + '%',))
    results = cursor.fetchall()
    conn.close()

    if results:
        for name, url, poster in results:
            markup = types.InlineKeyboardMarkup()
            markup.add(types.InlineKeyboardButton("🎬 Download Link", url=url))
            
            try:
                sent_photo = bot.send_photo(
                    message.chat.id, 
                    poster, 
                    caption=f"🍿 *Movie:* {name.upper()}", 
                    parse_mode="Markdown", 
                    reply_markup=markup
                )
                info_msg = bot.reply_to(sent_photo, "⚠️ এই মুভি কার্ডটি ৫ মিনিট পর অটো-ডিলিট হয়ে যাবে।")
                
                threading.Thread(target=delete_message_after_time, args=(message.chat.id, sent_photo.message_id, 300)).start()
                threading.Thread(target=delete_message_after_time, args=(message.chat.id, info_msg.message_id, 300)).start()
            except:
                sent_msg = bot.send_message(message.chat.id, f"🍿 *Movie:* {name}\n\n🔗 [Download Link]({url})", parse_mode="Markdown", reply_markup=markup)
                threading.Thread(target=delete_message_after_time, args=(message.chat.id, sent_msg.message_id, 300)).start()
    else:
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("📝 Request Admin", url=REQUEST_ADMIN_LINK))
        bot.reply_to(message, "😔 দুঃখিত, মুভিটি আমাদের ডাটাবেসে নেই।\n\nনিচের বাটনে ক্লিক করে রিকোয়েস্ট দিন।", reply_markup=markup)

if __name__ == "__main__":
    init_db()
    print("NexFlix Bot is starting...")
    # skip_pending=True দিলে আগের ঝুলে থাকা রিকোয়েস্ট এরর তৈরি করবে না
    bot.infinity_polling(skip_pending=True)
    
