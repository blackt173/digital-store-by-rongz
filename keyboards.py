from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton
from translations import t

# ============ KEYBOARDS ============
def user_main_keyboard(lang='km'):
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.add(KeyboardButton(t('btn_buy', lang)), KeyboardButton(t('btn_cart', lang)))
    keyboard.add(KeyboardButton(t('btn_orders', lang)), KeyboardButton(t('btn_profile', lang)))
    keyboard.add(KeyboardButton(t('btn_help', lang)))
    return keyboard

def admin_main_keyboard(lang='km'):
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.add(KeyboardButton(t('btn_dashboard', lang)), KeyboardButton(t('btn_products', lang)))
    keyboard.add(KeyboardButton(t('btn_add_product', lang)), KeyboardButton(t('btn_add_stock', lang)))
    keyboard.add(KeyboardButton(t('btn_users', lang)), KeyboardButton(t('btn_all_orders', lang)))
    keyboard.add(KeyboardButton(t('btn_main_menu', lang)))
    return keyboard

def back_keyboard(lang='km'):
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.add(KeyboardButton(t('btn_back', lang)), KeyboardButton("BACK"))
    return keyboard
