
import telebot
from telebot.types import Message, ReplyKeyboardMarkup, ReplyKeyboardRemove, ForceReply
from database import Database

TOKEN = "8560396008:AAFsT1MCeJbxqwqxK2kI7nQdm7GdjjMfHos"
ADMIN_ID = [8130553571, 7754612381]

bot = telebot.TeleBot(TOKEN)
db = Database("kinolar.db")

CHANNELS = []

# =======================
# 🔥 STATE
# =======================
user_state = {}

# =======================
# 👤 TRACK USER
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
        bot.send_message(message.chat.id, "👋 Salom Admin", reply_markup=admin_buttons())
    else:
        bot.send_message(message.chat.id, "🎬 Kino kodini yuboring", reply_markup=ReplyKeyboardRemove())

# =======================
# 📊 STATISTIKA
# =======================
@bot.message_handler(func=lambda m: m.text == "📊 Statistika")
def stats(message):
    if message.from_user.id not in ADMIN_ID:
        return

    total = db.get_users_count()
    active = db.get_active_users(1440)

    bot.send_message(message.chat.id, f"👥 Jami: {total}\n🔥 Aktiv: {active}")

# =======================
# 📢 REKLAMA
# =======================
@bot.message_handler(func=lambda m: m.text == "📢 Reklama")
def broadcast_start(message):
    if message.from_user.id not in ADMIN_ID:
        return

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
@bot.message_handler(func=lambda m: m.text == "📢 Kanal qo'shish")
def add_channel(message):
    if message.from_user.id not in ADMIN_ID:
        return

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
# 📋 KANALLAR
# =======================
@bot.message_handler(func=lambda m: m.text == "📋 Kanallar ro'yxati")
def show_channels(message):
    if message.from_user.id not in ADMIN_ID:
        return

    if CHANNELS:
        bot.send_message(message.chat.id, "\n".join(CHANNELS))
    else:
        bot.send_message(message.chat.id, "❌ Yo‘q")

# =======================
# ❌ KANAL O‘CHIRISH
# =======================
@bot.message_handler(func=lambda m: m.text == "❌ Kanal o'chirish")
def delete_channel(message):
    if message.from_user.id not in ADMIN_ID:
        return

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
@bot.message_handler(func=lambda m: m.text == "🗑 Kinoni o'chirish")
def del_movie(message):
    if message.from_user.id not in ADMIN_ID:
        return

    msg = bot.send_message(message.chat.id, "Kod:", reply_markup=ForceReply())
    bot.register_next_step_handler(msg, process_delete)

def process_delete(message):
    if db.delete_movie(message.text.strip().lower()):
        bot.send_message(message.chat.id, "✅ O'chirildi", reply_markup=admin_buttons())
    else:
        bot.send_message(message.chat.id, "❌ Yo'q")

# =======================
# 🎬 ADD MOVIE
# =======================
@bot.message_handler(func=lambda m: m.text == "➕ Kino qo'shish")
def ask_movie(message):
    if message.from_user.id not in ADMIN_ID:
        return

    user_state[message.from_user.id] = "waiting_movie"

    bot.send_message(
        message.chat.id,
        "🎬 Kino yuboring\n📌 Format: kod nom"
    )

@bot.message_handler(content_types=['video'])
def add_movie(message):
    user_id = message.from_user.id

    if user_id not in ADMIN_ID:
        return

    if user_state.get(user_id) != "waiting_movie":
        return

    if not message.caption:
        bot.send_message(message.chat.id, "❌ Caption yozing")
        return

    parts = message.caption.split(" ", 1)

    if len(parts) < 2:
        bot.send_message(message.chat.id, "❌ Format: kod nom")
        return

    code = parts[0].lower()
    name = parts[1]

    db.add_movie(code, name, message.video.file_id)

    user_state[user_id] = None

    bot.send_message(message.chat.id, "✅ Saqlandi!", reply_markup=admin_buttons())

# =======================
# 🎬 BARCHA KINOLAR (FIXED)
# =======================
@bot.message_handler(func=lambda m: m.text == "🎬 Barcha kinolar")
def all_movies(message):
    if message.from_user.id not in ADMIN_ID:
        return

    movies = db.get_all_movies()

    if not movies:
        bot.send_message(message.chat.id, "❌ Kino yo‘q")
        return

    text = "🎬 Barcha kinolar:\n\n"

    for m in movies:
        text += f"🎞 {m[0]} - {m[1]}\n"

    bot.send_message(message.chat.id, text)

# =======================
# 🔍 SEARCH (LAST PRIORITY!)
# =======================
@bot.message_handler(content_types=['text'])
def search(message):
    track_user(message)

    if message.text in [
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

# =======================
# ▶️ RUN
# =======================
if __name__ == "__main__":
    print("🤖 Bot ishladi")
    bot.infinity_polling()