from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from bot_instance import bot
from database import Database
from config import BOT_NAME_KHMER, BOT_NAME_ENGLISH, ADMIN_IDS
from keyboards import user_main_keyboard, admin_main_keyboard
from utils import add_user, is_admin, format_currency, get_user_lang, set_user_lang, send_and_delete_previous
from translations import t

def register_user_handlers():
    @bot.message_handler(commands=['start'])
    def start_command(message):
        user = message.from_user
        add_user(user.id, user.username, user.first_name, user.last_name)
        lang = get_user_lang(user.id)
        
        welcome_text = f"""
🌟 {t('welcome_user', lang, name=user.first_name)}

🛒 💳 ⚡ 🔒
        """

        
        if is_admin(user.id):
            send_and_delete_previous(message.chat.id, user.id, message.message_id, welcome_text + "\n\n👑 " + t('welcome_admin', lang, name=user.first_name), 
                            reply_markup=admin_main_keyboard(lang))
        else:
            send_and_delete_previous(message.chat.id, user.id, message.message_id, welcome_text, reply_markup=user_main_keyboard(lang))

    @bot.message_handler(commands=['language'])
    def language_command(message):
        user = message.from_user
        current_lang = get_user_lang(user.id)
        new_lang = 'en' if current_lang == 'km' else 'km'
        set_user_lang(user.id, new_lang)
        
        send_and_delete_previous(
            message.chat.id, user.id, message.message_id,
            t('language_changed', new_lang),
            reply_markup=admin_main_keyboard(new_lang) if is_admin(user.id) else user_main_keyboard(new_lang)
        )

    @bot.message_handler(commands=['request'])
    def request_command(message):
        lang = get_user_lang(message.from_user.id)
        msg = send_and_delete_previous(message.chat.id, message.from_user.id, message.message_id, t('request_prompt', lang))
        bot.register_next_step_handler(msg, process_request)

    def process_request(message):
        lang = get_user_lang(message.from_user.id)
        if message.text in ["🔙 ត្រឡប់ក្រោយ", "BACK", "Back", "back", "🔙"]:
            bot.send_message(message.chat.id, t('request_cancelled', lang))
            return universal_back_handler(message)
            
        request_text = message.text
        user = message.from_user
        username = f"@{user.username}" if user.username else user.first_name
        
        # Send to admins
        admin_msg = f"🔔 សំណើថ្មី (New Request)\n👤 ពី: {username} (ID: {user.id})\n📝 សំណើ: {request_text}"
        for admin_id in ADMIN_IDS:
            try:
                bot.send_message(admin_id, admin_msg)
            except:
                pass
                
        send_and_delete_previous(message.chat.id, message.from_user.id, message.message_id, t('request_success', lang))

    @bot.message_handler(commands=['feedback'])
    def feedback_command(message):
        lang = get_user_lang(message.from_user.id)
        with Database() as db:
            db.cursor.execute('''
                SELECT DISTINCT p.id, p.name 
                FROM orders o
                JOIN products p ON o.product_id = p.id
                WHERE o.user_id = ? AND o.payment_status = 'completed'
            ''', (message.from_user.id,))
            products = db.cursor.fetchall()
            
        if not products:
            send_and_delete_previous(message.chat.id, message.from_user.id, message.message_id, t('feedback_no_products', lang))
            return
            
        keyboard = InlineKeyboardMarkup(row_width=1)
        for p in products:
            keyboard.add(InlineKeyboardButton(p['name'], callback_data=f"fb_{p['id']}"))
            
        send_and_delete_previous(message.chat.id, message.from_user.id, message.message_id, t('feedback_select_product', lang), reply_markup=keyboard)

    @bot.message_handler(func=lambda m: m.text in [t('btn_buy', 'km'), t('btn_buy', 'en')])
    def buy_products(message):
        with Database() as db:
            db.cursor.execute("SELECT id, name, price, stock FROM products WHERE is_active = 1")
            products = db.cursor.fetchall()
        
        if not products:
            send_and_delete_previous(message.chat.id, message.from_user.id, message.message_id, "📦 សុំទោសបង ឥឡូវអស់អីវ៉ាន់លក់ហើយ។", 
                            reply_markup=user_main_keyboard())
            return
        
        keyboard = InlineKeyboardMarkup(row_width=1)
        for product in products:
            if product['stock'] > 0:
                text = f"{product['name']} - {format_currency(product['price'])} (សល់: {product['stock']})"
            else:
                text = f"❌ {product['name']} - {format_currency(product['price'])} (អស់ស្តុក)"
                
            keyboard.add(InlineKeyboardButton(text, callback_data=f"show_{product['id']}"))
        keyboard.add(InlineKeyboardButton("🔙 ត្រឡប់ក្រោយ", callback_data="back_to_menu"))
        
        send_and_delete_previous(message.chat.id, message.from_user.id, message.message_id, "🛒 អីវ៉ាន់ដែលមានលក់ឥឡូវនេះ:", reply_markup=keyboard)

    @bot.message_handler(func=lambda m: m.text in [t('btn_cart', 'km'), t('btn_cart', 'en')])
    def my_cart(message):
        user_id = message.from_user.id
        with Database() as db:
            db.cursor.execute('''
                SELECT c.id, c.quantity, p.name, p.price, (c.quantity * p.price) as total
                FROM cart c
                JOIN products p ON c.product_id = p.id
                WHERE c.user_id = ?
            ''', (user_id,))
            cart_items = db.cursor.fetchall()
            
        if not cart_items:
            send_and_delete_previous(message.chat.id, user_id, message.message_id, "កន្ត្រករបស់អ្នកទទេស្អាត។ សូមទិញអីវ៉ាន់សិន។")
            return
            
        text = "🛍️ កន្ត្រករបស់អ្នក:\n━━━━━━━━━━━━━━━━━━━\n"
        total_price = 0
        keyboard = InlineKeyboardMarkup(row_width=1)
        for idx, item in enumerate(cart_items, 1):
            text += f"{idx}. {item['name']} x{item['quantity']} = {format_currency(item['total'])}\n"
            total_price += item['total']
            keyboard.add(InlineKeyboardButton(f"❌ លុប {item['name']}", callback_data=f"rmcart_{item['id']}"))
            
        text += f"━━━━━━━━━━━━━━━━━━━\nសរុបទឹកប្រាក់: {format_currency(total_price)}\n"
        keyboard.add(InlineKeyboardButton("💳 គិតលុយ (Checkout)", callback_data="checkout_cart"))
        
        try:
            bot.send_message(message.chat.id, text, reply_markup=keyboard)
        except:
            pass

    @bot.message_handler(func=lambda m: m.text in [t('btn_orders', 'km'), t('btn_orders', 'en')])
    def my_orders(message):
        keyboard = InlineKeyboardMarkup(row_width=1)
        keyboard.add(
            InlineKeyboardButton("✅ ប្រវត្តិទិញជោគជ័យ", callback_data="history_completed"),
            InlineKeyboardButton("⏳ ប្រវត្តិមិនទាន់បង់លុយ", callback_data="history_pending"),
            InlineKeyboardButton("🔙 ត្រឡប់ក្រោយ", callback_data="back_to_menu")
        )
        send_and_delete_previous(
            message.chat.id, 
            message.from_user.id, 
            message.message_id, 
            "📦 សូមជ្រើសរើសប្រភេទប្រវត្តិទិញអីវ៉ាន់របស់អ្នក:", 
            reply_markup=keyboard
        )

    @bot.message_handler(func=lambda m: m.text in [t('btn_profile', 'km'), t('btn_profile', 'en')])
    def profile(message):
        with Database() as db:
            db.cursor.execute('''
                SELECT user_id, username, first_name, last_name, is_admin, created_at,
                       (SELECT COUNT(*) FROM orders WHERE user_id = ?) as orders_count,
                       (SELECT SUM(amount) FROM orders WHERE user_id = ? AND payment_status = 'completed') as total_spent
                FROM users WHERE user_id = ?
            ''', (message.from_user.id, message.from_user.id, message.from_user.id))
            user = db.cursor.fetchone()
        
        text = f"""
👤 គណនីខ្ញុំ
━━━━━━━━━━━━━━
លេខសម្គាល់: {user['user_id']}
ឈ្មោះ: {user['first_name']} {user['last_name'] or ''}
តួនាទី: {'👑 មេ (Admin)' if user['is_admin'] else '👤 ភ្ញៀវ'}
ប្រើចាប់ពី: {user['created_at'][:19]}

📊 ស្ថិតិការទិញ
━━━━━━━━━━━━━━
📦 ទិញបានចំនួន: {user['orders_count']} ដង
💰 ចំណាយអស់: {format_currency(user['total_spent'] or 0)}
━━━━━━━━━━━━━━
        """
        send_and_delete_previous(message.chat.id, message.from_user.id, message.message_id, text)

    @bot.message_handler(func=lambda m: m.text in [t('btn_help', 'km'), t('btn_help', 'en')])
    def help_command(message):
        text = f"""
❓ របៀបទិញអីវ៉ាន់
━━━━━━━━━━━━━━
🛒 ជំហានងាយៗ:
1. ចុចប៊ូតុង 'ទិញអីវ៉ាន់'
2. ជ្រើសរើសអីវ៉ាន់ដែលបងចង់បាន
3. មើលព័ត៌មានលម្អិត ហើយចុច 'ទិញ'
4. បញ្ចូលចំនួនដែលចង់ទិញ
5. ស្កេន QR កូដបង់លុយតាមកម្មវិធីធនាគារ
6. ធ្វើការទូទាត់ក្នុងរយៈពេល ៣ នាទី
7. ទទួលបានអីវ៉ាន់ភ្លាមៗហ្មង!

💎 ត្រូវការជំនួយបន្ថែម:
ឆាតសួរ @mengseanggg ផ្ទាល់បានបង!

⏰ ចំណាំ: QR កូដមានសុពលភាព ៣ នាទី
✅ ប្រព័ន្ធឆែកលុយដោយស្វ័យប្រវត្តិលឿនបំផុត
        """
        send_and_delete_previous(message.chat.id, message.from_user.id, message.message_id, text)

    @bot.message_handler(func=lambda m: m.text in ["🔙 ត្រឡប់ក្រោយ", "BACK", "Back", "back", "🔙", t('btn_back', 'en')])
    def universal_back_handler(message):
        bot.clear_step_handler_by_chat_id(message.chat.id)
        lang = get_user_lang(message.from_user.id)
        if is_admin(message.from_user.id):
            send_and_delete_previous(message.chat.id, message.from_user.id, message.message_id, t('menu_title', lang), reply_markup=admin_main_keyboard(lang))
        else:
            send_and_delete_previous(message.chat.id, message.from_user.id, message.message_id, t('menu_title', lang), reply_markup=user_main_keyboard(lang))

    @bot.message_handler(func=lambda m: m.text in [t('btn_main_menu', 'km'), t('btn_main_menu', 'en')])
    def main_menu(message):
        lang = get_user_lang(message.from_user.id)
        if is_admin(message.from_user.id):
            send_and_delete_previous(message.chat.id, message.from_user.id, message.message_id, t('menu_title', lang), reply_markup=admin_main_keyboard(lang))
        else:
            send_and_delete_previous(message.chat.id, message.from_user.id, message.message_id, t('menu_title', lang), reply_markup=user_main_keyboard(lang))
