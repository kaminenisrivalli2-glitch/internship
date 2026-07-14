# HE5 SiteGen — Rewritten Generation Pipeline

## Why the old approach produced placeholders

Asking an LLM to write raw HTML almost always produces `<img>` tags with
no real `src`, so the model fills the alt text / caption with whatever it
thinks the image *should* be ("About Image", "people watching movie", etc).
That's a prompting problem you can't fully fix — the fix is architectural:
**never let the LLM touch HTML or images at all.**

## New architecture

```
User Form  →  ai_service.py (Groq, JSON-only)  →  content_validator.py (repairs/guarantees)
                                                          ↓
                                            image_service.py (Unsplash/Pexels, by business type)
                                                          ↓
                                          generated_site.html (Jinja2 + Bootstrap 5)
```

1. **`ai_service.py`** calls Groq with `response_format={"type": "json_object"}`
   and a strict schema prompt. The model can *only* return the 6 content
   fields — never markup, never image URLs, never captions.
2. **`content_validator.py`** is the safety net. It regex-scans every field
   for placeholder patterns (`"about image"`, `"lorem ipsum"`, `"insert
   text here"`, etc.) and silently swaps in curated, business-type-aware
   fallback copy for anything that fails. This also covers total API
   failure — the page always renders complete, professional content.
3. **`image_service.py`** maps the business type string (fuzzy match, e.g.
   "Italian Restaurant" → `restaurant`) to a curated search keyword, then
   queries Unsplash first, Pexels second, and a keyless `source.unsplash.com`
   redirect as a last resort — so a page is *never* missing an image, even
   with zero API keys configured.
4. **`routes/generate.py`** is your rewritten `generate()` view. It no
   longer renders LLM output directly — it assembles `content` + `images`
   into one dict, persists it, and hands it to the template.
5. **`generated_site.html`** is a full premium one-page site: sticky navbar,
   full-bleed hero, about, services (cards with real photos), features,
   gallery, testimonial carousel, working contact form, footer. Styled with
   a dedicated design system (`generated.css`) — deep ink navy + brass gold
   + warm ivory, Fraunces/Inter type pairing, AOS scroll reveals, and
   hover/lift micro-interactions instead of generic Bootstrap defaults.

## Folder structure

```
he5_sitegen/
├── app.py                     # App factory, registers blueprints
├── config.py                  # Env-driven settings (Groq, Unsplash, Pexels, DB)
├── extensions.py              # db, login_manager singletons
├── models.py                  # User, GeneratedSite, ContactMessage
├── requirements.txt
├── .env.example
├── services/
│   ├── ai_service.py          # Groq call -> structured JSON only
│   ├── image_service.py       # Business-type -> real photos
│   └── content_validator.py  # Placeholder detection + fallback copy banks
├── routes/
│   ├── generate.py            # GET /generate form, POST /generate, GET /site/<id>
│   └── contact.py             # POST /site/<id>/contact
├── templates/
│   ├── generate_form.html     # Business input form
│   └── generated_site.html    # The premium generated website
└── static/
    ├── css/generated.css
    └── js/generated.js
```

## Integrating into your existing project

Since your current `He5 SiteGen` app already has its own `app.py`/routes:

1. Copy `services/`, and the `content_validator.py` + `image_service.py` +
   `ai_service.py` files into your project (adjust the `import` paths if
   your package layout differs, e.g. `from myapp.extensions import db`).
2. Replace your current `generate()` view with the one in
   `routes/generate.py`. If you don't use Flask blueprints yet, just copy
   the function body — the logic doesn't depend on blueprints.
3. Add the `GeneratedSite` model (or the two new columns
   `content_json`/`images_json`) to your existing `models.py`, then run
   your migration (`flask db migrate && flask db upgrade`, or
   `db.create_all()` if you're not using Alembic yet).
4. Copy `templates/generated_site.html`, `static/css/generated.css`, and
   `static/js/generated.js` into your existing `templates/`/`static/`
   folders.
5. Add the four keys from `.env.example` to your `.env`:
   `GROQ_API_KEY`, `GROQ_MODEL`, `UNSPLASH_ACCESS_KEY`, `PEXELS_API_KEY`.
   None are required for the app to run — without them you fall back to
   curated content and keyless stock images — but Groq + Unsplash give the
   best results.
6. Wire up `contact.py`'s blueprint (or its single route) alongside your
   existing routes.

## Setup (standalone run)

```bash
cd he5_sitegen
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # then fill in your real keys
python app.py
```

Visit `http://localhost:5000/generate`, fill in the form, and you'll get a
complete generated website at `/site/<id>` — no placeholders, real photos,
a working contact form.

## Notes on the Groq model name

`GROQ_MODEL` defaults to `llama-3.3-70b-versatile` but this is fully
configurable via env var — check the Groq console for the current list of
available models before deploying, since model availability on Groq
changes over time.

## Extending the fallback content banks

`content_validator.py`'s `FALLBACK_SERVICES` / `FALLBACK_FEATURES` dicts
are keyed by a lowercase substring of business type. Add more keys (e.g.
`"law"`, `"salon"`, `"photography"`) to get richer, more specific fallback
copy for those verticals — right now `"default"` covers anything not
explicitly listed.
