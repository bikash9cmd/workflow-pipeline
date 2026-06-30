import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    SECRET_KEY = os.getenv("FLASK_SECRET_KEY", "change-me")
    SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL", "sqlite:///sessions.db")
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # how long before a session a follow-up reminder fires
    FOLLOWUP_HOURS_BEFORE = 24
