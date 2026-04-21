import telebot
from telebot.types import (
    Message, ReplyKeyboardMarkup, KeyboardButton,
    ReplyKeyboardRemove, ForceReply,
    InlineKeyboardMarkup, InlineKeyboardButton
)
from database import Database

TOKEN = "8560396008:AAFsT1MCeJbxqwqxK2kI7nQdm7GdjjMfHos"
ADMIN_ID = 8130553571

bot = telebot.TeleBot(TOKEN)
db = Database("kinolar.db")

# 📢 Kanallar ro‘yxati (RAM)
CHANNELS = []


# 🔘 ADMIN PANEL
def admin_buttons():
    markup = ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(
        KeyboardButton("🎬 Barcha kinolar"),
        KeyboardButton("➕ Kino qo'shish"),
        KeyboardButton("🗑 Kinoni o'chirish"),
        KeyboardButton("📢 Kanal qo'shish"),
        KeyboardButton("📋 Kanallar ro'yxati"),
        KeyboardButton("❌ Kanal o'chirish")
    )
    return markup


# =======================
# 📢 KANAL QO'SHISH
# =======================
@bot.message_handler(func=lambda m: m.text == "📢 Kanal qo'shish" and m.from_user.id == ADMIN_ID)
def add_channel(message):
    msg = bot.send_message(
        message.chat.id,
        "📢 Kanal username yuboring:\nMisol: @kino_uz",
        reply_markup=ForceReply()
    )
    bot.register_next_step_handler(msg, save_channel)


def save_channel(message):
    username = message.text.strip()

    if not username.startswith("@"):
        bot.send_message(message.chat.id, "❌ @ bilan boshlanishi kerak!")
        return

    if username in CHANNELS:
        bot.send_message(message.chat.id, "⚠️ Kanal allaqachon bor!")
        return

    CHANNELS.append(username)

    bot.send_message(
        message.chat.id,
        f"✅ Qo‘shildi: {username}\nJami: {len(CHANNELS)} ta",
        reply_markup=admin_buttons()
    )


# =======================
# 📋 KANALLAR RO'YXATI
# =======================
@bot.message_handler(func=lambda m: m.text == "📋 Kanallar ro'yxati" and m.from_user.id == ADMIN_ID)
def show_channels(message):
    if not CHANNELS:
        bot.send_message(message.chat.id, "❌ Kanal yo‘q")
        return

    text = "📢 Kanallar:\n\n"
    for ch in CHANNELS:
        text += f"• {ch}\n"

    bot.send_message(message.chat.id, text)


# =======================
# ❌ KANAL O'CHIRISH (YANGI QO'SHILDI)
# =======================
@bot.message_handler(func=lambda m: m.text == "❌ Kanal o'chirish" and m.from_user.id == ADMIN_ID)
def delete_channel(message):
    if not CHANNELS:
        bot.send_message(message.chat.id, "❌ Hech qanday kanal yo‘q")
        return

    text = "❌ O'chirmoqchi bo'lgan kanalni yuboring:\n\n"
    for ch in CHANNELS:
        text += f"• {ch}\n"

    msg = bot.send_message(message.chat.id, text, reply_markup=ForceReply())
    bot.register_next_step_handler(msg, process_delete_channel)


def process_delete_channel(message):
    username = message.text.strip()

    if username in CHANNELS:
        CHANNELS.remove(username)
        bot.send_message(
            message.chat.id,
            f"✅ O'chirildi: {username}",
            reply_markup=admin_buttons()
        )
    else:
        bot.send_message(message.chat.id, "❌ Kanal topilmadi!", reply_markup=admin_buttons())


# =======================
# 🔍 OBUNA TEKSHIRISH
# =======================
def check_subscribe(user_id):
    if not CHANNELS:
        return True

    for ch in CHANNELS:
        try:
            member = bot.get_chat_member(ch, user_id)
            if member.status not in ["member", "creator", "administrator"]:
                return False
        except:
            return False
    return True


def join_channels():
    markup = InlineKeyboardMarkup()

    for ch in CHANNELS:
        markup.add(
            InlineKeyboardButton(f"📢 {ch}", url=f"https://t.me/{ch[1:]}")
        )

    markup.add(InlineKeyboardButton("✅ Tekshirish", callback_data="check_sub"))
    return markup


def is_subscribed(message):
    if not check_subscribe(message.from_user.id):
        bot.send_message(
            message.chat.id,
            "❗ Kanalga obuna bo‘ling:",
            reply_markup=join_channels()
        )
        return False
    return True


# =======================
# 🚀 START
# =======================
@bot.message_handler(commands=["start"])
def start(message: Message):
    if not check_subscribe(message.from_user.id):
        bot.send_message(
            message.chat.id,
            "❗ Obuna bo‘ling:",
            reply_markup=join_channels()
        )
        return

    if message.from_user.id == ADMIN_ID:
        bot.send_message(message.chat.id, "👋 Admin panel", reply_markup=admin_buttons())
    else:
        bot.send_message(message.chat.id, "🎬 Kino kodini yuboring:", reply_markup=ReplyKeyboardRemove())


# =======================
# ✅ CHECK BUTTON
# =======================
@bot.callback_query_handler(func=lambda call: call.data == "check_sub")
def check_callback(call):
    if check_subscribe(call.from_user.id):
        bot.answer_callback_query(call.id, "✅ OK")
        bot.send_message(call.message.chat.id, "🎬 Endi foydalanishingiz mumkin")
    else:
        bot.answer_callback_query(call.id, "❌ Obuna yo‘q", show_alert=True)


# =======================
# 🎬 KINOLAR
# =======================
@bot.message_handler(func=lambda m: m.text == "🎬 Barcha kinolar" and m.from_user.id == ADMIN_ID)
def show_movies(message):
    movies = db.get_all_movies()

    if not movies:
        bot.send_message(message.chat.id, "❌ Bo'sh")
        return

    text = "🎬 Kinolar:\n\n"
    for m in movies:
        text += f"{m[0]} - {m[1]}\n"

    bot.send_message(message.chat.id, text)


# =======================
# ➕ ADD MOVIE
# =======================
@bot.message_handler(func=lambda m: m.text == "➕ Kino qo'shish" and m.from_user.id == ADMIN_ID)
def add_help(message):
    bot.send_message(message.chat.id, "📥 Video + caption: kod nom")


@bot.message_handler(content_types=['video'])
def add_movie(message):
    if message.from_user.id != ADMIN_ID:
        return

    if not is_subscribed(message):
        return

    if not message.caption:
        bot.reply_to(message, "⚠️ Caption yoz!")
        return

    parts = message.caption.split(" ", 1)
    if len(parts) < 2:
        bot.reply_to(message, "⚠️ Format xato")
        return

    code = parts[0].lower()
    name = parts[1]

    if db.add_movie(code, name, message.video.file_id):
        bot.send_message(message.chat.id, "✅ Saqlandi!", reply_markup=admin_buttons())
    else:
        bot.send_message(message.chat.id, "❌ Bor")


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
# 🔍 SEARCH
# =======================
@bot.message_handler(func=lambda m: True)
def search(message):
    if not is_subscribed(message):
        return

    movie = db.get_movie(message.text.strip().lower())

    if movie:
        bot.send_video(message.chat.id, movie[2], caption=movie[1])
    else:
        if message.from_user.id != ADMIN_ID:
            bot.reply_to(message, "❌ Topilmadi")


# =======================
# ▶️ RUN
# =======================
if __name__ == "__main__":
    print("🤖 Bot ishladi")
    bot.infinity_polling()