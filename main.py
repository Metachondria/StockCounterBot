import logging
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    CallbackQueryHandler,
    ConversationHandler,
    MessageHandler,
    filters,
    ContextTypes
)
from config import TOKEN
from handlers import (
    start,
    button_handler,
    change_name,
    add_employee,
    delete_employee,
    cancel,
    CHANGE_NAME,
    ADD_EMPLOYEE,
    DELETE_EMPLOYEE,
    start_shift,
    end_shift,
    proceed_to_work,
    add_product,
    cancel_sale,
    product_stock,
    sell_product,
    handle_kitchen,
    handle_drinks,
    handle_snacks,
    handle_product_selection,  # Обработчик выбора конкретного товара
    handle_quantity_input,  # Обработчик ввода количества
    INPUT_QUANTITY  # Состояние для ввода количества
)

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.DEBUG  # Установите уровень DEBUG для подробных логов
)
logger = logging.getLogger(__name__)

if __name__ == '__main__':
    if not TOKEN:
        logger.error("Токен бота не найден. Проверьте файл token.txt.")
        exit(1)

    app = ApplicationBuilder().token(TOKEN).build()

    # Основная команда /start
    app.add_handler(CommandHandler("start", start))

    # ConversationHandler для состояний CHANGE_NAME, ADD_EMPLOYEE, DELETE_EMPLOYEE и INPUT_QUANTITY
    conv_handler = ConversationHandler(
        entry_points=[
            CallbackQueryHandler(button_handler, pattern='^(change_name|add_employee|delete_employee)$'),
            CallbackQueryHandler(handle_product_selection, pattern='^product_')  # Обработка выбора товара
        ],
        states={
            CHANGE_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, change_name)],
            ADD_EMPLOYEE: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_employee)],
            DELETE_EMPLOYEE: [MessageHandler(filters.TEXT & ~filters.COMMAND, delete_employee)],
            INPUT_QUANTITY: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_quantity_input)]  # Обработка ввода количества
        },
        fallbacks=[CommandHandler("cancel", cancel)]
    )
    app.add_handler(conv_handler)

    # Добавление обработчиков для кнопок начала и окончания смены
    app.add_handler(CallbackQueryHandler(start_shift, pattern='^start_shift$'))
    app.add_handler(CallbackQueryHandler(end_shift, pattern='^end_shift$'))

    # Добавление обработчика для кнопки 'Преступить к работе'
    app.add_handler(CallbackQueryHandler(proceed_to_work, pattern='^proceed_to_work$'))

    # Добавление обработчика для кнопки "Назад" к выбору категории
    app.add_handler(CallbackQueryHandler(sell_product, pattern='^back_to_categories$'))

    # Добавление обработчиков для функциональных кнопок рабочего меню
    app.add_handler(CallbackQueryHandler(add_product, pattern='^add_product$'))
    app.add_handler(CallbackQueryHandler(cancel_sale, pattern='^cancel_sale$'))
    app.add_handler(CallbackQueryHandler(product_stock, pattern='^product_stock$'))
    app.add_handler(CallbackQueryHandler(sell_product, pattern='^sell_product$'))

    # Обработчики для категорий продажи товара
    app.add_handler(CallbackQueryHandler(handle_kitchen, pattern='^category_кухня$'))
    app.add_handler(CallbackQueryHandler(handle_drinks, pattern='^category_напитки$'))
    app.add_handler(CallbackQueryHandler(handle_snacks, pattern='^category_снеки$'))

    # Добавление обработчика для выбора товара, когда пользователь выбирает конкретный продукт
    app.add_handler(CallbackQueryHandler(handle_product_selection, pattern='^product_'))

    # Добавление обработчиков для административных и персональных кнопок
    app.add_handler(CallbackQueryHandler(button_handler, pattern='^admin_panel$'))
    app.add_handler(CallbackQueryHandler(button_handler, pattern='^personnel$'))
    app.add_handler(CallbackQueryHandler(button_handler, pattern='^main_menu$'))

    # Глобальный обработчик ошибок
    async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE):
        logger.error(msg="Exception while handling an update:", exc_info=context.error)

    app.add_error_handler(error_handler)

    # Запускаем бота
    try:
        logger.info("Бот запущен")
        app.run_polling()
    except Exception as e:
        logger.error(f"Произошла ошибка при запуске бота: {e}")
