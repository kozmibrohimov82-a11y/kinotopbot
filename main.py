import telebot
from telebot.types import *
from database import Database

import time
from requests.exceptions import ReadTimeout, ConnectionError

# ─────────────────────────────────
TOKEN = "8560396008:AAFsT1MCeJbxqwqxK2kI7nQdm7GdjjMfHos"
ADMIN_ID = [8130553571, 7754612381]
# ─────────────────────────────────

bot = telebot.TeleBot(TOKEN)
db = Database("kinolar.db")

user_state = {}

# ═════════════════════════════════
# 🔐 SAFE API CALL (ANTI-TIMEOUT)
# ═════════════════════════════════
def safe_call(func, *args, **kwargs):
    for i in range(3):
        try:
            return func(*args, **kwargs)
        except (ReadTimeout, ConnectionError) as e:
            print(f"Retry {i+1}:", e)
            time.sleep(2)
        except Exception as e:
            print("Error:", e)
            break


# ═════════════════════════════════
# HELPERS
# ═════════════════════════════════
def is_admin(message):
    return message.from_user.id in ADMIN_ID


def admin_markup():
    markup = ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(
        "🎬 Barcha kinolar",
        "➕ Kino qo'shish",
        "🗑 Kinoni o'chirish",
        "📢 Reklama",
        "📊 Statistika",
    )
    return markup


def track_user(message):
    try:
        db.add_user(message.from_user.id)
    except:
        pass


# ═════════════════════════════════
# START
# ═════════════════════════════════
@bot.message_handler(commands=["start"])
def start(message):
    track_user(message)

    if is_admin(message):
        safe_call(bot.send_message, message.chat.id, "👋 Admin panel", reply_markup=admin_markup())
    else:
        safe_call(bot.send_message, message.chat.id, "🎬 Kino kodini yuboring:")


# ═════════════════════════════════
# STAT
# ═════════════════════════════════
@bot.message_handler(func=lambda m: m.text == "📊 Statistika")
def stats(message):
    if not is_admin(message):
        return

    total = db.get_users_count()
    safe_call(bot.send_message, message.chat.id, f"👥 Users: {total}")


# ═════════════════════════════════
# BROADCAST
# ═════════════════════════════════
@bot.message_handler(func=lambda m: m.text == "📢 Reklama")
def broadcast_start(message):
    if not is_admin(message):
        return

    msg = safe_call(bot.send_message, message.chat.id, "Xabar yubor:")
    bot.register_next_step_handler(msg, send_broadcast)


def send_broadcast(message):
    users = db.get_all_users()
    ok = fail = 0

    for uid in users:
        try:
            safe_call(bot.copy_message, uid, message.chat.id, message.message_id)
            ok += 1
            time.sleep(0.05)  # 🔥 MUHIM
        except:
            fail += 1

    safe_call(bot.send_message, message.chat.id, f"✅ {ok} | ❌ {fail}")


# ═════════════════════════════════
# ADD MOVIE
# ═════════════════════════════════
@bot.message_handler(func=lambda m: m.text == "➕ Kino qo'shish")
def add_movie_start(message):
    if not is_admin(message):
        return

    user_state[message.from_user.id] = "movie"
    msg = safe_call(bot.send_message, message.chat.id, "🎬 Video + caption: kod nom")
    bot.register_next_step_handler(msg, save_movie)


def save_movie(message):
    if message.content_type not in ["video", "document"]:
        safe_call(bot.send_message, message.chat.id, "❌ Faqat video")
        return

    caption = (message.caption or "").strip()

    if " " not in caption:
        safe_call(bot.send_message, message.chat.id, "❌ Format: kod nom")
        return

    code, name = caption.split(" ", 1)

    file_id = (
        message.video.file_id
        if message.content_type == "video"
        else message.document.file_id
    )

    if db.add_movie(code, name, file_id):
        safe_call(bot.send_message, message.chat.id, "✅ Saqlandi")
    else:
        safe_call(bot.send_message, message.chat.id, "❌ Kod mavjud")


# ═════════════════════════════════
# ALL MOVIES
# ═════════════════════════════════
@bot.message_handler(func=lambda m: m.text == "🎬 Barcha kinolar")
def all_movies(message):
    if not is_admin(message):
        return

    movies = db.get_all_movies()

    chunk = ""
    for code, name in movies:
        line = f"{code} - {name}\n"

        if len(chunk) > 3500:
            safe_call(bot.send_message, message.chat.id, chunk)
            chunk = ""
            time.sleep(0.3)

        chunk += line

    if chunk:
        safe_call(bot.send_message, message.chat.id, chunk)


# ═════════════════════════════════
# SEARCH
# ═════════════════════════════════
@bot.message_handler(content_types=["text"])
def search(message):
    track_user(message)

    if message.text in ["🎬 Barcha kinolar", "➕ Kino qo'shish", "📢 Reklama", "📊 Statistika"]:
        return

    code = message.text.strip()

    movie = db.get_movie(code)

    if movie:
        safe_call(bot.send_video, message.chat.id, movie[2], caption=movie[1])
    else:
        safe_call(bot.send_message, message.chat.id, "❌ Topilmadi")


# ═════════════════════════════════
# RUN
# ═════════════════════════════════
if __name__ == "__main__":
    print("🤖 Bot ishlayapti...")

    while True:
        try:
            bot.remove_webhook()
            bot.infinity_polling(timeout=60, long_polling_timeout=60)
        except Exception as e:
            print("Crash:", e)
            time.sleep(5)