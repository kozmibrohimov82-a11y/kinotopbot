from telebot.types import ReplyKeyboardMarkup,KeyboardButton

def movie_list():
    markup=ReplyKeyboardMarkup(row_width=True,resize_keyboard=True)
    btn=KeyboardButton("Barcha kinolar ro'yxati")
    markup.add(btn)
    return markup

# TOKEN = "8560396008:AAFsT1MCeJbxqwqxK2kI7nQdm7GdjjMfHos"
# ADMIN_ID = [8130553571, 7754612381]