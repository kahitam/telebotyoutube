import os
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, MessageHandler, filters
from subprocess import call
import sqlalchemy as db

from youtube_handler import save_channel, clear_channels, channel_list, remove_channel
from logs_handler import LOGS

print('Starting up bot...')

load_dotenv()

TOKEN = os.getenv('TELEGRAM_TOKEN')
BOTNAME = os.getenv('BOTNAME')
sUsers = os.getenv('SUPERUSERS')

# Create a decorator that takes users as an argument and if the user is in the list, it will run the function
def user_allowed(susers):
    def decorator(func):
        async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE):
            user = update.message.from_user
            LOGS.info(f'User {user.username} is trying to access the bot. id: {user.id}, message: {update.message.text}')
            if user.username in sUsers:
                await func(update, context)
            else:
                await update.message.reply_text("Your are not allowed to use this command")
        return wrapper
    return decorator

# Let us use the /start command
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(f'Hello {update.effective_user.first_name} I\'m a bot')

# Let us use the /channel command
# /channel add
# /channel remove
async def channel_command(update:Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.message.from_user
    msg = str(update.message.text).lower()
    arr = msg.split(' ')
    response = 'wrong commands! \n' \
        '/channel add <channelName> \n or \n' \
        '/channel remove <channelName>'
    if len(arr) == 3:
        if 'add' in arr:
            response = save_channel(arr[-1], user)
        if 'remove' in arr:
            print(arr[-1])
            response = remove_channel(arr[-1])
    await update.message.reply_text(response)

# Let us user the /help command
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text('This is help descriptions')

# Handle body messsage
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    response = 'body message...'
    await update.message.reply_text(response)

# Lets us use the /channels
@user_allowed(sUsers)
async def channels_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    channel_list()
    await update.message.reply_text('List of Channel info')

# Lets us use the /restart
@user_allowed(sUsers)
async def clear_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    clear_channels()
    await update.message.reply_text('Restarted the bot.')


if __name__ == '__main__':
    app = ApplicationBuilder().token(TOKEN).build()

    # Commands
    app.add_handler(CommandHandler('start', start_command))
    app.add_handler(CommandHandler('channels', channels_command))
    app.add_handler(CommandHandler('channel', channel_command))
    app.add_handler(CommandHandler('clear', clear_command))
    app.add_handler(CommandHandler('help', help_command))
    
    # Messages
    app.add_handler(MessageHandler(filters.ALL, handle_message))

    app.run_polling()
