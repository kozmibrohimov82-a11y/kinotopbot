from telebot import TeleBot
from databse import *
from telebot.types import Message, ReplyKeyboardMarkup, KeyboardButton
TOKEN = "8462672972:AAEZYp4YhzhLmff1eBd2pm_wABh_jesryV0"
bot = TeleBot(TOKEN)

# Bazani ulaymiz
db = Database("kinolar.db")

# Admin ID
ADMIN_ID = 978332731
# ... (Token va Admin_ID qismlari o'z joyida qoladi)

@bot.message_handler(commands=["start"])
def start(message: Message):
    chat_id = message.chat.id
    if message.from_user.id == ADMIN_ID:
        # Admin uchun Reply Button yaratish
        markup = ReplyKeyboardMarkup(resize_keyboard=True)
        btn = KeyboardButton("🎬 Barcha kinolar")
        markup.add(btn)

        bot.send_message(chat_id, "Xush kelibsiz, Admin! 👨‍💻\nKino qo'shish uchun videoni yuboring.",
                         reply_markup=markup)
    else:
        bot.send_message(chat_id, "Salom! Menga kino kodini yuboring, sizga kinoni jo'nataman! 🎬")


# "🎬 Barcha kinolar" tugmasi bosilganda ishlaydigan handler
@bot.message_handler(func=lambda message: message.text == "🎬 Barcha kinolar" and message.from_user.id == ADMIN_ID)
def show_all_movies(message: Message):
    movies = db.get_all_movies()

    if not movies:
        bot.send_message(message.chat.id, "❌ Bazada hali kinolar yo'q.")
        return

    text = "🎬 **Bazada mavjud kinolar ro'yxati:**\n\n"
    for movie in movies:
        # movie[0] - kod, movie[1] - nomi
        text += f"🆔 `{movie[0]}` — 🎥 {movie[1]}\n"

    # Agar tekst juda uzun bo'lsa, xabar ketmay qolishi mumkin (limit 4096 belgi)
    bot.send_message(message.chat.id, text, parse_mode="Markdown")


# --- ADMIN QISMI: Kino qo'shish ---
@bot.message_handler(content_types=['video'])
def add_movie_handler(message: Message):
    if message.from_user.id == ADMIN_ID:
        if message.caption:
            try:
                # Captiondan ma'lumotni ajratamiz (masalan: "101 Forsaj")
                parts = message.caption.split(" ", 1)
                if len(parts) < 2:
                    bot.reply_to(message, "⚠️ Xato! Videoga 'kod nomi' ko'rinishida izoh yozing.")
                    return

                code = parts[0]
                name = parts[1]
                f_id = message.video.file_id

                if db.add_movie(code, name, f_id):
                    bot.reply_to(message, f"✅ Baza yangilandi!\nKod: {code}\nNomi: {name}")
                else:
                    bot.reply_to(message, "❌ Bu kod bazada allaqachon mavjud!")
            except Exception as e:
                bot.reply_to(message, f"⚠️ Xatolik yuz berdi: {e}")
        else:
            bot.reply_to(message, "⚠️ Iltimos, videoga kod va nomni caption (izoh) qismida yozing.")


# --- FOYDALANUVCHI QISMI: Kino qidirish ---
@bot.message_handler(func=lambda message: True)
def search_movie_handler(message: Message):
    query = message.text.strip()

    # Faqat raqam yoki kod ekanligini tekshirish (ixtiyoriy)
    movie = db.get_movie(query)

    if movie:
        # movie[0] = kod, movie[1] = nomi, movie[2] = file_id
        bot.send_video(
            message.chat.id,
            video=movie[2],
            caption=f"🎬 Kino nomi: {movie[1]}\n🔍 Kod: {movie[0]}"
        )
    else:
        bot.reply_to(message, "🔍 Kechirasiz, bunday kodli kino topilmadi.")


if __name__ == '__main__':
    print("Bot ishga tushdi...")
    bot.infinity_polling()


