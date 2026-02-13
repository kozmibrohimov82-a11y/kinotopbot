from telebot.types import ReplyKeyboardMarkup,KeyboardButton

def movie_list():
    markup=ReplyKeyboardMarkup(row_width=True,resize_keyboard=True)
    btn=KeyboardButton("Barcha kinolar ro'yxati")
    markup.add(btn)
    return markup