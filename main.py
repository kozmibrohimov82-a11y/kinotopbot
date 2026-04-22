import telebot
from telebot.types import (
    Message, ReplyKeyboardMarkup, KeyboardButton,
    ReplyKeyboardRemove, ForceReply,
    InlineKeyboardMarkup, InlineKeyboardButton
)
from database import Database

TOKEN = "8560396008:AAFsT1MCeJbxqwqxK2kI7nQdm7GdjjMfHos"
ADMIN_ID = [8130553571,7754612381]

bot = telebot.TeleBot(TOKEN)
db = Database("kinolar.db")

CHANNELS = []


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
        KeyboardButton("🎬 Barcha kinolar"),
        KeyboardButton("➕ Kino qo'shish"),
        KeyboardButton("🗑 Kinoni o'chirish"),
        KeyboardButton("📢 Kanal qo'shish"),
        KeyboardButton("📋 Kanallar ro'yxati"),
        KeyboardButton("❌ Kanal o'chirish"),
        KeyboardButton("📊 Statistika"),
        KeyboardButton("📢 Reklama")
    )
    return markup


# =======================
# 📢 START
# =======================
@bot.message_handler(commands=["start"])
def start(message: Message):
    track_user(message)

    if message.from_user.id == ADMIN_ID:
        bot.send_message(message.chat.id, "👋 Admin panel", reply_markup=admin_buttons())
    else:
        bot.send_message(message.chat.id, "🎬 Kino kodini yuboring", reply_markup=ReplyKeyboardRemove())


# =======================
# 📊 STATISTIKA
# =======================
@bot.message_handler(func=lambda m: m.text == "📊 Statistika" and m.from_user.id == ADMIN_ID)
def stats(message):
    total = db.get_users_count()
    active = db.get_active_users(1440)

    bot.send_message(
        message.chat.id,
        f"👥 Jami: {total}\n🔥 Aktiv (24h): {active}"
    )


# =======================
# 📢 REKLAMA (BROADCAST)
# =======================
@bot.message_handler(func=lambda m: m.text == "📢 Reklama" and m.from_user.id == ADMIN_ID)
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
# 📢 KANAL QO'SHISH
# =======================
@bot.message_handler(func=lambda m: m.text == "📢 Kanal qo'shish" and m.from_user.id == ADMIN_ID)
def add_channel(message):
    msg = bot.send_message(message.chat.id, "📢 Kanal username:", reply_markup=ForceReply())
    bot.register_next_step_handler(msg, save_channel)


def save_channel(message):
    username = message.text.strip()

    if username in CHANNELS:
        return bot.send_message(message.chat.id, "⚠️ Bor")

    CHANNELS.append(username)
    bot.send_message(message.chat.id, f"✅ Qo‘shildi: {username}", reply_markup=admin_buttons())


# =======================
# 📋 KANALLAR
# =======================
@bot.message_handler(func=lambda m: m.text == "📋 Kanallar ro'yxati" and m.from_user.id == ADMIN_ID)
def show_channels(message):
    bot.send_message(message.chat.id, "\n".join(CHANNELS) if CHANNELS else "❌ Yo‘q")


# =======================
# ❌ DELETE CHANNEL
# =======================
@bot.message_handler(func=lambda m: m.text == "❌ Kanal o'chirish" and m.from_user.id == ADMIN_ID)
def delete_channel(message):
    msg = bot.send_message(message.chat.id, "Kanal:", reply_markup=ForceReply())
    bot.register_next_step_handler(msg, process_delete_channel)


def process_delete_channel(message):
    if message.text in CHANNELS:
        CHANNELS.remove(message.text)
        bot.send_message(message.chat.id, "✅ O‘chirildi", reply_markup=admin_buttons())
    else:
        bot.send_message(message.chat.id, "❌ Yo‘q")


# =======================
# 🔍 SEARCH FIXED
# =======================
@bot.message_handler(content_types=['text'])
def search(message):
    track_user(message)

    if message.from_user.id == ADMIN_ID and message.text in [
        "🎬 Barcha kinolar","➕ Kino qo'shish","🗑 Kinoni o'chirish",
        "📢 Kanal qo'shish","📋 Kanallar ro'yxati","❌ Kanal o'chirish",
        "📊 Statistika","📢 Reklama"
    ]:
        return

    movie = db.get_movie(message.text.strip().lower())

    if movie:
        bot.send_video(message.chat.id, movie[2], caption=movie[1])
    else:
        if message.from_user.id != ADMIN_ID:
            bot.reply_to(message, "❌ Topilmadi")


# =======================
# 🎬 ADD MOVIE
# =======================
@bot.message_handler(content_types=['video'])
def add_movie(message):
    if message.from_user.id != ADMIN_ID:
        return

    track_user(message)

    if not message.caption:
        return

    parts = message.caption.split(" ", 1)
    if len(parts) < 2:
        return

    code = parts[0].lower()
    name = parts[1]

    db.add_movie(code, name, message.video.file_id)
    bot.send_message(message.chat.id, "✅ Saqlandi", reply_markup=admin_buttons())


# =======================
# 🗑 DELETE MOVIE
# =======================
@bot.message_handler(func=lambda m: m.text == "🗑 Kinoni o'chirish" and m.from_user.id == ADMIN_ID)
def del_movie(message):
    msg = bot.send_message(message.chat.id, "Kod:", reply_markup=ForceReply())
    bot.register_next_step_handler(msg, process_delete)


def process_delete(message):
    if db.delete_movie(message.text.strip().lower()):
        bot.send_message(message.chat.id, "✅ O'chirildi", reply_markup=admin_buttons())
    else:
        bot.send_message(message.chat.id, "❌ Yo'q")


# =======================
# ▶️ RUN
# =======================
if __name__ == "__main__":
    print("🤖 Bot ishladi")
    bot.infinity_polling()