# Content & Communication Pipeline

Two automation systems I built in 2025 to stop doing repetitive publishing and
client-coordination work by hand.

1. **Content Pipeline** – takes a content brief, renders the video/image asset
   with Creatomate, runs it through Make.com scenarios, and pushes it out to
   Facebook Groups, Discord, and LinkedIn on a schedule. No more logging into
   three different apps every time something needs posting.
2. **Session Backend** – a small Flask service that owns the booking /
   cancellation / follow-up logic for client sessions and talks to LinkedIn,
   WhatsApp, and Gmail so the actual scheduling part doesn't need a human
   babysitting it.

Both pieces were originally glued together with a bunch of Make scenarios and
webhooks. This repo is the part of it that's actual code — the publishers,
the API wrappers, and the backend that the Make scenarios call into.

## Why this exists

I was manually re-posting the same promo clips to three platforms every week
and individually replying to "can I reschedule" messages across LinkedIn DMs,
WhatsApp, and email. Took maybe 5-6 hours a week. This got it down to
checking a dashboard once a day.

## Layout

```
content-pipeline/        -> render + schedule + publish content
  creatomate_render.py    -> kicks off a render job, polls until it's done
  scheduler.py            -> decides what goes out when, talks to Make webhook
  publishers/
    facebook_publisher.py
    discord_publisher.py
    linkedin_publisher.py

session-backend/         -> booking/cancellation/follow-up service
  app.py                  -> Flask routes
  models.py               -> Session + Client data shapes
  config.py
  integrations/
    linkedin_api.py
    whatsapp_api.py
    gmail_api.py

docs/architecture.md      -> how the pieces actually talk to each other
tests/                     -> a handful of sanity tests, not full coverage
```

## Stack

- Make.com — scenario orchestration / triggers (not in this repo, lives in
  the Make UI, screenshots in `docs/`)
- Creatomate — programmatic video/image rendering
- Flask + SQLite — session backend (kept it lightweight on purpose, this
  doesn't need Postgres)
- Meta Graph API, Discord webhooks, LinkedIn API, Twilio (WhatsApp), Gmail
  API

## Running it locally

```bash
cd session-backend
python -m venv venv && source venv/bin/activate
pip install -r ../requirements.txt
cp .env.example .env   # fill in your own keys, obviously
python app.py
```

The content pipeline scripts are meant to be triggered by Make webhooks, but
you can run `creatomate_render.py` directly for testing — see the docstring
at the top of the file.

## Status / what's left

- [x] Facebook + Discord publishing
- [x] LinkedIn publishing (rate-limited, see note in publisher)
- [x] Booking + cancellation flow
- [ ] Follow-up emails currently fire on a flat 24h delay, want to make this
      configurable per client tier
- [ ] No retry queue yet if Creatomate render fails mid-job — currently just
      logs and gives up, need to fix this before it's actually production safe

## Notes to self

Make scenario IDs and webhook secrets are NOT in this repo. See `.env.example`
for what needs to be set. Don't commit a real `.env`, I already did that once
and had to rotate every key.
