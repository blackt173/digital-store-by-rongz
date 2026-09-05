import time
import random
import string
from functools import wraps
from bot_instance import bot
from database import Database
from config import ADMIN_IDS

def generate_transaction_id():
    timestamp = int(time.time())
    random_str = ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
    return f"TRX{timestamp}{random_str}"

def parse_product_format(product_string):
    parts = product_string.split('|')
    if len(parts) >= 2:
        email = parts[0].strip()
        password = parts[1].strip()
        license_key = parts[2].strip() if len(parts) > 2 and parts[2].strip() else None
        twofa = parts[3].strip() if len(parts) > 3 and parts[3].strip() else None
        return email, password, license_key, twofa
    return None, None, None, None

def format_product_display(email, password, license_key, twofa):
    text = f"📧 អ៊ីមែល: `{email}`\n🔑 ពាក្យសម្ងាត់: `{password}`\n"
    if license_key:
        text += f"🔐 លេខកូដ: `{license_key}`\n"
    if twofa:
        text += f"🔒 2FA: `{twofa}`\n"
    return text

def format_currency(amount):
    return f"${amount:.2f}"

def send_and_delete_previous(chat_id, user_id, user_message_id, text, reply_markup=None, parse_mode=None):
    from bot_instance import bot, last_bot_messages
    
    # Try to delete user's message
    if user_message_id:
        try:
            bot.delete_message(chat_id, user_message_id)
        except:
            pass
        
    # Try to delete previous bot message
    if user_id in last_bot_messages:
        try:
            bot.delete_message(chat_id, last_bot_messages[user_id])
        except:
            pass
            
    # Send new message
    msg = bot.send_message(chat_id, text, reply_markup=reply_markup, parse_mode=parse_mode)
    last_bot_messages[user_id] = msg.message_id
    return msg

# ============ AUTHENTICATION HELPER ============
def add_user(user_id, username, first_name, last_name):
    with Database() as db:
        db.cursor.execute(
            "INSERT OR IGNORE INTO users (user_id, username, first_name, last_name) VALUES (?, ?, ?, ?)",
            (user_id, username, first_name, last_name)
        )
        db.commit()

def is_admin(user_id):
    if user_id in ADMIN_IDS:
        return True
    with Database() as db:
        db.cursor.execute("SELECT is_admin FROM users WHERE user_id = ?", (user_id,))
        result = db.cursor.fetchone()
        return result and result['is_admin'] == 1

def is_super_admin(user_id):
    return user_id in ADMIN_IDS

def get_user_lang(user_id):
    with Database() as db:
        db.cursor.execute("SELECT language FROM users WHERE user_id = ?", (user_id,))
        result = db.cursor.fetchone()
        return result['language'] if result else 'km'

def set_user_lang(user_id, lang_code):
    with Database() as db:
        db.cursor.execute("UPDATE users SET language = ? WHERE user_id = ?", (lang_code, user_id))
        db.commit()

def admin_only(func):
    @wraps(func)
    def wrapped(message):
        if is_admin(message.from_user.id):
            return func(message)
        else:
            bot.reply_to(message, "⛔ ពាក្យបញ្ជានេះសម្រាប់តែអ្នកគ្រប់គ្រងប៉ុណ្ណោះ។")
    return wrapped

def handle_invalid_input(message, retry_handler, error_message, *args, **kwargs):
    from bot_instance import bot, user_failures
    from keyboards import admin_main_keyboard, user_main_keyboard, back_keyboard
    
    user_id = message.from_user.id
    user_failures[user_id] = user_failures.get(user_id, 0) + 1
    
    if user_failures[user_id] > 2:
        bot.clear_step_handler_by_chat_id(message.chat.id)
        user_failures[user_id] = 0
        bot.send_message(
            message.chat.id, 
            "🚫 អ្នកបានបញ្ចូលខុសច្រើនដងពេក។ ប្រព័ន្ធត្រូវបានត្រឡប់ទៅម៉ឺនុយដើមវិញ។"
        )
        if is_admin(user_id):
            bot.send_message(message.chat.id, "ម៉ឺនុយមេ:", reply_markup=admin_main_keyboard())
        else:
            bot.send_message(message.chat.id, "ម៉ឺនុយមេ:", reply_markup=user_main_keyboard())
    else:
        msg = bot.send_message(message.chat.id, error_message, reply_markup=back_keyboard())
        bot.register_next_step_handler(msg, retry_handler, *args, **kwargs)
