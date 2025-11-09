# tg_bot/handlers/tickets.py
import uuid
import logging
from typing import Dict
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

# ===== Память процесса =====
tickets: Dict[str, dict] = {}          # ticket_id -> {user_id, username, type}
user_last_ticket: Dict[int, str] = {}  # user_id -> ticket_id
thread_to_ticket: Dict[int, str] = {}  # thread_id -> ticket_id
ticket_to_thread: Dict[str, int] = {}  # ticket_id -> thread_id
pending_reason: Dict[int, bool] = {}   # user_id -> ждём текст причины ("Другое")

def get_open_ticket_id(uid: int) -> str | None:
    tid = user_last_ticket.get(uid)
    if tid and tid in tickets:
        return tid
    user_last_ticket.pop(uid, None)
    return None

# ===== Клавиатуры =====
def main_menu_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([[InlineKeyboardButton("📝 Создать тикет", callback_data="menu_ticket")]])

def ticket_menu_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("⚙ Техническая", callback_data="ticket_tech"),
         InlineKeyboardButton("💰 Платёж",     callback_data="ticket_payment")],
        [InlineKeyboardButton("❓ Другое",     callback_data="ticket_other")],
        [InlineKeyboardButton("🔙 Назад",      callback_data="back_main")],
    ])

# ===== Кнопки =====
async def buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    if not q:
        return
    await q.answer()

    if q.data == "back_main":
        await q.edit_message_text("👋 Добро пожаловать! Выберите раздел:", reply_markup=main_menu_kb())
        return

    if q.data == "menu_ticket":
        tid = get_open_ticket_id(q.from_user.id)
        if tid:
            await q.edit_message_text(
                f"📨 У вас уже есть открытый тикет <code>{tid}</code>.\n"
                f"Напишите сообщение — оно уйдёт в поддержку.",
                parse_mode="HTML",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("❌ Закрыть тикет", callback_data="ticket_close")],
                    [InlineKeyboardButton("🔙 Назад", callback_data="back_main")],
                ]),
            )
            return
        await q.edit_message_text("📩 Создание тикета:", reply_markup=ticket_menu_kb())
        return

    if q.data == "ticket_close":
        uid = q.from_user.id
        tid = get_open_ticket_id(uid)
        if not tid:
            await q.edit_message_text("ℹ️ Открытых тикетов нет.", reply_markup=main_menu_kb())
            return
        thread_id = ticket_to_thread.pop(tid, None)
        tickets.pop(tid, None)
        user_last_ticket.pop(uid, None)
        if thread_id:
            thread_to_ticket.pop(thread_id, None)
            try:
                await context.bot.send_message(
                    chat_id=context.bot_data["ADMIN_CHAT_ID"],
                    message_thread_id=thread_id,
                    text=f"🚪 Пользователь закрыл тикет <code>{tid}</code>.",
                    parse_mode="HTML",
                )
            except Exception:
                pass
        await q.edit_message_text("✅ Тикет закрыт.", reply_markup=main_menu_kb())
        return

    if q.data == "ticket_other":
        pending_reason[q.from_user.id] = True
        await q.edit_message_text(
            "❓ Опишите причину одним сообщением:",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Назад", callback_data="menu_ticket")]]),
        )
        return

    if q.data in ("ticket_tech", "ticket_payment"):
        kind = "Техническая" if q.data.endswith("tech") else "Платёж"
        if get_open_ticket_id(q.from_user.id):
            await q.edit_message_text(
                "⚠️ У вас уже есть открытый тикет. Сначала закройте его.",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Назад", callback_data="back_main")]]),
            )
            return

        # создаём тикет и форум-топик
        uid = q.from_user.id
        tid = str(uuid.uuid4())[:8]
        tickets[tid] = {"user_id": uid, "username": q.from_user.full_name, "type": kind}
        user_last_ticket[uid] = tid

        await q.edit_message_text(
            f"✅ Тикет создан!\n🆔 <code>{tid}</code>\n📂 <b>{kind}</b>\n"
            f"Напишите сообщение — оно уйдёт в поддержку.",
            parse_mode="HTML",
            reply_markup=main_menu_kb(),
        )

        try:
            topic = await context.bot.create_forum_topic(
                chat_id=context.bot_data["ADMIN_CHAT_ID"], name=f"Тикет {tid}"
            )
            thread_id = topic.message_thread_id
            thread_to_ticket[thread_id] = tid
            ticket_to_thread[tid] = thread_id

            await context.bot.send_message(
                chat_id=context.bot_data["ADMIN_CHAT_ID"],
                message_thread_id=thread_id,
                text=(f"<b>📩 Новый тикет</b>\n"
                      f"🆔 <code>{tid}</code>\n"
                      f"👤 <a href='tg://user?id={uid}'>{q.from_user.full_name}</a>\n"
                      f"📂 <b>{kind}</b>"),
                parse_mode="HTML",
            )
        except Exception as e:
            logging.warning(f"[tickets] create_forum_topic failed: {e}")
        return

# ===== Пользователь → поддержка =====
async def handle_other_reason(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Любой текст без /команд — если ожидаем «Другое», создаём тикет и падаем в forward_user_message
    if update.effective_chat.type != "private" or not update.message:
        return
    uid = update.effective_user.id
    if pending_reason.pop(uid, None):
        reason = (update.message.text or "").strip() or "Другое"
        tid = str(uuid.uuid4())[:8]
        tickets[tid] = {"user_id": uid, "username": update.effective_user.full_name, "type": reason}
        user_last_ticket[uid] = tid
        await update.message.reply_text(
            f"✅ Тикет создан!\n🆔 <code>{tid}</code>\n📂 <b>{reason}</b>",
            parse_mode="HTML",
            reply_markup=main_menu_kb(),
        )
        # создадим топик
        try:
            topic = await context.bot.create_forum_topic(
                chat_id=context.bot_data["ADMIN_CHAT_ID"], name=f"Тикет {tid}"
            )
            thread_id = topic.message_thread_id
            thread_to_ticket[thread_id] = tid
            ticket_to_thread[tid] = thread_id
        except Exception as e:
            logging.warning(f"[tickets] create_forum_topic failed: {e}")
    # передать дальше в общий форвард
    await forward_user_message(update, context)

async def forward_user_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type != "private" or not update.message:
        return
    uid = update.effective_user.id
    tid = get_open_ticket_id(uid)
    if not tid:
        # предложим создать тикет
        await update.message.reply_text("Выберите действие:", reply_markup=main_menu_kb())
        return

    thread_id = ticket_to_thread.get(tid)
    if not thread_id:
        # восстановим топик
        try:
            topic = await context.bot.create_forum_topic(
                chat_id=context.bot_data["ADMIN_CHAT_ID"], name=f"Тикет {tid}"
            )
            thread_id = topic.message_thread_id
            thread_to_ticket[thread_id] = tid
            ticket_to_thread[tid] = thread_id
        except Exception as e:
            logging.warning(f"[tickets] restore topic failed: {e}")

    # копируем в топик
    if update.message.text:
        await context.bot.send_message(
            chat_id=context.bot_data["ADMIN_CHAT_ID"],
            message_thread_id=thread_id,
            text=(f"📨 <b>Сообщение по тикету</b>\n"
                  f"🆔 <code>{tid}</code>\n"
                  f"👤 <a href='tg://user?id={uid}'>{update.effective_user.full_name}</a>\n\n"
                  f"{update.message.text}"),
            parse_mode="HTML",
        )
    elif update.message.photo:
        await context.bot.send_photo(
            chat_id=context.bot_data["ADMIN_CHAT_ID"], message_thread_id=thread_id,
            photo=update.message.photo[-1].file_id,
            caption=f"📸 Фото по тикету {tid} — {update.effective_user.full_name}\n{update.message.caption or ''}",
            parse_mode="HTML",
        )
    elif update.message.animation:
        await context.bot.send_animation(
            chat_id=context.bot_data["ADMIN_CHAT_ID"], message_thread_id=thread_id,
            animation=update.message.animation.file_id,
            caption=f"🎞 GIF по тикету {tid} — {update.effective_user.full_name}\n{update.message.caption or ''}",
            parse_mode="HTML",
        )
    elif update.message.sticker:
        await context.bot.send_sticker(
            chat_id=context.bot_data["ADMIN_CHAT_ID"], message_thread_id=thread_id,
            sticker=update.message.sticker.file_id,
        )
    await update.message.reply_text("✅ Сообщение отправлено в поддержку.", reply_markup=main_menu_kb())

# ===== Поддержка → пользователю =====
async def forward_from_topic(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or update.effective_chat.id != context.bot_data["ADMIN_CHAT_ID"]:
        return
    thread_id = update.message.message_thread_id
    tid = thread_to_ticket.get(thread_id)
    info = tickets.get(tid)
    if not info:
        return
    user_id = info["user_id"]

    if update.message.text:
        await context.bot.send_message(
            chat_id=user_id,
            text=f"📬 Ответ по тикету <code>{tid}</code>:\n\n{update.message.text}",
            parse_mode="HTML",
        )
    elif update.message.photo:
        await context.bot.send_photo(
            chat_id=user_id,
            photo=update.message.photo[-1].file_id,
            caption=f"📸 Ответ по тикету {tid}\n{update.message.caption or ''}",
            parse_mode="HTML",
        )
    elif update.message.animation:
        await context.bot.send_animation(
            chat_id=user_id,
            animation=update.message.animation.file_id,
            caption=f"🎞 Ответ по тикету {tid}\n{update.message.caption or ''}",
            parse_mode="HTML",
        )
    elif update.message.sticker:
        await context.bot.send_sticker(chat_id=user_id, sticker=update.message.sticker.file_id)

# ===== Диагностика и закрытие =====
async def dbping_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("DB ping: локальный режим (без БД).")

async def dbdiag_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lines = [
        f"tickets: {len(tickets)}",
        f"users with open tickets: {len(user_last_ticket)}",
        f"threads: {len(thread_to_ticket)}",
    ]
    await update.message.reply_text("🔎 DIAG\n" + "\n".join(lines))

async def close_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    args = context.args
    if not args:
        await update.message.reply_text("Использование: /close <ticket_id> [причина]")
        return
    ticket_id = args[0]
    reason = " ".join(args[1:]) if len(args) > 1 else None
    info = tickets.pop(ticket_id, None)
    if not info:
        await update.message.reply_text(f"❗ Тикет {ticket_id} не найден.")
        return

    user_last_ticket.pop(info["user_id"], None)
    thread_id = ticket_to_thread.pop(ticket_id, None)
    if thread_id:
        thread_to_ticket.pop(thread_id, None)
        try:
            await context.bot.send_message(
                chat_id=context.bot_data["ADMIN_CHAT_ID"],
                message_thread_id=thread_id,
                text=f"✅ Тикет <code>{ticket_id}</code> закрыт.",
                parse_mode="HTML",
            )
        except Exception:
            pass

    await update.message.reply_text(f"✅ Тикет <code>{ticket_id}</code> закрыт.", parse_mode="HTML")
    try:
        txt = f"📪 Ваш тикет <code>{ticket_id}</code> закрыт."
        if reason:
            txt += f"\nПричина: {reason}"
        await context.bot.send_message(chat_id=info["user_id"], text=txt, parse_mode="HTML")
    except Exception:
        pass
