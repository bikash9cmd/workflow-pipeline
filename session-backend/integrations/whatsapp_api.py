"""
WhatsApp messages via Twilio's API. Picked Twilio over the raw Meta WhatsApp
Business API because getting a Meta WABA approved for a small project
account was more hassle than it was worth - Twilio's sandbox got me testing
the same day.
"""

import os
from twilio.rest import Client
from dotenv import load_dotenv

load_dotenv()

ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID")
AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")
FROM_NUMBER = os.getenv("TWILIO_WHATSAPP_FROM")

_client = None


def _get_client() -> Client:
    global _client
    if _client is None:
        _client = Client(ACCOUNT_SID, AUTH_TOKEN)
    return _client


def send_message(to_number: str, text: str) -> dict:
    """to_number should be E.164, e.g. +9779812345678. We add the
    'whatsapp:' prefix here so callers don't need to remember to."""
    client = _get_client()

    message = client.messages.create(
        from_=FROM_NUMBER,
        to=f"whatsapp:{to_number}",
        body=text,
    )

    return {"sid": message.sid, "status": message.status}
