from youtube_handler import(
    dur_parser,
    clear_channels,
    channel_list,
    get_channels,
    get_notify_history,
    remove_channel,
    save_channel_into_table,
    save_notification,
    video_info
)
from logs_handler import LOGS

import os
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, MessageHandler, filters
#from subprocess import call
import sqlalchemy as db
import feedparser

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
@user_allowed(sUsers)
async def channel_command(update:Update, context: ContextTypes.DEFAULT_TYPE):
    chatId = update.message.chat_id
    user = update.message.from_user
    msg = str(update.message.text).lower()
    arr = msg.split(' ')
    response = 'wrong commands! \n' \
        '/channel add <channelName> \n or \n' \
        '/channel remove <channelName>'
    if len(arr) == 3:
        if 'add' in arr:
            response = save_channel_into_table(arr[-1], user, chatId)
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
async def channels_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    results = channel_list(context._chat_id)
    response = 'List of Channels \n\n' + results
    await update.message.reply_text(response)

# Lets us use the /restart
@user_allowed(sUsers)
async def clear_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    clear_channels(context._chat_id)
    await update.message.reply_text('Restarted the bot.')

def proper_info_msg(videoId):
    video = video_info(videoId)
    info = video["items"][0]
    channelName = info["snippet"]["channelTitle"]
    videoTitle = info["snippet"]["title"]
    try:
        desc = info["snippet"]["description"]
        if len(desc) > 500:
            desc = desc[:300] + "..."
    except BaseException:
        desc = "Not Found!"
    pub_time = info["snippet"]["publishedAt"].replace("T", " ").replace("Z", " ")
    try:
        thumb = info["snippet"]["thumbnails"]["maxres"]["url"]
    except BaseException:
        thumb = info["snippet"]["thumbnails"]["high"]["url"]
    os.system(f"wget {thumb} -O {thumb.split('/')[-2]}.jpg")
    try:
        dur = dur_parser(info["contentDetails"]["duration"])
    except BaseException:
        dur = "Not Found!"
    text = ""
    text += f"https://www.youtube.com/watch?v={videoId}" + "\n"
    if info["snippet"]["liveBroadcastContent"] == "live":
        text += f"**{channelName} is Live 🔴**\n\n"
        dur = "♾"
    else:
        text += f"**{channelName} Just Uploaded A Video**\n\n"
    text += f"{videoTitle}\n\n"
    text += f"Description - {desc}\n\n"
    text += f"Duration - {dur}\n"
    text += f"Published At - {pub_time}```\n"
    results = []
    results.insert(0, thumb)
    results.insert(1, text)
    return results

async def callback_minute(context: ContextTypes.DEFAULT_TYPE):
    results = get_channels()
    if results:
        for res in results:
            chId = res[4]
            chatId = res[1]
            feed_url = f"https://www.youtube.com/feeds/videos.xml?channel_id={chId}"
            feed = feedparser.parse(feed_url)
            videoId = feed.entries[0].yt_videoid
            videos = proper_info_msg(videoId)
            notify = get_notify_history(chatId=chatId, videoId=videoId)
            if not notify:
                save_notification(chatId=chatId, videoId=videoId)
                await context.bot.send_photo(
                    chat_id=chatId,
                    photo=videos[0],
                    caption=videos[1]
                )

if __name__ == '__main__':
    print('Starting up bot...')
    app = ApplicationBuilder().token(TOKEN).build()
    job_queue = app.job_queue

    # Commands
    app.add_handler(CommandHandler('start', start_command))
    app.add_handler(CommandHandler('channels', channels_command))
    app.add_handler(CommandHandler('channel', channel_command))
    app.add_handler(CommandHandler('clear', clear_command))
    app.add_handler(CommandHandler('help', help_command))
    
    job_queue.run_repeating(callback_minute, interval=60, first=10)

    # Messages
    '''app.add_handler(MessageHandler(filters.ALL, handle_message))'''

    app.run_polling()
