from __future__ import annotations

from datetime import date, timedelta
from typing import List, Tuple

from telegram import InputMediaPhoto, Update
from telegram.ext import ContextTypes

from .. import db, keyboards, parking_map
from .common import escape, get_db_user, menu, need_registration, reply

CAL_STATE = "parking_cal"
CLOSE_STATE = "parking_close"
CLOSE_MAX_DAYS = 28

# --------------------------------------------------------------------------- #
# Views
# --------------------------------------------------------------------------- #
def _status_text(user) -> str:
    day = db.today()
    lines = [f"📋 <b>Status for {escape(user['name'])}</b>", f"<i>{day}</i>", ""]

    spot = db.owned_spot(user["id"])
    if spot is not None:
        state, other, _ = db.spot_status(spot, day)
        lines.append(
            f"Your spot: <b>#{spot['number']}</b> ({escape(spot['type'])})"
        )
        if state == db.OPEN:
            lines.append("🔓 Marked <b>open</b> — colleagues can take it today.")
        elif state == db.OCCUPIED:
            who = other["name"] if other is not None else "someone"
            lines.append(f"🚗 Taken today by <b>{escape(who)}</b>.")
        else:
            lines.append("🔒 Reserved for you (not shared).")
        end = db.rotation_end()
        if end is not None:
            lines.append(f"⏳ Rotation valid until <b>{end.isoformat()}</b>.")
    else:
        lines.append("You don't have a reserved or rotating spot.")
        claim = db.active_claim_user(user["id"], day)
        if claim is not None:
            s = db.get_spot_by_id(claim["spot_id"])
            if s is not None:
                lines.append(
                    f"🚗 You are parked in spot <b>#{s['number']}</b> today."
                )
        else:
            lines.append(
                "Check <b>Available spots</b> to find one you can use."
            )
    return "\n".join(lines)


def _available_text() -> Tuple[str, List[Tuple[int, str]]]:
    day = db.today()
    lines = [f"🅿️ <b>Free spots today</b> ({day})", ""]
    available: List[Tuple[int, str]] = []

    for spot in db.all_spots():
        state, other, _ = db.spot_status(spot, day)
        if state == db.OPEN:
            who = other["name"] if other is not None else "the owner"
            lines.append(f"<b>#{spot['number']}</b> — freed by {escape(who)}")
            available.append((spot["number"], f"#{spot['number']} (was {who})"))
        elif state == db.UNASSIGNED:
            lines.append(f"<b>#{spot['number']}</b> — unassigned (always free)")
            available.append((spot["number"], f"#{spot['number']} (unassigned)"))

    if not available:
        lines.append("No spots are open right now.")
    return "\n".join(lines), available


# --------------------------------------------------------------------------- #
# Commands
# --------------------------------------------------------------------------- #
async def cmd_status(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if await need_registration(update):
        return
    await reply(update, _status_text(get_db_user(update)), menu(update))


async def cmd_available(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if await need_registration(update):
        return
    user = get_db_user(update)
    if db.user_owns_spot(user["id"]):
        await reply(
            update,
            "You already have your own spot — available spots are for "
            "colleagues without one.",
            menu(update),
        )
        return
    text, _ = _available_text()
    await reply(update, text, menu(update))


async def cmd_map(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if await need_registration(update):
        return
    await _send_map(update, get_db_user(update))


def _free_numbers(day: str) -> List[int]:
    return [
        spot["number"]
        for spot in db.all_spots()
        if db.spot_status(spot, day)[0] in (db.OPEN, db.UNASSIGNED)
    ]


def _map_caption(day: str) -> str:
    free = _free_numbers(day)
    free_txt = ", ".join(f"#{n}" for n in free) if free else "none"
    return (
        f"{parking_map.CAPTION}\n\n"
        f"📅 <b>{day}</b>\n"
        f"🟢 Free on this day: {free_txt}"
    )


def _map_nav_kb(day: str) -> "keyboards.InlineKeyboardMarkup":
    today = date.fromisoformat(db.today())
    d = date.fromisoformat(day)
    prev = max(d - timedelta(days=1), today).isoformat()
    nxt = (d + timedelta(days=1)).isoformat()
    return keyboards.map_nav_kb(prev, nxt, db.today(), day)


async def _send_map(update: Update, user, day: str | None = None) -> None:
    day = day or db.today()
    try:
        png = parking_map.render_map(owner_user_id=user["id"], day=day)
    except Exception:
        await reply(
            update,
            "Something went wrong rendering the map. "
            "Make sure Pillow is installed and layout.py is valid.",
            menu(update),
        )
        return
    caption = _map_caption(day)
    kb = _map_nav_kb(day)

    query = update.callback_query
    if query is not None and query.message is not None and query.message.photo:
        try:
            await query.edit_message_media(
                media=InputMediaPhoto(png, caption=caption, parse_mode="HTML"),
                reply_markup=kb,
            )
            return
        except Exception:
            pass

    target = query.message if query is not None else update.effective_message
    try:
        await target.reply_photo(
            photo=png, caption=caption, parse_mode="HTML", reply_markup=kb
        )
    except Exception:
        await reply(update, "Could not send the map image.", menu(update))


async def _map_pick(update: Update, day_iso: str) -> None:
    query = update.callback_query
    d = date.fromisoformat(day_iso)
    kb = keyboards.map_calendar_kb(
        day_iso,
        d.year,
        d.month,
        min_day=db.today(),
        max_day=None,
        today=db.today(),
    )
    try:
        await query.edit_message_caption(
            caption="📅 <b>Pick a date</b> to see which spots are free that day.",
            reply_markup=kb,
            parse_mode="HTML",
        )
    except Exception:
        await query.edit_message_reply_markup(reply_markup=kb)


async def _map_cal(update: Update, user, action: str) -> None:
    if action == "ignore":
        return
    if action.startswith("day:"):
        await _send_map(update, user, day=action.split(":", 1)[1])
        return
    today = date.today()
    lo = (today.year, today.month)

    def _grid(year: int, back_ym: str) -> "keyboards.InlineKeyboardMarkup":
        year = max(year, lo[0])
        return keyboards.month_grid_kb(
            year, "mapcal", min_ym=lo, max_ym=None,
            back_callback=f"mapcal:month:{back_ym}",
        )

    async def _day_view(year: int, month: int, sel: str) -> None:
        if (year, month) < lo:
            return
        kb = keyboards.map_calendar_kb(
            sel,
            year,
            month,
            min_day=db.today(),
            max_day=None,
            today=db.today(),
        )
        await update.callback_query.edit_message_reply_markup(reply_markup=kb)

    if action.startswith("months:"):
        ym = action.split(":", 1)[1]
        year, month = (int(x) for x in ym.split("-"))
        await update.callback_query.edit_message_reply_markup(
            reply_markup=_grid(year, ym)
        )
        return
    if action.startswith("yprev:") or action.startswith("ynext:"):
        year = int(action.split(":")[1])
        year += -1 if action.startswith("yprev:") else 1
        parts = action.split(":")
        back_ym = parts[2] if len(parts) > 2 else db.today()[:7]
        await update.callback_query.edit_message_reply_markup(
            reply_markup=_grid(year, back_ym)
        )
        return
    if action.startswith("month:"):
        ym = action.split(":", 1)[1]
        year, month = (int(x) for x in ym.split("-"))
        await _day_view(year, month, f"{year:04d}-{month:02d}-01")
        return
    if action.startswith("nav:"):
        ym, _, direction = action.split(":", 1)[1].partition(":")
        year, month = (int(x) for x in ym.split("-"))
        month += -1 if direction == "prev" else 1
        if month == 0:
            year, month = year - 1, 12
        elif month == 13:
            year, month = year + 1, 1
        today = date.today()
        lo = (today.year, today.month)
        if (year, month) < lo:
            return
        sel = f"{year:04d}-{month:02d}-01"
        kb = keyboards.map_calendar_kb(
            sel,
            year,
            month,
            min_day=db.today(),
            max_day=None,
            today=db.today(),
        )
        await update.callback_query.edit_message_reply_markup(reply_markup=kb)


async def cmd_open(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if await need_registration(update):
        return
    await _show_open_picker(update, context, get_db_user(update))


def _max_open_day(spot) -> str | None:
    # No upper cap: shares are recorded per owner and only take effect while
    # the opener is the spot's effective owner, so picking dates beyond the
    # current rotation window is safe (they apply if you still own the spot).
    return None


def _min_ym() -> tuple:
    """Current (year, month): nothing before this is selectable."""
    t = date.today()
    return (t.year, t.month)


def _cal_state(context: ContextTypes.DEFAULT_TYPE) -> dict:
    state = context.chat_data.get(CAL_STATE)
    if state is None:
        t = date.today()
        state = {"year": t.year, "month": t.month, "dates": set()}
        context.chat_data[CAL_STATE] = state
    return state


def _calendar_kb(state: dict, spot) -> "keyboards.InlineKeyboardMarkup":
    return keyboards.datepicker_kb(
        state["dates"],
        state["year"],
        state["month"],
        min_day=db.today(),
        max_day=_max_open_day(spot),
    )


def _calendar_text(state: dict, spot) -> str:
    chosen = sorted(state["dates"])
    if chosen:
        pretty = ", ".join(date.fromisoformat(d).strftime("%a %d %b") for d in chosen)
    else:
        pretty = "none yet"
    note = ""
    end = db.rotation_end()
    if end is not None and spot["type"] == "rotating":
        note = f"\n<i>Rotation plan valid until {end.isoformat()}.</i>"
    return (
        f"<b>Share spot #{spot['number']}</b>\n"
        "Tap the day(s) you won't drive, then <b>Open these days</b>.\n"
        f"Selected: {pretty}{note}"
    )


async def _show_open_picker(update: Update, context: ContextTypes.DEFAULT_TYPE, user) -> None:
    spot = db.owned_spot(user["id"])
    if spot is None:
        await reply(
            update,
            "You don't own a spot, so there's nothing to share.",
            keyboards.back_menu(),
        )
        return
    state = _cal_state(context)
    state["dates"] = set()
    today = date.today()
    state["year"], state["month"] = today.year, today.month
    await reply(update, _calendar_text(state, spot), _calendar_kb(state, spot))


async def cmd_close(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if await need_registration(update):
        return
    await _show_close(update, context, get_db_user(update))


def _close_text(spot, chosen) -> str:
    if chosen:
        pretty = ", ".join(date.fromisoformat(d).strftime("%a %d %b") for d in sorted(chosen))
    else:
        pretty = "none"
    return (
        f"<b>Stop sharing spot #{spot['number']}</b>\n"
        "Tap the day(s) you want to take back, then <b>Close selected days</b> "
        "(or <b>Close ALL days</b>).\n"
        f"Selected: {pretty}"
    )


def _clamp_days(days: List[str]) -> Tuple[List[str], str]:
    shown = days[:CLOSE_MAX_DAYS]
    note = ""
    if len(days) > CLOSE_MAX_DAYS:
        note = f"\n<i>Showing the next {CLOSE_MAX_DAYS} days.</i>"
    return shown, note


async def _show_close(update: Update, context: ContextTypes.DEFAULT_TYPE, user) -> None:
    spot = db.owned_spot(user["id"])
    if spot is None:
        await reply(update, "You don't own a spot.", menu(update))
        return
    days = db.opening_days(spot["id"], user["id"])
    if not days:
        await reply(
            update,
            f"Your spot <b>#{spot['number']}</b> isn't shared right now.",
            menu(update),
        )
        return
    context.chat_data[CLOSE_STATE] = set()
    shown, note = _clamp_days(days)
    await reply(
        update, _close_text(spot, set()) + note, keyboards.close_days_kb(shown, set())
    )


async def _handle_close(update: Update, context: ContextTypes.DEFAULT_TYPE, user, action: str) -> None:
    spot = db.owned_spot(user["id"])
    if spot is None:
        await reply(update, "You don't own a spot.", menu(update))
        return
    days = db.opening_days(spot["id"], user["id"])
    if not days:
        await reply(
            update,
            f"Your spot <b>#{spot['number']}</b> isn't shared right now.",
            menu(update),
        )
        return
    shown, note = _clamp_days(days)
    chosen = context.chat_data.setdefault(CLOSE_STATE, set())

    if action.startswith("day:"):
        iso = action.split(":", 1)[1]
        if iso in chosen:
            chosen.discard(iso)
        else:
            chosen.add(iso)
        await reply(
            update, _close_text(spot, chosen) + note, keyboards.close_days_kb(shown, chosen)
        )
        return
    if action == "all":
        db.close_openings(spot["id"])
        context.chat_data.pop(CLOSE_STATE, None)
        await reply(
            update,
            f"🔒 Spot <b>#{spot['number']}</b> is no longer shared.",
            menu(update),
        )
        return
    if action == "ok":
        days_to_close = sorted(chosen)
        if not days_to_close:
            await reply(update, _close_text(spot, chosen), keyboards.close_days_kb(shown, chosen))
            return
        count = db.close_spot_days(spot["id"], days_to_close, user["id"])
        context.chat_data.pop(CLOSE_STATE, None)
        pretty = ", ".join(
            date.fromisoformat(d).strftime("%a %d %b") for d in days_to_close
        )
        await reply(
            update,
            f"🔒 Closed <b>{count}</b> day(s): {pretty}.\n"
            "The spot stays shared on the remaining days.",
            menu(update),
        )
        return


async def cmd_claim(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if await need_registration(update):
        return
    user = get_db_user(update)
    text = _claim_prompt(update, user)
    if isinstance(text, tuple):
        body, keyboard = text
    else:
        body, keyboard = text, keyboards.back_menu()
    await reply(update, body, keyboard)


def _claim_prompt(update: Update, user):
    if db.user_owns_spot(user["id"]):
        return (
            "You already have your own spot, so you can't take someone else's.",
            keyboards.back_menu(),
        )
    day = db.today()
    existing = db.active_claim_user(user["id"], day)
    if existing is not None:
        s = db.get_spot_by_id(existing["spot_id"])
        number = s["number"] if s is not None else "?"
        return (
            f"You already parked in <b>#{number}</b> today. "
            "Release it first if you moved.",
            keyboards.back_menu(),
        )
    _, available = _available_text()
    if not available:
        return ("There are no free spots to claim today.", keyboards.back_menu())
    return (
        "Which spot did you park in? Tap the number:",
        keyboards.claim_menu(available),
    )


async def cmd_release(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if await need_registration(update):
        return
    user = get_db_user(update)
    if db.user_owns_spot(user["id"]):
        await reply(
            update,
            "You have your own spot, so claiming/releasing shared spots "
            "doesn't apply to you.",
            menu(update),
        )
        return
    claim = db.active_claim_user(user["id"], db.today())
    if claim is None:
        await reply(update, "You have no active spot to release today.", menu(update))
        return
    db.release_claim(claim["id"])
    s = db.get_spot_by_id(claim["spot_id"])
    number = s["number"] if s is not None else "?"
    await reply(
        update,
        f"✅ Released spot <b>#{number}</b>. It's free for others again.",
        menu(update),
    )


# --------------------------------------------------------------------------- #
# Callback router
# --------------------------------------------------------------------------- #
async def on_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    data = query.data or ""

    if data == "cancel" or data == "menu":
        if await need_registration(update):
            return
        await reply(update, "What would you like to do?", menu(update))
        return

    if await need_registration(update):
        return
    user = get_db_user(update)

    if data == "status":
        await reply(update, _status_text(user), menu(update))
    elif data == "avail":
        if db.user_owns_spot(user["id"]):
            await reply(
                update,
                "You already have your own spot — available spots are for "
                "colleagues without one.",
                menu(update),
            )
        else:
            text, _ = _available_text()
            await reply(update, text, menu(update))
    elif data == "map":
        await _send_map(update, user)
    elif data.startswith("map:day:"):
        await _send_map(update, user, day=data.split(":", 2)[2])
    elif data.startswith("map:pick:"):
        await _map_pick(update, data.split(":", 2)[2])
    elif data.startswith("mapcal:"):
        await _map_cal(update, user, data.split(":", 1)[1])
    elif data == "open":
        await _show_open_picker(update, context, user)
    elif data.startswith("cal:"):
        await _handle_cal(update, context, user, data.split(":", 1)[1])
    elif data == "close":
        await _show_close(update, context, user)
    elif data.startswith("clz:"):
        await _handle_close(update, context, user, data.split(":", 1)[1])
    elif data == "claim":
        result = _claim_prompt(update, user)
        body, keyboard = result if isinstance(result, tuple) else (result, keyboards.back_menu())
        await reply(update, body, keyboard)
    elif data.startswith("claim:"):
        await _handle_claim(update, user, data.split(":", 1)[1])
    elif data == "release":
        if db.user_owns_spot(user["id"]):
            await reply(
                update,
                "You have your own spot, so claiming/releasing shared spots "
                "doesn't apply to you.",
                menu(update),
            )
            return
        claim = db.active_claim_user(user["id"], db.today())
        if claim is None:
            await reply(update, "You have no active spot to release today.", menu(update))
        else:
            db.release_claim(claim["id"])
            s = db.get_spot_by_id(claim["spot_id"])
            number = s["number"] if s is not None else "?"
            await reply(
                update,
                f"✅ Released spot <b>#{number}</b>. It's free for others again.",
                menu(update),
            )
    else:
        await reply(update, "What would you like to do?", menu(update))


def _month_bounds(spot) -> tuple:
    """Bounds for the share-spot month picker.

    Only the past is off-limits: every current/future month is selectable.
    Returns ``(lo, hi_nav, max_ym)`` with no upper cap (``hi_nav``/``max_ym``
    are None).
    """
    return _min_ym(), None, None


def _month_grid_kb(state: dict, spot) -> "keyboards.InlineKeyboardMarkup":
    lo, _, _ = _month_bounds(spot)
    year = max(state["year"], lo[0])
    state["year"] = year
    return keyboards.month_grid_kb(
        year, "cal", min_ym=lo, max_ym=None, back_callback="cal:back"
    )


async def _handle_cal(update: Update, context: ContextTypes.DEFAULT_TYPE, user, action: str) -> None:
    spot = db.owned_spot(user["id"])
    if spot is None:
        await reply(update, "You don't own a spot.", keyboards.back_menu())
        return

    state = _cal_state(context)
    today = date.today()

    if action == "ignore":
        return
    if action == "months":
        await reply(update, _calendar_text(state, spot), _month_grid_kb(state, spot))
        return
    if action == "back":
        await reply(update, _calendar_text(state, spot), _calendar_kb(state, spot))
        return
    if action.startswith("yprev:") or action.startswith("ynext:"):
        year = int(action.split(":")[1])
        year += -1 if action.startswith("yprev:") else 1
        state["year"] = year
        await reply(update, _calendar_text(state, spot), _month_grid_kb(state, spot))
        return
    if action.startswith("month:"):
        ym = action.split(":", 1)[1]
        year, month = (int(x) for x in ym.split("-"))
        lo, _, _ = _month_bounds(spot)
        if (year, month) < lo:
            return
        state["year"], state["month"] = year, month
        await reply(update, _calendar_text(state, spot), _calendar_kb(state, spot))
        return
    if action in ("prev", "next"):
        step = -1 if action == "prev" else 1
        month = state["month"] + step
        year = state["year"]
        if month == 0:
            month, year = 12, year - 1
        elif month == 13:
            month, year = 1, year + 1
        # Don't navigate before the current month; the future is open.
        if (year, month) >= (today.year, today.month):
            state["year"], state["month"] = year, month
        await reply(update, _calendar_text(state, spot), _calendar_kb(state, spot))
        return
    if action.startswith("day:"):
        iso = action.split(":", 1)[1]
        max_day = _max_open_day(spot)
        if iso < db.today() or (max_day and iso > max_day):
            return
        if iso in state["dates"]:
            state["dates"].discard(iso)
        else:
            state["dates"].add(iso)
        await reply(update, _calendar_text(state, spot), _calendar_kb(state, spot))
        return
    if action == "until":
        db.open_spot(spot["id"], user["id"], db.today(), None)
        context.chat_data.pop(CAL_STATE, None)
        await reply(
            update,
            f"🔓 Spot <b>#{spot['number']}</b> is now open until you close it. "
            "Colleagues without a spot can take it.",
            menu(update),
        )
        return
    if action == "ok":
        chosen = sorted(state["dates"])
        if not chosen:
            await reply(update, _calendar_text(state, spot), _calendar_kb(state, spot))
            return
        db.open_spot(spot["id"], user["id"], chosen[0], chosen[-1], dates=chosen)
        context.chat_data.pop(CAL_STATE, None)
        pretty = ", ".join(date.fromisoformat(d).strftime("%a %d %b") for d in chosen)
        await reply(
            update,
            f"🔓 Spot <b>#{spot['number']}</b> is now open on: {pretty}.\n"
            "Colleagues without a spot can take it.",
            menu(update),
        )
        return
    await reply(update, _calendar_text(state, spot), _calendar_kb(state, spot))


async def _handle_claim(update: Update, user, raw_number: str) -> None:
    if db.user_owns_spot(user["id"]):
        await reply(
            update,
            "You already have your own spot, so you can't take someone else's.",
            keyboards.back_menu(),
        )
        return
    try:
        number = int(raw_number)
    except ValueError:
        await reply(update, "Unknown spot.", keyboards.back_menu())
        return

    day = db.today()
    existing = db.active_claim_user(user["id"], day)
    if existing is not None:
        await reply(
            update,
            "You already have an active spot for today.",
            menu(update),
        )
        return

    spot = db.get_spot_by_number(number)
    if spot is None:
        await reply(update, "That spot doesn't exist.", keyboards.back_menu())
        return

    state, other, _ = db.spot_status(spot, day)
    if state == db.OPEN:
        if other is not None and other["id"] == user["id"]:
            await reply(update, "That's your own spot.", keyboards.back_menu())
            return
    elif state == db.UNASSIGNED:
        pass
    else:
        await reply(
            update,
            f"Spot <b>#{number}</b> is no longer available.",
            keyboards.back_menu(),
        )
        return

    db.add_claim(spot["id"], user["id"], day)
    await reply(
        update,
        f"🚗 You're parked in <b>#{number}</b> today.\n"
        "Your claim is only for today — it releases automatically at midnight. "
        "Tap <b>I left (release)</b> when you leave so others can use it "
        "right away.",
        menu(update),
    )
