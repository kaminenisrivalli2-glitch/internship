import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "change-this-in-production")

    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "DATABASE_URL", "sqlite:///he5_sitegen.db"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # --- Groq (LLM) ---
    GROQ_API_KEY = os.environ.get("GROQ_API_KEY")
    # Check your Groq console for currently available model IDs — this is
    # configurable via env var so you never have to touch code to upgrade.
    GROQ_MODEL = os.environ.get("GROQ_MODEL", "llama-3.3-70b-versatile")
    GROQ_TEMPERATURE = float(os.environ.get("GROQ_TEMPERATURE", 0.7))
    GROQ_MAX_TOKENS = int(os.environ.get("GROQ_MAX_TOKENS", 2500))

    # --- Images (never sourced from the LLM) ---
    UNSPLASH_ACCESS_KEY = os.environ.get("UNSPLASH_ACCESS_KEY")
    PEXELS_API_KEY = os.environ.get("PEXELS_API_KEY")
