from datetime import datetime
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


class Client(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(120))
    whatsapp_number = db.Column(db.String(32))  # E.164 format, +977...
    linkedin_urn = db.Column(db.String(120))    # for DM follow-ups

    sessions = db.relationship("Session", backref="client", lazy=True)


class Session(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    client_id = db.Column(db.Integer, db.ForeignKey("client.id"), nullable=False)

    scheduled_at = db.Column(db.DateTime, nullable=False)
    status = db.Column(db.String(20), default="booked")  # booked / cancelled / completed
    channel_preference = db.Column(db.String(20), default="email")  # email / whatsapp / linkedin

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    cancelled_at = db.Column(db.DateTime, nullable=True)
    followup_sent = db.Column(db.Boolean, default=False)

    def to_dict(self):
        return {
            "id": self.id,
            "client_id": self.client_id,
            "scheduled_at": self.scheduled_at.isoformat(),
            "status": self.status,
            "channel_preference": self.channel_preference,
            "followup_sent": self.followup_sent,
        }
