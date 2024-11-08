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
    cancel,
    CHANGE_NAME,
    ADD_EMPLOYEE,
    DELETE_EMPLOYEE,
    delete_employee,
    delete_employee_start
)

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.DEBUG
)
logger = logging.getLogger(__name__)

if __name__ == '__main__':
    if not TOKEN:
        logger.error("Токен бота не найден. Проверьте файл token.txt.")
        exit(1)

    app = ApplicationBuilder().token(TOKEN).build()

    # Основная команда /start
    app.add_handler(CommandHandler("start", start))

    # ConversationHandler для состояний CHANGE_NAME, ADD_EMPLOYEE и DELETE_EMPLOYEE
    conv_handler = ConversationHandler(
        entry_points=[CallbackQueryHandler(button_handler, pattern='^(change_name|add_employee|delete_employee)$')],
        states={
            CHANGE_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, change_name)],
            ADD_EMPLOYEE: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_employee)],
            DELETE_EMPLOYEE: [MessageHandler(filters.TEXT & ~filters.COMMAND, delete_employee)]  # Новое состояние
        },
        fallbacks=[CommandHandler("cancel", cancel)]
    )

    # Добавляем ConversationHandler перед другими CallbackQueryHandler
    app.add_handler(conv_handler)

    # Добавляем другие CallbackQueryHandler для остальных кнопок
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
