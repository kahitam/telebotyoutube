import os
import requests
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv('TELEGRAM_TOKEN')
url = f"https://api.telegram.org/bot{TOKEN}/getUpdates"
print(requests.get(url).json())