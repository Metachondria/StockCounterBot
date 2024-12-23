# handlers.py
from sales_handlers import select_category, CATEGORIES  # Убедитесь, что select_category импортируется
from telegram.ext import (
    CommandHandler,
    CallbackQueryHandler,
    ConversationHandler,
    MessageHandler,
    filters,
    ContextTypes
)
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from config import USERS, save_users
import logging

logger = logging.getLogger(__name__)

# Определение состояний для ConversationHandler
CHANGE_NAME, ADD_EMPLOYEE, DELETE_EMPLOYEE, INPUT_QUANTITY = range(4)

def get_user(user_id):
    """Получает пользователя по его ID."""
    user = next((user for user in USERS if user["id"] == user_id), None)
    logger.debug(f"Получен пользователь: {user}")
    return user

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /start."""
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
    """Меню Admin Panel с динамической кнопкой 'Преступить к работе'."""
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
        inline_keyboard.append([InlineKeyboardButton("Приступить к работе", callback_data='proceed_to_work')])

    inline_keyboard.append([InlineKeyboardButton("Вернуться в главное меню", callback_data='main_menu')])

    reply_markup_inline = InlineKeyboardMarkup(inline_keyboard)

    await query.edit_message_text(
        "Админ панель:",
        reply_markup=reply_markup_inline
    )

async def personnel_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Меню Personnel."""
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
        inline_keyboard.append([InlineKeyboardButton("Приступить к работе", callback_data='proceed_to_work')])

    inline_keyboard.append([InlineKeyboardButton("Вернуться в главное меню", callback_data='main_menu')])

    reply_markup_inline = InlineKeyboardMarkup(inline_keyboard)

    await query.edit_message_text(
        "Меню персонала:",
        reply_markup=reply_markup_inline
    )

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик всех нажатий кнопок."""
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
    elif query.data in ['write_off_product', 'add_product', 'cancel_sale', 'product_stock', 'sell_product']:
        await handle_operational_buttons(update, context, query.data, user_id)
    elif query.data == 'main_menu':
        await start(update, context)
    elif query.data in ['category_кухня', 'category_напитки', 'category_снеки']:
        # Обработка новых категорий продажи товара
        if query.data == 'category_кухня':
            await handle_kitchen(update, context)
        elif query.data == 'category_напитки':
            await handle_drinks(update, context)
        elif query.data == 'category_снеки':
            await handle_snacks(update, context)

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
            'add_product': add_product,
            'cancel_sale': cancel_sale,
            'product_stock': product_stock,
            'sell_product': sell_product  # Исправлено: без вызова функции
        }
    else:

        operations = {
            'add_product': add_product,
            'cancel_sale': cancel_sale,
            'product_stock': product_stock,
            'sell_product': sell_product  # Исправлено: без вызова функции
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
            [InlineKeyboardButton("Продажа товара", callback_data='sell_product')],
            [InlineKeyboardButton("Добавить товар", callback_data='add_product')],
            [InlineKeyboardButton("Отменить продажу", callback_data='cancel_sale')],
            [InlineKeyboardButton("Остаток товара на складе", callback_data='product_stock')],
            [InlineKeyboardButton("Закончить смену", callback_data='end_shift')],
            [InlineKeyboardButton("Вернуться в Admin Panel", callback_data='admin_panel')]
        ]
    else:
        # Меню для сотрудника
        inline_keyboard = [
            [InlineKeyboardButton("Продажа товара", callback_data='sell_product')],
            [InlineKeyboardButton("Добавить товар", callback_data='add_product')],
            [InlineKeyboardButton("Отменить продажу", callback_data='cancel_sale')],
            [InlineKeyboardButton("Остаток товара на складе", callback_data='product_stock')],
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
            [InlineKeyboardButton("Продажа товара", callback_data='sell_product')],
            [InlineKeyboardButton("Добавить товар", callback_data='add_product')],
            [InlineKeyboardButton("Отменить продажу", callback_data='cancel_sale')],
            [InlineKeyboardButton("Остаток товара на складе", callback_data='product_stock')],
            [InlineKeyboardButton("Закончить смену", callback_data='end_shift')],
            [InlineKeyboardButton("Вернуться в Admin Panel", callback_data='admin_panel')]
        ]
    else:
        # Меню для сотрудника
        inline_keyboard = [
            [InlineKeyboardButton("Продажа товара", callback_data='sell_product')],
            [InlineKeyboardButton("Добавить товар", callback_data='add_product')],
            [InlineKeyboardButton("Отменить продажу", callback_data='cancel_sale')],
            [InlineKeyboardButton("Остаток товара на складе", callback_data='product_stock')],
            [InlineKeyboardButton("Закончить смену", callback_data='end_shift')],
            [InlineKeyboardButton("Вернуться в Personnel Menu", callback_data='personnel')]
        ]

    reply_markup_inline = InlineKeyboardMarkup(inline_keyboard)

    await query.edit_message_text(
        "Вы в рабочем режиме. Выберите действие:",
        reply_markup=reply_markup_inline
    )
    logger.debug(f"Отправлено рабочее меню для роли '{user['role']}'.")

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

async def sell_product(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    inline_keyboard = [
        [InlineKeyboardButton("Кухня", callback_data='category_кухня')],  # Исправлено 'category_кухня'
        [InlineKeyboardButton("Напитки", callback_data='category_напитки')],
        [InlineKeyboardButton("Снеки", callback_data='category_снеки')],
        [InlineKeyboardButton("Вернуться в рабочее меню", callback_data='proceed_to_work')]
    ]

    reply_markup = InlineKeyboardMarkup(inline_keyboard)
    await query.edit_message_text("Выберите категорию товара для продажи:", reply_markup=reply_markup)
    return select_category  # Убедитесь, что состояние обновлено

async def handle_kitchen(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка кнопки 'Кухня': отображает список товаров."""
    await select_category(update, context)
    logger.info("Пользователь выбрал категорию 'Кухня' и видит список товаров.")

async def handle_drinks(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка кнопки 'Напитки': отображает список товаров."""
    query = update.callback_query

    # Список товаров для категории "Напитки"
    drinks_products = [
        "BoomBar лимонад",
        "BoomBar енергетики",
        "Gorilla",
        "LitEnergy",
        "MonsterEnergy",
        "Берн",
        "Добрый 0,33",
        "Липтон 0.5",
        "Палпи 0.5",
        "Ред Бул 0.25",
        "Свят источник",
        "Черноголовка"
    ]

    # Создаем инлайн-клавиатуру с товарами
    keyboard = [
        [InlineKeyboardButton(product, callback_data=f"product_{product.replace(' ', '_')}")]
        for product in drinks_products
    ]
    # Добавляем кнопку "Назад" для возврата к выбору категорий
    keyboard.append([InlineKeyboardButton("Назад", callback_data='back_to_categories')])

    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text("Выберите товар из категории 'Напитки':", reply_markup=reply_markup)


async def handle_snacks(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка кнопки 'Снеки': отображает список товаров."""
    query = update.callback_query

    # Список товаров для категории "Снеки"
    snacks_products = [
        "BoomBar батончики",
        "BoomBar Печенья",
        "Bueno",
        "M&Ms",
        "Дирол",
        "Лейс",
        "Пикник",
        "Сникерс",
        "Твикс",
        "Холсс",
        "Чебупелли",
        "Чебупицца",
        "Круггетсы"
    ]

    # Создаем инлайн-клавиатуру с товарами
    keyboard = [
        [InlineKeyboardButton(product, callback_data=f"product_{product.replace(' ', '_')}")]
        for product in snacks_products
    ]
    # Добавляем кнопку "Назад" для возврата к выбору категорий
    keyboard.append([InlineKeyboardButton("Назад", callback_data='back_to_categories')])

    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text("Выберите товар из категории 'Снеки':", reply_markup=reply_markup)


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /cancel."""
    logger.info("Операция отменена пользователем")
    if update.message:
        await update.message.reply_text("Операция отменена.")
    elif update.callback_query:
        await update.callback_query.edit_message_text("Операция отменена.")
    return ConversationHandler.END
async def handle_product_selection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обрабатывает выбор товара и запрашивает количество."""
    query = update.callback_query
    product = query.data.replace("product_", "").replace("_", " ")  # Получаем название товара
    context.user_data['selected_product'] = product  # Сохраняем выбранный товар в контексте
    await query.edit_message_text(f"Вы выбрали {product}. Пожалуйста, введите количество:")
    return INPUT_QUANTITY


from telegram import Update
from telegram.ext import ContextTypes, ConversationHandler
from sheets import update_product_quantity_by_row
import logging

async def handle_product_selection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    product = query.data.replace("product_", "").replace("_", " ")  # Получаем название товара
    context.user_data['selected_product'] = product  # Сохраняем выбранный товар в контексте
    await query.edit_message_text(f"Вы выбрали {product}. Пожалуйста, введите количество:")
    return INPUT_QUANTITY



logger = logging.getLogger(__name__)

# Состояние для обработки количества
INPUT_QUANTITY = range(1)


async def handle_quantity_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    quantity_str = update.message.text
    logger.debug(f"Получено количество: {quantity_str}")

    product = context.user_data.get('selected_product')  # Получаем выбранный продукт
    logger.debug(f"User data перед обработкой количества: {context.user_data}")

    # Проверка, что продукт выбран и сохранен в user_data
    if not product:
        await update.message.reply_text("Произошла ошибка. Пожалуйста, выберите товар заново.")
        logger.error("Продукт не был выбран. context.user_data['selected_product'] отсутствует.")
        return ConversationHandler.END

    # Проверка, что введенное значение - целое число
    if not quantity_str.isdigit():
        await update.message.reply_text("Пожалуйста, введите корректное количество (число).")
        logger.debug("Некорректное количество. Пользователь получил сообщение о неправильном вводе.")
        return INPUT_QUANTITY

    quantity = int(quantity_str)
    logger.debug(f"Получено количество: {quantity} для товара: {product}")

    # Обновляем количество товара в Google Таблице
    try:
        success, new_quantity = update_product_quantity_by_row(
            sheet_name="K15_SKLAD",
            product_name=product,
            quantity=quantity
        )
    except Exception as e:
        logger.error(f"Ошибка при попытке обновления количества в Google Sheets: {e}")
        await update.message.reply_text("Произошла ошибка при обновлении количества товара.")
        return ConversationHandler.END

    # Обработка результата обновления
    if success:
        await update.message.reply_text(f"Количество товара '{product}' обновлено. Остаток: {new_quantity}.")
        logger.debug(f"Количество товара '{product}' успешно обновлено. Новый остаток: {new_quantity}.")
    elif new_quantity is not None:
        await update.message.reply_text(
            f"Недостаточно товара '{product}' на складе. Текущее количество: {new_quantity}."
        )
        logger.debug(f"Недостаточно товара '{product}' на складе. Текущее количество: {new_quantity}.")
    else:
        await update.message.reply_text("Произошла ошибка при обновлении количества товара.")
        logger.error("Ошибка при обновлении количества товара.")

    return ConversationHandler.END



