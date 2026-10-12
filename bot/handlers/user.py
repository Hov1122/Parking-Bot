# -*- coding: utf-8 -*-
from __future__ import annotations

from datetime import date, timedelta
from typing import List, Tuple

from telegram import InputMediaPhoto, Update
from telegram.ext import ContextTypes

from .. import db, keyboards, parking_map
from ..i18n import pretty_day, t
from .common import escape, get_db_user, menu, need_registration, reply, set_role_commands

CAL_STATE = "parking_cal"
CLOSE_STATE = "parking_close"
CLOSE_MAX_DAYS = 28

# --------------------------------------------------------------------------- #
# Views
# --------------------------------------------------------------------------- #
def _status_text(user) -> str:
    lang = db.user_lang(user)
    day = db.today()
    lines = [t(lang, "status_title", name=escape(user["name"])), f"<i>{day}</i>", ""]

    spot = db.owned_spot(user["id"])
    if spot is not None:
        state, other, _ = db.spot_status(spot, day)
        lines.append(
            t(lang, "your_spot", n=spot["number"], type=t(lang, f"type_{spot['type']}"))
        )
        if state == db.OPEN:
            lines.append(t(lang, "spot_open"))
        elif state == db.OCCUPIED:
            who = other["name"] if other is not None else "someone"
            lines.append(t(lang, "spot_taken", who=escape(who)))
        else:
            lines.append(t(lang, "spot_locked"))
        end = db.rotation_end()
        if end is not None:
            lines.append(t(lang, "rotation_until", end=end.isoformat()))
    else:
        lines.append(t(lang, "no_spot"))
        claim = db.active_claim_user(user["id"], day)
        if claim is not None:
            s = db.get_spot_by_id(claim["spot_id"])
            if s is not None:
                lines.append(t(lang, "parked_here", n=s["number"]))
        else:
            lines.append(t(lang, "check_avail"))
    return "\n".join(lines)


def _available_text(lang: str = "en") -> Tuple[str, List[Tuple[int, str]]]:
    day = db.today()
    lines = [t(lang, "free_today", day=day), ""]
    available: List[Tuple[int, str]] = []

    for spot in db.all_spots():
        state, other, _ = db.spot_status(spot, day)
        if state == db.OPEN:
            who = other["name"] if other is not None else "the owner"
            lines.append(t(lang, "freed_by", n=spot["number"], who=escape(who)))
            available.append((spot["number"], t(lang, "claim_was", n=spot["number"], who=who)))
        elif state == db.UNASSIGNED:
            lines.append(t(lang, "unassigned_free", n=spot["number"]))
            available.append((spot["number"], t(lang, "claim_unassigned", n=spot["number"])))

    if not available:
        lines.append(t(lang, "no_free"))
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
        await reply(update, t(db.user_lang(user), "owns_block"), menu(update))
        return
    text, _ = _available_text(db.user_lang(user))
    await reply(update, text, menu(update))


async def cmd_map(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if await need_registration(update):
        return
    await _send_map(update, get_db_user(update))


async def cmd_language(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if await need_registration(update):
        return
    user = get_db_user(update)
    await reply(
        update, t(db.user_lang(user), "lang_pick"),
        keyboards.language_kb(db.user_lang(user)),
    )


async def _show_language(update: Update, user) -> None:
    lang = db.user_lang(user)
    await reply(update, t(lang, "lang_pick"), keyboards.language_kb(lang))


async def _set_language(update: Update, context: ContextTypes.DEFAULT_TYPE, user, lang: str) -> None:
    if lang not in db.VALID_LANGS:
        return
    db.set_lang(user["id"], lang)
    user = get_db_user(update)
    await reply(update, t(lang, "lang_now"), menu(update))
    if user["telegram_id"] is not None:
        await set_role_commands(
            context.bot, user["telegram_id"], db.user_owns_spot(user["id"]),
            bool(user["is_admin"]), lang,
        )


def _free_numbers(day: str) -> List[int]:
    return [
        spot["number"]
        for spot in db.all_spots()
        if db.spot_status(spot, day)[0] in (db.OPEN, db.UNASSIGNED)
    ]


def _map_caption(day: str, lang: str) -> str:
    free = _free_numbers(day)
    free_txt = ", ".join(f"#{n}" for n in free) if free else t(lang, "map_none")
    return t(lang, "map_caption") + "\n\n" + t(lang, "map_day", day=day, free=free_txt)


def _map_nav_kb(day: str, lang: str) -> "keyboards.InlineKeyboardMarkup":
    today = date.fromisoformat(db.today())
    d = date.fromisoformat(day)
    prev = max(d - timedelta(days=1), today).isoformat()
    nxt = (d + timedelta(days=1)).isoformat()
    return keyboards.map_nav_kb(prev, nxt, db.today(), day, lang)


async def _send_map(update: Update, user, day: str | None = None) -> None:
    day = day or db.today()
    lang = db.user_lang(user)
    try:
        png = parking_map.render_map(owner_user_id=user["id"], day=day)
    except Exception:
        await reply(update, t(lang, "map_render_fail"), menu(update))
        return
    caption = _map_caption(day, lang)
    kb = _map_nav_kb(day, lang)

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
        await reply(update, t(lang, "map_send_fail"), menu(update))


async def _map_pick(update: Update, day_iso: str, lang: str) -> None:
    query = update.callback_query
    d = date.fromisoformat(day_iso)
    kb = keyboards.map_calendar_kb(
        day_iso, d.year, d.month, min_day=db.today(), max_day=None,
        today=db.today(), lang=lang,
    )
    try:
        await query.edit_message_caption(
            caption=t(lang, "map_pick"), reply_markup=kb, parse_mode="HTML",
        )
    except Exception:
        await query.edit_message_reply_markup(reply_markup=kb)


async def _map_cal(update: Update, user, action: str) -> None:
    lang = db.user_lang(user)
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
            back_callback=f"mapcal:month:{back_ym}", lang=lang,
        )

    async def _day_view(year: int, month: int, sel: str) -> None:
        if (year, month) < lo:
            return
        kb = keyboards.map_calendar_kb(
            sel, year, month, min_day=db.today(), max_day=None,
            today=db.today(), lang=lang,
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
            sel, year, month, min_day=db.today(), max_day=None,
            today=db.today(), lang=lang,
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


def _cal_state(context: ContextTypes.DEFAULT_TYPE) -> dict:
    state = context.chat_data.get(CAL_STATE)
    if state is None:
        t_ = date.today()
        state = {"year": t_.year, "month": t_.month, "dates": set()}
        context.chat_data[CAL_STATE] = state
    return state


def _calendar_kb(state: dict, spot, lang: str) -> "keyboards.InlineKeyboardMarkup":
    return keyboards.datepicker_kb(
        state["dates"], state["year"], state["month"],
        min_day=db.today(), max_day=_max_open_day(spot), lang=lang,
    )


def _pretty_list(dates, lang: str) -> str:
    return ", ".join(pretty_day(d, lang) for d in sorted(dates))


def _calendar_text(state: dict, spot, lang: str) -> str:
    chosen = sorted(state["dates"])
    pretty = _pretty_list(chosen, lang) if chosen else t(lang, "sel_none")
    note = ""
    end = db.rotation_end()
    if end is not None and spot["type"] == "rotating":
        note = t(lang, "open_note", end=end.isoformat())
    return t(lang, "open_title", n=spot["number"], pretty=pretty, note=note)


def _min_ym() -> tuple:
    """Current (year, month): nothing before this is selectable."""
    t_ = date.today()
    return (t_.year, t_.month)


def _month_bounds(spot) -> tuple:
    """Only the past is off-limits: every current/future month is selectable."""
    return _min_ym(), None, None


def _month_grid_kb(state: dict, spot, lang: str) -> "keyboards.InlineKeyboardMarkup":
    lo, _, _ = _month_bounds(spot)
    year = max(state["year"], lo[0])
    state["year"] = year
    return keyboards.month_grid_kb(
        year, "cal", min_ym=lo, max_ym=None, back_callback="cal:back", lang=lang
    )


async def _show_open_picker(update: Update, context: ContextTypes.DEFAULT_TYPE, user) -> None:
    spot = db.owned_spot(user["id"])
    lang = db.user_lang(user)
    if spot is None:
        await reply(update, t(lang, "no_share"), keyboards.back_menu(lang))
        return
    state = _cal_state(context)
    state["dates"] = set()
    today = date.today()
    state["year"], state["month"] = today.year, today.month
    await reply(update, _calendar_text(state, spot, lang), _calendar_kb(state, spot, lang))


async def cmd_close(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if await need_registration(update):
        return
    await _show_close(update, context, get_db_user(update))


def _close_text(spot, chosen, lang: str) -> str:
    pretty = _pretty_list(chosen, lang) if chosen else t(lang, "sel_none_close")
    return t(lang, "close_title", n=spot["number"], pretty=pretty)


def _clamp_days(days: List[str]) -> Tuple[List[str], str]:
    shown = days[:CLOSE_MAX_DAYS]
    note = ""
    if len(days) > CLOSE_MAX_DAYS:
        note = f"\n<i>Showing the next {CLOSE_MAX_DAYS} days.</i>"
    return shown, note


async def _show_close(update: Update, context: ContextTypes.DEFAULT_TYPE, user) -> None:
    spot = db.owned_spot(user["id"])
    lang = db.user_lang(user)
    if spot is None:
        await reply(update, t(lang, "no_spot_short"), menu(update))
        return
    days = db.opening_days(spot["id"], user["id"])
    if not days:
        await reply(update, t(lang, "not_shared", n=spot["number"]), menu(update))
        return
    context.chat_data[CLOSE_STATE] = set()
    shown, note = _clamp_days(days)
    extra = t(lang, "close_more", max=CLOSE_MAX_DAYS) if note else ""
    await reply(
        update, _close_text(spot, set(), lang) + extra,
        keyboards.close_days_kb(shown, set(), lang),
    )


async def _handle_close(update: Update, context: ContextTypes.DEFAULT_TYPE, user, action: str) -> None:
    spot = db.owned_spot(user["id"])
    lang = db.user_lang(user)
    if spot is None:
        await reply(update, t(lang, "no_spot_short"), menu(update))
        return
    days = db.opening_days(spot["id"], user["id"])
    if not days:
        await reply(update, t(lang, "not_shared", n=spot["number"]), menu(update))
        return
    shown, note = _clamp_days(days)
    extra = t(lang, "close_more", max=CLOSE_MAX_DAYS) if note else ""
    chosen = context.chat_data.setdefault(CLOSE_STATE, set())

    if action.startswith("day:"):
        iso = action.split(":", 1)[1]
        if iso in chosen:
            chosen.discard(iso)
        else:
            chosen.add(iso)
        await reply(
            update, _close_text(spot, chosen, lang) + extra,
            keyboards.close_days_kb(shown, chosen, lang),
        )
        return
    if action == "all":
        db.close_openings(spot["id"])
        context.chat_data.pop(CLOSE_STATE, None)
        await reply(update, t(lang, "closed_all", n=spot["number"]), menu(update))
        return
    if action == "ok":
        days_to_close = sorted(chosen)
        if not days_to_close:
            await reply(
                update, _close_text(spot, chosen, lang),
                keyboards.close_days_kb(shown, chosen, lang),
            )
            return
        count = db.close_spot_days(spot["id"], days_to_close, user["id"])
        context.chat_data.pop(CLOSE_STATE, None)
        pretty = _pretty_list(days_to_close, lang)
        await reply(
            update, t(lang, "closed_days", count=count, pretty=pretty), menu(update)
        )
        return


async def cmd_claim(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if await need_registration(update):
        return
    user = get_db_user(update)
    lang = db.user_lang(user)
    text = _claim_prompt(update, user)
    if isinstance(text, tuple):
        body, keyboard = text
    else:
        body, keyboard = text, keyboards.back_menu(lang)
    await reply(update, body, keyboard)


def _claim_prompt(update: Update, user):
    lang = db.user_lang(user)
    if db.user_owns_spot(user["id"]):
        return t(lang, "claim_block"), keyboards.back_menu(lang)
    day = db.today()
    existing = db.active_claim_user(user["id"], day)
    if existing is not None:
        s = db.get_spot_by_id(existing["spot_id"])
        number = s["number"] if s is not None else "?"
        return (
            t(lang, "already_parked", n=number),
            keyboards.back_menu(lang),
        )
    _, available = _available_text(lang)
    if not available:
        return t(lang, "no_free_claim"), keyboards.back_menu(lang)
    return (
        t(lang, "claim_which"),
        keyboards.claim_menu(available, lang),
    )


async def cmd_release(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if await need_registration(update):
        return
    user = get_db_user(update)
    lang = db.user_lang(user)
    if db.user_owns_spot(user["id"]):
        await reply(update, t(lang, "release_block"), menu(update))
        return
    claim = db.active_claim_user(user["id"], db.today())
    if claim is None:
        await reply(update, t(lang, "no_release"), menu(update))
        return
    db.release_claim(claim["id"])
    s = db.get_spot_by_id(claim["spot_id"])
    number = s["number"] if s is not None else "?"
    await reply(update, t(lang, "released", n=number), menu(update))


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
        await reply(update, t(db.user_lang(get_db_user(update)), "what_next"), menu(update))
        return

    if await need_registration(update):
        return
    user = get_db_user(update)

    if data == "status":
        await reply(update, _status_text(user), menu(update))
    elif data == "avail":
        if db.user_owns_spot(user["id"]):
            await reply(update, t(db.user_lang(user), "owns_block"), menu(update))
        else:
            text, _ = _available_text(db.user_lang(user))
            await reply(update, text, menu(update))
    elif data == "map":
        await _send_map(update, user)
    elif data == "lang":
        await _show_language(update, user)
    elif data.startswith("lang:set:"):
        await _set_language(update, context, user, data.split(":", 2)[2])
    elif data.startswith("map:day:"):
        await _send_map(update, user, day=data.split(":", 2)[2])
    elif data.startswith("map:pick:"):
        await _map_pick(update, data.split(":", 2)[2], db.user_lang(user))
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
        body, keyboard = result if isinstance(result, tuple) else (result, keyboards.back_menu(db.user_lang(user)))
        await reply(update, body, keyboard)
    elif data.startswith("claim:"):
        await _handle_claim(update, user, data.split(":", 1)[1])
    elif data == "release":
        if db.user_owns_spot(user["id"]):
            await reply(update, t(db.user_lang(user), "release_block"), menu(update))
            return
        claim = db.active_claim_user(user["id"], db.today())
        if claim is None:
            await reply(update, t(db.user_lang(user), "no_release"), menu(update))
        else:
            db.release_claim(claim["id"])
            s = db.get_spot_by_id(claim["spot_id"])
            number = s["number"] if s is not None else "?"
            await reply(
                update, t(db.user_lang(user), "released", n=number), menu(update)
            )
    else:
        await reply(update, t(db.user_lang(user), "what_next"), menu(update))


async def _handle_cal(update: Update, context: ContextTypes.DEFAULT_TYPE, user, action: str) -> None:
    spot = db.owned_spot(user["id"])
    lang = db.user_lang(user)
    if spot is None:
        await reply(update, t(lang, "no_spot_short"), keyboards.back_menu(lang))
        return

    state = _cal_state(context)
    today = date.today()

    if action == "ignore":
        return
    if action == "months":
        await reply(update, _calendar_text(state, spot, lang), _month_grid_kb(state, spot, lang))
        return
    if action == "back":
        await reply(update, _calendar_text(state, spot, lang), _calendar_kb(state, spot, lang))
        return
    if action.startswith("yprev:") or action.startswith("ynext:"):
        year = int(action.split(":")[1])
        year += -1 if action.startswith("yprev:") else 1
        state["year"] = year
        await reply(update, _calendar_text(state, spot, lang), _month_grid_kb(state, spot, lang))
        return
    if action.startswith("month:"):
        ym = action.split(":", 1)[1]
        year, month = (int(x) for x in ym.split("-"))
        lo, _, _ = _month_bounds(spot)
        if (year, month) < lo:
            return
        state["year"], state["month"] = year, month
        await reply(update, _calendar_text(state, spot, lang), _calendar_kb(state, spot, lang))
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
        await reply(update, _calendar_text(state, spot, lang), _calendar_kb(state, spot, lang))
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
        await reply(update, _calendar_text(state, spot, lang), _calendar_kb(state, spot, lang))
        return
    if action == "until":
        db.open_spot(spot["id"], user["id"], db.today(), None)
        context.chat_data.pop(CAL_STATE, None)
        await reply(update, t(lang, "opened_until", n=spot["number"]), menu(update))
        return
    if action == "ok":
        chosen = sorted(state["dates"])
        if not chosen:
            await reply(update, _calendar_text(state, spot, lang), _calendar_kb(state, spot, lang))
            return
        db.open_spot(spot["id"], user["id"], chosen[0], chosen[-1], dates=chosen)
        context.chat_data.pop(CAL_STATE, None)
        pretty = _pretty_list(chosen, lang)
        await reply(update, t(lang, "opened_days", n=spot["number"], pretty=pretty), menu(update))
        return
    await reply(update, _calendar_text(state, spot, lang), _calendar_kb(state, spot, lang))


async def _handle_claim(update: Update, user, raw_number: str) -> None:
    lang = db.user_lang(user)
    if db.user_owns_spot(user["id"]):
        await reply(update, t(lang, "claim_block"), keyboards.back_menu(lang))
        return
    try:
        number = int(raw_number)
    except ValueError:
        await reply(update, t(lang, "unknown_spot"), keyboards.back_menu(lang))
        return

    day = db.today()
    existing = db.active_claim_user(user["id"], day)
    if existing is not None:
        await reply(update, t(lang, "already_active"), menu(update))
        return

    spot = db.get_spot_by_number(number)
    if spot is None:
        await reply(update, t(lang, "no_spot_num"), keyboards.back_menu(lang))
        return

    state, other, _ = db.spot_status(spot, day)
    if state == db.OPEN:
        if other is not None and other["id"] == user["id"]:
            await reply(update, t(lang, "own_spot"), keyboards.back_menu(lang))
            return
    elif state == db.UNASSIGNED:
        pass
    else:
        await reply(update, t(lang, "spot_gone", n=number), keyboards.back_menu(lang))
        return

    db.add_claim(spot["id"], user["id"], day)
    await reply(update, t(lang, "claimed", n=number), menu(update))
