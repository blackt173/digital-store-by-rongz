import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# ============ CONFIGURATION ============
BOT_TOKEN = os.getenv("BOT_TOKEN")

# Admin IDs (parse from string to list of ints, comma-separated if needed)
admin_ids_str = os.getenv("ADMIN_IDS", "")
ADMIN_IDS = [int(id_str.strip()) for id_str in admin_ids_str.split(",") if id_str.strip()]

# Group ID
GROUP_ID = int(os.getenv("GROUP_ID", "0"))

# Bakong KHQR Configuration
KHQR_ACCOUNT_ID = os.getenv("KHQR_ACCOUNT_ID")
MERCHANT_NAME = os.getenv("MERCHANT_NAME")
MERCHANT_CITY = os.getenv("MERCHANT_CITY")
BAKONG_TOKEN = os.getenv("BAKONG_TOKEN")
BAKONG_CHECK_URL = os.getenv("BAKONG_CHECK_URL")

BOT_NAME_KHMER = os.getenv("BOT_NAME_KHMER")
BOT_NAME_ENGLISH = os.getenv("BOT_NAME_ENGLISH")
