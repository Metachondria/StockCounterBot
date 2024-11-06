import json
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, ContextTypes

# подгрузка токена и json с валидными id
def load_token():
    with open('token.txt', 'r') as file:
        token = file.read().strip()
    return token

TOKEN = load_token()

def load_admins():
    with open('admins.json', 'r') as file:
        data = json.load(file)
    return data["admins"]

VALID_ADMIN_IDS = load_admins()

# Стартовое сообщение с кнопками admin_panel и персонал
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Встроенная клавиатура с кнопками
    inline_keyboard = [
        [InlineKeyboardButton("Admin Panel", callback_data='admin_panel')],
        [InlineKeyboardButton("Персонал", callback_data='personnel')]
    ]
    reply_markup_inline = InlineKeyboardMarkup(inline_keyboard)

    # Отправка сообщения с клавиатурой inline
    await update.message.reply_text(
        "Добрый день, авторизируйтесь в системе:",
        reply_markup=reply_markup_inline
    )

# Обработчик нажатий кнопок
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id

    # Проверка нажатой кнопки
    if query.data == 'admin_panel':
        if user_id in VALID_ADMIN_IDS:
            await query.edit_message_text("Добро пожаловать в админ панель!")
        else:
            await query.edit_message_text("Доступ разрешен только для администраторов!")
    elif query.data == 'personnel':
        await query.edit_message_text("Раздел 'Персонал'. Здесь информация о сотрудниках.")

if __name__ == '__main__':
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.run_polling()
