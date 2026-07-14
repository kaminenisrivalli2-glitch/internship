import json
from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import current_user
from extensions import db
from models import GeneratedSite
from services.ai_service import generate_site_content
from services.image_service import fetch_site_images

generate_bp = Blueprint("generate", __name__)


@generate_bp.route("/generate", methods=["GET"])
def generate_form():
    """Renders the input form where the user describes their business."""
    return render_template("generate_form.html")


@generate_bp.route("/generate", methods=["POST"])
def generate():
    """
    Core generation pipeline:

      1. Collect business inputs from the form.
      2. Ask the LLM for STRUCTURED JSON ONLY (never raw HTML).
      3. Validate/repair the JSON so no placeholder text can ever appear.
      4. Resolve real photography from Unsplash/Pexels based on business
         type (images never come from the LLM).
      5. Persist the result so it can be revisited without re-calling the
         LLM or the image API.
      6. Render the JSON + images into the professional Bootstrap template.
    """
    business_name = request.form.get("business_name", "").strip()
    business_type = request.form.get("business_type", "").strip()
    description = request.form.get("description", "").strip()
    tone = request.form.get("tone", "").strip()

    if not business_name or not business_type:
        flash("Please provide at least a business name and business type.", "warning")
        return redirect(url_for("generate.generate_form"))

    content = generate_site_content(business_name, business_type, description, tone)
    images = fetch_site_images(business_type)

    site_record = GeneratedSite(
        user_id=current_user.id if current_user.is_authenticated else None,
        business_name=content["business_name"],
        business_type=business_type,
        content_json=json.dumps(content),
        images_json=json.dumps(images),
    )
    db.session.add(site_record)
    db.session.commit()

    return redirect(url_for("generate.view_site", site_id=site_record.id))


@generate_bp.route("/site/<int:site_id>")
def view_site(site_id):
    """Renders a previously generated site without touching the LLM or
    image API again — everything needed is already stored."""
    site_record = GeneratedSite.query.get_or_404(site_id)
    site = site_record.to_site_dict()
    return render_template("generated_site.html", site=site)
