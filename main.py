# main.py
from telegram import (
    Update, 
    InlineKeyboardButton, 
    InlineKeyboardMarkup, 
    KeyboardButton, 
    ReplyKeyboardMarkup
)
from telegram.ext import (
    Application, 
    CommandHandler, 
    MessageHandler, 
    filters, 
    ContextTypes, 
    CallbackQueryHandler
)

from config import TOKEN, ADMIN_ID, ACCESS_USERS, REQUESTS
from print_request import PrintRequest
from storage import save_requests, load_requests


# ====== Startup ======
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if context._user_id in ACCESS_USERS:
        await update.message.reply_text("Если ты видишь это сообщение, значит ты админ, и тебе доступен просмотр запросов на печать!")

    await update.message.reply_text(
        "👋 Добро пожаловать в бота принтера! \n\n Нажмите на кнопку Меню, чтобы продолжить",
        reply_markup=persistent_keyboard()
    )


# ====== Button Handler ======
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query

    match query.data:
        case "send_file":
            context.user_data["awaiting_file"] = True
            await query.message.reply_text(
                "📄 Пожалуйста, отправьте ваш файл.\n\nУкажите желаемый тип печати и комментарии вместе с файлом."
            )
        case "instructions":
            await query.message.reply_text(
                "📝 При отправке запроса на печать, пожалуйста отправляйте всё в виде файла."
            )
        case "pricing":
            await query.message.reply_text("💰 15р/лист, двусторонняя печать 20р/лист")
        case "contact":
            await query.message.reply_text(f"📞 Связаться с разработчиком: {ADMIN_ID}")
        case "requests":
            await query.message.reply_text(
                f"Всего запросов: {len(REQUESTS)}",
                reply_markup=get_requests()
            )

    # Admin request view
    if query.data.startswith("raise_request:"):
        req_id = query.data.split(":")[1]

        decisions = InlineKeyboardMarkup([
            [
                InlineKeyboardButton("✅Принять", callback_data=f"approve:{req_id}"),
                InlineKeyboardButton("❌Отклонить", callback_data=f"reject:{req_id}")
            ]
        ])

        request = next((r for r in REQUESTS if r.id == req_id), None)

        if request:
            await query.message.reply_document(
                document=request.file_id,
                caption=f"""📄 Запрос от @{request.username}
\nПодпись: {request.caption or "—"}""",
                reply_markup=decisions
            )
        else:
            await query.message.reply_text("❌ Запрос не найден.")

    # Approve / Reject actions
    actions = ["approve", "reject"]
    if any(query.data.startswith(f"{a}:") for a in actions):
        action, req_id = query.data.split(":")
        request = next((r for r in REQUESTS if r.id == req_id), None)

        if not request:
            await query.message.reply_text("❌ Запрос не найден.")
            return

        context.user_data["awaiting_comment"] = {
            "action": action,
            "req_id": req_id
        }

        await query.message.reply_text(
            f"💬 Пожалуйста оставьте комментарий к {action.upper()} для запроса от @{request.username}:"
        )


# ====== Text Handler ======
async def text_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if context.user_data.get("awaiting_comment"):
        await handle_admin_comment(update, context)
        return
    await reply_keyboard_handler(update, context)


async def reply_keyboard_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.text == "Меню":
        keyboard = [
            [InlineKeyboardButton("📄 Отправить запрос на распечатку", callback_data="send_file")],
            [InlineKeyboardButton("📝 Инструкция по применению", callback_data="instructions")],
            [InlineKeyboardButton("💰 Расценки", callback_data="pricing")],
            [InlineKeyboardButton("📞 Поддержка", callback_data="contact")],
        ]
        if context._user_id in ACCESS_USERS:
            keyboard.append([InlineKeyboardButton("Запросы на печать", callback_data="requests")])

        kb_buttons = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text("Выберите опцию из меню", reply_markup=kb_buttons)


# ====== File Handler ======
async def handle_file(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if context.user_data.get("awaiting_file"):
        file = await update.message.document.get_file()

        # Send to admins
        for trusted_user in ACCESS_USERS:
            await context.bot.send_document(
                chat_id=trusted_user,
                document=file.file_id,
                caption=f"""Новый запрос на печать от пользователя @{update.message.from_user.username}
\n\nПодпись: {update.message.caption or "—"}"""
            )

        request = PrintRequest(
            update.message.from_user.username,
            context._user_id,
            file.file_id,
            update.message.caption
        )
        REQUESTS.append(request)
        save_requests(REQUESTS)

        await update.message.reply_text(f"✅ Запрос получен: {update.message.document.file_name}")
        context.user_data["awaiting_file"] = False


# ====== Comment Handler ======
async def handle_admin_comment(update: Update, context: ContextTypes.DEFAULT_TYPE):
    state = context.user_data.get("awaiting_comment")
    if not state:
        return

    req_id = state["req_id"]
    action = state["action"]
    comment = update.message.text

    request = next((r for r in REQUESTS if r.id == req_id), None)
    if not request:
        await update.message.reply_text("❌ Запрос не найден")
        context.user_data.pop("awaiting_comment", None)
        return

    # Update status
    request.status = "approved" if action == "approve" else "denied"

    # Send result back to customer
    result_text = (
        f"✅ Ваш запрос принят!\n\n💬 Комментарий: {comment}"
        if action == "approve"
        else f"❌ Ваш запрос отклонён.\n\n💬 Комментарий: {comment}"
    )

    await context.bot.send_document(
        chat_id=request.user_id,
        document=request.file_id,
        caption=result_text,
    )

    # Confirm to admin
    await update.message.reply_text(f"📤 {action.upper()} отправлено @{request.username}.")

    # Clear state & persist
    context.user_data.pop("awaiting_comment", None)
    REQUESTS.remove(request)
    save_requests(REQUESTS)


# ====== Helpers ======
def persistent_keyboard():
    return ReplyKeyboardMarkup([[KeyboardButton("Меню")]], resize_keyboard=True)

def get_requests():
    requests_keyboard = [
        [InlineKeyboardButton(r.username, callback_data=f"raise_request:{r.id}")]
        for r in REQUESTS
    ]
    return InlineKeyboardMarkup(requests_keyboard)


# ====== Main ======
def main():
    # Load persisted requests at startup
    REQUESTS[:] = load_requests()

    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(MessageHandler(filters.Document.ALL, handle_file))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, text_handler))
    app.run_polling()

if __name__ == "__main__":
    main()
