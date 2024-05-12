from telegram import Update, Bot,ChatMember
from telegram.ext import CommandHandler, CallbackContext, ChatMemberHandler,ContextTypes
import logging
from django.core.management.base import BaseCommand
# from core_service.settings import TELEGRAM_KEY
from telegram.ext import Application
from expense_service.models.users_model import User
from expense_service.models.groups_model import Groups
from asgiref.sync import sync_to_async


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
    chat_id = update.my_chat_member.chat.id
    
    print("update being printed:-",update,"\n")
    print("context is printed here:-",context,"\n")
    if result.new_chat_member.status == 'member' and result.new_chat_member.user.id == context.bot.id:
        print("result",result)
        await context.bot.send_message(
            chat_id=result.chat.id,
            text="Hey, Thanks for adding me to the group!\n"
                 "Please! Give me Admin rights to proceed further.\n"
                 "Type /help for guidance."
        )
    else:
        new_status = update.my_chat_member.new_chat_member.status
        if new_status == ChatMember.ADMINISTRATOR:
            await context.bot.send_message(
                chat_id=update.my_chat_member.chat.id,
                text="Thank you for the admin rights! Now, I can manage the group more effectively. Type /help to see what I can do."
            )
    
    telegram_user = update.effective_user
    print("telegram_user",telegram_user)
    if telegram_user:
        defaults = {
            'first_name': telegram_user.first_name,
            'last_name': telegram_user.last_name or '',
            'user_name' : telegram_user.username or ''
        }
        user,created = await sync_to_async(User.objects.update_or_create)(
            telegram_user_id = str(telegram_user.id),
            defaults=defaults
        )
        if created:
            print("New user added to the database.%s",user.username)
            await context.bot.send_message(
                chat_id=update.my_chat_member.chat.id,
                text=f"Added user {user.first_name} to DB"
            )
        else:
            print("User information updated.")
    
    group_id = update.my_chat_member.chat.id
    group_name = update.my_chat_member.chat.title
    admins = await context.bot.get_chat_administrators(chat_id)
    for admin in admins:
        if admin.status == 'creator':
            created_by = admin.user.id
    user_pk =await sync_to_async(User.objects.get)(telegram_user_id=created_by)
    defaults = {
        'group_name': group_name,
        'created_by': user_pk
    }
    group_id,created = await sync_to_async(Groups.objects.get_or_create)(
        id = str(group_id),
        defaults=defaults
    )

    if created:
        print("group name updated too")


#show admins
async def show_admins(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    try:
        # Fetching the list of administrators in the chat
        admins = await context.bot.get_chat_administrators(chat_id)
        admins_info = []
        for admin in admins:
            # Check if the administrator's status is 'creator'
            status = "Creator" if admin.status == 'creator' else "Administrator"
            admins_info.append(f"{admin.user.name} ({status})")
        # Sending the list of administrators to the chat
        await update.message.reply_text("Admins in this chat:\n" + "\n".join(admins_info))
    except Exception as e:
        await update.message.reply_text("Failed to fetch admins.")
        print(f"Error fetching admins: {e}")

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
        dp.add_handler(CommandHandler("admins", show_admins))
        # Log all errors
        dp.add_error_handler(error)
        
        # Start the Bot
        dp.run_polling()
        
  
if __name__ == '__main__':
    main()

class Command(BaseCommand):
    def handle(self,*args,**options):    
        main()
