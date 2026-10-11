from __future__ import annotations

from pathlib import Path
from typing import Optional

BASE_DIR = Path(__file__).resolve().parent.parent
LOGO_PATH = BASE_DIR / "logo.png"


def logo_path() -> Optional[Path]:
    """Path to the bot logo, or None when it isn't present."""
    return LOGO_PATH if LOGO_PATH.exists() else None
