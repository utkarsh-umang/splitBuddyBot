from telegram import Update, Bot
from telegram.ext import CommandHandler, CallbackContext, ChatMemberHandler
import logging
from django.core.management.base import BaseCommand
# from core_service.settings import TELEGRAM_KEY
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
    await update.message.reply_text('Hello! This is your friendly expense splitter bot.')

async def help_command(update: Update, context: CallbackContext) -> None:
    await update.message.reply_text("I am your friendly splitter bot to help you and your friends split expenses easily and effectively.")

# Adding our bot to a group
async def chat_member(update:  Update, context: CallbackContext) -> None:
    result = update.my_chat_member
    print("update being printed:-",update,"\n")
    print("context is printed here:-",context,"\n")
    if result.new_chat_member.status == 'member' and result.new_chat_member.user.id == context.bot.id:
        await context.bot.send_message(
            chat_id=result.chat.id,
            text="Hey, Thanks for adding me to the group!\n"
                 "Please! Give me Admin rights to proceed further.\n"
                 "Type /help for guidance."
        )


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
        dp = Application.builder().token(TELEGRAM_KEY).build()
        
        # Register handlers
        dp.add_handler(CommandHandler("start", start))
        dp.add_handler(CommandHandler("help", help_command))
        dp.add_handler(ChatMemberHandler(chat_member))

        # Log all errors
        dp.add_error_handler(error)
        
        # Start the Bot
        dp.run_polling()
        

if __name__ == '__main__':
    main()

class Command(BaseCommand):
    def handle(self,*args,**options):    
        main()
