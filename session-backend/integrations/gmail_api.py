"""
Sends emails via Gmail API using a long-lived refresh token (so this can
run unattended on a cron / server without anyone re-clicking an OAuth
consent screen every hour).
"""

import os
import base64
from email.mime.text import MIMEText
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from dotenv import load_dotenv

load_dotenv()

CLIENT_ID = os.getenv("GMAIL_CLIENT_ID")
CLIENT_SECRET = os.getenv("GMAIL_CLIENT_SECRET")
REFRESH_TOKEN = os.getenv("GMAIL_REFRESH_TOKEN")
SENDER = os.getenv("GMAIL_SENDER_ADDRESS")

TOKEN_URI = "https://oauth2.googleapis.com/token"


def _get_service():
    creds = Credentials(
        token=None,
        refresh_token=REFRESH_TOKEN,
        client_id=CLIENT_ID,
        client_secret=CLIENT_SECRET,
        token_uri=TOKEN_URI,
    )
    return build("gmail", "v1", credentials=creds)


def send_email(to_address: str, subject: str, body_text: str) -> dict:
    service = _get_service()

    message = MIMEText(body_text)
    message["to"] = to_address
    message["from"] = SENDER
    message["subject"] = subject

    raw = base64.urlsafe_b64encode(message.as_bytes()).decode()

    sent = service.users().messages().send(
        userId="me", body={"raw": raw}
    ).execute()

    return {"id": sent.get("id")}
