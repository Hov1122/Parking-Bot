from __future__ import annotations

from datetime import date

from telegram import Update
from telegram.ext import ApplicationHandlerStop, ContextTypes

from .. import cycles as cycle_parser
from .. import db, keyboards, layout
from .common import (
    clear_role_commands,
    escape,
    is_admin,
    is_admin_tg,
    reply,
    set_role_commands,
)

ADMIN_ONLY = "⛔ This command is for the admin only."
CYCLES_STATE = "awaiting_cycles"


async def _guard(update: Update) -> bool:
    if not is_admin(update):
        await reply(update, ADMIN_ONLY, None)
        return True
    return False


async def cmd_admin(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if await _guard(update):
        return
    text = (
        "<b>Admin commands</b>\n\n"
        "• /adduser &lt;name&gt; — pre-create a user account\n"
        "• /deluser &lt;name or tg-id&gt; — delete a user\n"
        "• /users — registered users and pending requests\n"
        "• /spots — every spot, owner and today's state\n"
        "• /assign &lt;spot#&gt; &lt;name or telegram-id&gt; — give a spot\n"
        "• /unassign &lt;spot# or name&gt; — free a spot (or a user's spot)\n"
        "• /settype &lt;spot#&gt; reserved|rotating — change type\n"
        "• /rename &lt;name or telegram-id&gt; &lt;new name&gt; — fix a display name\n"
        "• /resetclaims — clear all of today's \"I parked\" marks\n"
        "• /cycle — show rotation cycles (who has what, until when)\n"
        "• /addcycles — add one or more cycles by pasting a plan\n"
        "• /delcycle &lt;id&gt; · /clearcycles — remove cycles\n\n"
        "New people who message the bot are sent to you for approval before "
        "they can use it.\n\n"
        "For the 3-month rotation, use /addcycles with a block like:\n"
        "<pre>Cycle 1 12/10/26-31/12/26\n1 - Alice\n2 - Bob</pre>"
    )
    await reply(update, text, None)


async def cmd_adduser(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if await _guard(update):
        return
    args = context.args or []
    if not args:
        await reply(update, "Usage: /adduser &lt;name&gt;", None)
        return
    name = " ".join(args).strip()
    if not (1 <= len(name) <= 40):
        await reply(update, "The name must be between 1 and 40 characters.", None)
        return
    created = db.add_pending_user(name)
    if created is None:
        await reply(
            update,
            f"A user named <b>{escape(name)}</b> already exists. "
            "Use /rename to change it.",
            None,
        )
        return
    await reply(
        update,
        f"✅ Created <b>{escape(name)}</b>. When they send /start and type "
        "that exact name, you'll get a prompt to confirm them.",
        None,
    )


async def cmd_deluser(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if await _guard(update):
        return
    args = context.args or []
    if not args:
        await reply(update, "Usage: /deluser &lt;name or telegram-id&gt;", None)
        return
    target = " ".join(args).strip()
    user = _resolve_user(target)
    if user is None:
        await reply(
            update,
            f"I couldn't find a unique user matching <b>{escape(target)}</b>.\n"
            "Use the exact name from /users, or their telegram id.",
            None,
        )
        return
    if user["is_admin"] and db.count_admins() <= 1:
        await reply(update, "I can't remove the last admin.", None)
        return
    name = user["name"]
    tg_id = user["telegram_id"]
    db.delete_user(user["id"])
    if tg_id is not None:
        await clear_role_commands(context.bot, tg_id)
    await reply(
        update,
        f"🗑️ Deleted <b>{escape(name)}</b>. Any spot they owned is now "
        "unassigned and their openings/claims are gone.",
        None,
    )


async def cmd_users(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if await _guard(update):
        return
    users = db.all_users()
    requests = db.pending_requests()

    lines = ["<b>Registered users</b>", ""]
    if users:
        for u in users:
            flag = " [admin]" if u["is_admin"] else ""
            if u["telegram_id"] is None:
                status = " — <i>waiting to join</i>"
            else:
                status = f" — id {u['id']}, tg {u['telegram_id']}"
            lines.append(f"• <b>{escape(u['name'])}</b>{flag}{status}")
    else:
        lines.append("<i>none yet</i>")

    if requests:
        lines += [
            "",
            f"<b>Pending approval</b> ({len(requests)}) — buttons below, "
            "or use /approve &lt;tg-id&gt; / /reject &lt;tg-id&gt;",
            "",
        ]
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
            "🔔 <b>Registration request</b>\n\n"
            f"Name: <b>{escape(r['name'])}</b>\n"
            f"Telegram id: <code>{r['telegram_id']}</code>{username}\n\n"
            "Approve to let them into the bot."
        )
        try:
            await target.reply_text(
                text, reply_markup=keyboards.approval_kb(r["id"]), parse_mode="HTML"
            )
        except Exception:
            pass


async def cmd_approve(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if await _guard(update):
        return
    args = context.args or []
    if not args or not args[0].lstrip("-").isdigit():
        await reply(update, "Usage: /approve &lt;telegram-id&gt;", None)
        return
    req = db.latest_request(int(args[0]))
    if req is None or req["status"] != "pending":
        await reply(update, "No pending request for that id.", None)
        return
    await _resolve_request(update, context, req["id"], approve=True)


async def cmd_reject(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if await _guard(update):
        return
    args = context.args or []
    if not args or not args[0].lstrip("-").isdigit():
        await reply(update, "Usage: /reject &lt;telegram-id&gt;", None)
        return
    req = db.latest_request(int(args[0]))
    if req is None or req["status"] != "pending":
        await reply(update, "No pending request for that id.", None)
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
    if req is None:
        await reply(update, "That request no longer exists.", None)
        return
    if req["status"] != "pending":
        await reply(update, "That request was already handled.", None)
        return

    tg_id = req["telegram_id"]
    name = escape(req["name"])
    if approve:
        user = db.approve_request(req_id)
        if user is None:
            db.reject_request(req_id)
            await reply(
                update,
                f"⚠️ Couldn't approve <b>{name}</b> — that name or Telegram "
                "account is already used by another user. Use /rename to free "
                "the name, or ask them for a different one.",
                None,
            )
            return
        await reply(update, f"✅ Approved <b>{escape(user['name'])}</b>.", None)
        await _notify_user(
            context,
            tg_id,
            "🎉 <b>You're approved!</b> Welcome to the parking bot.\n\n"
            "Use /menu to get started.",
            keyboards.main_menu(db.user_owns_spot(user["id"])),
        )
        await set_role_commands(
            context.bot,
            tg_id,
            db.user_owns_spot(user["id"]),
            bool(user["is_admin"]),
        )
    else:
        db.reject_request(req_id)
        await reply(update, f"⛔ Rejected <b>{name}</b>.", None)
        await _notify_user(
            context,
            tg_id,
            "Your registration request was <b>rejected</b> by the admin.",
            None,
        )


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
    day = db.today()
    lines = [f"<b>Spots</b> ({day})", ""]
    for spot in db.all_spots():
        state, other, _ = db.spot_status(spot, day)
        spec = layout.by_number(spot["number"])
        floor = f" {escape(spec['floor'])}" if spec else ""
        owner_id = db.effective_owner_id(spot, day)
        owner = db.get_user(owner_id) if owner_id else None
        owner_name = escape(owner["name"]) if owner else "<i>unassigned</i>"
        if state == db.OPEN:
            state_txt = f"🔓 open (by {escape(other['name']) if other else '?'})"
        elif state == db.OCCUPIED:
            state_txt = f"🚗 taken by {escape(other['name']) if other else '?'}"
        elif state == db.OWNER:
            state_txt = "🔒 with owner"
        else:
            state_txt = "⚪ unassigned"
        lines.append(
            f"<b>#{spot['number']}</b>{floor} ({escape(spot['type'])}) — owner: "
            f"{owner_name} — {state_txt}"
        )
    await reply(update, "\n".join(lines), None)


async def cmd_assign(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if await _guard(update):
        return
    args = context.args or []
    if len(args) < 2:
        await reply(update, "Usage: /assign &lt;spot#&gt; &lt;name or telegram-id&gt;", None)
        return
    try:
        number = int(args[0])
    except ValueError:
        await reply(update, "The spot number must be a number.", None)
        return

    spot = db.get_spot_by_number(number)
    if spot is None:
        await reply(update, f"There is no spot #{number}.", None)
        return

    target = " ".join(args[1:]).strip()
    user = _resolve_user(target)
    if user is None:
        await reply(
            update,
            f"I couldn't find a unique user matching <b>{escape(target)}</b>.\n"
            "Use the exact name from /users, or their telegram id.",
            None,
        )
        return

    # A user can only own one spot.
    current = db.owned_spot(user["id"])
    if current is not None and current["id"] != spot["id"]:
        await reply(
            update,
            f"{escape(user['name'])} already owns spot "
            f"<b>#{current['number']}</b>. Unassign it first.",
            None,
        )
        return

    db.assign_spot(number, user["id"])
    if user["telegram_id"] is not None:
        await set_role_commands(
            context.bot, user["telegram_id"], True, bool(user["is_admin"])
        )
    note = ""
    if db.current_cycle() is not None:
        note = (
            "\n\n⚠️ A rotation cycle is active, so it overrides manual owners "
            "today. Use /addcycles or /clearcycles."
        )
    await reply(
        update,
        f"✅ Spot <b>#{number}</b> is now assigned to "
        f"<b>{escape(user['name'])}</b>.{note}",
        None,
    )


async def cmd_rename(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if await _guard(update):
        return
    args = context.args or []
    if len(args) < 2:
        await reply(update, "Usage: /rename &lt;name or telegram-id&gt; &lt;new name&gt;", None)
        return
    user = _resolve_user(args[0])
    if user is None:
        await reply(
            update,
            f"I couldn't find a unique user matching <b>{escape(args[0])}</b>.",
            None,
        )
        return
    new_name = " ".join(args[1:]).strip()
    if not (1 <= len(new_name) <= 40):
        await reply(update, "The new name must be between 1 and 40 characters.", None)
        return
    if db.name_exists(new_name, exclude_id=user["id"]):
        await reply(
            update,
            f"Another user is already named <b>{escape(new_name)}</b>. "
            "Names must be unique.",
            None,
        )
        return
    db.rename_user(user["id"], new_name)
    await reply(update, f"✏️ User renamed to <b>{escape(new_name)}</b>.", None)


async def cmd_unassign(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if await _guard(update):
        return
    args = context.args or []
    if not args:
        await reply(update, "Usage: /unassign &lt;spot# or name&gt;", None)
        return
    target = " ".join(args).strip()
    spot = None
    if target.lstrip("-").isdigit():
        spot = db.get_spot_by_number(int(target))
    if spot is None:
        user = _resolve_user(target)
        if user is None:
            await reply(
                update,
                f"There is no spot <b>#{escape(target)}</b> and no user matching "
                f"<b>{escape(target)}</b>.",
                None,
            )
            return
        spot = db.manual_spot(user["id"])
        if spot is None:
            await reply(
                update,
                f"<b>{escape(user['name'])}</b> doesn't own a spot.",
                None,
            )
            return
    owner = db.get_user(spot["owner_user_id"]) if spot["owner_user_id"] else None
    db.unassign_spot(spot["number"])
    if owner is not None and owner["telegram_id"] is not None:
        await set_role_commands(
            context.bot, owner["telegram_id"], False, bool(owner["is_admin"])
        )
    note = ""
    if db.current_cycle() is not None:
        note = (
            "\n\n⚠️ A rotation cycle is active, so it overrides manual owners "
            "today. The change takes visible effect once no cycle covers the day."
        )
    await reply(
        update, f"⚪ Spot <b>#{spot['number']}</b> is now unassigned.{note}", None
    )


async def cmd_settype(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if await _guard(update):
        return
    args = context.args or []
    if len(args) < 2 or args[1].lower() not in ("reserved", "rotating"):
        await reply(update, "Usage: /settype &lt;spot#&gt; reserved|rotating", None)
        return
    try:
        number = int(args[0])
    except ValueError:
        await reply(update, "The spot number must be a number.", None)
        return
    spot = db.get_spot_by_number(number)
    if spot is None:
        await reply(update, f"There is no spot #{number}.", None)
        return
    new_type = args[1].lower()
    db.set_spot_type(number, new_type)
    await reply(update, f"✅ Spot <b>#{number}</b> is now <b>{new_type}</b>.", None)


async def cmd_resetclaims(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if await _guard(update):
        return
    count = db.reset_claims(day=db.today())
    await reply(update, f"🧹 Cleared {count} active claim(s) for today.", None)


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
        )


async def cmd_cycle(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if await _guard(update):
        return
    all_cycles = db.all_cycles()
    if not all_cycles:
        await reply(
            update,
            "No rotation cycles yet. Add a plan with /addcycles.",
            None,
        )
        return

    current = db.current_cycle()
    lines = ["🔄 <b>Rotation cycles</b>", ""]
    if current is not None:
        until = _pretty_date(current["end_date"])
        lines.append(f"▶️ <b>Current cycle</b> — until <b>{until}</b>")
        for a in db.cycle_assignments(current["id"]):
            lines.append(f"   <b>#{a['spot_number']}</b> — {escape(a['user_name'])}")
        lines.append("")
    else:
        lines.append("<i>No cycle is active today.</i>")
        lines.append("")

    lines.append("<b>All cycles</b>")
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
    context.chat_data[CYCLES_STATE] = True
    text = (
        "Send the rotation plan as text. One block per cycle:\n\n"
        "<pre>Cycle 1 12/10/26-31/12/26\n"
        "1 - Test\n"
        "2 - Test2\n"
        "Cycle 2 01/01/27-31/03/27\n"
        "1 - test3\n"
        "2 - test2</pre>\n\n"
        "Dates are day-first (<b>DD/MM/YY</b>). Names that aren't known yet are "
        "created automatically. One user owns one spot: a name may appear only "
        "once per cycle, and while a cycle is active, spots you don't list "
        "count as unassigned (manual owners return when no cycle is active).\n"
        "Send /cancel to abort."
    )
    await reply(update, text, None)


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

    text = (update.message.text or "").strip()
    if text.startswith("/"):
        context.chat_data.pop(CYCLES_STATE, None)
        await reply(update, "Cancelled the cycle entry.", None)
        return  # let the command be handled normally in the main group

    try:
        parsed = cycle_parser.parse_cycles(text)
    except cycle_parser.CycleParseError as exc:
        await reply(
            update, f"⚠️ {escape(str(exc))}\n\nFix it and send again, or /cancel.", None
        )
        raise ApplicationHandlerStop

    known_spots = {s["number"] for s in db.all_spots()}
    for cyc in parsed:
        for number, _name in cyc.assignments:
            if number not in known_spots:
                await reply(
                    update,
                    f"⚠️ Spot <b>#{number}</b> doesn't exist. Nothing was saved — "
                    "fix it and send again, or /cancel.",
                    None,
                )
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
                    f"⚠️ Spot <b>#{number}</b> is listed twice in "
                    f"<b>{escape(cyc.label or 'a cycle')}</b>. Nothing was saved — "
                    "fix it and send again, or /cancel.",
                    None,
                )
                return
            if key in seen_names:
                await reply(
                    update,
                    f"⚠️ <b>{escape(name)}</b> is listed twice in "
                    f"<b>{escape(cyc.label or 'a cycle')}</b> — one user can own "
                    "one spot. Nothing was saved — fix it and send again, or /cancel.",
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
            await reply(
                update,
                f"⚠️ {escape(str(exc))} Nothing was saved — "
                "fix it and send again, or /cancel.",
                None,
            )
            return
        label = cyc.label or f"Cycle {cycle_id}"
        summary.append(
            f"• <b>{escape(label)}</b> ({_pretty_date(cyc.start)}–"
            f"{_pretty_date(cyc.end)}): {len(assignments)} spot(s)"
        )

    await _refresh_all_commands(context)

    lines = [f"✅ Added <b>{len(parsed)}</b> cycle(s):", ""]
    lines += summary
    if created:
        lines += ["", "👤 Created new (pending) users: " + escape(", ".join(created))]
    current = db.current_cycle()
    if current is not None:
        lines += [
            "",
            f"▶️ The cycle active today now ends on "
            f"<b>{_pretty_date(current['end_date'])}</b>.",
        ]
    await reply(update, "\n".join(lines), None)
    raise ApplicationHandlerStop


async def cmd_delcycle(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if await _guard(update):
        return
    args = context.args or []
    if not args or not args[0].isdigit():
        await reply(update, "Usage: /delcycle &lt;id&gt;  (see ids in /cycle)", None)
        return
    cycle_id = int(args[0])
    if db.get_cycle(cycle_id) is None:
        await reply(update, f"There is no cycle with id {cycle_id}.", None)
        return
    db.delete_cycle(cycle_id)
    await _refresh_all_commands(context)
    await reply(update, f"🗑️ Deleted cycle {cycle_id}.", None)


async def cmd_clearcycles(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if await _guard(update):
        return
    count = len(db.all_cycles())
    db.delete_all_cycles()
    await _refresh_all_commands(context)
    await reply(
        update,
        f"🧹 Removed {count} cycle(s). Spots fall back to their manual owners.",
        None,
    )