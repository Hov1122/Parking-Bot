from __future__ import annotations

import json
import logging
import sqlite3
import threading
from datetime import date, timedelta
from typing import Any, List, Optional

from . import config, layout

log = logging.getLogger(__name__)

_lock = threading.Lock()
_conn: Optional[sqlite3.Connection] = None

SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    telegram_id INTEGER UNIQUE,
    name        TEXT NOT NULL,
    is_admin    INTEGER NOT NULL DEFAULT 0,
    created_at  TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS spots (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    number        INTEGER UNIQUE NOT NULL,
    type          TEXT NOT NULL DEFAULT 'rotating'
                  CHECK (type IN ('reserved', 'rotating')),
    owner_user_id INTEGER REFERENCES users(id) ON DELETE SET NULL
);

CREATE TABLE IF NOT EXISTS openings (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    spot_id    INTEGER NOT NULL REFERENCES spots(id) ON DELETE CASCADE,
    user_id    INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    start_date TEXT NOT NULL,
    end_date   TEXT,
    dates      TEXT,
    closed     INTEGER NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS claims (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    spot_id    INTEGER NOT NULL REFERENCES spots(id) ON DELETE CASCADE,
    user_id    INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    date       TEXT NOT NULL,
    active     INTEGER NOT NULL DEFAULT 1,
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS registration_requests (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    telegram_id INTEGER UNIQUE NOT NULL,
    name        TEXT NOT NULL,
    username    TEXT,
    status      TEXT NOT NULL DEFAULT 'pending'
                CHECK (status IN ('pending', 'approved', 'rejected')),
    created_at  TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS rotation_cycles (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    label      TEXT,
    start_date TEXT NOT NULL,
    end_date   TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS rotation_assignments (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    cycle_id    INTEGER NOT NULL REFERENCES rotation_cycles(id) ON DELETE CASCADE,
    spot_number INTEGER NOT NULL,
    user_id     INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    UNIQUE(cycle_id, spot_number)
);

CREATE INDEX IF NOT EXISTS idx_claims_spot_date ON claims(spot_id, date, active);
CREATE INDEX IF NOT EXISTS idx_openings_spot ON openings(spot_id, closed);
CREATE INDEX IF NOT EXISTS idx_rot_assign_cycle ON rotation_assignments(cycle_id);
CREATE UNIQUE INDEX IF NOT EXISTS idx_rot_assign_cycle_user ON rotation_assignments(cycle_id, user_id);
"""


def conn() -> sqlite3.Connection:
    global _conn
    if _conn is None:
        _conn = sqlite3.connect(config.DB_PATH, check_same_thread=False)
        _conn.row_factory = sqlite3.Row
        _conn.execute("PRAGMA foreign_keys = ON")
    return _conn


def init_db() -> None:
    with _lock:
        c = conn()
        c.executescript(SCHEMA)
        c.commit()
        _migrate(c)
        _seed_spots(c)
        c.commit()


def _migrate(c: sqlite3.Connection) -> None:
    """Small upgrades for databases created by older versions.

    Foreign-key enforcement is disabled while rebuilding tables so that the
    REFERENCES clauses in ``spots``/``openings`` keep pointing at ``users``.
    """
    c.execute("PRAGMA foreign_keys = OFF")
    try:
        users_cols = {row[1]: row for row in c.execute("PRAGMA table_info(users)")}
        if "telegram_id" in users_cols and users_cols["telegram_id"][3]:  # was NOT NULL
            c.execute(
                "CREATE TABLE users_new ("
                "id INTEGER PRIMARY KEY AUTOINCREMENT, "
                "telegram_id INTEGER UNIQUE, "
                "name TEXT NOT NULL, "
                "is_admin INTEGER NOT NULL DEFAULT 0, "
                "created_at TEXT NOT NULL DEFAULT (datetime('now'))"
                ")"
            )
            c.execute(
                "INSERT INTO users_new (id, telegram_id, name, is_admin, created_at) "
                "SELECT id, telegram_id, name, is_admin, created_at FROM users"
            )
            c.execute("DROP TABLE users")
            c.execute("ALTER TABLE users_new RENAME TO users")

        openings_cols = {row[1] for row in c.execute("PRAGMA table_info(openings)")}
        if "dates" not in openings_cols:
            c.execute("ALTER TABLE openings ADD COLUMN dates TEXT")
        c.commit()
    finally:
        c.execute("PRAGMA foreign_keys = ON")

    _ensure_unique_name(c)

    # One user owns one spot per cycle: backfill the unique index for old DBs.
    try:
        c.execute(
            "CREATE UNIQUE INDEX IF NOT EXISTS idx_rot_assign_cycle_user "
            "ON rotation_assignments(cycle_id, user_id)"
        )
        c.commit()
    except sqlite3.IntegrityError:
        log.warning(
            "Duplicate user in a rotation cycle exists, so the unique "
            "per-cycle-user index was not created. Fix with /delcycle."
        )


def _ensure_unique_name(c: sqlite3.Connection) -> None:
    """Make display names unique (case-insensitive)."""
    try:
        c.execute(
            "CREATE UNIQUE INDEX IF NOT EXISTS idx_users_name_nocase "
            "ON users(name COLLATE NOCASE)"
        )
        c.commit()
    except sqlite3.IntegrityError:
        log.warning(
            "Duplicate user names exist, so the unique-name index was not "
            "created. Fix the duplicates with /rename or /deluser."
        )


def _seed_spots(c: sqlite3.Connection) -> None:
    """Create any spot missing from the database.

    The layout file decides the spot numbers and their default type; existence
    is checked so /settype changes made by the admin survive restarts.
    """
    for spec in layout.SPOTS:
        c.execute(
            "INSERT OR IGNORE INTO spots (number, type) VALUES (?, ?)",
            (spec["number"], spec["type"]),
        )


# --------------------------------------------------------------------------- #
# Date helpers
# --------------------------------------------------------------------------- #
def today() -> str:
    return date.today().isoformat()


def plus_days(n: int) -> str:
    return (date.today() + timedelta(days=n)).isoformat()


# --------------------------------------------------------------------------- #
# Users
# --------------------------------------------------------------------------- #
def get_user_by_tg(tg_id: int) -> Optional[sqlite3.Row]:
    return conn().execute(
        "SELECT * FROM users WHERE telegram_id = ?", (tg_id,)
    ).fetchone()


def get_user(user_id: int) -> Optional[sqlite3.Row]:
    return conn().execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()


def count_users() -> int:
    return conn().execute("SELECT COUNT(*) AS c FROM users").fetchone()["c"]


def count_admins() -> int:
    return conn().execute(
        "SELECT COUNT(*) AS c FROM users WHERE is_admin = 1"
    ).fetchone()["c"]


def create_user(tg_id: int, name: str, is_admin: bool = False) -> sqlite3.Row:
    with _lock:
        conn().execute(
            "INSERT INTO users (telegram_id, name, is_admin) VALUES (?, ?, ?)",
            (tg_id, name, 1 if is_admin else 0),
        )
        conn().commit()
    return get_user_by_tg(tg_id)


def add_pending_user(name: str) -> Optional[sqlite3.Row]:
    """Admin pre-creates a user with only a name (no telegram id yet)."""
    if name_exists(name):
        return None
    with _lock:
        cur = conn().execute(
            "INSERT INTO users (telegram_id, name, is_admin) VALUES (NULL, ?, 0)",
            (name,),
        )
        conn().commit()
        return get_user(cur.lastrowid)


def name_exists(name: str, exclude_id: Optional[int] = None) -> bool:
    row = conn().execute(
        "SELECT id FROM users WHERE name = ? COLLATE NOCASE LIMIT 1", (name,)
    ).fetchone()
    return row is not None and (exclude_id is None or row["id"] != exclude_id)


def find_pending_by_name(name: str) -> Optional[sqlite3.Row]:
    return conn().execute(
        "SELECT * FROM users WHERE telegram_id IS NULL AND name = ? COLLATE NOCASE "
        "LIMIT 1",
        (name,),
    ).fetchone()


def bind_telegram(user_id: int, tg_id: int) -> bool:
    """Link a pending account to a telegram id. Returns False if the id is taken."""
    try:
        with _lock:
            conn().execute(
                "UPDATE users SET telegram_id = ? WHERE id = ? AND telegram_id IS NULL",
                (tg_id, user_id),
            )
            conn().commit()
    except sqlite3.IntegrityError:
        return False
    return True


def set_admin(user_id: int, flag: bool = True) -> None:
    with _lock:
        conn().execute(
            "UPDATE users SET is_admin = ? WHERE id = ?", (1 if flag else 0, user_id)
        )
        conn().commit()


def rename_user(user_id: int, name: str) -> None:
    with _lock:
        conn().execute("UPDATE users SET name = ? WHERE id = ?", (name, user_id))
        conn().commit()


def all_users() -> List[sqlite3.Row]:
    return conn().execute(
        "SELECT * FROM users ORDER BY name COLLATE NOCASE"
    ).fetchall()


def find_users_by_name(name: str) -> List[sqlite3.Row]:
    return conn().execute(
        "SELECT * FROM users WHERE name = ? COLLATE NOCASE", (name,)
    ).fetchall()


def delete_user(user_id: int) -> None:
    """Delete a user.

    Any spot they owned is freed (FK SET NULL) and their openings/claims are
    removed (FK CASCADE). Their registration request, if any, is dropped too.
    """
    row = get_user(user_id)
    if row is None:
        return
    with _lock:
        if row["telegram_id"] is not None:
            conn().execute(
                "DELETE FROM registration_requests WHERE telegram_id = ?",
                (row["telegram_id"],),
            )
        conn().execute("DELETE FROM users WHERE id = ?", (user_id,))
        conn().commit()


# --------------------------------------------------------------------------- #
# Registration requests (new users wait for an admin to approve them)
# --------------------------------------------------------------------------- #
def upsert_request(tg_id: int, name: str, username: Optional[str]) -> sqlite3.Row:
    """Create or refresh a pending registration request for a telegram id."""
    with _lock:
        conn().execute(
            "INSERT INTO registration_requests (telegram_id, name, username, status) "
            "VALUES (?, ?, ?, 'pending') "
            "ON CONFLICT(telegram_id) DO UPDATE SET "
            "name = excluded.name, username = excluded.username, status = 'pending'",
            (tg_id, name, username),
        )
        conn().commit()
    return latest_request(tg_id)


def get_request(req_id: int) -> Optional[sqlite3.Row]:
    return conn().execute(
        "SELECT * FROM registration_requests WHERE id = ?", (req_id,)
    ).fetchone()


def latest_request(tg_id: int) -> Optional[sqlite3.Row]:
    return conn().execute(
        "SELECT * FROM registration_requests WHERE telegram_id = ? "
        "ORDER BY id DESC LIMIT 1",
        (tg_id,),
    ).fetchone()


def pending_requests() -> List[sqlite3.Row]:
    return conn().execute(
        "SELECT * FROM registration_requests WHERE status = 'pending' "
        "ORDER BY id"
    ).fetchall()


def delete_request(req_id: int) -> None:
    with _lock:
        conn().execute("DELETE FROM registration_requests WHERE id = ?", (req_id,))
        conn().commit()


def approve_request(req_id: int) -> Optional[sqlite3.Row]:
    """Approve a request: link a waiting account by name, or create a new one.

    Returns the resulting user row, or None when the telegram id is already in
    use by a different account.
    """
    req = get_request(req_id)
    if req is None:
        return None
    tg_id = req["telegram_id"]

    existing = get_user_by_tg(tg_id)
    if existing is not None:
        _set_request_status(req_id, "approved")
        return existing

    pending = find_pending_by_name(req["name"])
    if pending is not None:
        if not bind_telegram(pending["id"], tg_id):
            return None
        user = get_user(pending["id"])
    else:
        if name_exists(req["name"]):
            return None
        try:
            user = create_user(tg_id, req["name"])
        except sqlite3.IntegrityError:
            return None

    _set_request_status(req_id, "approved")
    return user


def reject_request(req_id: int) -> None:
    _set_request_status(req_id, "rejected")


def _set_request_status(req_id: int, status: str) -> None:
    with _lock:
        conn().execute(
            "UPDATE registration_requests SET status = ? WHERE id = ?",
            (status, req_id),
        )
        conn().commit()


# --------------------------------------------------------------------------- #
# Spots
# --------------------------------------------------------------------------- #
def all_spots() -> List[sqlite3.Row]:
    return conn().execute("SELECT * FROM spots ORDER BY number").fetchall()


def get_spot_by_number(number: int) -> Optional[sqlite3.Row]:
    return conn().execute(
        "SELECT * FROM spots WHERE number = ?", (number,)
    ).fetchone()


def get_spot_by_id(spot_id: int) -> Optional[sqlite3.Row]:
    return conn().execute("SELECT * FROM spots WHERE id = ?", (spot_id,)).fetchone()


def owned_spot(user_id: int, day: Optional[str] = None) -> Optional[sqlite3.Row]:
    """The spot this user effectively owns on ``day`` (cycle-aware)."""
    day = day or today()
    for spot in all_spots():
        if effective_owner_id(spot, day) == user_id:
            return spot
    return None


def user_owns_spot(user_id: int, day: Optional[str] = None) -> bool:
    return owned_spot(user_id, day) is not None


def manual_spot(user_id: int) -> Optional[sqlite3.Row]:
    """The spot manually assigned to a user, ignoring any active cycle."""
    for spot in all_spots():
        if spot["owner_user_id"] == user_id:
            return spot
    return None


def set_spot_type(number: int, spot_type: str) -> None:
    with _lock:
        conn().execute(
            "UPDATE spots SET type = ? WHERE number = ?", (spot_type, number)
        )
        conn().commit()


def assign_spot(number: int, user_id: int) -> None:
    """Give ``number`` to ``user_id``. One user owns one spot, so any other
    spot they held is freed first (a move, not a second ownership)."""
    with _lock:
        conn().execute(
            "UPDATE spots SET owner_user_id = NULL "
            "WHERE owner_user_id = ? AND number != ?",
            (user_id, number),
        )
        conn().execute(
            "UPDATE spots SET owner_user_id = ? WHERE number = ?",
            (user_id, number),
        )
        conn().commit()


def unassign_spot(number: int) -> None:
    with _lock:
        conn().execute(
            "UPDATE spots SET owner_user_id = NULL WHERE number = ?", (number,)
        )
        conn().commit()


# --------------------------------------------------------------------------- #
# Rotation cycles (a schedule of who holds which spot for a date range)
# --------------------------------------------------------------------------- #
def add_cycle(
    start_date: str,
    end_date: str,
    assignments: List[tuple],
    label: Optional[str] = None,
) -> int:
    """Create a cycle. ``assignments`` is a list of ``(spot_number, user_id)``.

    One user owns one spot, so a duplicate spot or a duplicate user inside
    the same cycle raises ``ValueError`` and nothing is saved.
    """
    seen_spots: set = set()
    seen_users: set = set()
    for number, user_id in assignments:
        if number in seen_spots:
            raise ValueError(f"Spot #{number} is listed twice in one cycle.")
        if user_id in seen_users:
            raise ValueError("One user can own one spot — a name is listed twice.")
        seen_spots.add(number)
        seen_users.add(user_id)
    with _lock:
        try:
            cur = conn().execute(
                "INSERT INTO rotation_cycles (label, start_date, end_date) "
                "VALUES (?, ?, ?)",
                (label, start_date, end_date),
            )
            cycle_id = cur.lastrowid
            conn().executemany(
                "INSERT INTO rotation_assignments (cycle_id, spot_number, user_id) "
                "VALUES (?, ?, ?)",
                [(cycle_id, number, user_id) for number, user_id in assignments],
            )
            conn().commit()
        except sqlite3.IntegrityError as exc:
            conn().rollback()
            raise ValueError(
                "One user can own one spot — duplicate spot or user."
            ) from exc
    return cycle_id


def all_cycles() -> List[sqlite3.Row]:
    return conn().execute(
        "SELECT * FROM rotation_cycles ORDER BY start_date, id"
    ).fetchall()


def get_cycle(cycle_id: int) -> Optional[sqlite3.Row]:
    return conn().execute(
        "SELECT * FROM rotation_cycles WHERE id = ?", (cycle_id,)
    ).fetchone()


def current_cycle(day: Optional[str] = None) -> Optional[sqlite3.Row]:
    """The cycle covering ``day`` (latest start wins if ranges overlap)."""
    day = day or today()
    return conn().execute(
        "SELECT * FROM rotation_cycles WHERE start_date <= ? AND end_date >= ? "
        "ORDER BY start_date DESC, id DESC LIMIT 1",
        (day, day),
    ).fetchone()


def cycle_assignments(cycle_id: int) -> List[sqlite3.Row]:
    return conn().execute(
        "SELECT ra.spot_number, ra.user_id, u.name AS user_name "
        "FROM rotation_assignments ra JOIN users u ON u.id = ra.user_id "
        "WHERE ra.cycle_id = ? ORDER BY ra.spot_number",
        (cycle_id,),
    ).fetchall()


def delete_cycle(cycle_id: int) -> None:
    with _lock:
        conn().execute("DELETE FROM rotation_cycles WHERE id = ?", (cycle_id,))
        conn().commit()


def delete_all_cycles() -> None:
    with _lock:
        conn().execute("DELETE FROM rotation_assignments")
        conn().execute("DELETE FROM rotation_cycles")
        conn().commit()


def cycle_owner_id(spot_number: int, day: Optional[str] = None) -> Optional[int]:
    """User id assigned to ``spot_number`` by the cycle covering ``day``."""
    cycle = current_cycle(day)
    if cycle is None:
        return None
    row = conn().execute(
        "SELECT user_id FROM rotation_assignments "
        "WHERE cycle_id = ? AND spot_number = ?",
        (cycle["id"], spot_number),
    ).fetchone()
    return row["user_id"] if row is not None else None


def effective_owner_id(spot: sqlite3.Row, day: Optional[str] = None) -> Optional[int]:
    """Cycle assignment for ``day`` if a cycle is active, else manual owner.

    While a cycle is active it is the whole schedule: spots not listed in
    the cycle count as unassigned (their manual owner returns when no cycle
    covers the day). This keeps "one user owns one spot" true during cycles.
    """
    if current_cycle(day) is None:
        return spot["owner_user_id"]
    return cycle_owner_id(spot["number"], day)


def rotation_end() -> Optional[date]:
    """Last day of the active rotation cycle, else the configured ROTATION_END."""
    cycle = current_cycle()
    if cycle is not None:
        try:
            return date.fromisoformat(cycle["end_date"])
        except ValueError:
            pass
    return config.rotation_end()


# --------------------------------------------------------------------------- #
# Openings (owner says "my spot is free")
# --------------------------------------------------------------------------- #
def close_openings(spot_id: int) -> None:
    with _lock:
        conn().execute(
            "UPDATE openings SET closed = 1 WHERE spot_id = ? AND closed = 0",
            (spot_id,),
        )
        conn().commit()


def open_spot(
    spot_id: int,
    user_id: int,
    start_date: str,
    end_date: Optional[str],
    dates: Optional[List[str]] = None,
) -> None:
    """Mark a spot open.

    ``dates`` (optional list of ISO days) replaces the range check with an
    exact set of days. If ``dates`` is None, a [start_date, end_date] range is
    used (end_date=None means "until the owner closes it").
    """
    close_openings(spot_id)
    dates_json = json.dumps(dates) if dates else None
    with _lock:
        conn().execute(
            "INSERT INTO openings (spot_id, user_id, start_date, end_date, dates) "
            "VALUES (?, ?, ?, ?, ?)",
            (spot_id, user_id, start_date, end_date, dates_json),
        )
        conn().commit()


def active_opening(spot_id: int, day: str) -> Optional[sqlite3.Row]:
    row = conn().execute(
        "SELECT * FROM openings WHERE spot_id = ? AND closed = 0 "
        "ORDER BY id DESC LIMIT 1",
        (spot_id,),
    ).fetchone()
    if row is None:
        return None
    if row["dates"]:
        try:
            return row if day in json.loads(row["dates"]) else None
        except ValueError:
            return None
    if (row["start_date"] is None or row["start_date"] <= day) and (
        row["end_date"] is None or row["end_date"] >= day
    ):
        return row
    return None


def owned_openings(user_id: int) -> List[sqlite3.Row]:
    return conn().execute(
        "SELECT * FROM openings WHERE user_id = ? AND closed = 0",
        (user_id,),
    ).fetchall()


def current_opening(spot_id: int, owner_id: Optional[int] = None) -> Optional[sqlite3.Row]:
    if owner_id is None:
        return conn().execute(
            "SELECT * FROM openings WHERE spot_id = ? AND closed = 0 "
            "ORDER BY id DESC LIMIT 1",
            (spot_id,),
        ).fetchone()
    return conn().execute(
        "SELECT * FROM openings WHERE spot_id = ? AND closed = 0 AND user_id = ? "
        "ORDER BY id DESC LIMIT 1",
        (spot_id, owner_id),
    ).fetchone()


def _opening_day_set(row: sqlite3.Row) -> set:
    if row["dates"]:
        try:
            return set(json.loads(row["dates"]))
        except ValueError:
            return set()
    days: set = set()
    start = date.fromisoformat(row["start_date"])
    if row["end_date"]:
        end = date.fromisoformat(row["end_date"])
    else:
        end = rotation_end() or (date.today() + timedelta(days=365))
    d = start
    while d <= end:
        days.add(d.isoformat())
        d += timedelta(days=1)
    return days


def opening_days(spot_id: int, owner_id: Optional[int] = None) -> List[str]:
    """Today + future ISO days on which the spot is currently open (sorted).

    When ``owner_id`` is given, only an opening by that user counts (so an
    opening left over by a previous rotation-cycle owner does not show up).
    """
    row = current_opening(spot_id, owner_id)
    if row is None:
        return []
    today = date.today()
    return sorted(d for d in _opening_day_set(row) if date.fromisoformat(d) >= today)


def close_spot_days(spot_id: int, days, owner_id: Optional[int] = None) -> int:
    """Take back specific days from the spot's current opening.

    Returns how many of the requested days were actually open. When the opening
    is an open-ended/range one, it is materialised into an explicit day list.
    """
    row = current_opening(spot_id, owner_id)
    if row is None:
        return 0
    existing = _opening_day_set(row)
    remove = set(days)
    removed = existing & remove
    remaining = existing - remove
    if not remaining:
        close_openings(spot_id)
        return len(removed)
    keep = sorted(remaining)
    with _lock:
        conn().execute(
            "UPDATE openings SET dates = ?, start_date = ?, end_date = ? WHERE id = ?",
            (json.dumps(keep), keep[0], keep[-1], row["id"]),
        )
        conn().commit()
    return len(removed)


# --------------------------------------------------------------------------- #
# Claims ("I parked in that free spot")
# --------------------------------------------------------------------------- #
def active_claim_spot(spot_id: int, day: str) -> Optional[sqlite3.Row]:
    return conn().execute(
        "SELECT * FROM claims WHERE spot_id = ? AND date = ? AND active = 1 "
        "ORDER BY id DESC LIMIT 1",
        (spot_id, day),
    ).fetchone()


def active_claim_user(user_id: int, day: str) -> Optional[sqlite3.Row]:
    return conn().execute(
        "SELECT * FROM claims WHERE user_id = ? AND date = ? AND active = 1 "
        "ORDER BY id DESC LIMIT 1",
        (user_id, day),
    ).fetchone()


def add_claim(spot_id: int, user_id: int, day: str) -> None:
    with _lock:
        conn().execute(
            "INSERT INTO claims (spot_id, user_id, date, active) VALUES (?, ?, ?, 1)",
            (spot_id, user_id, day),
        )
        conn().commit()


def release_claim(claim_id: int) -> None:
    with _lock:
        conn().execute("UPDATE claims SET active = 0 WHERE id = ?", (claim_id,))
        conn().commit()


def expire_old_claims() -> List[sqlite3.Row]:
    """Auto-release claims belonging to a past date.

    Returns the expired rows (joined with spot number, telegram id and a
    ``still_open`` flag = whether the owner's opening still covers today) and
    marks them inactive in the database. Safe to call any time; rows already
    released are left untouched.
    """
    day = today()
    expired = conn().execute(
        "SELECT c.id, c.spot_id, c.user_id, c.date, "
        "s.number AS spot_number, u.telegram_id AS telegram_id, "
        "op.id IS NOT NULL AS still_open "
        "FROM claims c "
        "JOIN spots s ON s.id = c.spot_id "
        "JOIN users u ON u.id = c.user_id "
        "LEFT JOIN openings op ON op.spot_id = c.spot_id AND op.closed = 0 AND ("
        "   (op.dates IS NOT NULL AND op.dates LIKE ?) "
        "   OR (op.dates IS NULL AND op.start_date <= ? "
        "       AND (op.end_date IS NULL OR op.end_date >= ?))"
        ") "
        "WHERE c.active = 1 AND c.date < ?",
        (f'%"{day}"%', day, day, day),
    ).fetchall()
    if expired:
        with _lock:
            conn().executemany(
                "UPDATE claims SET active = 0 WHERE id = ?",
                [(row["id"],) for row in expired],
            )
            conn().commit()
    return expired


def reset_claims(day: Optional[str] = None) -> int:
    with _lock:
        if day:
            cur = conn().execute(
                "UPDATE claims SET active = 0 WHERE active = 1 AND date = ?", (day,)
            )
        else:
            cur = conn().execute("UPDATE claims SET active = 0 WHERE active = 1")
        conn().commit()
        return cur.rowcount


# --------------------------------------------------------------------------- #
# Computed status
# --------------------------------------------------------------------------- #
OPEN = "open"
OCCUPIED = "occupied"
OWNER = "owner"
UNASSIGNED = "unassigned"


def spot_status(spot: sqlite3.Row, day: str) -> tuple[str, Optional[sqlite3.Row], Any]:
    """Return (state, user, record) for a spot on a given day.

    state is one of: OCCUPIED, OPEN, OWNER, UNASSIGNED.
    """
    owner_id = effective_owner_id(spot, day)
    claim = active_claim_spot(spot["id"], day)
    if claim:
        return OCCUPIED, get_user(claim["user_id"]), claim
    opening = active_opening(spot["id"], day)
    if opening and (owner_id is None or opening["user_id"] == owner_id):
        return OPEN, get_user(opening["user_id"]), opening
    if owner_id:
        return OWNER, get_user(owner_id), None
    return UNASSIGNED, None, None