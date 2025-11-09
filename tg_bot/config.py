import os
from dotenv import load_dotenv

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ENV_PATH = os.path.join(BASE_DIR, ".env")
load_dotenv(ENV_PATH, override=True)

TG_BOT_TOKEN   = os.getenv("TG_BOT_TOKEN")
ADMIN_CHAT_ID  = int(os.getenv("ADMIN_CHAT_ID"))
NEWS_CHAT_ID   = int(os.getenv("NEWS_CHAT_ID"))
DISCORD_WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL")

DB_HOST = os.getenv("DB_HOST")
DB_PORT = int(os.getenv("DB_PORT", "3306"))
DB_NAME = os.getenv("DB_NAME")
DB_USER = os.getenv("DB_USER")
DB_PASS = os.getenv("DB_PASS")
DB_SSL_MODE = os.getenv("DB_SSL_MODE", "DISABLED").upper()

CH_TABLE = os.getenv("CH_TABLE", "tg_challenges")
ONLINE_TABLE_PRIMARY = os.getenv("ONLINE_TABLE", "tg_online")
ONLINE_TABLE_FALLBACK = "online_players"
