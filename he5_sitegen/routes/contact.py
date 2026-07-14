from flask import Blueprint, request, redirect, url_for, flash
from extensions import db
from models import ContactMessage

contact_bp = Blueprint("contact", __name__)


@contact_bp.route("/site/<int:site_id>/contact", methods=["POST"])
def submit_contact(site_id):
    name = request.form.get("name", "").strip()
    email = request.form.get("email", "").strip()
    message = request.form.get("message", "").strip()

    if not name or not email or not message:
        flash("Please fill in every field before sending your message.", "danger")
        return redirect(url_for("generate.view_site", site_id=site_id) + "#contact")

    entry = ContactMessage(site_id=site_id, name=name, email=email, message=message)
    db.session.add(entry)
    db.session.commit()

    flash("Thanks — your message has been sent!", "success")
    return redirect(url_for("generate.view_site", site_id=site_id) + "#contact")
