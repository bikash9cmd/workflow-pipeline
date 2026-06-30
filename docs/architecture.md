# How this actually fits together

Quick sketch of the flow since the Make side isn't in this repo (lives in
the Make.com UI as scenarios, can't really export that as files in a useful
way - screenshots only, sorry future me).

## Content pipeline

1. A content brief gets dropped in (currently just a row in a Google Sheet,
   honestly the simplest input method I could get away with).
2. Make scenario picks it up, calls `creatomate_render.py` logic (ported
   into a Make HTTP module - the python file here is for local testing /
   reference, the actual call in production is an HTTP request module
   inside Make).
3. Once render is done, `scheduler.py` decides the posting time per platform
   and writes to `queue.json`.
4. A cron job runs `scheduler.run_due_jobs()` every 15 min, which pings the
   Make webhook for anything that's due.
5. Make scenario receives the webhook and routes to the right publisher
   logic. The Python publishers in `publishers/` are the same logic
   re-implemented for local testing and in case I move this off Make
   eventually - right now Make's HTTP modules do the actual API calls in
   production.

Honestly there's some duplication between "what Make does" and "what the
Python scripts do" right now. That's intentional for this stage - Make was
faster to get this actually running and shipped, the Python versions are
there so I'm not locked into Make if I want to migrate later, and so I had
something I could unit test without paying for Make operations.

## Session backend

This one's fully code, no Make involved on the booking/cancel side. Make
DOES come back into play for things like "post a public announcement when
a new cohort opens up" - that's still a content-pipeline scenario, separate
from this.

```
client submits booking form (Tally / Google Form)
        |
        v
Make scenario formats payload
        |
        v
POST /sessions/book  (this repo)
        |
        v
 SQLite row created -> notification sent via preferred channel
```

Follow-ups run on a 30-min interval check (APScheduler, inside `app.py`)
rather than a separate cron, just because it was less moving parts for a
single-server deployment. Would split this out into a real task queue
(Celery + Redis) if this needed to scale past one box.

## Known rough edges

- queue.json as a "database" for the content pipeline is obviously not
  going to survive concurrent writes well. Fine for now since it's one
  person's content going out, would move to SQLite or just a table in the
  session backend's DB if this gets busier.
- No retry/backoff on Creatomate render failures.
- LinkedIn DM sending requires partnership-tier API access I haven't been
  granted yet, so in practice that branch falls back to email for now.
