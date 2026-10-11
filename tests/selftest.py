"""Standalone logic test — no Telegram token required.

Run from the project root:  python tests/selftest.py
"""
from __future__ import annotations

import os
import sys
import tempfile
from datetime import date

# Use a throwaway database; the spot layout comes from bot/layout.py.
tmp_db = os.path.join(tempfile.gettempdir(), "parking_selftest.db")
if os.path.exists(tmp_db):
    os.remove(tmp_db)
os.environ["DB_PATH"] = tmp_db

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from bot import db  # noqa: E402


def check(label: str, condition: bool) -> None:
    status = "PASS" if condition else "FAIL"
    print(f"[{status}] {label}")
    if not condition:
        raise SystemExit(1)


def main() -> None:
    db.init_db()

    spots = db.all_spots()
    check("9 spots seeded", len(spots) == 9)
    reserved = sorted(s["number"] for s in spots if s["type"] == "reserved")
    rotating = sorted(s["number"] for s in spots if s["type"] == "rotating")
    check("reserved = 1,2,5,6", reserved == [1, 2, 5, 6])
    check("rotating = 3,4,7,8,9", rotating == [3, 4, 7, 8, 9])

    admin = db.create_user(1001, "Admin", is_admin=True)
    alice = db.create_user(1002, "Alice")  # owns rotating spot 3
    bob = db.create_user(1003, "Bob")      # owns reserved spot 1
    carol = db.create_user(1004, "Carol")  # owns nothing -> can claim

    db.assign_spot(3, alice["id"])
    db.assign_spot(1, bob["id"])
    check("alice owns #3", db.owned_spot(alice["id"])["number"] == 3)
    check("bob owns #1", db.owned_spot(bob["id"])["number"] == 1)
    check("carol owns nothing", db.owned_spot(carol["id"]) is None)
    check("carol cannot claim own spot", db.user_owns_spot(carol["id"]) is False)

    day = db.today()

    # Spot 3 is not open yet -> OWNER
    st, who, _ = db.spot_status(db.get_spot_by_number(3), day)
    check("spot 3 starts as OWNER", st == db.OWNER and who["name"] == "Alice")

    # Alice opens her spot until closed.
    db.open_spot(db.get_spot_by_number(3)["id"], alice["id"], day, None)
    st, who, _ = db.spot_status(db.get_spot_by_number(3), day)
    check("spot 3 is OPEN", st == db.OPEN and who["name"] == "Alice")

    # Carol claims it (she parked there).
    db.add_claim(db.get_spot_by_number(3)["id"], carol["id"], day)
    st, who, _ = db.spot_status(db.get_spot_by_number(3), day)
    check("spot 3 is OCCUPIED by Carol", st == db.OCCUPIED and who["name"] == "Carol")
    check("carol has active claim", db.active_claim_user(carol["id"], day) is not None)

    # Bob tries to claim but he owns a spot -> the handler blocks it; verify ownership.
    check("bob owns a spot (blocked from claiming)", db.user_owns_spot(bob["id"]) is True)

    # Carol releases -> spot becomes OPEN again.
    claim = db.active_claim_user(carol["id"], day)
    db.release_claim(claim["id"])
    st, _, _ = db.spot_status(db.get_spot_by_number(3), day)
    check("spot 3 OPEN after release", st == db.OPEN)

    # Alice closes -> back to OWNER.
    db.close_openings(db.get_spot_by_number(3)["id"])
    st, _, _ = db.spot_status(db.get_spot_by_number(3), day)
    check("spot 3 OWNER after close", st == db.OWNER)

    # Unassigned spot (e.g. during rotation) is free to claim.
    db.unassign_spot(5)
    st, _, _ = db.spot_status(db.get_spot_by_number(5), day)
    check("unassigned spot 5 is free", st == db.UNASSIGNED)

    # --- Auto-release of claims the next day (only meaningful if still open) ---
    spot6 = db.get_spot_by_number(6)
    db.open_spot(spot6["id"], alice["id"], day, None)  # owner sharing until closed
    db.add_claim(spot6["id"], carol["id"], day)        # today's claim (kept)
    cur = db.conn().execute(
        "INSERT INTO claims (spot_id, user_id, date, active) VALUES (?, ?, ?, 1)",
        (spot6["id"], carol["id"], db.plus_days(-1)),
    )
    old_id = cur.lastrowid
    check(
        "yesterday+today claims both recorded",
        db.active_claim_spot(spot6["id"], day) is not None,
    )

    expired = db.expire_old_claims()
    expired_ids = [r["id"] for r in expired]
    check("yesterday's claim was auto-released", old_id in expired_ids)
    check("today's claim is NOT auto-released", spot6["id"] not in expired_ids)
    open_row = next(r for r in expired if r["id"] == old_id)
    check("spot still open -> still_open=1", bool(open_row["still_open"]) is True)
    check("spot 6 still occupied today", db.spot_status(spot6, day)[0] == db.OCCUPIED)

    # Owner closes the spot -> an equivalent old claim reports still_open=0.
    db.close_openings(spot6["id"])
    db.add_claim(spot6["id"], carol["id"], db.plus_days(-2))
    cur2 = db.conn().execute(
        "INSERT INTO claims (spot_id, user_id, date, active) VALUES (?, ?, ?, 1)",
        (spot6["id"], carol["id"], db.plus_days(-2)),
    )
    expired2 = db.expire_old_claims()
    closed_row = next((r for r in expired2 if r["id"] == cur2.lastrowid), None)
    check("claim on closed spot -> still_open=0",
          closed_row is not None and bool(closed_row["still_open"]) is False)

    # Clean up Carol's today claim so the reassignment below stays unambiguous.
    today_claim = db.active_claim_user(carol["id"], day)
    db.release_claim(today_claim["id"])

    # Reassign rotating spot to a new owner.
    db.assign_spot(3, carol["id"])
    check("spot 3 reassigned to Carol", db.owned_spot(carol["id"])["number"] == 3)

    # --- Pre-created users + admin approval ---
    dana = db.add_pending_user("Dana")
    check("admin pre-creates a pending user", dana is not None and dana["telegram_id"] is None)
    check("duplicate name rejected (case-insensitive)", db.add_pending_user("dana") is None)

    req = db.upsert_request(1005, "Dana", "dana_tg")
    check("registration request created as pending", req["status"] == "pending")
    check("pending request listed", any(r["id"] == req["id"] for r in db.pending_requests()))

    linked = db.approve_request(req["id"])
    check("approval links the pre-created account",
          linked is not None and linked["telegram_id"] == 1005 and linked["name"] == "Dana")
    check("approved request no longer pending",
          db.get_request(req["id"])["status"] == "approved")

    # A brand-new name that was never pre-created is created on approval.
    req2 = db.upsert_request(1006, "Erin", None)
    erin = db.approve_request(req2["id"])
    check("approval creates an unknown user", erin is not None and erin["telegram_id"] == 1006)
    check("bound user resolvable by tg", db.get_user_by_tg(1006)["name"] == "Erin")

    req3 = db.upsert_request(1007, "Frank", None)
    db.reject_request(req3["id"])
    check("rejected request is not registered",
          db.get_request(req3["id"])["status"] == "rejected" and db.get_user_by_tg(1007) is None)

    # --- Date-picked openings ---
    spot4 = db.get_spot_by_number(4)
    picked = [day, db.plus_days(1)]
    db.open_spot(spot4["id"], alice["id"], picked[0], picked[-1], dates=picked)
    check("date-picked opening is OPEN on a chosen day",
          db.spot_status(spot4, day)[0] == db.OPEN)
    check("date-picked opening is NOT open on another day",
          db.spot_status(spot4, db.plus_days(2))[0] != db.OPEN)

    # --- Close specific days of an opening ---
    check("opening_days lists the chosen days",
          db.opening_days(spot4["id"]) == sorted(picked))
    removed = db.close_spot_days(spot4["id"], [day])
    check("close_spot_days removed the requested day", removed == 1)
    check("closed day is no longer open", db.spot_status(spot4, day)[0] != db.OPEN)
    check("remaining day is still open",
          db.spot_status(spot4, db.plus_days(1))[0] == db.OPEN)
    remaining = db.opening_days(spot4["id"])
    db.close_spot_days(spot4["id"], remaining)
    check("closing every day stops sharing", db.current_opening(spot4["id"]) is None)

    # --- Rotation-cycle plan parsing ---
    from bot import cycles as cycle_parser

    parsed = cycle_parser.parse_cycles(
        "Cycle 1 12/10/26-31/12/26\n"
        "1 - Test\n"
        "2 - Test2\n"
        "Cycle 2 01/01/27-31/03/27\n"
        "1 - test3\n"
        "2 - Some Long Name"
    )
    check(
        "parser reads two cycles with day-first dates",
        len(parsed) == 2
        and parsed[0].start == "2026-10-12"
        and parsed[0].end == "2026-12-31"
        and parsed[1].start == "2027-01-01"
        and parsed[1].assignments[-1] == (2, "Some Long Name"),
    )
    try:
        cycle_parser.parse_cycles("Cycle 1 31/12/26-01/12/26\n3 - Alice")
        reversed_ok = True
    except cycle_parser.CycleParseError:
        reversed_ok = False
    check("parser rejects an end date before the start", not reversed_ok)

    # --- Active cycle auto-applies ownership ---
    cycle_id = db.add_cycle(
        db.plus_days(-1),
        db.plus_days(30),
        [(3, bob["id"]), (9, alice["id"])],
        label="Cycle Test",
    )
    check("current cycle detected", (db.current_cycle() or {})["id"] == cycle_id)
    check(
        "cycle overrides spot 3's manual owner",
        db.effective_owner_id(db.get_spot_by_number(3), day) == bob["id"],
    )
    check("owned_spot returns a spot the cycle assigns to the user",
          db.owned_spot(bob["id"]) is not None and
          db.effective_owner_id(db.owned_spot(bob["id"]), day) == bob["id"])
    check(
        "rotation_end follows the active cycle",
        db.rotation_end().isoformat() == date.fromisoformat(db.plus_days(30)).isoformat(),
    )
    st3, who3, _ = db.spot_status(db.get_spot_by_number(3), day)
    check(
        "spot 3 shows Bob as owner via the cycle",
        st3 == db.OWNER and who3["id"] == bob["id"],
    )
    check(
        "unlisted spot is unassigned while a cycle is active",
        db.effective_owner_id(db.get_spot_by_number(1), day) is None
        and db.spot_status(db.get_spot_by_number(1), day)[0] == db.UNASSIGNED,
    )
    try:
        db.add_cycle(db.plus_days(-1), db.plus_days(30), [(4, bob["id"]), (5, bob["id"])])
        dup_ok = True
    except ValueError:
        dup_ok = False
    check("one user cannot own two spots in one cycle", not dup_ok)
    db.delete_all_cycles()
    check(
        "clearing cycles reverts to the manual owner",
        db.effective_owner_id(db.get_spot_by_number(3), day) == carol["id"],
    )

    # --- One user owns one spot: assigning moves, never duplicates ---
    db.assign_spot(2, bob["id"])
    check(
        "assign moves the user off their old spot",
        db.owned_spot(bob["id"])["number"] == 2
        and db.get_spot_by_number(1)["owner_user_id"] is None,
    )
    db.assign_spot(1, bob["id"])
    check("assign restores the original spot", db.owned_spot(bob["id"])["number"] == 1)
    check("manual_spot finds the user by ownership",
          db.manual_spot(bob["id"])["number"] == 1)
    check("manual_spot is None for a user with no spot",
          db.manual_spot(erin["id"]) is None)
    check("one admin at first", db.count_admins() == 1)
    db.set_admin(erin["id"], True)
    check("second admin promoted", db.count_admins() == 2
          and db.get_user(erin["id"])["is_admin"] == 1)
    db.set_admin(erin["id"], False)
    check("demote restores one admin", db.count_admins() == 1)

    # --- Delete a user frees their spot and drops their data ---
    db.assign_spot(9, carol["id"])
    db.add_claim(db.get_spot_by_number(9)["id"], carol["id"], day)
    db.delete_user(carol["id"])
    check("deleted user is gone", db.get_user(carol["id"]) is None)
    check("deleted user's spot is freed",
          db.get_spot_by_number(9)["owner_user_id"] is None)
    check("deleted user's claims are gone",
          db.active_claim_spot(db.get_spot_by_number(9)["id"], day) is None)

    print("\nAll checks passed.")

    # Map render smoke test (skips gracefully if Pillow is missing).
    try:
        from bot import parking_map
    except ImportError:
        print("[SKIP] parking map render (Pillow not installed)")
    else:
        try:
            png = parking_map.render_map(owner_user_id=alice["id"], day=day)
            is_png = png.startswith(b"\x89PNG\r\n\x1a\n") and len(png) > 1000
            check("map renders a valid PNG", is_png)
            png2 = parking_map.render_map(owner_user_id=alice["id"], day=db.plus_days(3))
            check("map renders for a future day", png2.startswith(b"\x89PNG\r\n\x1a\n"))
        except Exception as exc:  # report failures (e.g. missing fonts are OK)
            check(f"map renders a valid PNG ({exc})", False)

    # Keyboard builders (need the telegram lib; skip if unavailable).
    try:
        from bot import keyboards
        from bot.handlers import user as user_handlers
    except ImportError:
        print("[SKIP] keyboard builders (python-telegram-bot not installed)")
    else:
        nav = keyboards.map_nav_kb(db.plus_days(-1), db.plus_days(1), day)
        check("map nav keyboard builds", len(nav.inline_keyboard) == 2)
        check(
            "map Pick-a-date opens the viewed day",
            nav.inline_keyboard[1][0].callback_data == f"map:pick:{day}",
        )
        cal = keyboards.map_calendar_kb(day, 2026, 12, min_day=day, max_day="2026-12-31", today=day)
        check("map calendar keyboard builds", len(cal.inline_keyboard) >= 7)
        check(
            "map calendar title opens the month picker",
            cal.inline_keyboard[0][0].callback_data == "mapcal:months:2026-12",
        )
        pick = keyboards.datepicker_kb({day}, 2026, 10, min_day=day, max_day=day)
        check("date-picker keyboard builds", len(pick.inline_keyboard) >= 6)
        check(
            "date-picker title opens the month picker",
            pick.inline_keyboard[0][0].callback_data == "cal:months",
        )
        grid = keyboards.month_grid_kb(
            2026, "cal", min_ym=(2026, 10), max_ym=(2026, 12),
            back_callback="cal:back",
        )
        months = [
            b.callback_data for r in grid.inline_keyboard[1:-1] for b in r
            if b.callback_data.startswith("cal:month:")
        ]
        check("month grid lists in-range months", len(months) == 3)
        check(
            "month grid back button returns to days",
            grid.inline_keyboard[-1][0].callback_data == "cal:back",
        )
        future = keyboards.month_grid_kb(
            date.today().year + 1, "cal",
            min_ym=(date.today().year, date.today().month),
            max_ym=None,
            back_callback="cal:back",
        )
        future_months = [
            b.callback_data for r in future.inline_keyboard[1:-1] for b in r
            if b.callback_data.startswith("cal:month:")
        ]
        check("next year shows all 12 months", len(future_months) == 12)
        check("share picker has no rotation cap",
              user_handlers._max_open_day(None) is None)
        next_jan = keyboards.datepicker_kb(
            set(), date.today().year + 1, 1, min_day=day, max_day=None
        )
        jan_days = [
            b.callback_data for r in next_jan.inline_keyboard[2:-2] for b in r
            if b.callback_data.startswith("cal:day:")
        ]
        check("next january days are selectable", len(jan_days) == 31)

    # Admin notification on registration (catches import/runtime regressions).
    try:
        import asyncio

        from bot.handlers import registration
    except ImportError:
        print("[SKIP] registration notification (telegram lib missing)")
    else:
        class _StubBot:
            def __init__(self):
                self.sent = []

            async def send_message(self, chat_id, text, reply_markup=None, parse_mode=None):
                self.sent.append((chat_id, text, reply_markup))

        class _StubContext:
            def __init__(self):
                self.bot = _StubBot()

        ctx = _StubContext()
        req = db.upsert_request(2000, "NotifyTest", "notify_tg")
        asyncio.run(registration._notify_new_request(ctx, 2000, req))
        check(
            "registration sends an admin notification with buttons",
            len(ctx.bot.sent) >= 1 and ctx.bot.sent[0][2] is not None,
        )

    db.conn().close()
    try:
        os.remove(tmp_db)
    except OSError:
        pass


if __name__ == "__main__":
    main()
