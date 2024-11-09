from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler
import logging

logger = logging.getLogger(__name__)

# Определение состояний для ConversationHandler
SELECT_CATEGORY, SELECT_PRODUCT = range(2)

# Определение категорий и их товаров
CATEGORIES = {
    'кухня': [
        "Фунчоза с овощами",
        "Спагетти Карбонара",
        "Паста с цыпленком",
        "Котлеты с пюре",
        "Борщ с телятеной",
        "Грибной суп-пюре",
        "Боул с цыпленком терияки",
        "Люля-кебаб из цыпленка",
        "Удон с курицей",
        "Цыпленок в кисло-сладком соусе",
        "Традиционный плов с курицей",
        "Бефстроганов из говядины"
    ],
    'напитки': [
        "Кола 0.5л",
        "Сок яблочный 0.3л",
        "Минеральная вода 0.5л",
        "Чай черный",
        "Кофе эспрессо",
        "Лимонад 0.5л"
    ],
    'снеки': [
        "Чипсы соленые",
        "Орехи смешанные",
        "Попкорн",
        "Сухарики",
        "Сладкие батончики",
        "Фруктовые батончики"
    ]
}

# async def sell_product(update: Update, context: ContextTypes.DEFAULT_TYPE):
#     """Отображает меню с категориями товаров."""
#     query = update.callback_query
#     inline_keyboard = [
#         [InlineKeyboardButton("Кухня", callback_data='category_кухня')],
#         [InlineKeyboardButton("Напитки", callback_data='category_напитки')],
#         [InlineKeyboardButton("Снеки", callback_data='category_снеки')],
#         [InlineKeyboardButton("Вернуться в рабочее меню", callback_data='proceed_to_work')]
#     ]
#     reply_markup = InlineKeyboardMarkup(inline_keyboard)
#     await query.edit_message_text("Выберите категорию товара для продажи:", reply_markup=reply_markup)
#     logger.info("Пользователь выбрал 'Продажа товара' и видит категории.")
#     return SELECT_CATEGORY


async def select_category(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Сохраняет выбранную категорию и отображает список товаров."""
    query = update.callback_query
    data = query.data
    category = data.split('_')[1]  # Извлекаем категорию из callback_data
    context.user_data['sale_category'] = category

    products = CATEGORIES.get(category, [])
    if not products:
        await query.edit_message_text("В этой категории нет товаров.")
        return ConversationHandler.END

    # Создаём инлайн-клавиатуру с товарами
    keyboard = [
        [InlineKeyboardButton(product, callback_data=f"product_{product.replace(' ', '_')}")]
        for product in products
    ]
    # Добавляем кнопку "Назад", чтобы вернуться к выбору категории
    keyboard.append([InlineKeyboardButton("Назад", callback_data='back_to_categories')])

    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(f"Вы выбрали категорию: {category}. Выберите товар для продажи:", reply_markup=reply_markup)
    return SELECT_PRODUCT

