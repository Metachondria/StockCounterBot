from telegram.ext import (
    CommandHandler,
    CallbackQueryHandler,
    ConversationHandler,
    MessageHandler,
    filters,
    ContextTypes
)
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
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
    if user["role"] == "admin":
        inline_keyboard = [
            [InlineKeyboardButton("Admin Panel", callback_data='admin_panel')],
            [InlineKeyboardButton("Изменить имя", callback_data='change_name')]
        ]
    else:
        inline_keyboard = [
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
    query = update.callback_query
    user_id = query.from_user.id
    user = get_user(user_id)

    if not user:
        await query.edit_message_text("Пользователь не найден.")
        logger.error(f"Пользователь с ID {user_id} не найден при переходе в Admin Panel.")
        return

    if user["role"] != "admin":
        await query.edit_message_text("Доступ разрешен только для администраторов!")
        logger.warning(f"Пользователь {user_id} не имеет прав администратора.")
        return

    # Базовые кнопки
    inline_keyboard = [
        [InlineKeyboardButton("Начать смену", callback_data='start_shift')],
        [InlineKeyboardButton("Закончить смену", callback_data='end_shift')],
        [InlineKeyboardButton("Добавить сотрудника", callback_data='add_employee')],
        [InlineKeyboardButton("Удалить сотрудника", callback_data='delete_employee')],
    ]

    if user.get('on_shift', False):
        inline_keyboard.append([InlineKeyboardButton("Преступить к работе", callback_data='proceed_to_work')])

    inline_keyboard.append([InlineKeyboardButton("Вернуться в главное меню", callback_data='main_menu')])

    reply_markup_inline = InlineKeyboardMarkup(inline_keyboard)

    await query.edit_message_text(
        "Админ панель:",
        reply_markup=reply_markup_inline
    )

async def personnel_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.info("Переход в Personnel Menu")
    query = update.callback_query
    user_id = query.from_user.id
    user = get_user(user_id)

    if not user:
        await query.edit_message_text("Пользователь не найден.")
        logger.error(f"Пользователь с ID {user_id} не найден при переходе в Personnel Menu.")
        return

    if user["role"] != "personnel":
        await query.edit_message_text("Доступ разрешен только для сотрудников!")
        logger.warning(f"Пользователь {user_id} не имеет роли 'personnel'.")
        return

    inline_keyboard = [
        [InlineKeyboardButton("Начать смену", callback_data='start_shift')],
        [InlineKeyboardButton("Закончить смену", callback_data='end_shift')],
    ]

    if user.get('on_shift', False):
        inline_keyboard.append([InlineKeyboardButton("Преступить к работе", callback_data='proceed_to_work')])

    inline_keyboard.append([InlineKeyboardButton("Вернуться в главное меню", callback_data='main_menu')])

    reply_markup_inline = InlineKeyboardMarkup(inline_keyboard)

    await query.edit_message_text(
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
        logger.warning(f"Пользователь с ID {user_id} не найден при обработке кнопки.")
        return

    logger.info(f"Обработка callback_data: {query.data} от пользователя {user_id}")

    if query.data == 'admin_panel':
        if user["role"] == "admin":
            await admin_panel_menu(update, context)
        else:
            await query.edit_message_text("Доступ разрешен только для администраторов!")
            logger.warning(f"Пользователь {user_id} не имеет прав администратора.")
    elif query.data == 'personnel':
        if user["role"] == "personnel":
            await personnel_menu(update, context)
        else:
            await query.edit_message_text("Доступ разрешен только для сотрудников!")
            logger.warning(f"Пользователь {user_id} не имеет роли 'personnel'.")
    elif query.data == 'change_name':
        await query.edit_message_text("Введите новое имя:")
        return CHANGE_NAME
    elif query.data == 'add_employee':
        if user["role"] == "admin":
            await query.edit_message_text("Введите ID нового сотрудника:")
            return ADD_EMPLOYEE
        else:
            await query.edit_message_text("Доступ разрешен только для администраторов!")
            logger.warning(f"Пользователь {user_id} попытался добавить сотрудника без прав администратора.")
    elif query.data == 'delete_employee':
        if user["role"] == "admin":
            await delete_employee_start(update, context)  # Инициируем процесс удаления
            return DELETE_EMPLOYEE  # Возвращаем состояние
        else:
            await query.edit_message_text("Доступ разрешен только для администраторов!")
            logger.warning(f"Пользователь {user_id} попытался удалить сотрудника без прав администратора.")
    elif query.data == 'start_shift':
        await start_shift(update, context)
        return ConversationHandler.END
    elif query.data == 'end_shift':
        await end_shift(update, context)
        return ConversationHandler.END
    elif query.data == 'proceed_to_work':
        await proceed_to_work(update, context)
    elif query.data in ['write_off_product', 'add_product', 'cancel_sale', 'product_stock', 'check_stock_quantity']:

        await handle_operational_buttons(update, context, query.data, user_id)
    elif query.data == 'main_menu':
        await start(update, context)
    else:
        await query.edit_message_text("Неизвестная команда.")
        logger.warning(f"Неизвестный callback_data: {query.data}")

async def handle_operational_buttons(update: Update, context: ContextTypes.DEFAULT_TYPE, callback_data: str, user_id: int):

    query = update.callback_query
    user = get_user(user_id)

    if not user or not user.get('on_shift', False):
        await query.edit_message_text("Смена не начата или пользователь не найден.")
        logger.warning(f"Пользователь {user_id} попытался выполнить операцию без активной смены.")
        return


    if user["role"] == "admin":

        operations = {
            'write_off_product': write_off_product,
            'add_product': add_product,
            'cancel_sale': cancel_sale,
            'product_stock': product_stock,
            'check_stock_quantity': check_stock_quantity
        }
    else:

        operations = {
            'write_off_product': write_off_product,
            'add_product': add_product,
            'cancel_sale': cancel_sale,
            'product_stock': product_stock,
            'check_stock_quantity': check_stock_quantity
        }

    handler = operations.get(callback_data)
    if handler:
        await handler(update, context)
    else:
        await query.edit_message_text("Неизвестная команда.")
        logger.warning(f"Неизвестный callback_data: {callback_data}")

async def proceed_to_work(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Меню с кнопками для операций во время смены."""
    query = update.callback_query
    user_id = query.from_user.id
    user = get_user(user_id)

    if not user:
        await query.edit_message_text("Пользователь не найден.")
        logger.error(f"Пользователь с ID {user_id} не найден при попытке приступить к работе.")
        return

    if not user.get('on_shift', False):
        await query.edit_message_text("Смена не начата. Пожалуйста, начните смену сначала.")
        logger.warning(f"Пользователь {user_id} попытался приступить к работе без начала смены.")
        return

    if user["role"] == "admin":
        # Меню для администратора
        inline_keyboard = [
            [InlineKeyboardButton("Списать товар", callback_data='write_off_product')],
            [InlineKeyboardButton("Добавить товар", callback_data='add_product')],
            [InlineKeyboardButton("Отменить продажу", callback_data='cancel_sale')],
            [InlineKeyboardButton("Остаток товара на складе", callback_data='product_stock')],
            [InlineKeyboardButton("Узнать количество товара на складе", callback_data='check_stock_quantity')],
            [InlineKeyboardButton("Закончить смену", callback_data='end_shift')],
            [InlineKeyboardButton("Вернуться в Admin Panel", callback_data='admin_panel')]
        ]
    else:
        # Меню для сотрудника
        inline_keyboard = [
            [InlineKeyboardButton("Списать товар", callback_data='write_off_product')],
            [InlineKeyboardButton("Добавить товар", callback_data='add_product')],
            [InlineKeyboardButton("Отменить продажу", callback_data='cancel_sale')],
            [InlineKeyboardButton("Остаток товара на складе", callback_data='product_stock')],
            [InlineKeyboardButton("Узнать количество товара на складе", callback_data='check_stock_quantity')],
            [InlineKeyboardButton("Закончить смену", callback_data='end_shift')],
            [InlineKeyboardButton("Вернуться в Personnel Menu", callback_data='personnel')]
        ]

    reply_markup_inline = InlineKeyboardMarkup(inline_keyboard)

    await query.edit_message_text(
        "Вы в рабочем режиме. Выберите действие:",
        reply_markup=reply_markup_inline
    )
    logger.debug(f"Отправлено рабочее меню для роли '{user['role']}'.")

async def add_employee(update: Update, context: ContextTypes.DEFAULT_TYPE):

    logger.info("Добавление нового сотрудника")
    try:
        new_employee_id = int(update.message.text)
        logger.debug(f"Введён ID нового сотрудника: {new_employee_id}")
    except ValueError:
        await update.effective_message.reply_text("ID должен быть числом. Попробуйте снова.")
        logger.error("Введён некорректный ID для нового сотрудника.")
        return ADD_EMPLOYEE


    if get_user(new_employee_id):
        await update.effective_message.reply_text("Сотрудник с таким ID уже существует.")
        logger.warning(f"Попытка добавить существующего сотрудника с ID {new_employee_id}.")
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

    # Создание инлайн-клавиатуры с кнопкой "Вернуться в Admin Panel"
    inline_keyboard = [
        [InlineKeyboardButton("Вернуться в Admin Panel", callback_data='admin_panel')]
    ]
    reply_markup_inline = InlineKeyboardMarkup(inline_keyboard)

    await update.effective_message.reply_text(
        f"Сотрудник с ID {new_employee_id} добавлен с базовыми данными.",
        reply_markup=reply_markup_inline
    )
    return ConversationHandler.END

async def delete_employee_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Начало процесса удаления сотрудника. Запрашивает ID сотрудника."""
    logger.info("Запуск удаления сотрудника")
    await update.effective_message.reply_text("Введите ID сотрудника для удаления:")
    return DELETE_EMPLOYEE

async def delete_employee(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обрабатывает ввод ID сотрудника и удаляет его из списка."""
    logger.info("Удаление сотрудника")
    logger.info(f"Получен текст для удаления: {update.message.text}")

    try:
        employee_id = int(update.message.text)
        logger.debug(f"Введён ID сотрудника для удаления: {employee_id}")
    except ValueError:
        await update.effective_message.reply_text("ID должен быть числом. Попробуйте снова.")
        logger.error("Введён некорректный ID для удаления сотрудника.")
        return DELETE_EMPLOYEE

    user = get_user(employee_id)
    if not user:
        await update.effective_message.reply_text(f"Сотрудник с ID {employee_id} не найден.")
        logger.warning(f"Попытка удалить несуществующего сотрудника с ID {employee_id}.")
        return DELETE_EMPLOYEE


    USERS.remove(user)
    save_users(USERS)
    logger.info(f"Сотрудник с ID {employee_id} удалён.")

    # Создание инлайн-клавиатуры с кнопкой "Вернуться в Admin Panel"
    inline_keyboard = [
        [InlineKeyboardButton("Вернуться в Admin Panel", callback_data='admin_panel')]
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
            logger.warning(f"Пользователь с ID {user_id} не найден при изменении имени.")
            return ConversationHandler.END

        new_name = update.message.text.strip()
        if not new_name:
            await update.effective_message.reply_text("Имя не может быть пустым. Попробуйте снова.")
            logger.warning("Пользователь попытался установить пустое имя.")
            return CHANGE_NAME

        user["name"] = new_name
        save_users(USERS)
        logger.info(f"Имя пользователя {user_id} изменено на {new_name}.")

        await update.effective_message.reply_text(f"Ваше имя успешно изменено на {new_name}.")
        return ConversationHandler.END
    except Exception as e:
        logger.error(f"Ошибка при изменении имени: {e}")
        await update.effective_message.reply_text("Произошла ошибка. Попробуйте снова.")
        return ConversationHandler.END

async def start_shift(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка начала смены."""
    query = update.callback_query
    user_id = query.from_user.id
    user = get_user(user_id)

    if user:
        user['on_shift'] = True
        save_users(USERS)
        logger.info(f"Пользователь {user['name']} начал смену.")

        if user["role"] == "admin":
            await admin_panel_menu(update, context)
        else:
            await personnel_menu(update, context)
        logger.debug("Меню обновлено после начала смены.")
    else:
        await query.message.reply_text("Пользователь не найден.")
        logger.error(f"Пользователь с ID {user_id} не найден при попытке начать смену.")

async def end_shift(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.from_user.id
    user = get_user(user_id)

    if user and user.get('on_shift', False):
        user['on_shift'] = False
        save_users(USERS)
        logger.info(f"Пользователь {user['name']} закончил смену.")

        if user["role"] == "admin":
            await admin_panel_menu(update, context)
        else:
            await personnel_menu(update, context)
        logger.debug("Меню обновлено после окончания смены.")
    else:
        await query.message.reply_text("Смена не была начата.")
        logger.warning(f"Пользователь {user_id} попытался завершить неактивную смену.")

async def proceed_to_work(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.from_user.id
    user = get_user(user_id)

    if not user:
        await query.edit_message_text("Пользователь не найден.")
        logger.error(f"Пользователь с ID {user_id} не найден при попытке приступить к работе.")
        return

    if not user.get('on_shift', False):
        await query.edit_message_text("Смена не начата. Пожалуйста, начните смену сначала.")
        logger.warning(f"Пользователь {user_id} попытался приступить к работе без начала смены.")
        return

    if user["role"] == "admin":
        inline_keyboard = [
            [InlineKeyboardButton("Списать товар", callback_data='write_off_product')],
            [InlineKeyboardButton("Добавить товар", callback_data='add_product')],
            [InlineKeyboardButton("Отменить продажу", callback_data='cancel_sale')],
            [InlineKeyboardButton("Остаток товара на складе", callback_data='product_stock')],
            [InlineKeyboardButton("Узнать количество товара на складе", callback_data='check_stock_quantity')],
            [InlineKeyboardButton("Закончить смену", callback_data='end_shift')],
            [InlineKeyboardButton("Вернуться в Admin Panel", callback_data='admin_panel')]
        ]
    else:
        inline_keyboard = [
            [InlineKeyboardButton("Списать товар", callback_data='write_off_product')],
            [InlineKeyboardButton("Добавить товар", callback_data='add_product')],
            [InlineKeyboardButton("Отменить продажу", callback_data='cancel_sale')],
            [InlineKeyboardButton("Остаток товара на складе", callback_data='product_stock')],
            [InlineKeyboardButton("Узнать количество товара на складе", callback_data='check_stock_quantity')],
            [InlineKeyboardButton("Закончить смену", callback_data='end_shift')],
            [InlineKeyboardButton("Вернуться в Personnel Menu", callback_data='personnel')]
        ]

    reply_markup_inline = InlineKeyboardMarkup(inline_keyboard)

    await query.edit_message_text(
        "Вы в рабочем режиме. Выберите действие:",
        reply_markup=reply_markup_inline
    )
    logger.debug(f"Отправлено рабочее меню для роли '{user['role']}'.")

async def write_off_product(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.effective_message.reply_text("Функция списания товара ещё не реализована.")
    logger.info("Пользователь выбрал 'Списать товар'.")

async def add_product(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Функция добавления товара."""
    await update.effective_message.reply_text("Функция добавления товара ещё не реализована.")
    logger.info("Пользователь выбрал 'Добавить товар'.")

async def cancel_sale(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Функция отмены продажи."""
    await update.effective_message.reply_text("Функция отмены продажи ещё не реализована.")
    logger.info("Пользователь выбрал 'Отменить продажу'.")

async def product_stock(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Функция проверки остатка товара на складе."""
    await update.effective_message.reply_text("Функция проверки остатка товара на складе ещё не реализована.")
    logger.info("Пользователь выбрал 'Остаток товара на складе'.")

async def check_stock_quantity(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Функция проверки количества товара на складе."""
    await update.effective_message.reply_text("Функция проверки количества товара на складе ещё не реализована.")
    logger.info("Пользователь выбрал 'Узнать количество товара на складе'.")

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /cancel."""
    logger.info("Операция отменена пользователем")
    if update.message:
        await update.message.reply_text("Операция отменена.")
    elif update.callback_query:
        await update.callback_query.edit_message_text("Операция отменена.")
    return ConversationHandler.END
