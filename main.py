import telebot
from telebot.types import (
    Message,
    ReplyKeyboardMarkup,
    ReplyKeyboardRemove,
    ForceReply,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
)
from database import Database

# ─────────────────────────────────────────────────
TOKEN = "8560396008:AAFsT1MCeJbxqwqxK2kI7nQdm7GdjjMfHos"
ADMIN_ID = [8130553571, 7754612381]
# ─────────────────────────────────────────────────

bot = telebot.TeleBot(TOKEN)
db = Database("kinolar.db")

# user_id → "waiting_movie" | None
user_state: dict[int, str | None] = {}

ADMIN_BUTTONS = [
    "🎬 Barcha kinolar",
    "➕ Kino qo'shish",
    "🗑 Kinoni o'chirish",
    "📢 Kanal qo'shish",
    "📋 Kanallar ro'yxati",
    "❌ Kanal o'chirish",
    "📊 Statistika",
    "📢 Reklama",
]
def reset_to_menu(message: Message, text: str):
    user_id = message.from_user.id
    user_state[user_id] = None

    bot.send_message(
        message.chat.id,
        text,
        parse_mode="HTML",
        reply_markup=admin_markup(),
    )

# ══════════════════════════════════════════════════
# HELPERS
# ══════════════════════════════════════════════════

def admin_markup() -> ReplyKeyboardMarkup:
    markup = ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(*ADMIN_BUTTONS)
    return markup


def track_user(message: Message):
    try:
        db.add_user(message.from_user.id)
        db.update_last_active(message.from_user.id)
    except Exception:
        pass


def is_admin(message: Message) -> bool:
    return message.from_user.id in ADMIN_ID


def check_subscription(user_id: int) -> tuple[bool, list[str]]:
    """
    Returns (all_subscribed, list_of_channels_not_joined).
    If CHANNELS is empty → always True.
    """
    channels = db.get_channels()
    if not channels:
        return True, []

    not_joined = []
    for ch in channels:
        try:
            member = bot.get_chat_member(ch, user_id)
            if member.status in ("left", "kicked", "banned"):
                not_joined.append(ch)
        except Exception:
            not_joined.append(ch)

    return len(not_joined) == 0, not_joined


def subscription_markup(channels: list[str]) -> InlineKeyboardMarkup:
    markup = InlineKeyboardMarkup()
    for ch in channels:
        link = f"https://t.me/{ch.lstrip('@')}"
        markup.add(InlineKeyboardButton(f"📢 {ch}", url=link))
    markup.add(InlineKeyboardButton("✅ Obuna bo'ldim", callback_data="check_sub"))
    return markup


# ══════════════════════════════════════════════════
# /start
# ══════════════════════════════════════════════════

@bot.message_handler(commands=["start"])
def start(message: Message):
    track_user(message)
    if is_admin(message):
        bot.send_message(
            message.chat.id,
            "👋 Salom Admin!",
            reply_markup=admin_markup(),
        )
    else:
        bot.send_message(
            message.chat.id,
            "🎬 Kino kodini yuboring:",
            reply_markup=ReplyKeyboardRemove(),
        )


# ══════════════════════════════════════════════════
# CALLBACK: check subscription
# ══════════════════════════════════════════════════

@bot.callback_query_handler(func=lambda c: c.data == "check_sub")
def check_sub_callback(call):
    ok, missing = check_subscription(call.from_user.id)
    if ok:
        bot.answer_callback_query(call.id, "✅ Rahmat! Endi kino kodini yuboring.")
        bot.edit_message_reply_markup(call.message.chat.id, call.message.message_id)
    else:
        bot.answer_callback_query(call.id, "❌ Hali obuna bo'lmadingiz!", show_alert=True)


# ══════════════════════════════════════════════════
# ADMIN — 📊 Statistika
# ══════════════════════════════════════════════════

@bot.message_handler(func=lambda m: m.text == "📊 Statistika")
def stats(message: Message):
    if not is_admin(message):
        return
    total = db.get_users_count()
    active = db.get_active_users(1440)
    try:
        bot.send_message(
            message.chat.id,
            f"👥 Jami foydalanuvchilar: <b>{total}</b>\n"
            f"🔥 So'nggi 24 soatda aktiv: <b>{active}</b>",
            parse_mode="HTML",
    )
    except Exception as e:
        print("Send error:", e)


# ══════════════════════════════════════════════════
# ADMIN — 📢 Reklama
# ══════════════════════════════════════════════════

@bot.message_handler(func=lambda m: m.text == "📢 Reklama")
def broadcast_start(message: Message):
    if not is_admin(message):
        return
    msg = bot.send_message(message.chat.id, "📨 Tarqatmoqchi bo'lgan xabaringizni yuboring:", reply_markup=ForceReply())
    bot.register_next_step_handler(msg, send_broadcast)


def send_broadcast(message: Message):
    users = db.get_all_users()
    ok = fail = 0
    for uid in users:
        try:
            bot.copy_message(uid, message.chat.id, message.message_id)
            ok += 1
        except Exception:
            fail += 1
    bot.send_message(
        message.chat.id,
        f"📢 Xabar yuborildi!\n✅ Muvaffaqiyatli: {ok}\n❌ Xatolik: {fail}",
        reply_markup=admin_markup(),
    )


# ══════════════════════════════════════════════════
# ADMIN — 📢 Kanal qo'shish
# ══════════════════════════════════════════════════

@bot.message_handler(func=lambda m: m.text == "📢 Kanal qo'shish")
def add_channel(message: Message):
    if not is_admin(message):
        return
    msg = bot.send_message(
        message.chat.id,
        "📢 Kanal username-ni yuboring (masalan: @mychannel):",
        reply_markup=ForceReply(),
    )
    bot.register_next_step_handler(msg, save_channel)


def save_channel(message: Message):
    username = message.text.strip()
    if not username.startswith("@"):
        username = "@" + username

    if db.add_channel(username):
        bot.send_message(message.chat.id, f"✅ Kanal qo'shildi: {username}", reply_markup=admin_markup())
    else:
        bot.send_message(message.chat.id, f"⚠️ Bu kanal allaqachon ro'yxatda: {username}", reply_markup=admin_markup())


# ══════════════════════════════════════════════════
# ADMIN — 📋 Kanallar ro'yxati
# ══════════════════════════════════════════════════

@bot.message_handler(func=lambda m: m.text == "📋 Kanallar ro'yxati")
def show_channels(message: Message):
    if not is_admin(message):
        return
    channels = db.get_channels()
    if channels:
        bot.send_message(message.chat.id, "📋 Kanallar:\n" + "\n".join(channels))
    else:
        bot.send_message(message.chat.id, "❌ Hech qanday kanal yo'q")


# ══════════════════════════════════════════════════
# ADMIN — ❌ Kanal o'chirish
# ══════════════════════════════════════════════════

@bot.message_handler(func=lambda m: m.text == "❌ Kanal o'chirish")
def delete_channel(message: Message):
    if not is_admin(message):
        return
    msg = bot.send_message(message.chat.id, "Kanal username:", reply_markup=ForceReply())
    bot.register_next_step_handler(msg, process_delete_channel)


def process_delete_channel(message: Message):
    username = message.text.strip()
    if not username.startswith("@"):
        username = "@" + username

    if db.remove_channel(username):
        bot.send_message(message.chat.id, f"✅ O'chirildi: {username}", reply_markup=admin_markup())
    else:
        bot.send_message(message.chat.id, "❌ Bunday kanal topilmadi", reply_markup=admin_markup())


# ══════════════════════════════════════════════════
# ADMIN — 🗑 Kinoni o'chirish
# ══════════════════════════════════════════════════

@bot.message_handler(func=lambda m: m.text == "🗑 Kinoni o'chirish")
def del_movie(message: Message):
    if not is_admin(message):
        return
    msg = bot.send_message(message.chat.id, "🗑 O'chiriladigan kino kodini yuboring:", reply_markup=ForceReply())
    bot.register_next_step_handler(msg, process_delete)


def process_delete(message: Message):
    code = message.text.strip().lower()
    if db.delete_movie(code):
        bot.send_message(message.chat.id, f"✅ '{code}' o'chirildi", reply_markup=admin_markup())
    else:
        bot.send_message(message.chat.id, f"❌ '{code}' topilmadi", reply_markup=admin_markup())


# ══════════════════════════════════════════════════
# ADMIN — ➕ Kino qo'shish
# ══════════════════════════════════════════════════

@bot.message_handler(func=lambda m: m.text == "➕ Kino qo'shish")
def add_movie_start(message: Message):
    if not is_admin(message):
        return
    user_state[message.from_user.id] = "waiting_movie"
    bot.send_message(
        message.chat.id,
        "🎬 Video yoki hujjat yuboring.\n\n"
        "<b>Caption format:</b> <code>kod Kino nomi</code>\n"
        "Misol: <code>tt001 Spider-Man</code>",
        parse_mode="HTML",
        reply_markup=ForceReply(),
    )
@bot.message_handler(content_types=["video", "document"])
def receive_movie(message: Message):
    user_id = message.from_user.id

    if user_id not in ADMIN_ID:
        return

    if user_state.get(user_id) != "waiting_movie":
        return

    caption = (message.caption or "").strip()

    # ❌ Caption yo'q
    if not caption:
        return reset_to_menu(
            message,
            "❌ Caption yozilmadi!\nQaytadan urinib ko'ring."
        )

    parts = caption.split(" ", 1)

    # ❌ Format noto‘g‘ri
    if len(parts) < 2:
        return reset_to_menu(
            message,
            "❌ Format noto'g'ri!\n\nTo'g'risi: <code>kod Kino nomi</code>"
        )

    code = parts[0].lower()
    name = parts[1]

    file_id = (
        message.video.file_id
        if message.content_type == "video"
        else message.document.file_id
    )

    user_state[user_id] = None

    if db.add_movie(code, name, file_id):
        bot.send_message(
            message.chat.id,
            f"✅ Kino saqlandi!\n🎞 Kod: <code>{code}</code>\n📛 Nom: {name}",
            parse_mode="HTML",
            reply_markup=admin_markup(),
        )
    else:
        bot.send_message(
            message.chat.id,
            f"❌ <code>{code}</code> kodi allaqachon mavjud!",
            parse_mode="HTML",
            reply_markup=admin_markup(),
        )

@bot.message_handler(func=lambda m: user_state.get(m.from_user.id) == "waiting_movie", content_types=["text", "photo", "audio", "sticker"])
def wrong_input(message: Message):
    reset_to_menu(message, "❌ Faqat video yoki hujjat yuboring!")


# ══════════════════════════════════════════════════
# ADMIN — 🎬 Barcha kinolar
# ══════════════════════════════════════════════════
@bot.message_handler(func=lambda m: (m.text or "").strip() == "🎬 Barcha kinolar")
def all_movies(message: Message):
    if not is_admin(message):
        return

    movies = db.get_all_movies()
    if not movies:
        bot.send_message(message.chat.id, "❌ Hech qanday kino yo'q")
        return

    chunk = "🎬 <b>Barcha kinolar:</b>\n\n"

    for code, name in movies:
        line = f"🎞 <code>{code}</code> — {name}\n"

        # agar limit oshsa yuboramiz
        if len(chunk) + len(line) > 3800:
            bot.send_message(message.chat.id, chunk, parse_mode="HTML")
            chunk = "🎬 <b>Barcha kinolar (davomi):</b>\n\n"

        chunk += line

    if chunk:
        bot.send_message(message.chat.id, chunk, parse_mode="HTML")

# ══════════════════════════════════════════════════
# USER — kino qidirish (text handler, lowest priority)
# ══════════════════════════════════════════════════

@bot.message_handler(content_types=["text"])
def search(message: Message):
    track_user(message)

    # Ignore admin button texts so they don't fall through
    if message.text in ADMIN_BUTTONS:
        return

    code = message.text.strip().lower()

    # Admins can also search
    if is_admin(message):
        movie = db.get_movie(code)
        if movie:
            bot.send_video(message.chat.id, movie[2], caption=f"🎬 {movie[1]}")
        else:
            bot.reply_to(message, f"❌ <code>{code}</code> topilmadi", parse_mode="HTML")
        return

    # Regular user → check subscription first
    ok, missing = check_subscription(message.from_user.id)
    if not ok:
        bot.send_message(
            message.chat.id,
            "📢 Botdan foydalanish uchun quyidagi kanallarga obuna bo'ling:",
            reply_markup=subscription_markup(missing),
        )
        return

    movie = db.get_movie(code)
    if movie:
        bot.send_video(message.chat.id, movie[2], caption=f"🎬 {movie[1]}")
    else:
        bot.reply_to(message, "❌ Bunday kino topilmadi")


# ══════════════════════════════════════════════════
# RUN
# ══════════════════════════════════════════════════

if __name__ == "__main__":
    print("🤖 Bot ishga tushdi...")
    import time

    while True:
        try:
            bot.remove_webhook()
            bot.infinity_polling(skip_pending=True, timeout=60, long_polling_timeout=60)
        except Exception as e:
            print("Xatolik:", e)
            time.sleep(5)