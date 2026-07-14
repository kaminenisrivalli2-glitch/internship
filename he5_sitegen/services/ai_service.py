"""
Calls Groq to produce STRUCTURED JSON ONLY — never raw HTML, never image
descriptions. The JSON is then repaired by content_validator before it's
allowed anywhere near a template.
"""

import json
import re
from groq import Groq
from flask import current_app
from services.content_validator import validate_and_fix

SCHEMA_INSTRUCTIONS = """
You are a professional copywriter for premium business websites.

Return ONLY valid JSON — no markdown fences, no commentary, no explanation.
Match this exact schema:

{
  "business_name": "string",
  "hero_title": "string, punchy, under 8 words",
  "hero_subtitle": "string, 1 sentence, under 20 words",
  "about": "string, 3-4 sentences, warm and specific to the business",
  "services": [
    {"title": "string", "description": "string, 1-2 sentences"}
  ],
  "features": [
    {"title": "string", "description": "string, 1 sentence"}
  ],
  "testimonials": [
    {"name": "realistic full name", "review": "string, 1-2 sentences, specific and genuine-sounding"}
  ]
}

Rules:
- Provide exactly 3 to 4 items in "services", 3 to 4 in "features", and 3 in "testimonials".
- NEVER write generic placeholders like "About Image", "Feature Image", "Service Image",
  "image here", "Lorem ipsum", or any text describing an image instead of real copy.
- Every field must contain real, specific, publish-ready marketing copy — as if written
  by a professional copywriter for this exact business.
- Do not mention images, photos, or visuals in any text field.
"""


def _build_user_prompt(business_name, business_type, description, tone):
    return (
        f"Business name: {business_name}\n"
        f"Business type: {business_type}\n"
        f"Business description: {description or 'Not provided — infer something plausible and specific.'}\n"
        f"Tone: {tone or 'professional and warm'}\n\n"
        f"Write the JSON content for this business's website now."
    )


def _extract_json(raw_text):
    """Handles the rare case where the model wraps JSON in fences or adds
    stray text despite instructions."""
    raw_text = raw_text.strip()
    try:
        return json.loads(raw_text)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", raw_text, re.DOTALL)
        if match:
            return json.loads(match.group(0))
        raise


def generate_site_content(business_name, business_type, description="", tone=""):
    """Returns a validated, placeholder-free dict matching the required
    schema. Falls back entirely to curated content if the API call or
    parsing fails for any reason — the caller never has to handle errors."""

    api_key = current_app.config.get("GROQ_API_KEY")
    model = current_app.config.get("GROQ_MODEL")

    data = {}
    if api_key:
        try:
            client = Groq(api_key=api_key)
            completion = client.chat.completions.create(
                model=model,
                temperature=current_app.config.get("GROQ_TEMPERATURE", 0.7),
                max_tokens=current_app.config.get("GROQ_MAX_TOKENS", 2500),
                response_format={"type": "json_object"},
                messages=[
                    {"role": "system", "content": SCHEMA_INSTRUCTIONS},
                    {
                        "role": "user",
                        "content": _build_user_prompt(
                            business_name, business_type, description, tone
                        ),
                    },
                ],
            )
            raw_text = completion.choices[0].message.content
            data = _extract_json(raw_text)
        except Exception as exc:  # noqa: BLE001 - we deliberately never crash the request
            current_app.logger.warning("Groq generation failed, using fallback content: %s", exc)
            data = {}

    # Whether the AI succeeded, partially succeeded, or failed entirely,
    # validate_and_fix() guarantees a complete, placeholder-free result.
    return validate_and_fix(data, business_name, business_type)
