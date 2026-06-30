"""
Posts to a Facebook Group via the Graph API.

Note: Graph API doesn't let you post to a Group the same way as a Page -
groups need the group's feed endpoint and the token needs the
publish_to_groups permission, which Meta is annoyingly strict about
approving. Took about 2 weeks of app review back and forth to get this
working on a non-test group.
"""

import os
import requests
from dotenv import load_dotenv

load_dotenv()

GRAPH_API_VERSION = "v19.0"
PAGE_TOKEN = os.getenv("FB_PAGE_ACCESS_TOKEN")
GROUP_ID = os.getenv("FB_GROUP_ID")


def publish(asset_url: str, caption: str) -> dict:
    """Publish a video/image asset + caption to the configured FB group.

    Returns the raw API response so the caller can log the post id.
    """
    endpoint = f"https://graph.facebook.com/{GRAPH_API_VERSION}/{GROUP_ID}/feed"

    resp = requests.post(
        endpoint,
        data={
            "message": caption,
            "link": asset_url,
            "access_token": PAGE_TOKEN,
        },
        timeout=20,
    )

    if resp.status_code != 200:
        # Meta's error payloads are actually pretty useful, worth surfacing
        # as-is instead of wrapping in a generic exception
        raise RuntimeError(f"FB publish failed ({resp.status_code}): {resp.text}")

    return resp.json()
