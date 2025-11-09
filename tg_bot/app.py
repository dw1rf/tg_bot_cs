import logging
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters
from .config import TG_BOT_TOKEN, ADMIN_CHAT_ID
from .handlers.common import start, ping
from .handlers.tickets import (
    buttons,
    handle_other_reason, forward_user_message, forward_from_topic,
    dbping_cmd, dbdiag_cmd, close_command
)

# новостной мост по желанию
try:
    from .handlers.news import news_handler
    HAS_NEWS = True
except Exception:
    HAS_NEWS = False

logging.basicConfig(level=logging.INFO)

def build_app():
    app = Application.builder().token(TG_BOT_TOKEN).build()

    # важно: чтобы handlers/tickets видели id админ-чата
    app.bot_data["ADMIN_CHAT_ID"] = ADMIN_CHAT_ID

    # кнопки меню/тикетов
    app.add_handler(CallbackQueryHandler(buttons), group=0)

    # текст без /команд → «Другое»/тикеты
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_other_reason), group=1)

    # ответы админов из форум-топика → пользователю
    app.add_handler(
        MessageHandler(
            filters.Chat(ADMIN_CHAT_ID) & (
                filters.TEXT | filters.PHOTO | filters.ANIMATION | filters.Sticker.ALL
            ) & ~filters.COMMAND,
            forward_from_topic
        ),
        group=2
    )

    # ЛС пользователя → в тикет
    app.add_handler(
        MessageHandler(
            filters.ChatType.PRIVATE & (
                filters.TEXT | filters.PHOTO | filters.ANIMATION | filters.Sticker.ALL
            ) & ~filters.COMMAND,
            forward_user_message
        ),
        group=3
    )

    # новости из канала (если модуль есть)
    if HAS_NEWS:
        app.add_handler(MessageHandler(filters.ChatType.CHANNEL, news_handler), group=4)

    # команды
    app.add_handler(CommandHandler("start", start), group=10)
    app.add_handler(CommandHandler("ping",  ping),  group=10)
    app.add_handler(CommandHandler("dbping", dbping_cmd), group=10)
    app.add_handler(CommandHandler("dbdiag", dbdiag_cmd), group=10)
    app.add_handler(CommandHandler("close",  close_command), group=10)

    return app

if __name__ == "__main__":
    app = build_app()
    print("Бот запущен, ожидает команды…")
    app.run_polling()
