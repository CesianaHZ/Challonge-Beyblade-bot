import os
from dotenv import load_dotenv

load_dotenv()

DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
CHALLONGE_USERNAME = os.getenv("CHALLONGE_USERNAME")
CHALLONGE_API_KEY = os.getenv("CHALLONGE_API_KEY")