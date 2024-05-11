from telegram import Update, Bot
from telegram.ext import Updater, CommandHandler, MessageHandler, CallbackContext
import logging
# from core_service.settings import TELEGRAM_KEY
import telegram.ext.filters as Filters
from telegram.ext import Application
TELEGRAM_KEY = "6503310536:AAGlqVv7dJZllqtVl6nl3szclPcHfPTrYJE"

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)
logger = logging.getLogger(__name__)


def initialize_bot():
    try:
        bot = Bot(TELEGRAM_KEY)
        logger.info("Bot initialized successfully")
        return bot
    except Exception as e:
        logger.error("Failed to connect to bot: %s", e)
        return None

# Command handlers
async def start(update: Update, context: CallbackContext) -> None:
    await update.message.reply_text('Hello! This is your friendly expense splitter bot. BSDK')

async def help_command(update: Update, context: CallbackContext) -> None:
    await update.message.reply_text("Send me a message and I'll echo it back!")

# Message handler
async def echo(update: Update, context: CallbackContext) -> None:
    text = update.message.text
    await update.message.reply_text(f'You said: {text}')

# Error handler
def error(update: Update, context: CallbackContext) -> None:
    logger.warning('Update "%s" caused error "%s"', update, context.error)

# Main function to start the bot
def main() -> None:
    bot = initialize_bot()
    if bot:
        print(bot.getMe())
        # updater = Updater(bot.token, use_context=True)
        dp = Application.builder().token(TELEGRAM_KEY).build()
        
        # Get the dispatcher to register handlers
        
        
        # Register handlers
        dp.add_handler(CommandHandler("start", start))
        dp.add_handler(CommandHandler("help", help_command))
        # dp.add_handler(MessageHandler(Filters.text & ~Filters.command, echo))
        
        # Log all errors
        dp.add_error_handler(error)
        
        # Start the Bot
        # updater.start_polling()
        dp.run_polling()
        

if __name__ == '__main__':
    main()
