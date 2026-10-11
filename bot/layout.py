from __future__ import annotations

"""Physical parking lot layout.

Positions are in map units (SCALE px per unit), measured top-to-bottom,
left-to-right. Edit this file to match your real garage — the numbers are the
spot numbers used everywhere in the bot (/assign, /map, /status...).

B1 (ground floor): spots 1-3 in a row, spot 4 is perpendicular and closes the
front of spots 2 & 3.
B2 (upper floor): spots 5-9 — 5 standalone (reserved), 6+7 side by side
(6 reserved), 8 closes the front of 6 & 7, 9 standalone.
"""

SCALE = 3  # pixels per map unit

SPOTS = [
    # ---------------- B2 (upper floor) ----------------
    {"number": 5, "type": "reserved", "floor": "B2", "x": 10,  "y": 30, "w": 60, "h": 40},
    {"number": 6, "type": "reserved", "floor": "B2", "x": 120, "y": 30, "w": 60, "h": 40},
    {"number": 7, "type": "rotating", "floor": "B2", "x": 190, "y": 30, "w": 60, "h": 40},
    {"number": 8, "type": "rotating", "floor": "B2", "x": 120, "y": 90, "w": 130, "h": 40},
    {"number": 9, "type": "rotating", "floor": "B2", "x": 300, "y": 30, "w": 60, "h": 40},
    # ---------------- B1 (ground floor) ----------------
    {"number": 1, "type": "reserved", "floor": "B1", "x": 10,  "y": 190, "w": 60, "h": 40},
    {"number": 2, "type": "reserved", "floor": "B1", "x": 80,  "y": 190, "w": 60, "h": 40},
    {"number": 3, "type": "rotating", "floor": "B1", "x": 150, "y": 190, "w": 60, "h": 40},
    {"number": 4, "type": "rotating", "floor": "B1", "x": 80,  "y": 240, "w": 130, "h": 40},
]


def by_number(number: int) -> dict | None:
    return next((s for s in SPOTS if s["number"] == number), None)