import os
import logging
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
from subprocess import call

print('Starting up bot...')

load_dotenv()

TOKEN = os.getenv('TELEGRAM_TOKEN')
BOTNAME = os.getenv('BOTNAME')
sUsers = os.getenv('SUPERUSERS')

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# Create a decorator that takes users as an argument and if the user is in the list, it will run the function
def user_allowed(susers):
    def decorator(func):
        async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE):
            user = update.message.from_user
            logging.info(f'User {user.username} is trying to access the bot. id: {user.id}, message: {update.message.text}')
            if user.username in sUsers:
                await func(update, context)
            else:
                await update.message.reply_text("Your are not allowed to use this command")
        return wrapper
    return decorator

# Let us use the /start command
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(f'Hello {update.effective_user.first_name} I\'m a bot')

# Let us user the /help command
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text('This is help descriptions')

@user_allowed(sUsers)
async def channelinfo_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text('List of Channel info')


if __name__ == '__main__':
    app = ApplicationBuilder().token(TOKEN).build()

    # Commands
    app.add_handler(CommandHandler('start', start_command))
    app.add_handler(CommandHandler('channelinfo', channelinfo_command))
    app.add_handler(CommandHandler('help', help_command))

    app.run_polling()
