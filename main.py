import time
import sys

# Ensure stdout supports UTF-8 for Windows console
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

from database import init_db
from bot_instance import bot
from config import BOT_NAME_KHMER, BOT_NAME_ENGLISH, ADMIN_IDS, GROUP_ID, KHQR_ACCOUNT_ID, MERCHANT_NAME, MERCHANT_CITY
from handlers.user import register_user_handlers
from handlers.admin import register_admin_handlers
from handlers.callbacks import register_callback_handlers
import threading
from database import Database

def auto_delete_loop():
    while True:
        try:
            with Database() as db:
                # Find expired products
                db.cursor.execute('''
                    SELECT id FROM products 
                    WHERE auto_delete_days > 0 
                    AND (julianday(datetime('now', '+7 hours')) - julianday(created_at)) >= auto_delete_days
                ''')
                expired = db.cursor.fetchall()
                
                for p in expired:
                    pid = p['id']
                    db.cursor.execute("DELETE FROM digital_products WHERE product_id = ?", (pid,))
                    db.cursor.execute("DELETE FROM products WHERE id = ?", (pid,))
                    db.commit()
                    print(f"🗑️ ស្វ័យប្រវត្តិ: បានលុបផលិតផល #{pid} ដោយសារដល់ថ្ងៃកំណត់។")
        except Exception as e:
            print(f"Auto delete error: {e}")
        
        # Check every 6 hours
        time.sleep(21600)

def reminder_loop():
    while True:
        try:
            with Database() as db:
                # Find digital products expiring in <= 3 days that haven't been reminded
                db.cursor.execute('''
                    SELECT d.id, d.sold_to, d.expiry_date, p.name, d.email
                    FROM digital_products d
                    JOIN products p ON d.product_id = p.id
                    WHERE d.is_sold = 1 
                      AND d.expiry_date IS NOT NULL 
                      AND d.reminder_sent = 0
                      AND (julianday(d.expiry_date) - julianday(datetime('now', '+7 hours'))) <= 3.0
                      AND (julianday(d.expiry_date) - julianday(datetime('now', '+7 hours'))) > 0
                ''')
                expiring = db.cursor.fetchall()
                
                for item in expiring:
                    try:
                        days_left = (datetime.strptime(item['expiry_date'], '%Y-%m-%d %H:%M:%S') - datetime.now()).days
                        msg = f"""
⏰ **សេចក្តីជូនដំណឹង:** គណនីរបស់អ្នកជិតផុតកំណត់ហើយ!
━━━━━━━━━━━━━━━━━━━
📦 ផលិតផល: {item['name']}
📧 គណនី: {item['email']}
⏳ ផុតកំណត់នៅ: {item['expiry_date']}

សូមធ្វើការទិញជាថ្មី (Renew) ប្រសិនបើអ្នកចង់បន្តប្រើប្រាស់។
━━━━━━━━━━━━━━━━━━━
"""
                        bot.send_message(item['sold_to'], msg, parse_mode='Markdown')
                        
                        # Mark as reminded
                        db.cursor.execute("UPDATE digital_products SET reminder_sent = 1 WHERE id = ?", (item['id'],))
                        db.commit()
                        print(f"⏰ បានផ្ញើសាររំលឹកទៅកាន់ {item['sold_to']} សម្រាប់គណនី {item['email']}")
                    except Exception as e:
                        print(f"Error sending reminder to {item['sold_to']}: {e}")
        except Exception as e:
            print(f"Reminder loop error: {e}")
            
        # Check every 6 hours
        time.sleep(21600)

def main():
    # Initialize the database
    init_db()
    
    # Set bot commands menu
    from telebot.types import BotCommand
    bot.set_my_commands([
        BotCommand("start", "ម៉ឺនុយមេ (Main Menu)"),
        BotCommand("language", "ប្តូរភាសា (Change Language)"),
        BotCommand("feedback", "ផ្តល់មតិយោបល់ (Provide Feedback)"),
        BotCommand("request", "ស្នើសុំសេវាកម្មថ្មី (Request New Service)")
    ])
    
    # Setup anti-spam middleware
    from bot_instance import AntiSpamMiddleware
    bot.setup_middleware(AntiSpamMiddleware())
    
    # Start auto delete thread
    delete_thread = threading.Thread(target=auto_delete_loop, daemon=True)
    delete_thread.start()
    
    # Start reminder thread
    reminder_thread = threading.Thread(target=reminder_loop, daemon=True)
    reminder_thread.start()
    
    # Register all handlers
    register_user_handlers()
    register_admin_handlers()
    register_callback_handlers()
    
    print(f"🤖 {BOT_NAME_KHMER} ({BOT_NAME_ENGLISH}) កំពុងដំណើរការ...")
    print(f"👑 អ្នកគ្រប់គ្រង IDs: {ADMIN_IDS}")
    print(f"👥 Mart Group ID: {GROUP_ID}")
    print(f"💳 Bakong Merchant: {MERCHANT_NAME} ({KHQR_ACCOUNT_ID})")
    print(f"🏙️ Merchant City: {MERCHANT_CITY}")
    print("⏰ ប្រព័ន្ធពិនិត្យការទូទាត់៖ ដំណើរការរៀងរាល់ ៥ វិនាទី (ក្នុងមួយប្រតិបត្តិការ)")
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    
    try:
        # Start the bot
        bot.infinity_polling(timeout=60, long_polling_timeout=60)
    except Exception as e:
        print(f"កំហុស Bot: {e}")
        time.sleep(5)
        main()

if __name__ == "__main__":
    main()
