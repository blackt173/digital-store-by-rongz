import time
import random
import hashlib
from io import BytesIO
import requests
import qrcode
import threading
from datetime import datetime

from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from bot_instance import bot, active_sessions
from database import Database
from config import (
    KHQR_ACCOUNT_ID, MERCHANT_NAME, MERCHANT_CITY, 
    BAKONG_TOKEN, BAKONG_CHECK_URL, ADMIN_IDS, GROUP_ID
)
from utils import format_currency, format_product_display

# ============ BAKONG KHQR LIBRARY FALLBACK ============
try:
    from bakong_khqr import KHQR
except ImportError:
    class KHQR:
        def create_qr(self, bank_account, merchant_name, merchant_city, amount, currency,
                      store_label, terminal_label, phone_number, bill_number):
            return f"KHQR|{bank_account}|{amount}|{bill_number}|{merchant_name}|{merchant_city}|3"

def generate_api_khqr(amount):
    try:
        khqr = KHQR()
        bill_id = f"TRX{int(time.time())}{random.randint(10,99)}"
        phone = KHQR_ACCOUNT_ID if KHQR_ACCOUNT_ID and KHQR_ACCOUNT_ID.isdigit() else "085000000"
        
        qr_string = khqr.create_qr(
            bank_account=KHQR_ACCOUNT_ID,
            merchant_name=MERCHANT_NAME,
            merchant_city=MERCHANT_CITY,
            amount=amount,
            currency='USD',
            store_label='Bot',
            terminal_label='POS',
            phone_number=phone,
            bill_number=bill_id
        )
        md5_hash = hashlib.md5(qr_string.encode('utf-8')).hexdigest()
        
        qr = qrcode.QRCode(box_size=10, border=2)
        qr.add_data(qr_string)
        qr.make(fit=True)
        img = qr.make_image(fill_color="black", back_color="white")
        bio = BytesIO()
        img.save(bio, 'PNG')
        bio.seek(0)
        
        return bio, bill_id, md5_hash
    except Exception as e:
        print(f"❌ KHQR generation error: {e}")
        return None, None, None

def check_bakong_api(md5_hash):
    url = BAKONG_CHECK_URL
    headers = {
        "Authorization": f"Bearer {BAKONG_TOKEN}",
        "Content-Type": "application/json",
        "Accept": "application/json"
    }
    payload = {"md5": md5_hash}
    
    try:
        try:
            from curl_cffi import requests as c_requests
            req_session = c_requests.Session(impersonate="chrome110")
            response = req_session.post(url, json=payload, headers=headers, timeout=8)
        except ImportError:
            import requests
            response = requests.post(url, json=payload, headers=headers, timeout=8)
            
        if response.status_code != 200:
            print(f"⚠️ API returned status {response.status_code}: {response.text[:200]}")
            
        data = response.json()
        
        if data.get('success') or data.get('paid') or data.get('responseCode') == 0 or data.get('status') in ['success', 'paid'] or data.get('isPaid'):
            return True
        return False
        
    except Exception as e:
        print(f"⚠️ API Error (MD5: {md5_hash[:8]}): {e}")
        try:
            print(f"Response Body: {response.text[:200]}")
        except:
            pass
        return False

def process_successful_payment(order_id, transaction_id, bakong_transaction_id=None):
    with Database() as db:
        db.cursor.execute('''
            SELECT o.id, o.user_id, o.product_id, o.amount, o.quantity, p.name, p.subscription_days 
            FROM orders o 
            JOIN products p ON o.product_id = p.id 
            WHERE o.transaction_id = ? OR o.transaction_id LIKE ?
        ''', (transaction_id, f"{transaction_id}_%"))
        orders = db.cursor.fetchall()
        
        if not orders:
            return
            
        user_id = orders[0]['user_id']
        all_product_texts = []
        total_amount = 0
        order_names = []
        
        for order in orders:
            total_amount += order['amount']
            order_names.append(f"{order['name']} (x{order['quantity']})")
            
            db.cursor.execute('''
                SELECT id, email, password, license_key, twofa_secret 
                FROM digital_products 
                WHERE product_id = ? AND is_sold = 0 
                ORDER BY id ASC
                LIMIT ?
            ''', (order['product_id'], order['quantity']))
            products = db.cursor.fetchall()
            
            if len(products) == order['quantity']:
                product_ids = [p['id'] for p in products]
                placeholders = ','.join('?' * len(product_ids))
                
                sub_days = order['subscription_days']
                if sub_days and sub_days > 0:
                    expiry_expr = f"datetime('now', '+7 hours', '+{sub_days} days')"
                else:
                    expiry_expr = "NULL"
                    
                db.cursor.execute(f'''
                    UPDATE digital_products 
                    SET is_sold = 1, sold_to = ?, sold_at = datetime('now', '+7 hours'), order_id = ?,
                        expiry_date = {expiry_expr}, reminder_sent = 0
                    WHERE id IN ({placeholders})
                ''', (user_id, order['id'], *product_ids))
                
                db.cursor.execute('''
                    UPDATE orders 
                    SET payment_status = 'completed', 
                        completed_at = datetime('now', '+7 hours'),
                        bakong_transaction_id = ?
                    WHERE id = ?
                ''', (bakong_transaction_id, order['id']))
                
                db.cursor.execute('''
                    UPDATE products 
                    SET stock = (SELECT COUNT(*) FROM digital_products WHERE product_id = ? AND is_sold = 0)
                    WHERE id = ?
                ''', (order['product_id'], order['product_id']))
                
                for idx, prod in enumerate(products, 1):
                    text = f"**{order['name']} - គណនីទី {idx}:**\n"
                    text += format_product_display(
                        prod['email'],
                        prod['password'],
                        prod['license_key'],
                        prod['twofa_secret']
                    )
                    all_product_texts.append(text)
            else:
                bot.send_message(
                    user_id,
                    f"❌ សូមទោស ផលិតផល {order['name']} អស់ស្តុកហើយ (ស្នើសុំ {order['quantity']} តែមាន {len(products)} ទេ)。\n"
                    "សូមទាក់ទងអ្នកគ្រប់គ្រងសម្រាប់ការសងប្រាក់វិញ។"
                )
                for admin_id in ADMIN_IDS:
                    try:
                        bot.send_message(
                            admin_id,
                            f"⚠️ អស់ស្តុក!\n"
                            f"ផលិតផល ID: {order['product_id']} ត្រូវបានទិញប៉ុន្តែមាន {len(products)}/{order['quantity']}!\n"
                            f"ការបញ្ជាទិញ ID: {order['id']}\n"
                            f"អ្នកប្រើ ID: {user_id}"
                        )
                    except:
                        pass
        
        db.commit()
        
        if not all_product_texts:
            return
            
        accounts_message = "\n━━━━━━━━━━━━━━━━━━━\n".join(all_product_texts)
        names_str = ", ".join(order_names)
        
        success_message = f"""
✅ ការទូទាត់បានជោគជ័យ!
━━━━━━━━━━━━━━━━━━━
សូមអរគុណសម្រាប់ការទិញ: {names_str}
ទឹកប្រាក់សរុប: {format_currency(total_amount)}
លេខកូដប្រតិបត្តិការ: `{transaction_id}`

📦 ផលិតផលឌីជីថលរបស់អ្នក:
━━━━━━━━━━━━━━━━━━━
{accounts_message}
━━━━━━━━━━━━━━━━━━━

⚠️ សូមរក្សាទុកព័ត៌មាននេះដោយសុវត្ថិភាព
💎 គាំទ្រ: @mengsienggg
        """
        
        try:
            bot.send_message(user_id, success_message, parse_mode='Markdown')
        except:
            pass
            
        # Generate and send PDF Invoice
        try:
            from invoice import generate_invoice
            import os
            
            # Get customer name
            db.cursor.execute("SELECT first_name, last_name FROM users WHERE user_id = ?", (user_id,))
            user_info = db.cursor.fetchone()
            customer_name = "Customer"
            if user_info:
                customer_name = user_info['first_name']
                if user_info['last_name']:
                    customer_name += " " + user_info['last_name']
            
            pdf_path = generate_invoice(
                transaction_id=transaction_id,
                customer_name=customer_name,
                customer_id=user_id,
                product_name=names_str,
                quantity=1, # Bundled
                total_amount=total_amount
            )
            
            # Send to user
            with open(pdf_path, 'rb') as pdf_file:
                bot.send_document(user_id, pdf_file)
                
            # Store it in memory temporarily to send to group
            if GROUP_ID:
                try:
                    with open(pdf_path, 'rb') as pdf_file:
                        bot.send_document(GROUP_ID, pdf_file)
                except:
                    pass
            
            # Clean up
            os.remove(pdf_path)
        except Exception as e:
            print(f"⚠️ Error generating/sending invoice: {e}")
        
        for admin_id in ADMIN_IDS:
            try:
                bot.send_message(
                    admin_id,
                    f"💰 ការលក់ថ្មី!\n"
                    f"អ្នកប្រើ: {user_id}\n"
                    f"ផលិតផល: {names_str}\n"
                    f"ទឹកប្រាក់សរុប: {format_currency(total_amount)}\n"
                    f"ប្រតិបត្តិការ: `{transaction_id}`"
                )
            except:
                pass

        try:
            if GROUP_ID:
                group_message = f"""
🛒 **ការបញ្ជាទិញថ្មី!**
━━━━━━━━━━━━━━━━━━━
👤 អ្នកប្រើ: `{user_id}`
🆔 លេខប្រតិបត្តិការ: `{transaction_id}`
💰 តម្លៃសរុប: {format_currency(total_amount)}
📅 កាលបរិច្ឆេទ: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
━━━━━━━━━━━━━━━━━━━
📦 **ព័ត៌មានគណនី:**
{accounts_message}
━━━━━━━━━━━━━━━━━━━
                """
                bot.send_message(GROUP_ID, group_message, parse_mode='Markdown')
        except Exception as e:
            print(f"⚠️ Error sending group notification: {e}")

def monitor_payment_loop(chat_id, message_id, user_id, amount, transaction_id, md5_hash, order_id, product_name, quantity):
    start_time = time.time()
    check_count = 0
    
    while time.time() - start_time < 180:
        check_count += 1
        
        if user_id in active_sessions and active_sessions[user_id] != transaction_id:
            print(f"🛑 Session cancelled for {transaction_id}")
            return
            
        with Database() as db:
            db.cursor.execute("SELECT status FROM payment_verifications WHERE transaction_id = ?", (transaction_id,))
            row = db.cursor.fetchone()
            if row and row['status'] == 'completed':
                print(f"✅ Transaction already completed: {transaction_id}")
                return
        
        print(f"🔍 Check #{check_count} for {transaction_id} (MD5: {md5_hash[:8]}...)")
        
        if check_bakong_api(md5_hash):
            process_successful_payment(order_id, transaction_id, bakong_transaction_id=None)
            
            with Database() as db:
                db.cursor.execute('''
                    UPDATE payment_verifications 
                    SET status = 'completed', last_checked = datetime('now', '+7 hours')
                    WHERE transaction_id = ?
                ''', (transaction_id,))
                db.commit()
            
            try:
                bot.delete_message(chat_id, message_id)
                bot.send_message(
                    chat_id,
                    f"✅ **ការទូទាត់បានជោគជ័យ!**\n"
                    f"🛒 ផលិតផល: {product_name}\n"
                    f"💰 តម្លៃ: {format_currency(amount)} (x{quantity})\n"
                    f"🆔 លេខកូដ: `{transaction_id}`\n\n",
                    parse_mode='Markdown'
                )
            except Exception as e:
                print(f"⚠️ Error updating message: {e}")
            
            for admin_id in ADMIN_IDS:
                try:
                    bot.send_message(
                        admin_id,
                        f"💰 **ការទូទាត់ស្វ័យប្រវត្តិ!**\n"
                        f"អ្នកប្រើ: `{user_id}`\n"
                        f"ផលិតផល: {product_name}\n"
                        f"ទឹកប្រាក់: {format_currency(amount)} (x{quantity})\n"
                        f"ប្រតិបត្តិការ: `{transaction_id}`",
                        parse_mode='Markdown'
                    )
                except:
                    pass
            
            if user_id in active_sessions and active_sessions[user_id] == transaction_id:
                del active_sessions[user_id]
            return
            
        time.sleep(7)
    
    if user_id in active_sessions and active_sessions[user_id] == transaction_id:
        del active_sessions[user_id]
        print(f"⏰ Payment timeout: {transaction_id}")
        
        with Database() as db:
            db.cursor.execute('''
                UPDATE orders 
                SET payment_status = 'expired'
                WHERE transaction_id = ?
            ''', (transaction_id,))
            db.cursor.execute('''
                UPDATE payment_verifications 
                SET status = 'expired', last_checked = datetime('now', '+7 hours')
                WHERE transaction_id = ?
            ''', (transaction_id,))
            db.commit()
        
        try:
            bot.edit_message_caption(
                chat_id=chat_id,
                message_id=message_id,
                caption=f"""
❌ ការទូទាត់បានផុតកំណត់
━━━━━━━━━━━━━━━━━━━
🛒 ផលិតផល: {product_name}
💰 តម្លៃ: {format_currency(amount)} (x{quantity})
⏰ រយៈពេល: 3 នាទី

ការទូទាត់របស់អ្នកបានផុតកំណត់ហើយ។
សូមធ្វើការបញ្ជាទិញថ្មីម្តងទៀត។
━━━━━━━━━━━━━━━━━━━
                """
            )
        except:
            pass

def initiate_payment(message, product_id, user_id, quantity):
    from utils import generate_transaction_id
    with Database() as db:
        db.cursor.execute("SELECT name, price, stock FROM products WHERE id = ?", (product_id,))
        product = db.cursor.fetchone()
        
        if not product:
            bot.send_message(message.chat.id, "❌ រកអីវ៉ាន់នេះអត់ឃើញទេ។")
            return
        
        if product['stock'] < quantity:
            bot.send_message(message.chat.id, f"❌ អធ្យាស្រ័យបង សល់ស្តុកតែ {product['stock']} ទេ។")
            return
        
        total_amount = product['price'] * quantity
        transaction_id = generate_transaction_id()
        img, bill_id, md5_hash = generate_api_khqr(total_amount)
        
        if not img:
            bot.send_message(message.chat.id, "❌ បរាជ័យក្នុងការបង្កើត QR កូដ។ សូមព្យាយាមម្តងទៀត។")
            return
        
        db.cursor.execute('''
            INSERT INTO orders (user_id, product_id, transaction_id, amount, quantity, payment_status)
            VALUES (?, ?, ?, ?, ?, 'pending')
        ''', (user_id, product_id, transaction_id, total_amount, quantity))
        order_id = db.cursor.lastrowid
        
        db.cursor.execute('''
            INSERT INTO payment_verifications (order_id, transaction_id, md5_hash, status)
            VALUES (?, ?, ?, 'pending')
        ''', (order_id, transaction_id, md5_hash))
        db.commit()
        
        caption = f"""
💳 សូមធ្វើការទូទាត់
━━━━━━━━━━━━━━━━━━━
🛒 ផលិតផល: {product['name']}
💰 តម្លៃ: {format_currency(product['price'])} x {quantity} = {format_currency(total_amount)}
⏰ ផុតកំណត់: ៣ នាទី
🆔 លេខកូដ: `{transaction_id}`

📱 ស្កេន QR កូដជាមួយកម្មវិធីធនាគារ
✅ ប្រព័ន្ធនឹងពិនិត្យរៀងរាល់ ៥ វិនាទី
━━━━━━━━━━━━━━━━━━━
        """
        keyboard = InlineKeyboardMarkup()
        keyboard.add(InlineKeyboardButton("❌ បោះបង់", callback_data=f"cancel_order_{transaction_id}"))
        
        sent_message = bot.send_photo(
            message.chat.id,
            img,
            caption=caption,
            reply_markup=keyboard,
            parse_mode='Markdown'
        )
        
        active_sessions[user_id] = transaction_id
        monitor_thread = threading.Thread(
            target=monitor_payment_loop,
            args=(message.chat.id, sent_message.message_id, user_id, total_amount, transaction_id, md5_hash, order_id, product['name'], quantity)
        )
        monitor_thread.daemon = True
        monitor_thread.start()

def cancel_order(message, transaction_id, user_id):
    with Database() as db:
        db.cursor.execute(
            "UPDATE orders SET payment_status = 'cancelled' WHERE transaction_id = ? AND user_id = ?",
            (transaction_id, user_id)
        )
        db.commit()
    if user_id in active_sessions and active_sessions[user_id] == transaction_id:
        del active_sessions[user_id]
        
    try:
        bot.delete_message(message.chat.id, message.message_id)
    except:
        pass
        
    bot.send_message(message.chat.id, "❌ ខេនសល (បោះបង់) ហើយបង។")

def initiate_cart_payment(message, user_id):
    from utils import generate_transaction_id
    with Database() as db:
        db.cursor.execute('''
            SELECT c.product_id, c.quantity, p.name, p.price, p.stock 
            FROM cart c
            JOIN products p ON c.product_id = p.id
            WHERE c.user_id = ?
        ''', (user_id,))
        cart_items = db.cursor.fetchall()
        
        if not cart_items:
            bot.send_message(message.chat.id, "❌ កន្ត្រករបស់អ្នកទទេស្អាត។")
            return
            
        total_amount = 0
        names = []
        for item in cart_items:
            if item['stock'] < item['quantity']:
                bot.send_message(message.chat.id, f"❌ សូមទោស ផលិតផល {item['name']} មានស្តុកត្រឹមតែ {item['stock']} ទេ។")
                return
            total_amount += item['price'] * item['quantity']
            names.append(f"{item['name']} (x{item['quantity']})")
            
        transaction_id = generate_transaction_id()
        img, bill_id, md5_hash = generate_api_khqr(total_amount)
        
        if not img:
            bot.send_message(message.chat.id, "❌ បរាជ័យក្នុងការបង្កើត QR កូដ។ សូមព្យាយាមម្តងទៀត។")
            return
            
        first_order_id = None
        for i, item in enumerate(cart_items):
            db.cursor.execute('''
                INSERT INTO orders (user_id, product_id, transaction_id, amount, quantity, payment_status)
                VALUES (?, ?, ?, ?, ?, 'pending')
            ''', (user_id, item['product_id'], f"{transaction_id}_{i}", item['price'] * item['quantity'], item['quantity']))
            order_id = db.cursor.lastrowid
            if first_order_id is None:
                first_order_id = order_id
                
        db.cursor.execute('''
            INSERT INTO payment_verifications (order_id, transaction_id, md5_hash, status)
            VALUES (?, ?, ?, 'pending')
        ''', (first_order_id, transaction_id, md5_hash))
        
        # Clear cart
        db.cursor.execute("DELETE FROM cart WHERE user_id = ?", (user_id,))
        db.commit()
        
        names_str = ", ".join(names)
        caption = f"""
💳 សូមធ្វើការទូទាត់ (Checkout កន្ត្រក)
━━━━━━━━━━━━━━━━━━━
🛒 ផលិតផល: {names_str}
💰 សរុប: {format_currency(total_amount)}
⏰ ផុតកំណត់: ៣ នាទី
🆔 លេខកូដ: `{transaction_id}`

📱 ស្កេន QR កូដជាមួយកម្មវិធីធនាគារ
✅ ប្រព័ន្ធនឹងពិនិត្យរៀងរាល់ ៥ វិនាទី
━━━━━━━━━━━━━━━━━━━
        """
        keyboard = InlineKeyboardMarkup()
        keyboard.add(InlineKeyboardButton("❌ បោះបង់", callback_data=f"cancel_order_{transaction_id}"))
        
        sent_message = bot.send_photo(
            message.chat.id,
            img,
            caption=caption,
            reply_markup=keyboard,
            parse_mode='Markdown'
        )
        
        active_sessions[user_id] = transaction_id
        monitor_thread = threading.Thread(
            target=monitor_payment_loop,
            args=(message.chat.id, sent_message.message_id, user_id, total_amount, transaction_id, md5_hash, first_order_id, "កន្ត្រកទំនិញ", 1)
        )
        monitor_thread.daemon = True
        monitor_thread.start()
