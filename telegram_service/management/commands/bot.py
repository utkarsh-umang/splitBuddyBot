from telegram import Update, Bot,ChatMember
from telegram.ext import CommandHandler, CallbackContext, ChatMemberHandler,ContextTypes, MessageHandler, filters
import logging
from django.core.management.base import BaseCommand
# from core_service.settings import TELEGRAM_KEY
from telegram.ext import Application
from expense_service.models.users_model import User
from expense_service.models.groups_model import Groups
from expense_service.models.group_members_model import GroupMembers
from asgiref.sync import sync_to_async
# from expense_service.utils import add_expense_to_db

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
async def start_command(update: Update, context: CallbackContext) -> None:
    await update.message.reply_text('Hello! This is your friendly expense splitter bot. Please add me in a group to begin')

async def help_command(update: Update, context: CallbackContext) -> None:
    help_text = "Available Commands with Usage:\n\n"
    for command, description in commands.items():
        help_text += f"/{command} - {description}\n\n"
    await update.message.reply_text(help_text)

async def unknown_command(update, context):
    await update.message.reply_text("Please type /help for guidance!")

async def make_me_admin_command(update: Update, context: CallbackContext) -> None:
    await update.message.reply_text("Please follow the youtube tutorial to give me admin rights!\n https://youtu.be/h4AwKkES0Xg?si=THlM0mPBfplNGu3M")

async def show_admins_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
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

async def group_info_command(update: Update, context: CallbackContext) -> None:
    try:
        group_members = "List of all the members in the group!\n\n"
        group_id = str(update.message.chat_id)
        members = await sync_to_async(list)(GroupMembers.objects.filter(group=group_id))
        for member in members:
            group_members += str(member.user) + "\n"
        group_members += "If anyone is missing please press /start"
        await update.message.reply_text(group_members)
    except Exception as e:
        await update.message.reply_text("Failed to fetch group information. Please try again.")


async def add_expense_command(update: Update, context: CallbackContext) -> None:
    try:
        # Expected message format: /add <amount> <description>
        args = update.message.text.split(maxsplit=2)
        if len(args) < 3:
            await update.message.reply_text("Usage: /add_expense <amount> <description>")
            return
        amount = float(args[1])
        description = args[2]
        # TODO: the django function to handle entries
        await update.message.reply_text(f"Expense Added: {amount} {description}")
    except Exception as e:
        logger.error(f"Error adding expense: {str(e)}")
        await update.message.reply_text("Failed to add expense. Please try again")

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
            text="Thanks for adding me to the group! You've completed step 1/3 of the process\n\n"
                 "Please! Give me Admin rights to proceed to next step.\n\n"
                 "Type /make_me_admin for guidance."
        )
    elif result.new_chat_member.status == 'administrator' and result.new_chat_member.user.id == context.bot.id:
        if result.old_chat_member.status != 'administrator':
            await context.bot.send_message(
                chat_id=result.chat.id,
                text="Thanks for making me an admin! Step 2 of 3 done\n\n"
                     "Requesting all group members to respond with /start. Last Step!!!\n\n"
                     "Please type /group_help for guidance!\n" 
            )
    elif result.old_chat_member.status == 'administrator' and result.new_chat_member.status != 'administrator':
        await context.bot.send_message(
            chat_id=result.chat.id,
            text="Removed admin rights. Please make admin again to function properly."
        )
    elif result.new_chat_member.status == 'left':
        await context.bot.send_message(
            chat_id=result.chat.id,
            text="Removed from group. Can't function anymore."
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

# Message handler
async def echo(update: Update, context: CallbackContext) -> None:
    text = update.message.text
    await update.message.reply_text(f'You said: {text}')

# Error handler
def error(update: Update, context: CallbackContext) -> None:
    logger.warning('Update "%s" caused error "%s"', update, context.error)

commands = {
    'start': 'To learn how to integrate me as your expense splitter!',
    'help': 'To show list of available Commands',
    'make_me_admin': 'Learn how to give admin rights to the bot',
    'show_admins': 'To list the admins of the Group',
    'add_expense': 'To add a new Expense. Usage: /add_expense <amount> <description>',
    'group_info': 'To check the members of the group in our DB'
}

# Main function to start the bot
def main() -> None:
    bot = initialize_bot()
    if bot:
        logger.info(bot.getMe())
        dp = Application.builder().token(TELEGRAM_KEY).build()
        
        # Register handlers
        dp.add_handler(ChatMemberHandler(chat_member))
        dp.add_handler(CommandHandler("help", help_command))

        for command in commands:
            if command != 'help':
                dp.add_handler(CommandHandler(command, globals()[f"{command}_command"]))

        dp.add_handler(MessageHandler(filters.COMMAND, unknown_command)) # To handle unknown commands
        dp.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, unknown_command)) # To handle non-command texts

        # Log all errors
        dp.add_error_handler(error)
        
        # Start the Bot
        dp.run_polling()
        
  
if __name__ == '__main__':
    main()

class Command(BaseCommand):
    def handle(self,*args,**options):    
        main()
