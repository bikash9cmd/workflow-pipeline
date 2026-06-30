"""
Flask app handling booking, cancellation, and follow-up for client
sessions. Make scenarios hit these endpoints instead of having booking
logic spread across a bunch of Make modules - keeps the actual business
rules (can't cancel something that already happened, etc.) in one place
I can actually unit test.
"""

from datetime import datetime, timedelta
from flask import Flask, request, jsonify
from apscheduler.schedulers.background import BackgroundScheduler

from config import Config
from models import db, Client, Session
from integrations import linkedin_api, whatsapp_api, gmail_api

app = Flask(__name__)
app.config.from_object(Config)
db.init_app(app)

with app.app_context():
    db.create_all()


def _notify(client: Client, channel: str, message: str):
    """Send through whatever channel the client prefers, fall back to
    email if the preferred one isn't configured for them."""
    try:
        if channel == "whatsapp" and client.whatsapp_number:
            whatsapp_api.send_message(client.whatsapp_number, message)
            return
        if channel == "linkedin" and client.linkedin_urn:
            result = linkedin_api.send_message(client.linkedin_urn, message)
            if result.get("ok"):
                return
            # fall through to email if linkedin didn't go through
    except Exception as e:
        # logging would be nicer than print but this is still early stage
        print(f"notify via {channel} failed for client {client.id}: {e}")

    if client.email:
        gmail_api.send_email(client.email, "Session update", message)


@app.route("/sessions/book", methods=["POST"])
def book_session():
    data = request.get_json(force=True)

    client = Client.query.get(data.get("client_id"))
    if not client:
        client = Client(
            name=data["name"],
            email=data.get("email"),
            whatsapp_number=data.get("whatsapp_number"),
            linkedin_urn=data.get("linkedin_urn"),
        )
        db.session.add(client)
        db.session.commit()

    scheduled_at = datetime.fromisoformat(data["scheduled_at"])
    if scheduled_at < datetime.utcnow():
        return jsonify({"error": "can't book a session in the past"}), 400

    session = Session(
        client_id=client.id,
        scheduled_at=scheduled_at,
        channel_preference=data.get("channel_preference", "email"),
    )
    db.session.add(session)
    db.session.commit()

    _notify(client, session.channel_preference,
            f"Hey {client.name}, you're booked for {scheduled_at.strftime('%b %d, %I:%M %p')}.")

    return jsonify(session.to_dict()), 201


@app.route("/sessions/<int:session_id>/cancel", methods=["POST"])
def cancel_session(session_id):
    session = Session.query.get_or_404(session_id)

    if session.status == "cancelled":
        return jsonify({"error": "already cancelled"}), 400
    if session.status == "completed":
        return jsonify({"error": "can't cancel a completed session"}), 400

    session.status = "cancelled"
    session.cancelled_at = datetime.utcnow()
    db.session.commit()

    client = session.client
    _notify(client, session.channel_preference,
            f"Hi {client.name}, your session on "
            f"{session.scheduled_at.strftime('%b %d')} has been cancelled. "
            f"Let us know if you'd like to rebook.")

    return jsonify(session.to_dict())


@app.route("/sessions/<int:session_id>", methods=["GET"])
def get_session(session_id):
    session = Session.query.get_or_404(session_id)
    return jsonify(session.to_dict())


def run_followup_check():
    """Looks for sessions starting within FOLLOWUP_HOURS_BEFORE that haven't
    had a reminder sent yet, and fires one off. Registered with APScheduler
    below, runs inside app context."""
    with app.app_context():
        cutoff = datetime.utcnow() + timedelta(hours=Config.FOLLOWUP_HOURS_BEFORE)
        due = Session.query.filter(
            Session.status == "booked",
            Session.followup_sent == False,  # noqa: E712 - sqlalchemy needs the literal here
            Session.scheduled_at <= cutoff,
        ).all()

        for session in due:
            client = session.client
            _notify(client, session.channel_preference,
                    f"Reminder: your session is coming up on "
                    f"{session.scheduled_at.strftime('%b %d, %I:%M %p')}.")
            session.followup_sent = True

        if due:
            db.session.commit()


scheduler = BackgroundScheduler()
scheduler.add_job(run_followup_check, "interval", minutes=30)
scheduler.start()


if __name__ == "__main__":
    app.run(debug=True, port=5000)
