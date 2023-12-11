import os
from datetime import datetime
import sqlalchemy as db


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

# Handle response message save to Channels table
def handle_response(text, user, message_id) -> str:
    splitTexts = str.split(text)
    print(splitTexts)
    print('addchannel' in splitTexts)
    if ('addchannel' in splitTexts):
        response = 'dev handle response process..'
    else:
        # Need to create help commands response
        response = 'Wrong commands!'
    return response