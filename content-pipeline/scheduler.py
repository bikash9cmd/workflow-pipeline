"""
Decides WHEN a rendered asset should go out and pings the Make webhook to
actually trigger the publish scenario. The actual posting logic lives in
the publishers/ folder and in the Make scenario itself - this file is just
the "is it time yet + who needs this" part.

I went back and forth on whether scheduling should live here or in Make
itself. Ended up keeping it here because Make's built-in scheduler module
charges an operation every time it checks, and this was cheaper to just run
on a cron.
"""

import os
import json
import requests
from datetime import datetime, timedelta
from dotenv import load_dotenv

load_dotenv()

MAKE_WEBHOOK_URL = os.getenv("MAKE_WEBHOOK_URL")
MAKE_WEBHOOK_SECRET = os.getenv("MAKE_WEBHOOK_SECRET")

# platform -> best posting window, learned this mostly from trial and error
# watching engagement over a couple months, not some official benchmark
PLATFORM_WINDOWS = {
    "facebook": (11, 13),   # 11am - 1pm
    "linkedin": (8, 10),    # 8am - 10am, before people get buried in meetings
    "discord": (18, 21),    # evening, community's mostly active then
}

QUEUE_FILE = os.path.join(os.path.dirname(__file__), "queue.json")


def _load_queue() -> list:
    if not os.path.exists(QUEUE_FILE):
        return []
    with open(QUEUE_FILE) as f:
        return json.load(f)


def _save_queue(queue: list) -> None:
    with open(QUEUE_FILE, "w") as f:
        json.dump(queue, f, indent=2)


def queue_asset(asset_url: str, platforms: list[str], caption: str) -> None:
    """Add a rendered asset to the queue for one or more platforms."""
    queue = _load_queue()
    now = datetime.utcnow()

    for platform in platforms:
        window_start, _ = PLATFORM_WINDOWS.get(platform, (9, 18))
        scheduled_for = now.replace(hour=window_start, minute=0, second=0)
        if scheduled_for < now:
            scheduled_for += timedelta(days=1)

        queue.append({
            "asset_url": asset_url,
            "platform": platform,
            "caption": caption,
            "scheduled_for": scheduled_for.isoformat(),
            "status": "pending",
        })

    _save_queue(queue)


def run_due_jobs() -> int:
    """Check the queue, fire anything that's due via the Make webhook.

    Meant to be called from a cron entry every 10-15 min, see docs/architecture.md
    """
    queue = _load_queue()
    now = datetime.utcnow()
    fired = 0

    for job in queue:
        if job["status"] != "pending":
            continue
        if datetime.fromisoformat(job["scheduled_for"]) > now:
            continue

        try:
            _trigger_make(job)
            job["status"] = "sent"
            fired += 1
        except requests.RequestException as e:
            # leave it pending, cron will retry it next run
            job["status"] = "pending"
            job["last_error"] = str(e)

    _save_queue(queue)
    return fired


def _trigger_make(job: dict) -> None:
    payload = {
        "platform": job["platform"],
        "asset_url": job["asset_url"],
        "caption": job["caption"],
        "secret": MAKE_WEBHOOK_SECRET,
    }
    resp = requests.post(MAKE_WEBHOOK_URL, json=payload, timeout=15)
    resp.raise_for_status()


if __name__ == "__main__":
    n = run_due_jobs()
    print(f"fired {n} job(s)")
