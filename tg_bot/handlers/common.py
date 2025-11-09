
from telegram import Update
from telegram.ext import ContextTypes
from ..keyboards import main_menu_kb

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text('👋 Привет! Нажми кнопку, чтобы создать тикет, или просто напиши сообщение.',
                                    reply_markup=main_menu_kb())

async def ping(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text('pong')
