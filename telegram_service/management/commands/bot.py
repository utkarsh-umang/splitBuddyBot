from telegram import Update, Bot,ChatMember
from telegram.ext import CommandHandler, CallbackContext, ChatMemberHandler,ContextTypes, MessageHandler, filters
import logging
from django.core.management.base import BaseCommand
from django.db import IntegrityError
from telegram.ext import Application
from decimal import Decimal
from functools import wraps
from expense_service.models.users_model import User
from expense_service.models.groups_model import Groups
from expense_service.models.group_members_model import GroupMembers
from expense_service.models.expenses_model import Expenses
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

# Decorators
def ensure_user_exists(func):
    @wraps(func)
    async def wrapper(update: Update, context: CallbackContext, *args, **kwargs):
        telegram_user = update.effective_user
        if telegram_user:
            try:
                user, created = await sync_to_async(User.objects.update_or_create)(
                    telegram_user_id=str(telegram_user.id),
                    defaults={
                        'first_name': telegram_user.first_name,
                        'last_name': telegram_user.last_name or '',
                        'user_name': telegram_user.username or f"user_{telegram_user.id}"
                    }
                )
                if created:
                    logger.info(f"New User added to the database: {user.user_name}")
                else:
                    logger.info(f"User Information updated: {user.user_name}")
            except IntegrityError as e:
                logger.error(f"IntegrityError while creating/updating user: {str(e)}")
                await update.message.reply_text("There was an error processing your request. Please try again later.")
                return
        return await func(update, context, *args, **kwargs)
    return wrapper

# Command handlers
@ensure_user_exists
async def start_command(update: Update, context: CallbackContext) -> None:
    try:
        if update.effective_chat.type == 'private':
            await update.message.reply_text(
                "Hello! I'm your friendly expense splitter bot. "
                "To use me, please add me to a group and make me an admin. "
                "Then, you can use /help in the group to see available commands."
            )
        else:
            group_id = str(update.effective_chat.id)
            user_id = str(update.effective_user.id)
            
            group, _ = await sync_to_async(Groups.objects.get_or_create)(id=group_id)
            user = await sync_to_async(User.objects.get)(telegram_user_id=user_id)
            
            _, created = await sync_to_async(GroupMembers.objects.get_or_create)(
                group=group,
                user=user
            )
            
            if created:
                await update.message.reply_text(
                    f"Welcome to the expense splitting group, {update.effective_user.first_name}! "
                    "You've been added as a member. Use /help to see available commands."
                )
            else:
                await update.message.reply_text(
                    f"Welcome back, {update.effective_user.first_name}! "
                    "You're already a member of this expense splitting group. "
                    "Use /help to see available commands."
                )
    except Exception as e:
        logger.error(f"Error in start_command: {str(e)}")
        await update.message.reply_text("An error occurred. Please try again or contact support.")

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
        group_id = str(update.message.chat_id)
        group = await sync_to_async(Groups.objects.get)(id=group_id)
        members = await sync_to_async(list)(GroupMembers.objects.filter(group=group))
        if not members:
            await update.message.reply_text("No members found in this group. Please ensure all members have used /start.")
            return
        group_members = "List of all the members in the group!\n\n"
        for member in members:
            user = await sync_to_async(User.objects.get)(id=member.user_id)
            group_members += f"{user.first_name} (@{user.user_name})\n"
        group_members += "If anyone is missing please press /start"
        await update.message.reply_text(group_members)
    except Groups.DoesNotExist:
        await update.message.reply_text("This group is not registered. Please remove and re-add the bot to the group.")
    except User.DoesNotExist:
        await update.message.reply_text("There was an error fetching user information. Please try /start again.")
    except Exception as e:
        logger.error(f"Error in group_info_command: {str(e)}")
        await update.message.reply_text(f"An error occurred: {str(e)}")

@ensure_user_exists
async def add_expense_command(update: Update, context: CallbackContext) -> None:
    try:
        if update.effective_chat.type == 'private':
            await update.message.reply_text("This command can only be used in a group. Please add me to a group first!")
            return
        # Expected message format: /add <amount> <description>
        args = update.message.text.split(maxsplit=2)
        if len(args) < 3:
            await update.message.reply_text("Usage: /add_expense <amount> <description>")
            return
        amount = Decimal(args[1])
        description = args[2]
        group_id = str(update.effective_chat.id)
        user_id = str(update.effective_user.id)

        group = await sync_to_async(Groups.objects.get)(id=group_id)
        user = await sync_to_async(User.objects.get)(telegram_user_id=user_id)

        is_member = await sync_to_async(GroupMembers.objects.filter(group=group, user=user).exists)()
        if not is_member:
            await update.message.reply_text("You are not registered as a member of this group. Please use /start first.")
            return
        
        expense = await sync_to_async(Expenses.objects.create)(
            group=group,
            paid_by=user,
            amount=amount,
            description=description,
            category=''
        )
        await update.message.reply_text(f"Expense Added: {amount} for {description}")
        await display_group_balances(update, context)
    except Groups.DoesNotExist:
        await update.message.reply_text("This group is not registered for expense splitting. Please remove and re-add the bot to the group.")
    except User.DoesNotExist:
        await update.message.reply_text("You are not registered as a user. Please use /start first.")
    except GroupMembers.DoesNotExist:
        await update.message.reply_text("You are not registered as a member of this group. Please use /start in this group.")
    except ValueError:
        await update.message.reply_text("Invalid amount. Please enter a numeric value.")
    except Exception as e:
        logger.error(f"Error adding expense: {str(e)}")
        await update.message.reply_text(f"Failed to add expense: {str(e)}")

async def display_group_balances(update: Update, context: CallbackContext):
    group_id = str(update.effective_chat.id)
    try:
        group = await sync_to_async(Groups.objects.get)(id=group_id)
        expenses = await sync_to_async(list)(Expenses.objects.filter(group=group))
        members = await sync_to_async(list)(GroupMembers.objects.filter(group=group))
        
        total_expenses = sum(expense.amount for expense in expenses)
        num_members = len(members)
        if num_members == 0:
            await update.message.reply_text("No members in this group.")
            return
        
        per_person_share = Decimal(total_expenses) / Decimal(num_members)
        
        balances = {}
        for member in members:
            user = await sync_to_async(User.objects.get)(id=member.user_id)
            user_expenses = sum(expense.amount for expense in expenses if expense.paid_by_id == user.id)
            balance = Decimal(user_expenses) - per_person_share
            balances[user] = balance
        
        balance_message = "Current group balances:\n\n"
        for user, balance in balances.items():
            if balance > 0:
                balance_message += f"{user.first_name} is owed {balance:.2f}\n"
            elif balance < 0: 
                balance_message += f"{user.first_name} owes {-balance:.2f}\n"
            else:
                balance_message += f"{user.first_name} is settled up\n"
        
        await update.message.reply_text(balance_message)
    except Groups.DoesNotExist:
        await update.message.reply_text("This group is not registered for expense splitting.")
    except Exception as e:
        logger.error(f"Error displaying group balances: {str(e)}")
        await update.message.reply_text(f"Failed to display balances: {str(e)}")

async def view_balances_command(update: Update, context: CallbackContext) -> None:
    await display_group_balances(update, context)

@ensure_user_exists
async def list_groups_command(update: Update, context: CallbackContext) -> None:
    user_id = str(update.effective_user.id)
    user = await sync_to_async(User.objects.get)(telegram_user_id=user_id)
    group_memberships = await sync_to_async(list)(GroupMembers.objects.filter(user=user).select_related('group'))
    if not group_memberships:
        await update.message.reply_text("You are not a member of any expense-splitting groups yet.")
    else:
        group_list = "You are a member of the following groups:\n\n"
        for membership in group_memberships:
            group_list += f"- {membership.group.group_name}\n"
        await update.message.reply_text(group_list)

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
def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    logger.error(f"Exception while handling an update: {context.error}")
    if update is None or not isinstance(update, Update):
        return
    if update.effective_message:
        error_message = "An error occurred while processing your request. Please try again later."
        update.effective_message.reply_text(error_message)

commands = {
    'start': 'To learn how to integrate me as your expense splitter!',
    'help': 'To show list of available Commands',
    'make_me_admin': 'Learn how to give admin rights to the bot',
    'show_admins': 'To list the admins of the Group',
    'add_expense': 'To add a new Expense. Usage: /add_expense <amount> <description>',
    'group_info': 'To check the members of the group in our DB',
    'view_balances': 'View Current group balances',
    'list_groups': 'List all groups you are a part of'
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
        dp.add_error_handler(error_handler)
        
        # Start the Bot
        dp.run_polling()
        
  
if __name__ == '__main__':
    main()

class Command(BaseCommand):
    def handle(self,*args,**options):    
        main()
