"""
Sends a DM-style notification to a client via LinkedIn.

LinkedIn doesn't really have a public "send a DM" API for regular accounts -
this uses the messaging endpoint that's only available on partnership-tier
access, so for most setups this will need to fall back to a connection
request + manual message, or just skip LinkedIn and let it go through email
instead. Leaving this in because the partnership scope is something I'm
applying for, not because it works out of the box for everyone.
"""

import os
import requests
from dotenv import load_dotenv

load_dotenv()

ACCESS_TOKEN = os.getenv("LINKEDIN_ACCESS_TOKEN")


def send_message(recipient_urn: str, text: str) -> dict:
    if not ACCESS_TOKEN:
        raise RuntimeError("LINKEDIN_ACCESS_TOKEN not set, can't send message")

    resp = requests.post(
        "https://api.linkedin.com/v2/messages",
        headers={
            "Authorization": f"Bearer {ACCESS_TOKEN}",
            "Content-Type": "application/json",
        },
        json={
            "recipients": [recipient_urn],
            "body": text,
        },
        timeout=15,
    )

    if resp.status_code not in (200, 201):
        # not raising hard here - LinkedIn DM failing shouldn't block the
        # rest of the booking flow, caller decides whether to fall back
        return {"ok": False, "status": resp.status_code, "body": resp.text}

    return {"ok": True}
