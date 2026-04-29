import telebot
from telebot.types import (
    Message, ReplyKeyboardMarkup, ReplyKeyboardRemove, ForceReply
)
from database import Database

TOKEN = "8560396008:AAFsT1MCeJbxqwqxK2kI7nQdm7GdjjMfHos"
ADMIN_ID = [8130553571, 7754612381]

bot = telebot.TeleBot(TOKEN)
db = Database("kinolar.db")

CHANNELS = []

# =======================
# 🔥 STATE (ENG MUHIM FIX)
# =======================
user_state = {}

# =======================
# 👤 USER TRACKER
# =======================
def track_user(message):
    try:
        db.add_user(message.from_user.id)
        db.update_last_active(message.from_user.id)
    except:
        pass

# =======================
# 🔘 ADMIN PANEL
# =======================
def admin_buttons():
    markup = ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(
        "🎬 Barcha kinolar",
        "➕ Kino qo'shish",
        "🗑 Kinoni o'chirish",
        "📢 Kanal qo'shish",
        "📋 Kanallar ro'yxati",
        "❌ Kanal o'chirish",
        "📊 Statistika",
        "📢 Reklama"
    )
    return markup

# =======================
# 📢 START
# =======================
@bot.message_handler(commands=["start"])
def start(message: Message):
    track_user(message)

    if message.from_user.id in ADMIN_ID:
        bot.send_message(message.chat.id, "👋 Salom Admin ", reply_markup=admin_buttons())
    else:
        bot.send_message(message.chat.id, "🎬 Kino kodini yuboring", reply_markup=ReplyKeyboardRemove())

# =======================
# 📊 STATISTIKA
# =======================
@bot.message_handler(func=lambda m: m.text == "📊 Statistika" and m.from_user.id in ADMIN_ID)
def stats(message):
    total = db.get_users_count()
    active = db.get_active_users(1440)
    bot.send_message(message.chat.id, f"👥 Jami: {total}\n🔥 Aktiv (24h): {active}")

# =======================
# 📢 REKLAMA
# =======================
@bot.message_handler(func=lambda m: m.text == "📢 Reklama" and m.from_user.id in ADMIN_ID)
def broadcast_start(message):
    msg = bot.send_message(message.chat.id, "📨 Xabar yuboring:", reply_markup=ForceReply())
    bot.register_next_step_handler(msg, send_broadcast)

def send_broadcast(message):
    users = db.get_all_users()
    ok, fail = 0, 0

    for user_id in users:
        try:
            bot.copy_message(user_id, message.chat.id, message.message_id)
            ok += 1
        except:
            fail += 1

    bot.send_message(message.chat.id, f"✅ {ok}\n❌ {fail}", reply_markup=admin_buttons())

# =======================
# 📢 KANAL QO‘SHISH
# =======================
@bot.message_handler(func=lambda m: m.text == "📢 Kanal qo'shish" and m.from_user.id in ADMIN_ID)
def add_channel(message):
    msg = bot.send_message(message.chat.id, "📢 Kanal username:", reply_markup=ForceReply())
    bot.register_next_step_handler(msg, save_channel)

def save_channel(message):
    username = message.text.strip()

    if username in CHANNELS:
        bot.send_message(message.chat.id, "⚠️ Bor")
        return

    CHANNELS.append(username)
    bot.send_message(message.chat.id, f"✅ Qo‘shildi: {username}", reply_markup=admin_buttons())

# =======================
# ❌ KANAL O‘CHIRISH
# =======================
@bot.message_handler(func=lambda m: m.text == "❌ Kanal o'chirish" and m.from_user.id in ADMIN_ID)
def delete_channel(message):
    msg = bot.send_message(message.chat.id, "Kanal username:", reply_markup=ForceReply())
    bot.register_next_step_handler(msg, process_delete_channel)

def process_delete_channel(message):
    username = message.text.strip()

    if username in CHANNELS:
        CHANNELS.remove(username)
        bot.send_message(message.chat.id, "✅ O‘chirildi", reply_markup=admin_buttons())
    else:
        bot.send_message(message.chat.id, "❌ Yo‘q")

# =======================
# 🗑 MOVIE DELETE
# =======================
@bot.message_handler(func=lambda m: m.text == "🗑 Kinoni o'chirish" and m.from_user.id in ADMIN_ID)
def del_movie(message):
    msg = bot.send_message(message.chat.id, "Kod:", reply_markup=ForceReply())
    bot.register_next_step_handler(msg, process_delete)

def process_delete(message):
    if db.delete_movie(message.text.strip().lower()):
        bot.send_message(message.chat.id, "✅ O'chirildi", reply_markup=admin_buttons())
    else:
        bot.send_message(message.chat.id, "❌ Yo'q")

# =======================
# 🎬 ➕ KINO QO‘SHISH (FIX QILINGAN)
# =======================
@bot.message_handler(func=lambda m: m.text == "➕ Kino qo'shish" and m.from_user.id in ADMIN_ID)
def ask_movie(message):
    user_state[message.from_user.id] = "waiting_movie"

    bot.send_message(
        message.chat.id,
        "🎬 Salom!\n\n"
        "📥 Kino videosini yuboring va captionga yozing:\n"
        "👉 kod nomi\n\n"
        "Misol: 1 Titanic"
    )

@bot.message_handler(content_types=['video', 'document', 'audio', 'photo', 'text'])
def add_movie(message):
    user_id = message.from_user.id

    if user_id not in ADMIN_ID:
        return

    if user_state.get(user_id) != "waiting_movie":
        return

    # ❌ VIDEO EMAS BO'LSA
    if not message.content_type == "video":
        bot.send_message(
            message.chat.id,
            "❌ Noto‘g‘ri format!\n\n"
            "📥 Faqat VIDEO yuboring."
        )
        return

    # ❌ CAPTION YO'Q BO'LSA
    if not message.caption:
        bot.send_message(
            message.chat.id,
            "❌ Caption yozing!\nFormat: kod nomi"
        )
        return

    parts = message.caption.split(" ", 1)

    if len(parts) < 2:
        bot.send_message(
            message.chat.id,
            "❌ Format noto‘g‘ri!\nTo‘g‘ri format: kod nomi"
        )
        return

    code = parts[0].lower()
    name = parts[1]

    db.add_movie(code, name, message.video.file_id)

    user_state[user_id] = None

    bot.send_message(
        message.chat.id,
        "✅ Kino saqlandi!",
        reply_markup=admin_buttons()
    )
# =======================
# 🔍 SEARCH
# =======================
@bot.message_handler(content_types=['text'])
def search(message):
    track_user(message)

    if message.from_user.id in ADMIN_ID and message.text in [
        "🎬 Barcha kinolar",
        "➕ Kino qo'shish",
        "🗑 Kinoni o'chirish",
        "📢 Kanal qo'shish",
        "📋 Kanallar ro'yxati",
        "❌ Kanal o'chirish",
        "📊 Statistika",
        "📢 Reklama"
    ]:
        return

    movie = db.get_movie(message.text.strip().lower())

    if movie:
        bot.send_video(message.chat.id, movie[2], caption=movie[1])
    else:
        if message.from_user.id not in ADMIN_ID:
            bot.reply_to(message, "❌ Topilmadi")




@bot.message_handler(func=lambda m: m.text == "🎬 Barcha kinolar" and m.from_user.id in ADMIN_ID)
def all_movies(message):
    movies = db.get_all_movies()  # DB da shunaqa funksiya bo‘lishi kerak

    if not movies:
        bot.send_message(message.chat.id, "❌ Hech qanday kino yo‘q")
        return

    text = "🎬 Barcha kinolar:\n\n"

    for movie in movies:
        # movie = (code, name, file_id)
        text += f"🎞 {movie[0]} - {movie[1]}\n"

    bot.send_message(message.chat.id, text)
# =======================
# ▶️ RUN
# =======================
if __name__ == "__main__":
    print("🤖 Bot ishladi")
    bot.infinity_polling()