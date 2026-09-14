import os


def get_allowed_origins() -> list[str]:
    """
    Reads the CORS_ORIGINS environment variable as a comma-separated list
    of allowed frontend origins, defaulting to the local Next.js dev server
    when unset -- so a deployed backend (e.g. on Render) can allow its
    deployed frontend's real origin (e.g. on Vercel) without a code change.
    """
    raw = os.environ.get("CORS_ORIGINS", "http://localhost:3000")
    return [origin.strip() for origin in raw.split(",") if origin.strip()]
