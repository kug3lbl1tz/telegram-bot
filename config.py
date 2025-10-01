import os
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = os.getenv("ADMIN_ID")
ACCESS_USERS = [int(x) for x in os.getenv("REQUEST_ACCESS_ID").split(",")]

# REQUESTS will be populated at startup
REQUESTS = []