from telegram import Update
from telegram.ext import ContextTypes
from ..config import NEWS_CHAT_ID
from ..services.news_bridge import forward_to_discord

async def news_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.channel_post:
        return
    chat = update.effective_chat
    if not chat or chat.id != NEWS_CHAT_ID:
        return
    text = update.channel_post.text or update.channel_post.caption
    if text:
        forward_to_discord(text)
