"""
Guarantees that no field ever reaches the template as a placeholder.

Two layers of defense:
 1. `is_placeholder()` catches known bad patterns ("about image", "lorem
    ipsum", "insert text here", too-short strings, etc).
 2. `validate_and_fix()` walks the whole AI JSON payload and repairs any
    field that fails validation using curated, business-type-aware
    fallback copy — never a generic "Lorem ipsum" or empty string.
"""

import re

PLACEHOLDER_PATTERNS = [
    r"\bimage here\b",
    r"\babout image\b",
    r"\bfeature image\b",
    r"\bservice image\b",
    r"\bhero image\b",
    r"\bgallery image\b",
    r"\bplaceholder\b",
    r"\blorem ipsum\b",
    r"\binsert (text|content|image)\b",
    r"\byour (text|content) here\b",
    r"\bpeople watching\b",
    r"\btodo\b",
    r"^\s*image\s*\d*\s*$",
    r"^\s*text\s*$",
]

_PLACEHOLDER_RE = re.compile("|".join(PLACEHOLDER_PATTERNS), re.IGNORECASE)


def is_placeholder(text, min_len=8):
    if not text or not isinstance(text, str):
        return True
    stripped = text.strip()
    if len(stripped) < min_len:
        return True
    if _PLACEHOLDER_RE.search(stripped):
        return True
    return False


# --------------------------------------------------------------------------
# Fallback copy banks, grouped by business type. "default" is used for any
# business type that doesn't match a known key.
# --------------------------------------------------------------------------

FALLBACK_SERVICES = {
    "restaurant": [
        {"title": "Fine Dining Experience", "description": "Chef-curated dishes made from locally sourced ingredients, served in a warm and elegant setting."},
        {"title": "Private Events & Catering", "description": "From intimate dinners to large celebrations, our team handles every detail with precision."},
        {"title": "Seasonal Tasting Menus", "description": "Rotating menus that showcase the best flavors of every season, crafted by our culinary team."},
    ],
    "gym": [
        {"title": "Personal Training", "description": "One-on-one coaching tailored to your goals, with certified trainers guiding every session."},
        {"title": "Group Fitness Classes", "description": "High-energy classes including HIIT, strength, and mobility work for every fitness level."},
        {"title": "Nutrition Coaching", "description": "Personalized meal planning and nutrition guidance to complement your training program."},
    ],
    "hotel": [
        {"title": "Luxury Accommodations", "description": "Elegantly designed rooms and suites offering comfort, privacy, and stunning views."},
        {"title": "Concierge Services", "description": "Our concierge team is available around the clock to curate your perfect stay."},
        {"title": "Spa & Wellness", "description": "Rejuvenate with our full-service spa, offering massages, treatments, and wellness programs."},
    ],
    "bakery": [
        {"title": "Fresh Daily Bakes", "description": "Breads, pastries, and cakes baked fresh every morning using traditional techniques."},
        {"title": "Custom Celebration Cakes", "description": "Beautifully designed cakes for weddings, birthdays, and every special occasion."},
        {"title": "Coffee & Pastry Bar", "description": "Pair our fresh pastries with specialty coffee brewed by our in-house baristas."},
    ],
    "clinic": [
        {"title": "General Consultations", "description": "Comprehensive checkups and consultations from experienced, board-certified physicians."},
        {"title": "Diagnostic Services", "description": "Modern diagnostic equipment and rapid results to support accurate, timely care."},
        {"title": "Preventive Care Programs", "description": "Personalized wellness plans designed to keep you and your family healthy year-round."},
    ],
    "startup": [
        {"title": "Product Strategy", "description": "We help define roadmaps and priorities that turn early ideas into scalable products."},
        {"title": "Engineering & Development", "description": "A senior team building robust, production-ready software fast."},
        {"title": "Growth & Analytics", "description": "Data-driven strategies to acquire, retain, and grow your user base."},
    ],
    "portfolio": [
        {"title": "Web Development", "description": "Building fast, responsive, and accessible websites using modern frameworks."},
        {"title": "UI/UX Design", "description": "Designing intuitive interfaces backed by real user research."},
        {"title": "Technical Consulting", "description": "Helping teams make sound architecture and technology decisions."},
    ],
    "default": [
        {"title": "Professional Consultation", "description": "Personalized guidance from an experienced team dedicated to your success."},
        {"title": "Tailored Solutions", "description": "Every service is customized to match your specific needs and goals."},
        {"title": "Ongoing Support", "description": "We stay with you after the first delivery, providing continuous, reliable support."},
    ],
}

FALLBACK_FEATURES = {
    "default": [
        {"title": "Trusted Experience", "description": "Years of hands-on expertise delivering consistent, reliable results."},
        {"title": "Customer-First Approach", "description": "Every decision we make starts with what's best for the people we serve."},
        {"title": "Transparent Pricing", "description": "No hidden fees — you always know exactly what you're paying for."},
        {"title": "Fast, Responsive Service", "description": "Our team responds quickly and follows through on every commitment."},
    ],
}

FALLBACK_TESTIMONIALS = [
    {"name": "Sarah Mitchell", "review": "The attention to detail and quality of service exceeded every expectation. Highly recommended."},
    {"name": "James Carter", "review": "Professional from start to finish. They made the entire experience effortless."},
    {"name": "Priya Nair", "review": "A genuinely great team to work with — responsive, thoughtful, and reliable."},
]


def _fallback_about(business_name, business_type):
    return (
        f"{business_name} is a dedicated {business_type} committed to delivering "
        f"exceptional quality and genuine care in everything we do. Our team "
        f"combines experience, craftsmanship, and a customer-first mindset to "
        f"create an experience you can trust — every single time you visit."
    )


def _fallback_hero_title(business_name):
    return f"Welcome to {business_name}"


def _fallback_hero_subtitle(business_type):
    return f"Experience the finest in {business_type} — crafted with care, delivered with excellence."


def _bank_for(bank, business_type):
    key = (business_type or "").strip().lower()
    return bank.get(key, bank["default"])


def _valid_item(item, keys, min_len=8):
    if not isinstance(item, dict):
        return False
    for k in keys:
        if is_placeholder(str(item.get(k, "")), min_len=min_len):
            return False
    return True


def validate_and_fix(data, business_name, business_type):
    """Repairs an AI JSON payload in place, guaranteeing every field is
    real, professional copy — never a placeholder, never empty."""

    data = dict(data or {})

    data["business_name"] = (
        data.get("business_name")
        if not is_placeholder(data.get("business_name", ""), min_len=2)
        else business_name
    )

    data["hero_title"] = (
        data.get("hero_title")
        if not is_placeholder(data.get("hero_title", ""), min_len=4)
        else _fallback_hero_title(business_name)
    )

    data["hero_subtitle"] = (
        data.get("hero_subtitle")
        if not is_placeholder(data.get("hero_subtitle", ""), min_len=10)
        else _fallback_hero_subtitle(business_type)
    )

    data["about"] = (
        data.get("about")
        if not is_placeholder(data.get("about", ""), min_len=40)
        else _fallback_about(business_name, business_type)
    )

    # --- services: keep valid AI items, top up with fallback if short ---
    services = data.get("services") if isinstance(data.get("services"), list) else []
    services = [s for s in services if _valid_item(s, ["title", "description"])]
    if len(services) < 3:
        pool = _bank_for(FALLBACK_SERVICES, business_type)
        for item in pool:
            if len(services) >= 3:
                break
            if item not in services:
                services.append(item)
    data["services"] = services[:6]

    # --- features ---
    features = data.get("features") if isinstance(data.get("features"), list) else []
    features = [f for f in features if _valid_item(f, ["title", "description"])]
    if len(features) < 3:
        pool = _bank_for(FALLBACK_FEATURES, business_type)
        for item in pool:
            if len(features) >= 4:
                break
            if item not in features:
                features.append(item)
    data["features"] = features[:6]

    # --- testimonials ---
    testimonials = data.get("testimonials") if isinstance(data.get("testimonials"), list) else []
    testimonials = [t for t in testimonials if _valid_item(t, ["name", "review"], min_len=15)]
    if len(testimonials) < 3:
        for item in FALLBACK_TESTIMONIALS:
            if len(testimonials) >= 3:
                break
            if item not in testimonials:
                testimonials.append(item)
    data["testimonials"] = testimonials[:6]

    return data
