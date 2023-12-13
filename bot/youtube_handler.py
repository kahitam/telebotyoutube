import asyncio
import os
import sys
import urllib.request
import json
from dotenv import load_dotenv

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from googleapiclient.discovery import build
from datetime import datetime
import sqlalchemy as db

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

def dur_parser(_time):
    if not _time:
        return "Not Found!"
    xx = _time.replace("PT", "")
    return xx.lower()

# Get Channel Information
def channel_info(channelName):
    url = 'https://youtube.googleapis.com/youtube/v3/search?part=snippet&q='+channelName+'&type=channel&key='+YT_API_KEY
    response = urllib.request.urlopen(url)
    data = json.load(response)
    for key in data['items']:
        channelId = key['id']['channelId']

    info = YT.channels().list(part="statistics,snippet,contentDetails", id=channelId).execute()
    return info
    #return (
    #    YT.channels().list(part="statistics,snippet,contentDetails", id=channelId).execute()
    #)


# Handle response message save to Channels table
def handle_response(text, user, message_id) -> str:
    splitTexts = str.split(text)
    channelName = splitTexts[-1]
    if ('addchannel' in splitTexts):
        info = channel_info(channelName)
        print(info)
        response = 'dev handle response process..'
    else:
        # Need to create help commands response
        response = 'Wrong commands!'
    return response