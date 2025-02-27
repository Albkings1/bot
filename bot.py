import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters
import config
import handlers
import asyncio
import nest_asyncio

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# Apply nest_asyncio to fix event loop issues
nest_asyncio.apply()

async def main():
    # Create application
    application = Application.builder().token(config.TELEGRAM_BOT_TOKEN).build()

    # Add command handlers
    application.add_handler(CommandHandler("start", handlers.start_command))
    application.add_handler(CommandHandler("help", handlers.help_command))
    application.add_handler(CommandHandler("status", handlers.status_command))
    application.add_handler(CommandHandler("createlicence", handlers.create_license_command))
    application.add_handler(CommandHandler("sendsignal", handlers.send_signal_command))
    application.add_handler(CommandHandler("activatelicense", handlers.activate_license_command))
    application.add_handler(CommandHandler("manualsignal", handlers.manual_signal_command))
    application.add_handler(CommandHandler("removelicense", handlers.remove_license_command))
    application.add_handler(CommandHandler("viewusers", handlers.view_users_command))

    # Add text message handler for keyboard buttons
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handlers.handle_text_message))

    # Add callback query handlers
    application.add_handler(CallbackQueryHandler(handlers.signal_callback, pattern="^signal_"))
    application.add_handler(CallbackQueryHandler(handlers.button_callback))

    # Start the bot
    logging.info("Starting bot")
    await application.run_polling(drop_pending_updates=True)

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass