"""
Posts to a Discord channel via webhook. This one's the easy one - no oauth
dance, just a POST.
"""

import os
import requests
from dotenv import load_dotenv

load_dotenv()

WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL")


def publish(asset_url: str, caption: str) -> dict:
    payload = {
        "content": f"{caption}\n{asset_url}",
        "username": "Content Bot",
    }

    resp = requests.post(WEBHOOK_URL, json=payload, timeout=15)

    # discord webhooks return 204 with no body on success, which trips up
    # anyone expecting json back the first time they see it
    if resp.status_code not in (200, 204):
        raise RuntimeError(f"Discord publish failed ({resp.status_code}): {resp.text}")

    return {"status_code": resp.status_code}
