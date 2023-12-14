import asyncio
import os
import sys
import urllib.request
import json
import numpy as np
from dotenv import load_dotenv

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from googleapiclient.discovery import build
from datetime import datetime
import sqlalchemy as db, sqlite3

from logs_handler import LOGS

load_dotenv()

api_service_name = "youtube"
api_version = "v3"
YT_API_KEY = os.getenv('YT_API_KEY')

sch = AsyncIOScheduler()
MEMORY = []

try:
    YT = build(api_service_name, api_version, developerKey=YT_API_KEY)
    LOGS.info("Successfully Connected With YouTube...")
except BaseException as er:
    LOGS.info(str(er))
    exit()

engine = db.create_engine("sqlite:///db.sqlite3")
connection = engine.connect()
metadata = db.MetaData()

channelTable = db.Table('channels',
                        metadata,
                        db.Column('id', db.Integer, primary_key=True),
                        db.Column('user_id', db.Integer),
                        db.Column('user_name', db.String),
                        db.Column('channel_id', db.Integer),
                        db.Column('channel_name', db.String),
                        db.Column('created_at', db.DateTime, default=datetime.now)
                        )

try:
    channels = db.Table('channels', metadata, autoload=True, autoload_with=engine)
except:
    channels = channelTable
    metadata.create_all(engine)

def dur_parser(_time):
    if not _time:
        return "Not Found!"
    xx = _time.replace("PT", "")
    return xx.lower()

# Clear table channels
def clear_channels():
    try:
        channels = db.Table('channels', metadata, autoload=True, autoload_with=engine)
    except:
        channels = channelTable
        metadata.create_all(engine)
    # delete all rows
    query = db.delete(channels)
    ResultProxy = connection.execute(query)
    LOGS.info('Deleted all rows from channels table')

# Get Channel Information
def channel_info(channelName):
    url = 'https://youtube.googleapis.com/youtube/v3/search?part=snippet&q='+channelName+'&type=channel&key='+YT_API_KEY
    response = urllib.request.urlopen(url)
    data = json.load(response)

    if not data['items']:
        return None

    for key in data['items']:
        channelId = key['id']['channelId']

    info = YT.channels().list(part="statistics,snippet,contentDetails", id=channelId).execute()
    return info['items'][0]

# Save channel
def save_channel(channelName, user):
    con = sqlite3.Connection('db.sqlite3')
    cursor = con.cursor()
    
    now = datetime.now()
    info = channel_info(channelName)
    if (info == None):
        return "Sorry, I can't find the channel"
    else:
        chid = info['id']
        sql_select_query = """select channel_id, channel_name from channels where channel_id = ?"""
        record = cursor.execute(sql_select_query, (chid,))
        if record.fetchone() is None:
            query = db.insert(channels).values(user_id=user.id, user_name=user.username, channel_id=chid, channel_name=channelName, created_at=now)
            ResultProxy = connection.execute(query)
            LOGS.info(ResultProxy.inserted_primary_key)
            return f'Channel {channelName} has been added.'
        else:
            return 'The channel is already on the list'