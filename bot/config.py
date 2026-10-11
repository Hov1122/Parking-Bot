from __future__ import annotations

import os
from datetime import date

try:
    from dotenv import load_dotenv

    load_dotenv()
except Exception:  # dotenv is optional (lets the DB layer be tested standalone)
    pass

BOT_TOKEN: str = os.getenv("BOT_TOKEN", "").strip()
ADMIN_TELEGRAM_ID: str = os.getenv("ADMIN_TELEGRAM_ID", "").strip()
DB_PATH: str = os.getenv("DB_PATH", "parking.db").strip() or "parking.db"
ALLOWED_CHAT_ID: str = os.getenv("ALLOWED_CHAT_ID", "").strip()
ROTATION_END: str = os.getenv("ROTATION_END", "").strip()


def admin_id() -> int | None:
    try:
        return int(ADMIN_TELEGRAM_ID)
    except (TypeError, ValueError):
        return None


def allowed_chat_id() -> int | None:
    try:
        return int(ALLOWED_CHAT_ID)
    except (TypeError, ValueError):
        return None


def rotation_end() -> date | None:
    """Last day the rotation is valid (spot owners may open days up to this)."""
    if not ROTATION_END:
        return None
    try:
        return date.fromisoformat(ROTATION_END)
    except ValueError:
        return None