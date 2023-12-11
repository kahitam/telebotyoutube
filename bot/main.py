import os
import logging
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, MessageHandler, filters
from subprocess import call
from yt_handler import handle_response
import sqlalchemy as db

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
    
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message_type = update.message.chat.type
    text = str(update.message.text).lower()
    user = update.message.from_user
    message_id = update.message.message_id
    response = ''
    
    # Print a log for debugging
    print(f'User ({update.message.chat.id}) says: "{text}" in: {message_type}')
    
    if text.startswith(BOTNAME):
        print('got the bot name: ' + BOTNAME)
        response = handle_response(text, user, message_id)
    await update.message.reply_text(response)

# Lets us use the /channelinfo
@user_allowed(sUsers)
async def channelinfo_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text('List of Channel info')

# Lets us use the /restart
@user_allowed(sUsers)
async def restart_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # delete the db.sqlite3 file
    engine = db.create_engine("sqlite:///db.sqlite3")
    connection = engine.connect()
    metadata = db.MetaData()

    try:
        channels = db.Table('channels', metadata, autoload=True, autoload_with=engine)
    except:
        channels = db.Table('channels',
                        metadata,
                        db.Column('id', db.Integer, primary_key=True),
                        db.Column('user_id', db.Integer),
                        db.Column('user_name', db.String),
                        db.Column('channel_id', db.Integer),
                        db.Column('channel_name', db.String),
                        db.Column('created_at', db.DateTime, default=datetime.now)
                        )
    metadata.create_all(engine)

    # delete all rows
    query = db.delete(channels)
    ResultProxy = connection.execute(query)
    print('Deleted all rows from channels table')

    await update.message.reply_text('Restarted the bot.')


if __name__ == '__main__':
    app = ApplicationBuilder().token(TOKEN).build()

    # Commands
    app.add_handler(CommandHandler('start', start_command))
    app.add_handler(CommandHandler('channelinfo', channelinfo_command))
    app.add_handler(CommandHandler('restart', restart_command))
    app.add_handler(CommandHandler('help', help_command))
    
    # Messages
    app.add_handler(MessageHandler(filters.ALL, handle_message))

    app.run_polling()
