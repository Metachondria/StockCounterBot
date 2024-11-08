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
    delete_employee_start,
    delete_employee,
    cancel,
    CHANGE_NAME,
    ADD_EMPLOYEE,
    DELETE_EMPLOYEE,
    start_shift,
    end_shift,
    proceed_to_work,
    add_product,
    write_off_product,
    cancel_sale,
    product_stock,
    check_stock_quantity
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

    app.add_handler(CommandHandler("start", start))

    conv_handler = ConversationHandler(
        entry_points=[CallbackQueryHandler(button_handler, pattern='^(change_name|add_employee|delete_employee)$')],
        states={
            CHANGE_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, change_name)],
            ADD_EMPLOYEE: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_employee)],
            DELETE_EMPLOYEE: [MessageHandler(filters.TEXT & ~filters.COMMAND, delete_employee)]
        },
        fallbacks=[CommandHandler("cancel", cancel)]
    )
    app.add_handler(conv_handler)

    app.add_handler(CallbackQueryHandler(start_shift, pattern='^start_shift$'))
    app.add_handler(CallbackQueryHandler(end_shift, pattern='^end_shift$'))

    app.add_handler(CallbackQueryHandler(proceed_to_work, pattern='^proceed_to_work$'))

    app.add_handler(CallbackQueryHandler(write_off_product, pattern='^write_off_product$'))
    app.add_handler(CallbackQueryHandler(add_product, pattern='^add_product$'))
    app.add_handler(CallbackQueryHandler(cancel_sale, pattern='^cancel_sale$'))
    app.add_handler(CallbackQueryHandler(product_stock, pattern='^product_stock$'))
    app.add_handler(CallbackQueryHandler(check_stock_quantity, pattern='^check_stock_quantity$'))

    app.add_handler(CallbackQueryHandler(button_handler, pattern='^admin_panel$'))
    app.add_handler(CallbackQueryHandler(button_handler, pattern='^personnel$'))
    app.add_handler(CallbackQueryHandler(button_handler, pattern='^main_menu$'))

    async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE):
        logger.error(msg="Exception while handling an update:", exc_info=context.error)

    app.add_error_handler(error_handler)

    try:
        logger.info("Бот запущен")
        app.run_polling()
    except Exception as e:
        logger.error(f"Произошла ошибка при запуске бота: {e}")
