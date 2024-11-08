
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    CallbackQueryHandler,
    ConversationHandler,
    MessageHandler,
    filters,
    ContextTypes
)
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from config import USERS, save_users

logger = logging.getLogger(__name__)

CHANGE_NAME, ADD_EMPLOYEE, DELETE_EMPLOYEE = range(3)

def get_user(user_id):
    user = next((user for user in USERS if user["id"] == user_id), None)
    logger.debug(f"Получен пользователь: {user}")
    return user

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.info("Команда /start вызвана")
    if update.message:
        user_id = update.message.from_user.id
    elif update.callback_query:
        user_id = update.callback_query.from_user.id
    else:
        logger.warning("Неизвестный тип обновления в start")
        return

    user = get_user(user_id)
    if not user:
        if update.message:
            await update.message.reply_text("Доступ запрещен.")
        elif update.callback_query:
            await update.callback_query.edit_message_text("Доступ запрещен.")
        logger.warning(f"Пользователь с ID {user_id} не найден")
        return

    role_name = "Администратор" if user["role"] == "admin" else "Сотрудник"
    inline_keyboard = [
        [InlineKeyboardButton("Admin Panel", callback_data='admin_panel')],
        [InlineKeyboardButton("Персонал", callback_data='personnel')],
        [InlineKeyboardButton("Изменить имя", callback_data='change_name')]
    ]
    reply_markup_inline = InlineKeyboardMarkup(inline_keyboard)

    if update.message:
        await update.message.reply_text(
            f"Добрый день, {user['name']}! Вы авторизованы как {role_name}.",
            reply_markup=reply_markup_inline
        )
    elif update.callback_query:
        await update.callback_query.edit_message_text(
            f"Добрый день, {user['name']}! Вы авторизованы как {role_name}.",
            reply_markup=reply_markup_inline
        )

async def admin_panel_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.info("Переход в Admin Panel")
    inline_keyboard = [
        [InlineKeyboardButton("Начать смену", callback_data='start_shift')],
        [InlineKeyboardButton("Закончить смену", callback_data='end_shift')],
        [InlineKeyboardButton("Добавить сотрудника", callback_data='add_employee')],
        [InlineKeyboardButton("Удалить сотрудника", callback_data='delete_employee')],
        [InlineKeyboardButton("Вернуться в главное меню", callback_data='main_menu')]
    ]
    reply_markup_inline = InlineKeyboardMarkup(inline_keyboard)

    await update.callback_query.edit_message_text(
        "Админ панель:",
        reply_markup=reply_markup_inline
    )

async def personnel_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.info("Переход в Personnel Menu")
    inline_keyboard = [
        [InlineKeyboardButton("Начать смену", callback_data='start_shift')],
        [InlineKeyboardButton("Закончить смену", callback_data='end_shift')],
        [InlineKeyboardButton("Вернуться в главное меню", callback_data='main_menu')]
    ]
    reply_markup_inline = InlineKeyboardMarkup(inline_keyboard)

    await update.callback_query.edit_message_text(
        "Меню персонала:",
        reply_markup=reply_markup_inline
    )

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    user = get_user(user_id)

    if not user:
        await query.edit_message_text("Доступ запрещен.")
        logger.warning(f"Пользователь с ID {user_id} не найден при обработке кнопки")
        return

    logger.info(f"Обработка callback_data: {query.data} от пользователя {user_id}")

    if query.data == 'admin_panel':
        if user["role"] == "admin":
            await admin_panel_menu(update, context)
        else:
            await query.edit_message_text("Доступ разрешен только для администраторов!")
            logger.warning(f"Пользователь {user_id} не имеет прав администратора")
    elif query.data == 'personnel':
        await personnel_menu(update, context)
    elif query.data == 'change_name':
        await query.edit_message_text("Введите новое имя:")
        return CHANGE_NAME
    elif query.data == 'add_employee':
        await query.edit_message_text("Введите ID нового сотрудника:")
        return ADD_EMPLOYEE
    elif query.data == 'delete_employee':
        await delete_employee_start(update, context)  # Инициируем процесс удаления
        return DELETE_EMPLOYEE  # Возвращаем состояние
    elif query.data == 'main_menu':
        await start(update, context)
    else:
        await query.edit_message_text("Неизвестная команда.")
        logger.warning(f"Неизвестный callback_data: {query.data}")

async def add_employee(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.info("Добавление нового сотрудника")
    try:
        new_employee_id = int(update.message.text)
        logger.debug(f"Введён ID нового сотрудника: {new_employee_id}")
    except ValueError:
        await update.effective_message.reply_text("ID должен быть числом. Попробуйте снова.")
        logger.error("Введён некорректный ID для нового сотрудника")
        return ADD_EMPLOYEE

    new_employee = {
        "id": new_employee_id,
        "name": "NoName",
        "role": "personnel",
        "on_shift": False
    }
    USERS.append(new_employee)
    save_users(USERS)
    logger.info(f"Добавлен новый сотрудник: {new_employee}")

    # Создание инлайн-клавиатуры с кнопкой "Вернуться в главное меню"
    inline_keyboard = [
        [InlineKeyboardButton("Вернуться в главное меню", callback_data='main_menu')]
    ]
    reply_markup_inline = InlineKeyboardMarkup(inline_keyboard)

    await update.effective_message.reply_text(
        f"Сотрудник с ID {new_employee_id} добавлен с базовыми данными.",
        reply_markup=reply_markup_inline
    )
    return ConversationHandler.END

async def delete_employee_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Начало процесса удаления сотрудника. Запрашивает ID сотрудника.
    """
    logger.info("Запуск удаления сотрудника")
    await update.effective_message.reply_text("Введите ID сотрудника для удаления:")
    return DELETE_EMPLOYEE

async def delete_employee(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Обрабатывает ввод ID сотрудника и удаляет его из списка.
    """
    logger.info("Удаление сотрудника")
    logger.info(f"Получен текст для удаления: {update.message.text}")

    try:
        employee_id = int(update.message.text)
        logger.debug(f"Введён ID сотрудника для удаления: {employee_id}")
    except ValueError:
        await update.effective_message.reply_text("ID должен быть числом. Попробуйте снова.")
        logger.error("Введён некорректный ID для удаления сотрудника")
        return DELETE_EMPLOYEE

    user = get_user(employee_id)
    if not user:
        await update.effective_message.reply_text(f"Сотрудник с ID {employee_id} не найден.")
        logger.warning(f"Попытка удалить несуществующего сотрудника с ID {employee_id}")
        return DELETE_EMPLOYEE

    # Удаление сотрудника из списка
    USERS.remove(user)
    save_users(USERS)
    logger.info(f"Сотрудник с ID {employee_id} удалён")

    # Создание инлайн-клавиатуры с кнопкой "Вернуться в главное меню"
    inline_keyboard = [
        [InlineKeyboardButton("Вернуться в главное меню", callback_data='main_menu')]
    ]
    reply_markup_inline = InlineKeyboardMarkup(inline_keyboard)

    await update.effective_message.reply_text(
        f"Сотрудник с ID {employee_id} успешно удалён.",
        reply_markup=reply_markup_inline
    )
    return ConversationHandler.END

async def change_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.info("Изменение имени пользователя")
    try:
        user_id = update.message.from_user.id
        user = get_user(user_id)

        if not user:
            await update.effective_message.reply_text("Пользователь не найден.")
            logger.warning(f"Пользователь с ID {user_id} не найден при изменении имени")
            return ConversationHandler.END

        new_name = update.message.text
        user["name"] = new_name
        save_users(USERS)
        logger.info(f"Имя пользователя {user_id} изменено на {new_name}")

        await update.effective_message.reply_text(f"Ваше имя успешно изменено на {new_name}.")
        return ConversationHandler.END
    except Exception as e:
        logger.error(f"Ошибка при изменении имени: {e}")
        await update.effective_message.reply_text("Произошла ошибка. Попробуйте снова.")
        return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.info("Операция отменена пользователем")
    if update.message:
        await update.message.reply_text("Операция отменена.")
    elif update.callback_query:
        await update.callback_query.edit_message_text("Операция отменена.")
    return ConversationHandler.END
