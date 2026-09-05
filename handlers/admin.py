from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from bot_instance import bot
from database import Database
from utils import is_admin, admin_only, format_currency, parse_product_format, handle_invalid_input, send_and_delete_previous
from bot_instance import user_failures
from keyboards import admin_main_keyboard, back_keyboard

def register_admin_handlers():
    @bot.message_handler(func=lambda m: m.text == "📊 ផ្ទាំងគ្រប់គ្រង")
    @admin_only
    def admin_dashboard(message):
        with Database() as db:
            db.cursor.execute("SELECT COUNT(*) as count FROM users")
            total_users = db.cursor.fetchone()['count']
            
            db.cursor.execute("SELECT COUNT(*) as count FROM products")
            total_products = db.cursor.fetchone()['count']
            
            db.cursor.execute("SELECT SUM(stock) as total FROM products")
            total_stock = db.cursor.fetchone()['total'] or 0
            
            db.cursor.execute("SELECT COUNT(*) as count FROM orders WHERE payment_status = 'pending'")
            pending_orders = db.cursor.fetchone()['count']
            
            db.cursor.execute('''
                SELECT COALESCE(SUM(amount), 0) as total 
                FROM orders 
                WHERE payment_status = 'completed' 
                AND date(completed_at) = date('now')
            ''')
            today_revenue = db.cursor.fetchone()['total']
            
            db.cursor.execute('''
                SELECT COALESCE(SUM(amount), 0) as total 
                FROM orders 
                WHERE payment_status = 'completed' 
                AND strftime('%Y-%W', completed_at) = strftime('%Y-%W', 'now')
            ''')
            week_revenue = db.cursor.fetchone()['total']
            
            db.cursor.execute('''
                SELECT COALESCE(SUM(amount), 0) as total 
                FROM orders 
                WHERE payment_status = 'completed' 
                AND strftime('%Y-%m', completed_at) = strftime('%Y-%m', 'now')
            ''')
            month_revenue = db.cursor.fetchone()['total']
            
            db.cursor.execute('''
                SELECT COALESCE(SUM(amount), 0) as total 
                FROM orders 
                WHERE payment_status = 'completed'
            ''')
            total_revenue = db.cursor.fetchone()['total']
        
        text = f"""
📊 ផ្ទាំងគ្រប់គ្រង
━━━━━━━━━━━━━━━━━
👥 អ្នកប្រើប្រាស់: {total_users}
📦 ផលិតផល: {total_products}
💎 ស្តុកសរុប: {total_stock}
⏳ ការបញ្ជាទិញរង់ចាំ: {pending_orders}

💰 ចំណូលប្រចាំកាល
━━━━━━━━━━━━━━━━━
▪️ ថ្ងៃនេះ: {format_currency(today_revenue)}
▪️ សប្តាហ៍នេះ: {format_currency(week_revenue)}
▪️ ខែនេះ: {format_currency(month_revenue)}

💰 ចំណូលសរុប
━━━━━━━━━━━━━━━━━
{format_currency(total_revenue)}
        """
        send_and_delete_previous(message.chat.id, message.from_user.id, message.message_id, text)

    @bot.message_handler(func=lambda m: m.text == "📦 ផលិតផល")
    @admin_only
    def admin_products(message):
        with Database() as db:
            db.cursor.execute('''
                SELECT p.*, 
                       (SELECT COUNT(*) FROM digital_products WHERE product_id = p.id AND is_sold = 0) as available,
                       (SELECT COUNT(*) FROM digital_products WHERE product_id = p.id) as total
                FROM products p
                WHERE p.is_active = 1
                ORDER BY p.id DESC
                LIMIT 80
            ''')
            products = db.cursor.fetchall()
        
        if not products:
            send_and_delete_previous(message.chat.id, message.from_user.id, message.message_id, "មិនទាន់មានផលិតផលទេ។ ប្រើ '➕ បន្ថែមផលិតផល' ដើម្បីបង្កើត។")
            return
        
        keyboard = InlineKeyboardMarkup(row_width=1)
        for product in products:
            stock_text = f"{product['available']}/{product['total']} នៅសល់"
            keyboard.add(InlineKeyboardButton(
                f"{product['name']} - {format_currency(product['price'])} ({stock_text})",
                callback_data=f"admin_product_{product['id']}"
            ))
        
        send_and_delete_previous(message.chat.id, message.from_user.id, message.message_id, "📦 គ្រប់គ្រងផលិតផល:", reply_markup=keyboard)

    @bot.message_handler(func=lambda m: m.text == "➕ បន្ថែមផលិតផល")
    @admin_only
    def add_product(message):
        msg = send_and_delete_previous(message.chat.id, message.from_user.id, message.message_id, "📝 បញ្ចូលឈ្មោះផលិតផល:", reply_markup=back_keyboard())
        bot.register_next_step_handler(msg, process_product_name)

    def process_product_name(message):
        if message.text in ["🔙 ត្រឡប់ក្រោយ", "BACK", "Back", "back"]:
            bot.send_message(message.chat.id, "បានបោះបង់។", reply_markup=admin_main_keyboard())
            return
        
        product_name = message.text
        msg = bot.send_message(message.chat.id, "📝 បញ្ចូលការពិពណ៌នាផលិតផល:", reply_markup=back_keyboard())
        bot.register_next_step_handler(msg, process_product_description, product_name)

    def process_product_description(message, product_name):
        if message.text in ["🔙 ត្រឡប់ក្រោយ", "BACK", "Back", "back"]:
            bot.send_message(message.chat.id, "បានបោះបង់។", reply_markup=admin_main_keyboard())
            return
        
        description = message.text
        msg = bot.send_message(message.chat.id, "💰 បញ្ចូលតម្លៃផលិតផល (USD):", reply_markup=back_keyboard())
        bot.register_next_step_handler(msg, process_product_price, product_name, description)

    def process_product_price(message, product_name, description):
        if message.text in ["🔙 ត្រឡប់ក្រោយ", "BACK", "Back", "back"]:
            bot.send_message(message.chat.id, "បានបោះបង់។", reply_markup=admin_main_keyboard())
            return
        
        try:
            price = float(message.text)
            user_failures[message.from_user.id] = 0
            msg = bot.send_message(
                message.chat.id, 
                "⏳ តើអ្នកចង់កំណត់ឱ្យលុប Product នេះដោយស្វ័យប្រវត្តិរយៈពេលប៉ុន្មានថ្ងៃ? (បញ្ចូល 0 ប្រសិនបើមិនចង់លុប):",
                reply_markup=back_keyboard()
            )
            bot.register_next_step_handler(msg, process_product_auto_delete, product_name, description, price)
        except ValueError:
            handle_invalid_input(message, process_product_price, "❌ តម្លៃមិនត្រឹមត្រូវ។ សូមបញ្ចូលលេខ:", product_name, description)

    def process_product_auto_delete(message, product_name, description, price):
        if message.text in ["🔙 ត្រឡប់ក្រោយ", "BACK", "Back", "back"]:
            bot.send_message(message.chat.id, "បានបោះបង់។", reply_markup=admin_main_keyboard())
            return
        
        try:
            auto_delete_days = int(message.text)
            if auto_delete_days < 0:
                raise ValueError
                
            user_failures[message.from_user.id] = 0
            msg = bot.send_message(
                message.chat.id, 
                "📅 តើផលិតផលនេះមានសុពលភាពប៉ុន្មានថ្ងៃ? (បញ្ចូល 0 ប្រសិនបើប្រើបានរហូត គ្មានថ្ងៃផុតកំណត់):",
                reply_markup=back_keyboard()
            )
            bot.register_next_step_handler(msg, process_product_subscription_days, product_name, description, price, auto_delete_days)
        except ValueError:
            handle_invalid_input(message, process_product_auto_delete, "❌ ថ្ងៃមិនត្រឹមត្រូវ។ សូមបញ្ចូលលេខ (ឧទាហរណ៍ 0, 10, 30):", product_name, description, price)

    def process_product_subscription_days(message, product_name, description, price, auto_delete_days):
        if message.text in ["🔙 ត្រឡប់ក្រោយ", "BACK", "Back", "back"]:
            bot.send_message(message.chat.id, "បានបោះបង់។", reply_markup=admin_main_keyboard())
            return
        
        try:
            subscription_days = int(message.text)
            if subscription_days < 0:
                raise ValueError
                
            user_failures[message.from_user.id] = 0
            with Database() as db:
                db.cursor.execute(
                    "INSERT INTO products (name, description, price, stock, auto_delete_days, subscription_days) VALUES (?, ?, ?, 0, ?, ?)",
                    (product_name, description, price, auto_delete_days, subscription_days)
                )
                product_id = db.cursor.lastrowid
                db.commit()
            
            delete_text = f"(លុបស្វ័យប្រវត្តិក្រោយ {auto_delete_days} ថ្ងៃ)" if auto_delete_days > 0 else "(មិនលុបស្វ័យប្រវត្តិ)"
            sub_text = f"(សុពលភាព {subscription_days} ថ្ងៃ)" if subscription_days > 0 else "(ប្រើបានរហូត)"
            
            bot.send_message(
                message.chat.id, 
                f"✅ បានបង្កើតផលិតផល '{product_name}' រួចរាល់!\n"
                f"• {delete_text}\n"
                f"• {sub_text}\n"
                f"លេខសម្គាល់ផលិតផល: {product_id}\n\n"
                f"ឥឡូវសូមប្រើ '📥 បន្ថែមស្តុក' ដើម្បីបន្ថែមផលិតផលឌីជីថល។",
                reply_markup=admin_main_keyboard()
            )
        except ValueError:
            handle_invalid_input(message, process_product_subscription_days, "❌ ថ្ងៃមិនត្រឹមត្រូវ។ សូមបញ្ចូលលេខ (ឧទាហរណ៍ 0, 30, 365):", product_name, description, price, auto_delete_days)

    @bot.message_handler(func=lambda m: m.text == "📥 បន្ថែមស្តុក")
    @admin_only
    def add_stock(message):
        with Database() as db:
            db.cursor.execute("SELECT id, name FROM products ORDER BY name")
            products = db.cursor.fetchall()
        
        if not products:
            send_and_delete_previous(message.chat.id, message.from_user.id, message.message_id, "❌ រកមិនឃើញផលិតផលទេ។ សូមបង្កើតផលិតផលសិន។")
            return
        
        keyboard = InlineKeyboardMarkup(row_width=1)
        for product in products:
            keyboard.add(InlineKeyboardButton(product['name'], callback_data=f"stock_{product['id']}"))
        
        send_and_delete_previous(message.chat.id, message.from_user.id, message.message_id, "ជ្រើសរើសផលិតផលដើម្បីបន្ថែមស្តុក:", reply_markup=keyboard)

    @bot.message_handler(func=lambda m: m.text == "👥 អ្នកប្រើប្រាស់")
    @admin_only
    def admin_users(message):
        with Database() as db:
            db.cursor.execute('''
                SELECT user_id, username, first_name, 
                       (SELECT COUNT(*) FROM orders WHERE user_id = users.user_id) as orders,
                       is_admin
                FROM users 
                ORDER BY created_at DESC 
                LIMIT 10
            ''')
            users = db.cursor.fetchall()
        
        keyboard = InlineKeyboardMarkup(row_width=1)
        keyboard.add(InlineKeyboardButton("🔍 ស្វែងរកអ្នកប្រើប្រាស់", callback_data="search_user"))
        for user in users:
            name = user['first_name'][:15] + "..." if len(user['first_name']) > 15 else user['first_name']
            username = f"@{user['username']}" if user['username'] else "គ្មាន UserName"
            admin_star = " 👑" if user['is_admin'] else ""
            keyboard.add(InlineKeyboardButton(
                f"{name}{admin_star} - {username} ({user['orders']} បញ្ជាទិញ)",
                callback_data=f"user_{user['user_id']}"
            ))
        
        send_and_delete_previous(message.chat.id, message.from_user.id, message.message_id, "👥 អ្នកប្រើប្រាស់ថ្មីៗ:", reply_markup=keyboard)

    @bot.message_handler(func=lambda m: m.text == "📈 ការបញ្ជាទិញទាំងអស់")
    @admin_only
    def all_orders(message):
        with Database() as db:
            db.cursor.execute('''
                SELECT o.id, u.username, p.name, o.amount, o.quantity, o.payment_status, o.created_at 
                FROM orders o 
                JOIN users u ON o.user_id = u.user_id 
                JOIN products p ON o.product_id = p.id 
                ORDER BY o.created_at DESC 
                LIMIT 20
            ''')
            orders = db.cursor.fetchall()
        
        if not orders:
            send_and_delete_previous(message.chat.id, message.from_user.id, message.message_id, "មិនទាន់មានការបញ្ជាទិញទេ។")
            return
        
        text = "📈 ការបញ្ជាទិញទាំងអស់ (២០ ចុងក្រោយ):\n\n"
        for order in orders:
            status_text = '✅ បានទូទាត់' if order['payment_status'] == 'completed' else '⏳ រង់ចាំ'
            text += f"{status_text} #{order['id']} - @{order['username']}\n"
            text += f"   {order['name']} x{order['quantity']} - {format_currency(order['amount'])}\n"
            text += f"   {order['created_at'][:19]}\n\n"
        
        send_and_delete_previous(message.chat.id, message.from_user.id, message.message_id, text)
