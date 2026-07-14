import json
from datetime import datetime
from flask_login import UserMixin
from extensions import db


class User(UserMixin, db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    sites = db.relationship("GeneratedSite", backref="owner", lazy=True)


class GeneratedSite(db.Model):
    """Stores the structured JSON content + resolved image set for a
    generated site, so it can be re-rendered or edited later without
    calling the LLM or the image API again."""

    __tablename__ = "generated_sites"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)

    business_name = db.Column(db.String(255), nullable=False)
    business_type = db.Column(db.String(120), nullable=False)

    content_json = db.Column(db.Text, nullable=False)  # AI structured content
    images_json = db.Column(db.Text, nullable=False)    # resolved image URLs

    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_site_dict(self):
        data = json.loads(self.content_json)
        data["images"] = json.loads(self.images_json)
        data["id"] = self.id
        return data


class ContactMessage(db.Model):
    __tablename__ = "contact_messages"

    id = db.Column(db.Integer, primary_key=True)
    site_id = db.Column(db.Integer, db.ForeignKey("generated_sites.id"), nullable=True)

    name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(255), nullable=False)
    message = db.Column(db.Text, nullable=False)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
