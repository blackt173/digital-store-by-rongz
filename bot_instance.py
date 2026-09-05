import telebot
from config import BOT_TOKEN

# Initialize the bot instance
bot = telebot.TeleBot(BOT_TOKEN, use_class_middlewares=True)

# Shared active sessions dictionary (used for payment monitoring)
active_sessions = {}

# Shared dictionary for tracking input failures
user_failures = {}

# Shared dictionary for tracking last bot message per user to auto-delete
last_bot_messages = {}

import time
import datetime
from telebot.handler_backends import BaseMiddleware, CancelUpdate

class AntiSpamMiddleware(BaseMiddleware):
    def __init__(self):
        super().__init__()
        self.update_types = ['message', 'callback_query']
        self.user_last_msgs = {}
        self.user_bans = {} # user_id -> ban_expire_timestamp
        self.user_penalties = {} # user_id -> {'date': 'YYYY-MM-DD', 'duration': 0}

    def pre_process(self, message, data):
        user_id = message.from_user.id
        now = time.time()
        # Track when we last warned a user about their ban
        if not hasattr(self, 'user_last_warnings'):
            self.user_last_warnings = {}
            
        today = datetime.date.today().isoformat()
        
        # Check if currently banned
        if user_id in self.user_bans:
            if now < self.user_bans[user_id]:
                # Calculate remaining time
                remaining_seconds = int(self.user_bans[user_id] - now)
                m, s = divmod(remaining_seconds, 60)
                
                # Only send warning if we haven't warned them in the last 5 seconds to prevent bot from spamming
                last_warning = self.user_last_warnings.get(user_id, 0)
                if now - last_warning > 5:
                    try:
                        if hasattr(message, 'chat'):
                            bot.send_message(message.chat.id, f"⛔ គណនីរបស់អ្នកត្រូវបានផ្អាកជាបណ្ដោះអាសន្នដោយសារការផ្ញើសារញឹកញាប់ (Spam)។\n⏱️ អ្នកនៅសល់ពេល {m} នាទី និង {s} វិនាទីទៀត ដើម្បីអាចប្រើប្រាស់ឡើងវិញបាន។")
                            self.user_last_warnings[user_id] = now
                    except:
                        pass
                return CancelUpdate()
            else:
                # Ban expired
                del self.user_bans[user_id]
                try:
                    if hasattr(message, 'chat'):
                        bot.send_message(message.chat.id, "✅ រយៈពេលរាំងខ្ទប់របស់អ្នកត្រូវបានបញ្ចប់។ អ្នកអាចប្រើប្រាស់ Bot បានវិញហើយ។")
                except:
                    pass
        
        # Track messages
        msgs = self.user_last_msgs.get(user_id, [])
        msgs = [ts for ts in msgs if now - ts < 3]
        msgs.append(now)
        self.user_last_msgs[user_id] = msgs
        
        # 5 messages in 3 seconds triggers spam
        if len(msgs) > 5:
            penalty_info = self.user_penalties.get(user_id, {'date': today, 'duration': 0})
            
            # Reset penalty if it's a new day
            if penalty_info['date'] != today:
                penalty_info = {'date': today, 'duration': 0}
                
            # Increase duration by 5 minutes (300 seconds)
            if penalty_info['duration'] == 0:
                new_duration = 300
            else:
                new_duration = penalty_info['duration'] + 300
                
            # Max ban duration per day is 2 hours (7200 seconds)
            if new_duration > 7200:
                new_duration = 7200
                
            penalty_info['duration'] = new_duration
            self.user_penalties[user_id] = penalty_info
            
            self.user_bans[user_id] = now + new_duration
            self.user_last_msgs[user_id] = []
            
            minutes = new_duration // 60
            try:
                if hasattr(message, 'chat'):
                    bot.send_message(message.chat.id, f"⛔ អ្នកបានផ្ញើសារញឹកញាប់ពេក (Spam)។ អ្នកត្រូវបានរាំងខ្ទប់ចំនួន {minutes} នាទី។")
            except:
                pass
            return CancelUpdate()

    def post_process(self, message, data, exception):
        pass
