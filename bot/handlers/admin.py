# -*- coding: utf-8 -*-
from __future__ import annotations

from datetime import date

from telegram import Update
from telegram.ext import ApplicationHandlerStop, ContextTypes

from .. import cycles as cycle_parser
from .. import db, keyboards, layout
from ..i18n import t
from .common import (
    clear_role_commands,
    escape,
    get_db_user,
    is_admin,
    is_admin_tg,
    reply,
    set_role_commands,
)

CYCLES_STATE = "awaiting_cycles"


async def _guard(update: Update) -> bool:
    if not is_admin(update):
        await reply(update, t("en", "admin_only"), None)
        return True
    return False


def _lang(update: Update) -> str:
    return db.user_lang(get_db_user(update))


async def cmd_admin(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if await _guard(update):
        return
    await reply(update, t(_lang(update), "admin_help"), None)


async def cmd_adduser(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if await _guard(update):
        return
    lang = _lang(update)
    args = context.args or []
    if not args:
        await reply(update, t(lang, "usage_adduser"), None)
        return
    name = " ".join(args).strip()
    if not (1 <= len(name) <= 40):
        await reply(update, t(lang, "name_len"), None)
        return
    created = db.add_pending_user(name)
    if created is None:
        await reply(update, t(lang, "user_exists", name=escape(name)), None)
        return
    await reply(update, t(lang, "user_created", name=escape(name)), None)


async def cmd_deluser(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if await _guard(update):
        return
    lang = _lang(update)
    args = context.args or []
    if not args:
        await reply(update, t(lang, "usage_deluser"), None)
        return
    target = " ".join(args).strip()
    user = _resolve_user(target)
    if user is None:
        await reply(update, t(lang, "no_user_match", target=escape(target)), None)
        return
    if user["is_admin"] and db.count_admins() <= 1:
        await reply(update, t(lang, "last_admin_del"), None)
        return
    name = user["name"]
    tg_id = user["telegram_id"]
    db.delete_user(user["id"])
    if tg_id is not None:
        await clear_role_commands(context.bot, tg_id)
    await reply(update, t(lang, "user_deleted", name=escape(name)), None)


async def cmd_makeadmin(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if await _guard(update):
        return
    lang = _lang(update)
    args = context.args or []
    if not args:
        await reply(update, t(lang, "usage_makeadmin"), None)
        return
    target = " ".join(args).strip()
    user = _resolve_user(target)
    if user is None:
        await reply(update, t(lang, "no_user_match", target=escape(target)), None)
        return
    if user["is_admin"]:
        await reply(update, t(lang, "already_admin", name=escape(user["name"])), None)
        return
    db.set_admin(user["id"], True)
    if user["telegram_id"] is not None:
        await set_role_commands(
            context.bot,
            user["telegram_id"],
            db.user_owns_spot(user["id"]),
            True,
            db.user_lang(user),
        )
    await reply(update, t(lang, "now_admin", name=escape(user["name"])), None)


async def cmd_demoadmin(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if await _guard(update):
        return
    lang = _lang(update)
    args = context.args or []
    if not args:
        await reply(update, t(lang, "usage_demote"), None)
        return
    target = " ".join(args).strip()
    user = _resolve_user(target)
    if user is None:
        await reply(update, t(lang, "no_user_match", target=escape(target)), None)
        return
    if not user["is_admin"]:
        await reply(update, t(lang, "not_admin", name=escape(user["name"])), None)
        return
    if db.count_admins() <= 1:
        await reply(update, t(lang, "last_admin_dem"), None)
        return
    db.set_admin(user["id"], False)
    if user["telegram_id"] is not None:
        await set_role_commands(
            context.bot,
            user["telegram_id"],
            db.user_owns_spot(user["id"]),
            False,
            db.user_lang(user),
        )
    await reply(update, t(lang, "demoted", name=escape(user["name"])), None)


async def cmd_users(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if await _guard(update):
        return
    lang = _lang(update)
    users = db.all_users()
    requests = db.pending_requests()

    lines = [t(lang, "users_title"), ""]
    if users:
        for u in users:
            flag = " [admin]" if u["is_admin"] else ""
            if u["telegram_id"] is None:
                status = t(lang, "users_waiting")
            else:
                status = f" — id {u['id']}, tg {u['telegram_id']}"
            lines.append(f"• <b>{escape(u['name'])}</b>{flag}{status}")
    else:
        lines.append(t(lang, "users_none"))

    if requests:
        lines += ["", t(lang, "pending_title", n=len(requests)), ""]
        for r in requests:
            username = f" (@{escape(r['username'])})" if r["username"] else ""
            lines.append(
                f"• <b>{escape(r['name'])}</b> — tg {r['telegram_id']}{username}"
            )
    await reply(update, "\n".join(lines), None)

    # Send a separate, buttoned message per pending request so the admin can
    # approve/reject without hunting for the original notification.
    target = update.effective_message
    for r in requests:
        username = f" (@{escape(r['username'])})" if r["username"] else ""
        text = (
            t(lang, "req_title") + "\n\n"
            + t(lang, "req_body", name=escape(r["name"]), tg=r["telegram_id"], username=username)
        )
        try:
            await target.reply_text(
                text, reply_markup=keyboards.approval_kb(r["id"], lang), parse_mode="HTML"
            )
        except Exception:
            pass


async def cmd_approve(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if await _guard(update):
        return
    lang = _lang(update)
    args = context.args or []
    if not args or not args[0].lstrip("-").isdigit():
        await reply(update, t(lang, "usage_approve"), None)
        return
    req = db.latest_request(int(args[0]))
    if req is None or req["status"] != "pending":
        await reply(update, t(lang, "no_pending"), None)
        return
    await _resolve_request(update, context, req["id"], approve=True)


async def cmd_reject(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if await _guard(update):
        return
    lang = _lang(update)
    args = context.args or []
    if not args or not args[0].lstrip("-").isdigit():
        await reply(update, t(lang, "usage_reject"), None)
        return
    req = db.latest_request(int(args[0]))
    if req is None or req["status"] != "pending":
        await reply(update, t(lang, "no_pending"), None)
        return
    await _resolve_request(update, context, req["id"], approve=False)


async def on_approval_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle the Approve/Reject inline buttons sent to admins."""
    query = update.callback_query
    await query.answer()
    if update.effective_user is None or not is_admin_tg(update.effective_user.id):
        await query.edit_message_text("⛔ This action is for the admin only.")
        return
    action, _, raw_id = (query.data or "").partition(":")
    if not raw_id.isdigit():
        return
    await _resolve_request(update, context, int(raw_id), approve=(action == "appr"))


async def _resolve_request(update: Update, context: ContextTypes.DEFAULT_TYPE, req_id: int, approve: bool) -> None:
    req = db.get_request(req_id)
    lang = _lang(update)
    if req is None:
        await reply(update, t(lang, "req_gone"), None)
        return
    if req["status"] != "pending":
        await reply(update, t(lang, "req_handled"), None)
        return

    tg_id = req["telegram_id"]
    name = escape(req["name"])
    if approve:
        user = db.approve_request(req_id)
        if user is None:
            db.reject_request(req_id)
            await reply(update, t(lang, "approve_conflict", name=name), None)
            return
        await reply(update, t(lang, "approved", name=escape(user["name"])), None)
        await _notify_user(
            context,
            tg_id,
            t(db.user_lang(user), "approved_dm"),
            keyboards.main_menu(db.user_owns_spot(user["id"]), db.user_lang(user)),
        )
        await set_role_commands(
            context.bot,
            tg_id,
            db.user_owns_spot(user["id"]),
            bool(user["is_admin"]),
            db.user_lang(user),
        )
    else:
        db.reject_request(req_id)
        await reply(update, t(lang, "rejected", name=name), None)
        await _notify_user(context, tg_id, t("en", "rejected_dm"), None)


async def _notify_user(context: ContextTypes.DEFAULT_TYPE, tg_id: int, text: str, keyboard=None) -> None:
    try:
        await context.bot.send_message(
            chat_id=tg_id, text=text, reply_markup=keyboard, parse_mode="HTML"
        )
    except Exception:
        pass



async def cmd_spots(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if await _guard(update):
        return
    lang = _lang(update)
    day = db.today()
    lines = [t(lang, "spots_title", day=day), ""]
    for spot in db.all_spots():
        state, other, _ = db.spot_status(spot, day)
        spec = layout.by_number(spot["number"])
        floor = f" {escape(spec['floor'])}" if spec else ""
        owner_id = db.effective_owner_id(spot, day)
        owner = db.get_user(owner_id) if owner_id else None
        owner_name = escape(owner["name"]) if owner else t(lang, "no_owner")
        stype = t(lang, "type_" + spot["type"])
        if state == db.OPEN:
            state_txt = t(lang, "spot_open_by", who=escape(other["name"]) if other else "?")
        elif state == db.OCCUPIED:
            state_txt = t(lang, "spot_taken_by", who=escape(other["name"]) if other else "?")
        elif state == db.OWNER:
            state_txt = t(lang, "spot_owner")
        else:
            state_txt = t(lang, "spot_free")
        lines.append(
            f"<b>#{spot['number']}</b>{floor} ({stype}) — owner: "
            f"{owner_name} — {state_txt}"
        )
    await reply(update, "\n".join(lines), None)


async def cmd_assign(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if await _guard(update):
        return
    lang = _lang(update)
    args = context.args or []
    if len(args) < 2:
        await reply(update, t(lang, "usage_assign"), None)
        return
    try:
        number = int(args[0])
    except ValueError:
        await reply(update, t(lang, "spot_num"), None)
        return

    spot = db.get_spot_by_number(number)
    if spot is None:
        await reply(update, t(lang, "no_spot_n", n=number), None)
        return

    target = " ".join(args[1:]).strip()
    user = _resolve_user(target)
    if user is None:
        await reply(update, t(lang, "no_user_match", target=escape(target)), None)
        return

    # A user can only own one spot.
    current = db.owned_spot(user["id"])
    if current is not None and current["id"] != spot["id"]:
        await reply(
            update,
            t(lang, "owns_other", name=escape(user["name"]), n=current["number"]),
            None,
        )
        return

    db.assign_spot(number, user["id"])
    if user["telegram_id"] is not None:
        await set_role_commands(
            context.bot, user["telegram_id"], True, bool(user["is_admin"]),
            db.user_lang(user),
        )
    note = ""
    if db.current_cycle() is not None:
        note = t(lang, "cycle_note")
    await reply(
        update, t(lang, "assigned", n=number, name=escape(user["name"]), note=note), None
    )


async def cmd_rename(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if await _guard(update):
        return
    lang = _lang(update)
    args = context.args or []
    if len(args) < 2:
        await reply(update, t(lang, "usage_rename"), None)
        return
    user = _resolve_user(args[0])
    if user is None:
        await reply(update, t(lang, "no_user_match", target=escape(args[0])), None)
        return
    new_name = " ".join(args[1:]).strip()
    if not (1 <= len(new_name) <= 40):
        await reply(update, t(lang, "new_name_len"), None)
        return
    if db.name_exists(new_name, exclude_id=user["id"]):
        await reply(update, t(lang, "name_used", name=escape(new_name)), None)
        return
    db.rename_user(user["id"], new_name)
    await reply(update, t(lang, "renamed", name=escape(new_name)), None)


async def cmd_unassign(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if await _guard(update):
        return
    lang = _lang(update)
    args = context.args or []
    if not args:
        await reply(update, t(lang, "usage_unassign"), None)
        return
    target = " ".join(args).strip()
    spot = None
    if target.lstrip("-").isdigit():
        spot = db.get_spot_by_number(int(target))
    if spot is None:
        user = _resolve_user(target)
        if user is None:
            await reply(update, t(lang, "no_spot_user", target=escape(target)), None)
            return
        spot = db.manual_spot(user["id"])
        if spot is None:
            await reply(update, t(lang, "owns_nothing", name=escape(user["name"])), None)
            return
    owner = db.get_user(spot["owner_user_id"]) if spot["owner_user_id"] else None
    db.unassign_spot(spot["number"])
    if owner is not None and owner["telegram_id"] is not None:
        await set_role_commands(
            context.bot, owner["telegram_id"], False, bool(owner["is_admin"]),
            db.user_lang(owner),
        )
    note = ""
    if db.current_cycle() is not None:
        note = t(lang, "cycle_note_un")
    await reply(update, t(lang, "unassigned", n=spot["number"], note=note), None)


async def cmd_settype(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if await _guard(update):
        return
    lang = _lang(update)
    args = context.args or []
    if len(args) < 2 or args[1].lower() not in ("reserved", "rotating"):
        await reply(update, t(lang, "usage_settype"), None)
        return
    try:
        number = int(args[0])
    except ValueError:
        await reply(update, t(lang, "spot_num"), None)
        return
    spot = db.get_spot_by_number(number)
    if spot is None:
        await reply(update, t(lang, "no_spot_n", n=number), None)
        return
    new_type = args[1].lower()
    db.set_spot_type(number, new_type)
    await reply(
        update, t(lang, "settype_ok", n=number, type=t(lang, f"type_{new_type}")), None
    )


async def cmd_resetclaims(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if await _guard(update):
        return
    lang = _lang(update)
    count = db.reset_claims(day=db.today())
    await reply(update, t(lang, "resetclaims", n=count), None)


def _resolve_user(target: str):
    users = db.all_users()
    lowered = target.lower()
    # telegram id
    if target.lstrip("-").isdigit():
        tg_id = int(target)
        for u in users:
            if u["telegram_id"] == tg_id:
                return u
    matches = [u for u in users if u["name"].lower() == lowered]
    if len(matches) == 1:
        return matches[0]
    return None


# --------------------------------------------------------------------------- #
# Rotation cycles
# --------------------------------------------------------------------------- #
def _pretty_date(iso: str) -> str:
    try:
        return date.fromisoformat(iso).strftime("%d/%m/%y")
    except (TypeError, ValueError):
        return str(iso)


async def _refresh_all_commands(context: ContextTypes.DEFAULT_TYPE) -> None:
    """Ownership may have changed for everyone, so refresh their menus."""
    for u in db.all_users():
        if u["telegram_id"] is None:
            continue
        await set_role_commands(
            context.bot,
            u["telegram_id"],
            db.user_owns_spot(u["id"]),
            bool(u["is_admin"]),
            db.user_lang(u),
        )


async def cmd_cycle(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if await _guard(update):
        return
    lang = _lang(update)
    all_cycles = db.all_cycles()
    if not all_cycles:
        await reply(update, t(lang, "cycle_none"), None)
        return

    current = db.current_cycle()
    lines = [t(lang, "cycle_title"), ""]
    if current is not None:
        until = _pretty_date(current["end_date"])
        lines.append(t(lang, "cycle_current", until=until))
        for a in db.cycle_assignments(current["id"]):
            lines.append(f"   <b>#{a['spot_number']}</b> — {escape(a['user_name'])}")
        lines.append("")
    else:
        lines.append(t(lang, "cycle_idle"))
        lines.append("")

    lines.append(t(lang, "cycle_all"))
    for c in all_cycles:
        marker = "▶️ " if current is not None and c["id"] == current["id"] else "• "
        label = escape(c["label"]) if c["label"] else f"Cycle {c['id']}"
        lines.append(
            f"{marker}{label} ({_pretty_date(c['start_date'])}–"
            f"{_pretty_date(c['end_date'])}) · id {c['id']}"
        )
    await reply(update, "\n".join(lines), None)


async def cmd_addcycles(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if await _guard(update):
        return
    lang = _lang(update)
    context.chat_data[CYCLES_STATE] = True
    await reply(update, t(lang, "addcycles_prompt"), None)


def _resolve_or_create(name: str, created: list[str]) -> int:
    matches = db.find_users_by_name(name)
    if matches:
        return matches[0]["id"]
    user = db.add_pending_user(name)
    if user is None:
        again = db.find_users_by_name(name)
        return again[0]["id"] if again else None
    created.append(name)
    return user["id"]


async def on_cycles_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Consume the pasted cycle block when the admin is entering a plan."""
    if not context.chat_data.get(CYCLES_STATE):
        return
    if update.effective_user is None or not is_admin_tg(update.effective_user.id):
        return
    if update.message is None:
        return

    admin = db.get_user_by_tg(update.effective_user.id)
    lang = db.user_lang(admin)
    text = (update.message.text or "").strip()
    if text.startswith("/"):
        context.chat_data.pop(CYCLES_STATE, None)
        await reply(update, t(lang, "cycles_cancelled"), None)
        return  # let the command be handled normally in the main group

    try:
        parsed = cycle_parser.parse_cycles(text)
    except cycle_parser.CycleParseError as exc:
        await reply(update, t(lang, "parse_fix", err=escape(str(exc))), None)
        raise ApplicationHandlerStop

    known_spots = {s["number"] for s in db.all_spots()}
    for cyc in parsed:
        for number, _name in cyc.assignments:
            if number not in known_spots:
                await reply(update, t(lang, "cycles_no_exist", n=number), None)
                raise ApplicationHandlerStop

    context.chat_data.pop(CYCLES_STATE, None)
    created: list[str] = []
    summary: list[str] = []
    for cyc in parsed:
        # One user owns one spot: reject a duplicated name/spot in one cycle.
        seen_names: set[str] = set()
        seen_numbers: set[int] = set()
        for number, name in cyc.assignments:
            key = name.strip().lower()
            if number in seen_numbers:
                await reply(
                    update,
                    t(lang, "cycles_dup_spot", n=number, label=escape(cyc.label or "a cycle")),
                    None,
                )
                return
            if key in seen_names:
                await reply(
                    update,
                    t(lang, "cycles_dup_user", name=escape(name), label=escape(cyc.label or "a cycle")),
                    None,
                )
                return
            seen_numbers.add(number)
            seen_names.add(key)
        assignments = [
            (number, _resolve_or_create(name, created))
            for number, name in cyc.assignments
        ]
        try:
            cycle_id = db.add_cycle(cyc.start, cyc.end, assignments, label=cyc.label)
        except ValueError as exc:
            await reply(update, t(lang, "cycles_save_fail", err=escape(str(exc))), None)
            return
        label = cyc.label or f"Cycle {cycle_id}"
        summary.append(
            f"• <b>{escape(label)}</b> ({_pretty_date(cyc.start)}–"
            f"{_pretty_date(cyc.end)}): {len(assignments)} spot(s)"
        )

    await _refresh_all_commands(context)

    lines = [t(lang, "cycles_added", n=len(parsed)), ""]
    lines += summary
    if created:
        lines += ["", t(lang, "cycles_created", names=escape(", ".join(created)))]
    current = db.current_cycle()
    if current is not None:
        lines += ["", t(lang, "cycles_live", until=_pretty_date(current["end_date"]))]
    await reply(update, "\n".join(lines), None)
    raise ApplicationHandlerStop


async def cmd_delcycle(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if await _guard(update):
        return
    lang = _lang(update)
    args = context.args or []
    if not args or not args[0].isdigit():
        await reply(update, t(lang, "usage_delcycle"), None)
        return
    cycle_id = int(args[0])
    if db.get_cycle(cycle_id) is None:
        await reply(update, t(lang, "no_cycle", id=cycle_id), None)
        return
    db.delete_cycle(cycle_id)
    await _refresh_all_commands(context)
    await reply(update, t(lang, "cycle_deleted", id=cycle_id), None)


async def cmd_clearcycles(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if await _guard(update):
        return
    lang = _lang(update)
    count = len(db.all_cycles())
    db.delete_all_cycles()
    await _refresh_all_commands(context)
    await reply(update, t(lang, "cycles_cleared", n=count), None)
