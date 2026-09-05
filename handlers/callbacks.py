import threading
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from bot_instance import bot, active_sessions, user_failures
from database import Database
from utils import is_admin, is_super_admin, format_currency, parse_product_format, handle_invalid_input, get_user_lang
from keyboards import admin_main_keyboard, user_main_keyboard, back_keyboard
from payment import initiate_payment, cancel_order
from translations import t

def register_callback_handlers():
    @bot.callback_query_handler(func=lambda call: True)
    def handle_callbacks(call):
        user_id = call.from_user.id
        try:
            if call.data.startswith("show_"):
                product_id = int(call.data.split("_")[1])
                show_product_details(call.message, product_id, user_id)
            elif call.data.startswith("buynow_"):
                product_id = int(call.data.split("_")[1])
                ask_quantity(call.message, product_id, user_id)
            elif call.data.startswith("fb_"):
                product_id = int(call.data.split("_")[1])
                ask_feedback_rating(call.message, product_id, user_id)
            elif call.data.startswith("rate_"):
                parts = call.data.split("_")
                ask_feedback_comment(call.message, int(parts[1]), user_id, int(parts[2]))
            elif call.data.startswith("addcart_"):
                product_id = int(call.data.split("_")[1])
                ask_cart_quantity(call.message, product_id, user_id)
            elif call.data.startswith("rmcart_"):
                cart_id = int(call.data.split("_")[1])
                remove_from_cart(call.message, cart_id, user_id)
            elif call.data == "checkout_cart":
                from payment import initiate_cart_payment
                initiate_cart_payment(call.message, user_id)
            elif call.data == "history_completed":
                show_order_history(call.message, user_id, completed=True)
            elif call.data == "history_pending":
                show_order_history(call.message, user_id, completed=False)
            elif call.data.startswith("order_detail_"):
                order_id = int(call.data.split("_")[2])
                show_order_detail(call.message, user_id, order_id)
            elif call.data.startswith("admin_product_"):
                product_id = int(call.data.split("_")[2])
                show_admin_product(call.message, product_id)
            elif call.data.startswith("stock_"):
                product_id = int(call.data.split("_")[1])
                msg = bot.send_message(
                    call.message.chat.id,
                    "📝 បញ្ជូនផលិតផលឌីជីថលតាមទម្រង់នេះ:\n"
                    "អ៊ីមែល|ពាក្យសម្ងាត់|លេខកូដ(ស្រេចចិត្ត)|2FA(ស្រេចចិត្ត)\n\n"
                    "អ្នកអាចបញ្ជូនច្រើនក្នុងពេលតែម្តង មួយបន្ទាត់មួយ:\n"
                    "user1@example.com|pass123|KEY123|2FA123\n"
                )
                bot.register_next_step_handler(msg, process_bulk_stock, product_id)
            elif call.data.startswith("view_content_"):
                product_id = int(call.data.split("_")[2])
                view_product_content(call.message, product_id)
            elif call.data.startswith("delete_product_"):
                product_id = int(call.data.split("_")[2])
                confirm_delete_product(call.message, product_id)
            elif call.data.startswith("confirm_delete_"):
                product_id = int(call.data.split("_")[2])
                delete_product(call.message, product_id)
            elif call.data.startswith("edit_price_"):
                product_id = int(call.data.split("_")[2])
                msg = bot.send_message(call.message.chat.id, "💰 បញ្ចូលតម្លៃថ្មី:", reply_markup=back_keyboard())
                bot.register_next_step_handler(msg, process_edit_price, product_id)
            elif call.data.startswith("edit_name_"):
                product_id = int(call.data.split("_")[2])
                msg = bot.send_message(call.message.chat.id, "📝 បញ្ចូលឈ្មោះថ្មី:", reply_markup=back_keyboard())
                bot.register_next_step_handler(msg, process_edit_name, product_id)
            elif call.data.startswith("edit_desc_"):
                product_id = int(call.data.split("_")[2])
                msg = bot.send_message(call.message.chat.id, "📝 បញ្ចូលការពិពណ៌នាថ្មី:", reply_markup=back_keyboard())
                bot.register_next_step_handler(msg, process_edit_description, product_id)
            elif call.data.startswith("user_"):
                # Avoid conflict with user_orders_
                if not call.data.startswith("user_orders_"):
                    target_user_id = int(call.data.split("_")[1])
                    show_user_details(call.message, target_user_id)
            elif call.data.startswith("make_admin_"):
                target_user_id = int(call.data.split("_")[2])
                make_admin(call.message, target_user_id)
            elif call.data.startswith("revoke_admin_"):
                target_user_id = int(call.data.split("_")[2])
                revoke_admin(call.message, target_user_id)
            elif call.data == "search_user":
                msg = bot.send_message(call.message.chat.id, "🔍 សូមបញ្ចូល ID អ្នកប្រើប្រាស់ (ឧទាហរណ៍: 123456789):", reply_markup=back_keyboard())
                bot.register_next_step_handler(msg, process_search_user)
            elif call.data.startswith("user_orders_"):
                target_user_id = int(call.data.split("_")[2])
                view_user_orders(call.message, target_user_id)
            elif call.data == "back_to_menu":
                bot.delete_message(call.message.chat.id, call.message.message_id)
                if is_admin(user_id):
                    bot.send_message(call.message.chat.id, "ម៉ឺនុយមេ:", reply_markup=admin_main_keyboard())
                else:
                    bot.send_message(call.message.chat.id, "ម៉ឺនុយមេ:", reply_markup=user_main_keyboard())
            elif call.data == "back_to_products":
                bot.delete_message(call.message.chat.id, call.message.message_id)
                if is_admin(user_id):
                    from handlers.admin import admin_products
                    admin_products(call.message)
                else:
                    from handlers.user import buy_products
                    buy_products(call.message)
            elif call.data == "back_to_users":
                bot.delete_message(call.message.chat.id, call.message.message_id)
                from handlers.admin import admin_users
                admin_users(call.message)
            elif call.data.startswith("check_payment_"):
                bot.answer_callback_query(call.id, "✅ ប្រព័ន្ធកំពុងឆែកមើលលុយដោយស្វ័យប្រវត្តិ។ សូមរង់ចាំបន្តិច...")
            elif call.data.startswith("cancel_order_"):
                transaction_id = call.data.split("_")[2]
                cancel_order(call.message, transaction_id, user_id)
        except Exception as e:
            bot.answer_callback_query(call.id, f"កំហុស: {str(e)}")
        bot.answer_callback_query(call.id)

# ============ CALLBACK LOGIC FUNCTIONS ============

def show_product_details(message, product_id, user_id):
    with Database() as db:
        db.cursor.execute("SELECT name, description, price, stock FROM products WHERE id = ?", (product_id,))
        product = db.cursor.fetchone()
        
        db.cursor.execute("SELECT AVG(rating) as avg_rating, COUNT(*) as total_fb FROM feedbacks WHERE product_id = ?", (product_id,))
        fb = db.cursor.fetchone()
        avg_rating = round(fb['avg_rating'], 1) if fb['avg_rating'] else 0
        total_fb = fb['total_fb']
        
        if not product:
            bot.send_message(message.chat.id, "❌ រកអីវ៉ាន់នេះអត់ឃើញទេ។")
            return
    
    text = f"""
📦 {product['name']}
━━━━━━━━━━━━━━━━━━━
⭐ រង្វាយតម្លៃ (Rating): {avg_rating} ({total_fb} feedbacks)

📝 ព័ត៌មានលម្អិត:
{product['description']}

💰 តម្លៃ: {format_currency(product['price'])} ក្នុងមួយគ្រឿង
📦 ស្តុកនៅសល់: {product['stock']}
━━━━━━━━━━━━━━━━━━━
    """
    keyboard = InlineKeyboardMarkup(row_width=2)
    if product['stock'] > 0:
        keyboard.add(
            InlineKeyboardButton("🛒 ទិញ", callback_data=f"buynow_{product_id}"),
            InlineKeyboardButton("🛍️ ដាក់កន្ត្រក", callback_data=f"addcart_{product_id}")
        )
    keyboard.add(InlineKeyboardButton("🔙 ត្រឡប់ក្រោយ", callback_data="back_to_menu"))
    try:
        bot.edit_message_text(chat_id=message.chat.id, message_id=message.message_id, text=text, reply_markup=keyboard)
    except:
        bot.send_message(message.chat.id, text, reply_markup=keyboard)

def show_order_history(message, user_id, completed):
    with Database() as db:
        if completed:
            db.cursor.execute('''
                SELECT o.id, p.name, o.amount, o.quantity, o.created_at 
                FROM orders o 
                JOIN products p ON o.product_id = p.id 
                WHERE o.user_id = ? AND o.payment_status = 'completed'
                ORDER BY o.created_at DESC LIMIT 20
            ''', (user_id,))
            orders = db.cursor.fetchall()
            title = "✅ ប្រវត្តិទិញជោគជ័យ"
            empty_msg = "បងមិនទាន់មានប្រវត្តិទិញជោគជ័យនៅឡើយទេ។"
        else:
            db.cursor.execute('''
                SELECT o.id, p.name, o.amount, o.quantity, o.payment_status, o.created_at 
                FROM orders o 
                JOIN products p ON o.product_id = p.id 
                WHERE o.user_id = ? AND o.payment_status != 'completed'
                ORDER BY o.created_at DESC LIMIT 20
            ''', (user_id,))
            orders = db.cursor.fetchall()
            title = "⏳ ប្រវត្តិមិនទាន់បង់លុយ"
            empty_msg = "បងមិនទាន់មានប្រវត្តិមិនទាន់បង់លុយនៅឡើយទេ។"
            
    keyboard = InlineKeyboardMarkup(row_width=1)
    if not orders:
        text = f"{title}:\n\n{empty_msg}"
    else:
        if completed:
            text = f"{title}:\n\nសូមចុចលើអីវ៉ាន់នីមួយៗខាងក្រោម ដើម្បីមើលគណនី (Account) និងព័ត៌មានលម្អិត:"
            for order in orders:
                btn_text = f"✅ #{order['id']} - {order['name']} (x{order['quantity']}) - {format_currency(order['amount'])}"
                keyboard.add(InlineKeyboardButton(btn_text, callback_data=f"order_detail_{order['id']}"))
        else:
            text = f"{title}:\n\nការបញ្ជាទិញទាំងនេះត្រូវបានបោះបង់ ឬមិនទាន់បង់លុយជោគជ័យ:\n\n"
            for order in orders:
                status_text = '⏳ រង់ចាំទូទាត់' if order['payment_status'] == 'pending' else '❌ បោះបង់'
                text += f"{status_text} ការបញ្ជាទិញ #{order['id']}\n"
                text += f"អីវ៉ាន់: {order['name']}\n"
                text += f"ចំនួន: {order['quantity']}\n"
                text += f"ទឹកប្រាក់: {format_currency(order['amount'])}\n"
                text += f"កាលបរិច្ឆេទ: {order['created_at'][:19]}\n\n"
                
    keyboard.add(InlineKeyboardButton("🔙 ត្រឡប់ក្រោយ", callback_data="back_to_menu"))
    try:
        bot.edit_message_text(chat_id=message.chat.id, message_id=message.message_id, text=text, reply_markup=keyboard)
    except:
        bot.send_message(message.chat.id, text, reply_markup=keyboard)

def show_order_detail(message, user_id, order_id):
    from utils import format_product_display
    with Database() as db:
        db.cursor.execute('''
            SELECT o.id, p.name, p.description, o.amount, o.quantity, o.created_at, o.bakong_transaction_id
            FROM orders o 
            JOIN products p ON o.product_id = p.id 
            WHERE o.id = ? AND o.user_id = ? AND o.payment_status = 'completed'
        ''', (order_id, user_id))
        order = db.cursor.fetchone()
        
        if not order:
            bot.answer_callback_query(message.id, "❌ រកអីវ៉ាន់នេះអត់ឃើញទេ។")
            return
            
        db.cursor.execute('''
            SELECT email, password, license_key, twofa_secret 
            FROM digital_products 
            WHERE order_id = ?
        ''', (order_id,))
        accounts = db.cursor.fetchall()
        
    text = f"📦 លម្អិតការបញ្ជាទិញ #{order['id']}\n"
    text += f"━━━━━━━━━━━━━━━━━━━\n"
    text += f"អីវ៉ាន់: {order['name']}\n"
    text += f"កាលបរិច្ឆេទ: {order['created_at'][:19]}\n"
    text += f"លេខកូដប្រតិបត្តិការ (Bank): {order['bakong_transaction_id'] or 'N/A'}\n\n"
    
    text += "📝 ការពិពណ៌នាអីវ៉ាន់ និងការធានា:\n"
    text += f"{order['description']}\n\n"
    
    text += "🔑 គណនីរបស់អ្នក:\n"
    for idx, acc in enumerate(accounts, 1):
        text += f"**គណនីទី {idx}:**\n"
        text += format_product_display(acc['email'], acc['password'], acc['license_key'], acc['twofa_secret'])
        text += "\n"
        
    keyboard = InlineKeyboardMarkup()
    keyboard.add(InlineKeyboardButton("🔙 ត្រឡប់ក្រោយ", callback_data="history_completed"))
    try:
        bot.edit_message_text(chat_id=message.chat.id, message_id=message.message_id, text=text, parse_mode='Markdown', reply_markup=keyboard)
    except:
        bot.send_message(message.chat.id, text, parse_mode='Markdown', reply_markup=keyboard)

def ask_quantity(message, product_id, user_id):
    text = "🔢 បងចង់ទិញប៉ុន្មានដែរ? វាយលេខមកបង (ឧទាហរណ៍: 1, 2, 3...):"
    try:
        bot.edit_message_text(chat_id=message.chat.id, message_id=message.message_id, text=text, reply_markup=back_keyboard())
    except:
        bot.send_message(message.chat.id, text, reply_markup=back_keyboard())
    bot.register_next_step_handler(message, process_quantity, product_id, user_id)

def process_quantity(message, product_id, user_id):
    if message.text in ["🔙 ត្រឡប់ក្រោយ", "BACK", "Back", "back"]:
        bot.clear_step_handler_by_chat_id(message.chat.id)
        if is_admin(user_id):
            bot.send_message(message.chat.id, "ម៉ឺនុយ:", reply_markup=admin_main_keyboard())
        else:
            bot.send_message(message.chat.id, "ម៉ឺនុយ:", reply_markup=user_main_keyboard())
        return
    
    try:
        quantity = int(message.text)
        if quantity <= 0:
            raise ValueError
            
        user_failures[user_id] = 0
        
        with Database() as db:
            db.cursor.execute("SELECT stock FROM products WHERE id = ?", (product_id,))
            result = db.cursor.fetchone()
            if not result:
                bot.send_message(message.chat.id, "❌ រកអីវ៉ាន់នេះអត់ឃើញទេ។")
                return
            stock = result['stock']
            
            if quantity > stock:
                bot.send_message(
                    message.chat.id,
                    f"❌ អធ្យាស្រ័យបង សល់ស្តុកតែ {stock} ទេ។ បងវាយលេខម្តងទៀតមក:",
                    reply_markup=back_keyboard()
                )
                bot.register_next_step_handler(message, process_quantity, product_id, user_id)
                return
        
        initiate_payment(message, product_id, user_id, quantity)
    except ValueError:
        handle_invalid_input(message, process_quantity, "❌ បងវាយលេខអត់ត្រូវទេ។ សុំវាយជាលេខទទេមកបង (ឧទាហរណ៍: 1, 2, 3...):", product_id, user_id)

def ask_cart_quantity(message, product_id, user_id):
    text = "🔢 តើបងចង់ដាក់ចូលកន្ត្រកប៉ុន្មានដែរ? វាយលេខមកបង (ឧទាហរណ៍: 1, 2, 3...):"
    try:
        bot.edit_message_text(chat_id=message.chat.id, message_id=message.message_id, text=text, reply_markup=back_keyboard())
    except:
        bot.send_message(message.chat.id, text, reply_markup=back_keyboard())
    bot.register_next_step_handler(message, process_cart_quantity, product_id, user_id)

def process_cart_quantity(message, product_id, user_id):
    if message.text in ["🔙 ត្រឡប់ក្រោយ", "BACK", "Back", "back"]:
        bot.clear_step_handler_by_chat_id(message.chat.id)
        if is_admin(user_id):
            bot.send_message(message.chat.id, "ម៉ឺនុយ:", reply_markup=admin_main_keyboard())
        else:
            bot.send_message(message.chat.id, "ម៉ឺនុយ:", reply_markup=user_main_keyboard())
        return
    
    try:
        quantity = int(message.text)
        if quantity <= 0:
            raise ValueError
            
        user_failures[user_id] = 0
        
        with Database() as db:
            db.cursor.execute("SELECT stock FROM products WHERE id = ?", (product_id,))
            result = db.cursor.fetchone()
            if not result:
                bot.send_message(message.chat.id, "❌ រកអីវ៉ាន់នេះអត់ឃើញទេ។")
                return
            stock = result['stock']
            
            if quantity > stock:
                bot.send_message(
                    message.chat.id,
                    f"❌ អធ្យាស្រ័យបង សល់ស្តុកតែ {stock} ទេ។ បងវាយលេខម្តងទៀតមក:",
                    reply_markup=back_keyboard()
                )
                bot.register_next_step_handler(message, process_cart_quantity, product_id, user_id)
                return
            
            # Check if already in cart
            db.cursor.execute("SELECT id, quantity FROM cart WHERE user_id = ? AND product_id = ?", (user_id, product_id))
            existing = db.cursor.fetchone()
            
            if existing:
                new_quantity = existing['quantity'] + quantity
                if new_quantity > stock:
                    bot.send_message(message.chat.id, f"❌ ស្តុកមានតែ {stock} ទេ តែក្នុងកន្ត្រកបងមាន {existing['quantity']} ហើយ។")
                    return
                db.cursor.execute("UPDATE cart SET quantity = ? WHERE id = ?", (new_quantity, existing['id']))
            else:
                db.cursor.execute("INSERT INTO cart (user_id, product_id, quantity) VALUES (?, ?, ?)", (user_id, product_id, quantity))
            
            db.commit()
            
        bot.send_message(
            message.chat.id, 
            "✅ ដាក់ចូលកន្ត្រកបានជោគជ័យ!", 
            reply_markup=user_main_keyboard(get_user_lang(user_id))
        )
    except ValueError:
        handle_invalid_input(message, process_cart_quantity, "❌ លេខមិនត្រឹមត្រូវ។ សូមបញ្ចូលលេខ:", product_id, user_id)

def remove_from_cart(message, cart_id, user_id):
    with Database() as db:
        db.cursor.execute("DELETE FROM cart WHERE id = ? AND user_id = ?", (cart_id, user_id))
        db.commit()
    
    bot.answer_callback_query(message.id, "✅ បានលុបចេញពីកន្ត្រក!")
    # Call my_cart to refresh UI
    from handlers.user import my_cart
    # Fake message object for my_cart
    message.text = t('btn_cart', get_user_lang(user_id))
    my_cart(message)

def ask_feedback_rating(message, product_id, user_id):
    lang = get_user_lang(user_id)
    with Database() as db:
        db.cursor.execute("SELECT name FROM products WHERE id = ?", (product_id,))
        product = db.cursor.fetchone()
    
    keyboard = InlineKeyboardMarkup(row_width=5)
    keyboard.add(
        InlineKeyboardButton("1⭐", callback_data=f"rate_{product_id}_1"),
        InlineKeyboardButton("2⭐", callback_data=f"rate_{product_id}_2"),
        InlineKeyboardButton("3⭐", callback_data=f"rate_{product_id}_3"),
        InlineKeyboardButton("4⭐", callback_data=f"rate_{product_id}_4"),
        InlineKeyboardButton("5⭐", callback_data=f"rate_{product_id}_5")
    )
    bot.edit_message_text(
        chat_id=message.chat.id,
        message_id=message.message_id,
        text=t('feedback_ask_rating', lang, product_name=product['name']),
        reply_markup=keyboard
    )

def ask_feedback_comment(message, product_id, user_id, rating):
    lang = get_user_lang(user_id)
    with Database() as db:
        db.cursor.execute("SELECT name FROM products WHERE id = ?", (product_id,))
        product = db.cursor.fetchone()
        
    msg = bot.edit_message_text(
        chat_id=message.chat.id,
        message_id=message.message_id,
        text=t('feedback_ask_comment', lang, product_name=product['name'])
    )
    bot.register_next_step_handler(message, process_feedback_comment, product_id, user_id, rating)

def process_feedback_comment(message, product_id, user_id, rating):
    lang = get_user_lang(user_id)
    if message.text in ["🔙 ត្រឡប់ក្រោយ", "BACK", "Back", "back", "🔙", t('btn_back', 'en')]:
        bot.send_message(message.chat.id, t('feedback_cancelled', lang))
        return
        
    comment = message.text
    with Database() as db:
        db.cursor.execute('''
            INSERT INTO feedbacks (user_id, product_id, rating, comment)
            VALUES (?, ?, ?, ?)
        ''', (user_id, product_id, rating, comment))
        db.commit()
        
    bot.send_message(message.chat.id, t('feedback_success', lang))

def show_admin_product(message, product_id):
    with Database() as db:
        db.cursor.execute("SELECT * FROM products WHERE id = ?", (product_id,))
        product = db.cursor.fetchone()
        
        if not product:
            bot.send_message(message.chat.id, "រកមិនឃើញផលិតផល។")
            return
        
        db.cursor.execute('''
            SELECT 
                COUNT(*) as total,
                SUM(CASE WHEN is_sold = 0 THEN 1 ELSE 0 END) as available,
                SUM(CASE WHEN is_sold = 1 THEN 1 ELSE 0 END) as sold
            FROM digital_products 
            WHERE product_id = ?
        ''', (product_id,))
        stats = db.cursor.fetchone()
    
    text = f"""
📦 ព័ត៌មានលម្អិតផលិតផល
━━━━━━━━━━━━━━━━━━━
ID: {product['id']}
ឈ្មោះ: {product['name']}
តម្លៃ: {format_currency(product['price'])}
ស្តុក: {stats['available'] or 0}/{stats['total'] or 0}

📝 ការពិពណ៌នា:
{product['description']}

📊 ស្ថិតិ
━━━━━━━━━━━━━━━━━━━
📦 ស្តុកសរុប: {stats['total'] or 0}
✅ នៅសល់: {stats['available'] or 0}
💰 បានលក់: {stats['sold'] or 0}
━━━━━━━━━━━━━━━━━━━
    """
    keyboard = InlineKeyboardMarkup(row_width=2)
    keyboard.add(
        InlineKeyboardButton("📥 មើលមាតិកា", callback_data=f"view_content_{product_id}"),
        InlineKeyboardButton("💰 កែតម្លៃ", callback_data=f"edit_price_{product_id}")
    )
    keyboard.add(
        InlineKeyboardButton("📝 កែឈ្មោះ", callback_data=f"edit_name_{product_id}"),
        InlineKeyboardButton("📄 កែការពិពណ៌នា", callback_data=f"edit_desc_{product_id}")
    )
    keyboard.add(InlineKeyboardButton("❌ លុបផលិតផល", callback_data=f"delete_product_{product_id}"))
    keyboard.add(InlineKeyboardButton("🔙 ត្រឡប់ក្រោយ", callback_data="back_to_products"))
    
    try:
        bot.edit_message_text(chat_id=message.chat.id, message_id=message.message_id, text=text, reply_markup=keyboard)
    except:
        bot.send_message(message.chat.id, text, reply_markup=keyboard)

def process_bulk_stock(message, product_id):
    if message.text in ["🔙 ត្រឡប់ក្រោយ", "BACK", "Back", "back"]:
        bot.send_message(message.chat.id, "បានបោះបង់។", reply_markup=admin_main_keyboard())
        return
    
    lines = message.text.strip().split('\n')
    added = 0
    errors = 0
    
    with Database() as db:
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            email, password, license_key, twofa = parse_product_format(line)
            if email and password:
                db.cursor.execute('''
                    INSERT INTO digital_products (product_id, email, password, license_key, twofa_secret)
                    VALUES (?, ?, ?, ?, ?)
                ''', (product_id, email, password, license_key, twofa))
                added += 1
            else:
                errors += 1
        
        db.cursor.execute('''
            UPDATE products 
            SET stock = (SELECT COUNT(*) FROM digital_products WHERE product_id = ? AND is_sold = 0)
            WHERE id = ?
        ''', (product_id, product_id))
        db.commit()
    
    result_text = f"✅ បន្ថែមស្តុកបានជោគជ័យ!\n✓ បន្ថែមបាន: {added} ផលិតផល"
    if errors > 0:
        result_text += f"\n⚠️ បរាជ័យ: {errors} ផលិតផល (ទម្រង់មិនត្រឹមត្រូវ)"
    
    bot.send_message(message.chat.id, result_text, reply_markup=admin_main_keyboard())

def view_product_content(message, product_id):
    with Database() as db:
        db.cursor.execute('''
            SELECT id, email, password, license_key, twofa_secret, is_sold, sold_at
            FROM digital_products 
            WHERE product_id = ?
            ORDER BY is_sold, id
            LIMIT 100
        ''', (product_id,))
        contents = db.cursor.fetchall()
    
    if not contents:
        bot.send_message(message.chat.id, "មិនទាន់មានផលិតផលឌីជីថលសម្រាប់ផលិតផលនេះទេ។")
        return
    
    text = f"📦 ផលិតផលឌីជីថល (១០០ ចុងក្រោយ):\n\n"
    for item in contents:
        status = "✅ បានលក់" if item['is_sold'] else "📦 នៅសល់"
        text += f"ID: {item['id']} - {status}\n"
        text += f"📧 {item['email']}\n"
        text += f"🔑 {item['password']}\n"
        if item['license_key']:
            text += f"🔐 {item['license_key']}\n"
        if item['twofa_secret']:
            text += f"🔒 {item['twofa_secret']}\n"
        if item['sold_at']:
            text += f"📅 {item['sold_at'][:19]}\n"
        text += "━━━━━━━━━━━━━━━━━━━\n"
    
    if len(text) > 4000:
        chunks = [text[i:i+4000] for i in range(0, len(text), 4000)]
        for chunk in chunks:
            bot.send_message(message.chat.id, chunk)
    else:
        bot.send_message(message.chat.id, text)

def confirm_delete_product(message, product_id):
    keyboard = InlineKeyboardMarkup()
    keyboard.add(
        InlineKeyboardButton("✅ បាទ/ចាស លុប", callback_data=f"confirm_delete_{product_id}"),
        InlineKeyboardButton("❌ ទេ", callback_data=f"admin_product_{product_id}")
    )
    text = (
        f"⚠️ តើអ្នកប្រាកដថាចង់លុបផលិតផល #{product_id} ទេ?\n"
        f"ការលុបនឹងលុបផលិតផលឌីជីថលទាំងអស់ដែលភ្ជាប់ជាមួយវាផងដែរ!\n"
        f"សកម្មភាពនេះមិនអាចត្រឡប់ក្រោយវិញបានទេ។"
    )
    try:
        bot.edit_message_text(chat_id=message.chat.id, message_id=message.message_id, text=text, reply_markup=keyboard)
    except:
        bot.send_message(message.chat.id, text, reply_markup=keyboard)

def delete_product(message, product_id):
    with Database() as db:
        # We soft-delete the product so old order histories don't break.
        db.cursor.execute("UPDATE products SET is_active = 0, stock = 0 WHERE id = ?", (product_id,))
        # Also mark all unsold digital products as deleted by removing them
        db.cursor.execute("DELETE FROM digital_products WHERE product_id = ? AND is_sold = 0", (product_id,))
        db.commit()
    bot.send_message(message.chat.id, f"✅ បានលុបផលិតផល #{product_id} រួចរាល់។", reply_markup=admin_main_keyboard())

def process_edit_price(message, product_id):
    if message.text in ["🔙 ត្រឡប់ក្រោយ", "Back", "back"]:
        show_admin_product(message, product_id)
        return
    try:
        price = float(message.text)
        user_failures[message.from_user.id] = 0
        with Database() as db:
            db.cursor.execute("UPDATE products SET price = ? WHERE id = ?", (price, product_id))
            db.commit()
        bot.send_message(message.chat.id, f"✅ បានកែតម្លៃទៅ {format_currency(price)}")
        show_admin_product(message, product_id)
    except ValueError:
        handle_invalid_input(message, process_edit_price, "❌ តម្លៃមិនត្រឹមត្រូវ។ សូមបញ្ចូលលេខ:", product_id)

def process_edit_name(message, product_id):
    if message.text in ["🔙 ត្រឡប់ក្រោយ", "Back", "back"]:
        show_admin_product(message, product_id)
        return
    name = message.text
    with Database() as db:
        db.cursor.execute("UPDATE products SET name = ? WHERE id = ?", (name, product_id))
        db.commit()
    bot.send_message(message.chat.id, f"✅ បានកែឈ្មោះទៅ '{name}'")
    show_admin_product(message, product_id)

def process_edit_description(message, product_id):
    if message.text in ["🔙 ត្រឡប់ក្រោយ", "Back", "back"]:
        show_admin_product(message, product_id)
        return
    description = message.text
    with Database() as db:
        db.cursor.execute("UPDATE products SET description = ? WHERE id = ?", (description, product_id))
        db.commit()
    bot.send_message(message.chat.id, "✅ បានកែការពិពណ៌នារួចរាល់")
    show_admin_product(message, product_id)

def show_user_details(message, user_id):
    with Database() as db:
        db.cursor.execute('''
            SELECT u.*, 
                   (SELECT COUNT(*) FROM orders WHERE user_id = u.user_id) as orders_count,
                   (SELECT SUM(amount) FROM orders WHERE user_id = u.user_id AND payment_status = 'completed') as total_spent
            FROM users u
            WHERE u.user_id = ?
        ''', (user_id,))
        user = db.cursor.fetchone()
    
    if not user:
        bot.send_message(message.chat.id, "រកមិនឃើញអ្នកប្រើប្រាស់។")
        return
    
    text = f"""
👤 ព័ត៌មានលម្អិតអ្នកប្រើប្រាស់
━━━━━━━━━━━━━━
ID: {user['user_id']}
UserName: @{user['username'] if user['username'] else 'N/A'}
ឈ្មោះ: {user['first_name']} {user['last_name'] or ''}
តួនាទី: {'👑 អ្នកគ្រប់គ្រង' if user['is_admin'] else '👤 អ្នកប្រើប្រាស់'}
ចូលរួម: {user['created_at'][:19]}

📊 ស្ថិតិ
━━━━━━━━━━━━━━
📦 ការបញ្ជាទិញសរុប: {user['orders_count']}
💰 ទឹកប្រាក់សរុប: {format_currency(user['total_spent'] or 0)}
━━━━━━━━━━━━━━
    """
    keyboard = InlineKeyboardMarkup()
    if is_super_admin(message.chat.id):
        if not user['is_admin']:
            keyboard.add(InlineKeyboardButton("👑 តែងតាំងជាអ្នកគ្រប់គ្រង", callback_data=f"make_admin_{user['user_id']}"))
        elif not is_super_admin(user['user_id']):
            keyboard.add(InlineKeyboardButton("🚫 ដកសិទ្ធិអ្នកគ្រប់គ្រង", callback_data=f"revoke_admin_{user['user_id']}"))
            
    keyboard.add(InlineKeyboardButton("📦 មើលការបញ្ជាទិញ", callback_data=f"user_orders_{user['user_id']}"))
    keyboard.add(InlineKeyboardButton("🔙 ត្រឡប់ក្រោយ", callback_data="back_to_users"))
    
    try:
        bot.edit_message_text(chat_id=message.chat.id, message_id=message.message_id, text=text, reply_markup=keyboard)
    except:
        bot.send_message(message.chat.id, text, reply_markup=keyboard)

def make_admin(message, user_id):
    if not is_super_admin(message.chat.id):
        bot.send_message(message.chat.id, "⛔ សុំទោស មានតែ Super Admin ប៉ុណ្ណោះដែលអាចផ្តល់សិទ្ធិបាន។")
        return
    with Database() as db:
        db.cursor.execute("UPDATE users SET is_admin = 1 WHERE user_id = ?", (user_id,))
        db.commit()
    bot.send_message(message.chat.id, f"✅ អ្នកប្រើប្រាស់ {user_id} ឥឡូវជាអ្នកគ្រប់គ្រងហើយ។")
    try:
        bot.send_message(user_id, "👑 សូមអបអរសាទរ! អ្នកត្រូវបានតែងតាំងជាអ្នកគ្រប់គ្រង。\nប្រើ /start ដើម្បីចូលប្រើមុខងារអ្នកគ្រប់គ្រង។")
    except:
        pass

def revoke_admin(message, user_id):
    if not is_super_admin(message.chat.id):
        bot.send_message(message.chat.id, "⛔ សុំទោស មានតែ Super Admin ប៉ុណ្ណោះដែលអាចដកសិទ្ធិបាន។")
        return
    with Database() as db:
        db.cursor.execute("UPDATE users SET is_admin = 0 WHERE user_id = ?", (user_id,))
        db.commit()
    bot.send_message(message.chat.id, f"✅ បានដកសិទ្ធិអ្នកគ្រប់គ្រងពី {user_id} រួចរាល់។")
    show_user_details(message, user_id)

def process_search_user(message):
    if message.text in ["🔙 ត្រឡប់ក្រោយ", "BACK", "Back", "back"]:
        from handlers.admin import admin_users
        admin_users(message)
        return
    
    try:
        user_id = int(message.text)
        user_failures[message.from_user.id] = 0
        show_user_details(message, user_id)
    except ValueError:
        handle_invalid_input(message, process_search_user, "❌ ID មិនត្រឹមត្រូវ។ សូមបញ្ចូលលេខ:")

def view_user_orders(message, user_id):
    with Database() as db:
        db.cursor.execute('''
            SELECT o.id, p.name, o.amount, o.quantity, o.payment_status, o.created_at 
            FROM orders o 
            JOIN products p ON o.product_id = p.id 
            WHERE o.user_id = ? 
            ORDER BY o.created_at DESC
        ''', (user_id,))
        orders = db.cursor.fetchall()
    
    if not orders:
        bot.send_message(message.chat.id, "អ្នកប្រើប្រាស់នេះមិនទាន់មានការបញ្ជាទិញទេ។")
        return
    
    text = f"📦 ការបញ្ជាទិញរបស់អ្នកប្រើប្រាស់ {user_id}:\n\n"
    for order in orders:
        status_text = '✅ បានទូទាត់' if order['payment_status'] == 'completed' else '⏳ រង់ចាំ'
        text += f"{status_text} #{order['id']} - {order['name']}\n"
        text += f"   ចំនួន: {order['quantity']} - {format_currency(order['amount'])} - {order['created_at'][:19]}\n\n"
        
    keyboard = InlineKeyboardMarkup()
    keyboard.add(InlineKeyboardButton("🔙 ត្រឡប់ក្រោយ", callback_data=f"user_{user_id}"))
    
    try:
        bot.edit_message_text(chat_id=message.chat.id, message_id=message.message_id, text=text, reply_markup=keyboard)
    except:
        bot.send_message(message.chat.id, text, reply_markup=keyboard)
