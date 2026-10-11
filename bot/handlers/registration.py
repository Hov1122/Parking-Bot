from __future__ import annotations

import logging

from telegram import Update
from telegram.ext import ContextTypes

from .. import db, keyboards
from ..assets import logo_path
from .common import (
    escape,
    get_db_user,
    is_bootstrap_admin,
    menu,
    notify_admins,
    reply,
    set_role_commands,
)

log = logging.getLogger(__name__)

WELCOME = (
    "👋 <b>Welcome to the office parking bot!</b>\n\n"
    "I keep track of who has which parking spot and let colleagues share a "
    "spot when they don't drive to the office.\n\n"
    "An admin has to approve you before you can start. Send the <b>name</b> "
    "the admin told you to use (it must match), or your own name if you're "
    "new — the admin will get a message to confirm you."
)

WAITING = (
    "⏳ Your registration request is waiting for the admin to approve it. "
    "You'll be notified here as soon as it's confirmed."
)


async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = get_db_user(update)
    if user is not None:
        await reply(
            update,
            f"Welcome back, {escape(user['name'])}! What would you like to do?",
            menu(update),
        )
        await _refresh_commands(context, user)
        return

    if update.effective_user is not None:
        req = db.latest_request(update.effective_user.id)
        if req is not None and req["status"] == "pending":
            await reply(update, WAITING, None)
            return

    await _send_welcome(update)


async def _send_welcome(update: Update) -> None:
    """Send the welcome, with the logo as a photo when it's available."""
    path = logo_path()
    message = update.effective_message
    if path is not None and message is not None:
        try:
            with open(path, "rb") as handle:
                await message.reply_photo(handle, caption=WELCOME, parse_mode="HTML")
            return
        except Exception:
            pass
    await reply(update, WELCOME, None)


async def cmd_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if get_db_user(update) is None:
        return await cmd_start(update, context)
    await reply(update, "What would you like to do?", menu(update))
    await _refresh_commands(context, get_db_user(update))


async def _refresh_commands(context: ContextTypes.DEFAULT_TYPE, user) -> None:
    if user is None or user["telegram_id"] is None:
        return
    await set_role_commands(
        context.bot,
        user["telegram_id"],
        db.user_owns_spot(user["id"]),
        bool(user["is_admin"]),
    )


async def cmd_help(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    text = (
        "<b>Parking bot — help</b>\n\n"
        "<b>Everyone</b>\n"
        "• /map — parking map: green free, red in use, blue yours\n"
        "• /status — your spot and today's situation\n"
        "• /available — spots that are free today\n"
        "• /open — pick the day(s) your spot is free\n"
        "• /close — take back specific days (or stop sharing)\n"
        "• /claim — record that you parked in a free spot\n"
        "• /release — record that you left that spot\n"
        "• /menu — main menu, /help — this text\n\n"
        "<b>Admin only</b>\n"
        "• /adduser &lt;name&gt; — pre-create a user account\n"
        "• /deluser &lt;name or tg-id&gt; — delete a user\n"
        "• /makeadmin &lt;name or tg-id&gt; — grant admin rights\n"
        "• /demote &lt;name or tg-id&gt; — remove admin rights\n"
        "• /spots — list every spot and its state\n"
        "• /users — list users and pending requests\n"
        "• /assign &lt;spot&gt; &lt;name&gt; — give a spot to a user\n"
        "• /unassign &lt;spot&gt; — remove the owner of a spot\n"
        "• /settype &lt;spot&gt; reserved|rotating — change a spot type\n"
        "• /rename &lt;name&gt; &lt;new name&gt; — fix a user's display name\n"
        "• /resetclaims — clear today's \"I parked\" marks\n"
        "• /cycle — show the rotation cycles (who has what, until when)\n"
        "• /addcycles — add rotation cycles by pasting a plan\n"
        "• /delcycle, /clearcycles — remove cycles\n"
    )
    await reply(update, text, None)


async def on_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Non-command text: register the user's name, or nudge registered users."""
    if update.effective_user is None or update.message is None:
        return

    if get_db_user(update) is not None:
        await reply(
            update,
            "I only understand buttons and commands. Use /menu to get started.",
            menu(update),
        )
        return

    name = update.message.text.strip()
    if not (1 <= len(name) <= 40):
        await reply(update, "Please send a name between 1 and 40 characters.", None)
        return

    tg_id = update.effective_user.id

    # The configured admin (or the very first user when none is configured) is
    # trusted immediately and does not need to be approved.
    if is_bootstrap_admin(tg_id):
        pending = db.find_pending_by_name(name)
        if pending is not None:
            db.bind_telegram(pending["id"], tg_id)
            db.set_admin(pending["id"], True)
            user = db.get_user(pending["id"])
        elif db.name_exists(name):
            await reply(
                update,
                f"Someone is already named <b>{escape(name)}</b>. "
                "Please send a different name.",
                None,
            )
            return
        else:
            user = db.create_user(tg_id, name, is_admin=True)
        await reply(
            update,
            f"Nice to meet you, {escape(user['name'])}! You're registered.\n\n"
            "👑 You've been set up as the <b>admin</b>. Use /help to see the "
            "admin commands for assigning spots.",
            menu(update),
        )
        await _refresh_commands(context, user)
        return

    req = db.upsert_request(tg_id, name, update.effective_user.username)
    await reply(update, WAITING, None)
    try:
        await _notify_new_request(context, tg_id, req)
    except Exception:
        log.warning("Could not notify admins about a new registration", exc_info=True)


async def _notify_new_request(context: ContextTypes.DEFAULT_TYPE, tg_id: int, req) -> None:
    username = f" (@{escape(req['username'])})" if req["username"] else ""
    text = (
        "🔔 <b>New registration request</b>\n\n"
        f"Name: <b>{escape(req['name'])}</b>\n"
        f"Telegram id: <code>{tg_id}</code>{username}\n\n"
        "Tap a button below, or use /users, /approve, /reject."
    )
    await notify_admins(context, text, keyboards.approval_kb(req["id"]))
