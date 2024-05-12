from telegram import Update, Bot,ChatMember
from telegram.ext import CommandHandler, CallbackContext, ChatMemberHandler,ContextTypes
import logging
from django.core.management.base import BaseCommand
# from core_service.settings import TELEGRAM_KEY
from telegram.ext import Application
from expense_service.models.users_model import User
from expense_service.models.groups_model import Groups
from expense_service.models.group_members_model import GroupMembers
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
    logger.info("here")
    await update.message.reply_text('Hello! This is your friendly expense splitter bot.')

async def help_command(update: Update, context: CallbackContext) -> None:
    await update.message.reply_text("Please follow the youtube tutorial to give me admin rights!\n https://youtu.be/h4AwKkES0Xg?si=THlM0mPBfplNGu3M")

# Adding our bot to a group and checking for permission change
async def chat_member(update:  Update, context: CallbackContext) -> None:
    result = update.my_chat_member
    chat_id = update.my_chat_member.chat.id
    logger.info("update being logged:-",update,"\n")
    logger.info("context is logged here:-",context,"\n")
    # handling chatbot addition in group and admin privileges
    if result.old_chat_member.status in ('left', 'kicked') and result.new_chat_member.status == 'member' and result.new_chat_member.user.id == context.bot.id:
        await context.bot.send_message(
            chat_id=result.chat.id,
            text="Hey, Thanks for adding me to the group!\n"
                 "Please! Give me Admin rights to proceed further.\n"
                 "Type /help for guidance."
        )
    elif result.new_chat_member.status == 'administrator' and result.new_chat_member.user.id == context.bot.id:
        if result.old_chat_member.status != 'administrator':
            await context.bot.send_message(
                chat_id=result.chat.id,
                text="Thanks for making me an admin!\n"
                     "Requesting all group members to respond with /start" 
            )
    elif result.old_chat_member.status == 'administrator' and result.new_chat_member.status != 'administrator':
        await context.bot.send_message(
            chat_id=result.chat.id,
            text="Removed admin rights. Please make admin again to function properly."
        )
    # to create a user entry for the person adding the bot to the group
    telegram_user = update.effective_user
    logger.info("telegram_user",telegram_user)
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
            logger.info("New user added to the database.%s",user.username)
            await context.bot.send_message(
                chat_id=update.my_chat_member.chat.id,
                text=f"Added user {user.first_name} to DB"
            )
        else:
            logger.info("User information updated.")
    # to create a group entry 
    chat_id = update.my_chat_member.chat.id
    group_name = update.my_chat_member.chat.title
    admins = await context.bot.get_chat_administrators(chat_id)
    for admin in admins:
        if admin.status == 'creator':
            created_by = admin.user.id
    user_pk = await sync_to_async(User.objects.get)(telegram_user_id=created_by)
    defaults = {
        'group_name': group_name,
        'created_by': user_pk
    }
    group, group_created = await sync_to_async(Groups.objects.get_or_create)(
        id = str(chat_id),
        defaults=defaults
    )
    if group_created:
        logger.info("Group Added.")
    else: 
        logger.info("Group Updated.")
    try:
        import traceback
        group_member, member_created = await sync_to_async(GroupMembers.objects.get_or_create)(
            group=group,
            user=user_pk
        )
        if member_created:
            logger.info("Group Member Added.")
        else: 
            logger.info("Group Member Updated.")
    except Exception as e:
        traceback.print_exc()
        print("exception:---",e)
    


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
        logger.error(f"Error fetching admins: {e}")

# Message handler
async def echo(update: Update, context: CallbackContext) -> None:
    text = update.message.text
    await update.message.reply_text(f'You said: {text}')

# to add a new expense
async def add_expense(update: Update, context: CallbackContext) -> None:
    try:
        # Expected message format: /add <amount> <description>
        args = update.message.text.split(maxsplit=2)
        if len(args) < 3:
            await update.message.reply_text("Usage: /add <amount> <description>")
            return
        amount = float(args[1])
        description = args[2]
        # calling the django function to handle entries
        await update.message.reply_text(f"Expense Added: {amount} {description}")
    except Exception as e:
        logger.error(f"Error adding expense: {str(e)}")
        await update.message.reply_text("Failed to add expense. Please try again")

# Error handler
def error(update: Update, context: CallbackContext) -> None:
    logger.warning('Update "%s" caused error "%s"', update, context.error)

# Main function to start the bot
def main() -> None:
    bot = initialize_bot()
    if bot:
        logger.info(bot.getMe())
        dp = Application.builder().token(TELEGRAM_KEY).build()
        
        # Register handlers
        dp.add_handler(CommandHandler("start", start))
        dp.add_handler(CommandHandler("help", help_command))
        dp.add_handler(ChatMemberHandler(chat_member))
        dp.add_handler(CommandHandler("admins", show_admins))
        dp.add_handler(CommandHandler("add", add_expense))

        # Log all errors
        dp.add_error_handler(error)
        
        # Start the Bot
        dp.run_polling()
        
  
if __name__ == '__main__':
    main()

class Command(BaseCommand):
    def handle(self,*args,**options):    
        main()
