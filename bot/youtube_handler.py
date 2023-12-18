import os
import urllib.request
import json
from dotenv import load_dotenv

from googleapiclient.discovery import build
from datetime import datetime
import sqlalchemy as db, sqlite3
from sqlalchemy.exc import SQLAlchemyError

from logs_handler import LOGS

load_dotenv()

api_service_name = "youtube"
api_version = "v3"
YT_API_KEY = os.getenv('YT_API_KEY')

try:
    YT = build(api_service_name, api_version, developerKey=YT_API_KEY)
    LOGS.info("Successfully Connected With YouTube...")
except BaseException as er:
    LOGS.info(str(er))
    exit()

engine = db.create_engine("sqlite:///db.sqlite3")
connection = engine.connect()
metadata = db.MetaData()

try:
    channels = db.Table('channels',
                        metadata,
                        db.Column('id', db.Integer, primary_key=True),
                        db.Column('chat_id', db.String),
                        db.Column('user_id', db.Integer),
                        db.Column('user_name', db.String),
                        db.Column('channel_id', db.Integer),
                        db.Column('channel_name', db.String),
                        db.Column('created_at', db.DateTime, default=datetime.now)
                        )
    notifications = db.Table('notifications',
                        metadata,
                        db.Column('id', db.Integer, primary_key=True),
                        db.Column('chat_id', db.String),
                        db.Column('video_id', db.String),
                        db.Column('published_at', db.DateTime),
                        db.Column('created_at', db.DateTime, default=datetime.now)
                        )
    metadata.create_all(engine)
except SQLAlchemyError as e:
    error = str(e.orig)

def dur_parser(_time):
    if not _time:
        return "Not Found!"
    xx = _time.replace("PT", "")
    return xx.lower()

# Clear table channels
def clear_channels(chatId):
    con = sqlite3.connect('db.sqlite3')
    c = con.cursor()
    query = """DELETE FROM channels WHERE chat_id = ?"""
    c.execute(query, (chatId,))
    LOGS.info('Deleted all rows from channels table')
    con.commit()

# Get Channel Information by Name
def get_channel_info_byName(channelName):
    url = 'https://youtube.googleapis.com/youtube/v3/search?part=snippet&q='+channelName+'&type=channel&key='+YT_API_KEY
    response = urllib.request.urlopen(url)
    data = json.load(response)

    if not data['items']:
        return None
    res = data['items'][0]
    channelId = res['id']['channelId']

    info = YT.channels().list(part="statistics,snippet,contentDetails", id=channelId).execute()
    return info['items'][0]

# Save channel
def save_channel_into_table(channelName, user, chatId):
    con = sqlite3.Connection('db.sqlite3')
    cursor = con.cursor()
    
    now = datetime.now()
    info = get_channel_info_byName(channelName)
    if (info == None):
        return "Sorry, I can't find the channel"
    else:
        chid = info['id']
        sql_select_query = """select channel_id, channel_name from channels where channel_id = ? and chat_id = ?"""
        record = cursor.execute(sql_select_query, (chid, chatId,))
        result = record.fetchone()
        if not result:
            query = db.insert(channels).values(
                chat_id=chatId,
                user_id=user.id,
                user_name=user.username,
                channel_id=chid,
                channel_name=channelName,
                created_at=now
            )
            ResultProxy = connection.execute(query)
            LOGS.info(ResultProxy.inserted_primary_key)
            return f'Channel {channelName} has been added.'
        else:
            return 'The channel is already on the list'

# Delete/Remove channel by id
def remove_channel(id):
    con = sqlite3.connect('db.sqlite3')
    cursor = con.cursor()
    sql_delete_query = """DELETE FROM channels WHERE id=?"""
    cursor.execute(sql_delete_query, (id,))
    if cursor.rowcount > 0:
        response = f'Record id {id} deleted successfully'
        con.commit()
    else:
        response = f'No channel found with id: {id}'
    con.close()
    return response

# Get channels
def get_channels():
    con = sqlite3.Connection('db.sqlite3')
    cursor = con.cursor()
    cursor.execute("SELECT * FROM channels")
    results = cursor.fetchall()
    return results

# Channel List
def channel_list(chatId):
    con = sqlite3.Connection('db.sqlite3')
    cursor = con.cursor()
    sql_query = """select * from channels where chat_id = ?"""
    cursor.execute(sql_query, (chatId,))
    results = cursor.fetchall()
    res = []
    for row in results:
        res.append(f"Id: {row[0]}  Name: {row[5]}")
    return "\n".join(map(str, res))

# Saving Notification history
def save_notification(chatId, videoId):
    query = db.insert(notifications).values(chat_id=chatId, video_id=videoId)
    connection.execute(query)
    LOGS.info(f'Save notify video_id: {videoId} for chat_id: {chatId}')

# Get Notification history
def get_notify_history(chatId, videoId):
    con = sqlite3.Connection('db.sqlite3')
    cursor = con.cursor()
    query = """SELECT * FROM notifications WHERE chat_id = ? AND video_id = ?"""
    cursor.execute(query, (chatId, videoId,))
    result = cursor.fetchone()
    print(result)
    return result

# Get video info
def video_info(_id):
    return YT.videos().list(part="snippet,contentDetails", id=_id).execute()