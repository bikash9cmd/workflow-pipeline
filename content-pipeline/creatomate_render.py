"""
Kicks off a Creatomate render job for a content brief and waits for it to
finish, then hands the resulting media URL off to the scheduler.

Usage (manual test):
    python creatomate_render.py --text "New batch starting Monday" --output test.mp4

In production this gets called by a Make scenario via webhook, not run
directly, but I kept the CLI bit so I'm not redeploying just to check the
template still renders.
"""

import os
import time
import argparse
import requests
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("CREATOMATE_API_KEY")
TEMPLATE_ID = os.getenv("CREATOMATE_TEMPLATE_ID")
BASE_URL = "https://api.creatomate.com/v1"

# render usually takes 8-20s for our template, polling faster than this is
# just wasting requests
POLL_INTERVAL_SECONDS = 4
MAX_POLL_ATTEMPTS = 30


def start_render(text_overlay: str, image_url: str | None = None) -> str:
    """Fire off the render and return the render job id."""
    modifications = {"Text-1.text": text_overlay}
    if image_url:
        modifications["Image-1.source"] = image_url

    resp = requests.post(
        f"{BASE_URL}/renders",
        headers={"Authorization": f"Bearer {API_KEY}"},
        json={"template_id": TEMPLATE_ID, "modifications": modifications},
        timeout=20,
    )
    resp.raise_for_status()
    data = resp.json()
    # creatomate returns a list even for a single render request
    return data[0]["id"]


def poll_until_done(render_id: str) -> str:
    """Poll the render status and return the final asset url once ready."""
    for attempt in range(MAX_POLL_ATTEMPTS):
        resp = requests.get(
            f"{BASE_URL}/renders/{render_id}",
            headers={"Authorization": f"Bearer {API_KEY}"},
            timeout=20,
        )
        resp.raise_for_status()
        status = resp.json()

        if status["status"] == "succeeded":
            return status["url"]
        if status["status"] == "failed":
            # not retrying here on purpose - if the template itself is
            # broken, retrying just burns render credits for nothing
            raise RuntimeError(f"Creatomate render {render_id} failed: {status}")

        time.sleep(POLL_INTERVAL_SECONDS)

    raise TimeoutError(f"Render {render_id} didn't finish in time, giving up")


def render_and_get_url(text_overlay: str, image_url: str | None = None) -> str:
    render_id = start_render(text_overlay, image_url)
    return poll_until_done(render_id)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--text", required=True)
    parser.add_argument("--image", default=None)
    args = parser.parse_args()

    url = render_and_get_url(args.text, args.image)
    print(f"done -> {url}")
