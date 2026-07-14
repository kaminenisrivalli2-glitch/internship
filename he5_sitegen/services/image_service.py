"""
Resolves real, relevant photography for a generated site based on the
business type. Images are NEVER produced by the LLM — this module is the
single source of truth for every <img> on the page.

Order of preference:
  1. Unsplash API      (best quality, requires UNSPLASH_ACCESS_KEY)
  2. Pexels API        (fallback, requires PEXELS_API_KEY)
  3. source.unsplash.com "featured" redirect (no key required — guarantees
     the page never ships with a broken image even with zero API keys
     configured)
"""

import requests
from flask import current_app

# Maps a loosely-typed "business_type" string to a curated search keyword.
# Keys are matched by substring, so "Italian Restaurant" -> "restaurant".
BUSINESS_IMAGE_KEYWORDS = {
    "restaurant": "restaurant interior fine dining",
    "cafe": "cozy coffee shop interior",
    "coffee": "cozy coffee shop interior",
    "bakery": "artisan bakery bread pastries",
    "gym": "modern gym fitness training",
    "fitness": "modern gym fitness training",
    "hotel": "luxury hotel lobby",
    "resort": "luxury resort pool",
    "clinic": "modern medical clinic",
    "hospital": "modern medical clinic",
    "dental": "dental clinic office",
    "salon": "modern hair salon interior",
    "spa": "spa wellness relaxation",
    "startup": "modern office team startup",
    "tech": "modern office technology team",
    "software": "software developers office",
    "portfolio": "developer working laptop",
    "photography": "professional photographer camera",
    "law": "law firm office professional",
    "real estate": "modern luxury home exterior",
    "realtor": "modern luxury home exterior",
    "education": "university classroom students",
    "school": "classroom students learning",
    "ecommerce": "product photography retail",
    "retail": "modern retail store interior",
    "wedding": "wedding event elegant decor",
    "construction": "construction site architecture",
    "automotive": "modern car showroom",
    "travel": "travel destination scenic landscape",
    "consulting": "business meeting professionals",
    "finance": "modern finance office professionals",
}

DEFAULT_KEYWORD = "professional modern business"


def resolve_keyword(business_type: str) -> str:
    bt = (business_type or "").strip().lower()
    for key, keyword in BUSINESS_IMAGE_KEYWORDS.items():
        if key in bt:
            return keyword
    return DEFAULT_KEYWORD


def _unsplash_search(query, count, access_key):
    try:
        resp = requests.get(
            "https://api.unsplash.com/search/photos",
            params={"query": query, "per_page": count, "orientation": "landscape"},
            headers={"Authorization": f"Client-ID {access_key}"},
            timeout=6,
        )
        resp.raise_for_status()
        results = resp.json().get("results", [])
        return [r["urls"]["regular"] for r in results]
    except requests.RequestException:
        return []


def _pexels_search(query, count, api_key):
    try:
        resp = requests.get(
            "https://api.pexels.com/v1/search",
            params={"query": query, "per_page": count, "orientation": "landscape"},
            headers={"Authorization": api_key},
            timeout=6,
        )
        resp.raise_for_status()
        photos = resp.json().get("photos", [])
        return [p["src"]["large"] for p in photos]
    except requests.RequestException:
        return []


def _source_fallback(query, count):
    # No API key required, always resolves to a real relevant photo.
    safe_query = query.replace(" ", ",")
    return [
        f"https://source.unsplash.com/featured/1200x800/?{safe_query}&sig={i}"
        for i in range(count)
    ]


def fetch_images(query, count=1):
    unsplash_key = current_app.config.get("UNSPLASH_ACCESS_KEY")
    pexels_key = current_app.config.get("PEXELS_API_KEY")

    urls = []
    if unsplash_key:
        urls = _unsplash_search(query, count, unsplash_key)
    if len(urls) < count and pexels_key:
        urls += _pexels_search(query, count - len(urls), pexels_key)
    if len(urls) < count:
        urls += _source_fallback(query, count - len(urls))

    return urls[:count]


def fetch_site_images(business_type: str, service_count=3, feature_count=4, gallery_count=6):
    """Returns every image the template needs, resolved up front."""
    keyword = resolve_keyword(business_type)

    hero = fetch_images(f"{keyword} wide banner", 1)
    about = fetch_images(f"{keyword} team people", 1)
    services = fetch_images(f"{keyword}", service_count)
    features = fetch_images(f"{keyword} detail closeup", feature_count)
    gallery = fetch_images(f"{keyword}", gallery_count)

    return {
        "hero": hero[0] if hero else "",
        "about": about[0] if about else "",
        "services": services,
        "features": features,
        "gallery": gallery,
    }
