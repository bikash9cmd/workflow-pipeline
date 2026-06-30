"""
Publishes a post to a LinkedIn Company Page using the UGC Posts API.

LinkedIn's rate limits are tight on the free developer tier (basically a
handful of posts per day per app), so this is the one platform where I
actually queue things up instead of firing immediately - see scheduler.py's
PLATFORM_WINDOWS, only one slot per day for linkedin on purpose.
"""

import os
import requests
from dotenv import load_dotenv

load_dotenv()

ACCESS_TOKEN = os.getenv("LINKEDIN_ACCESS_TOKEN")
ORG_URN = os.getenv("LINKEDIN_ORG_URN")  # e.g. "urn:li:organization:12345678"

API_URL = "https://api.linkedin.com/v2/ugcPosts"


def publish(asset_url: str, caption: str) -> dict:
    headers = {
        "Authorization": f"Bearer {ACCESS_TOKEN}",
        "X-Restli-Protocol-Version": "2.0.0",
        "Content-Type": "application/json",
    }

    body = {
        "author": ORG_URN,
        "lifecycleState": "PUBLISHED",
        "specificContent": {
            "com.linkedin.ugc.ShareContent": {
                "shareCommentary": {"text": caption},
                "shareMediaCategory": "ARTICLE",
                "media": [
                    {
                        "status": "READY",
                        "originalUrl": asset_url,
                    }
                ],
            }
        },
        "visibility": {
            "com.linkedin.ugc.MemberNetworkVisibility": "PUBLIC"
        },
    }

    resp = requests.post(API_URL, headers=headers, json=body, timeout=20)

    if resp.status_code not in (200, 201):
        raise RuntimeError(f"LinkedIn publish failed ({resp.status_code}): {resp.text}")

    return {"post_id": resp.headers.get("x-restli-id"), "raw": resp.json() if resp.text else {}}
