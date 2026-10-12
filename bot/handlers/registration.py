# -*- coding: utf-8 -*-
from __future__ import annotations

import logging

from telegram import Update
from telegram.ext import ContextTypes

from .. import db, keyboards
from ..assets import logo_path
from ..i18n import t
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


async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = get_db_user(update)
    if user is not None:
        lang = db.user_lang(user)
        await reply(
            update,
            t(lang, "welcome_back", name=escape(user["name"])),
            menu(update),
        )
        await _refresh_commands(context, user)
        return

    if update.effective_user is not None:
        req = db.latest_request(update.effective_user.id)
        if req is not None and req["status"] == "pending":
            await reply(update, t("en", "waiting"), None)
            return

    await _send_welcome(update)


async def _send_welcome(update: Update) -> None:
    """Send the welcome, with the logo as a photo when it's available."""
    path = logo_path()
    message = update.effective_message
    if path is not None and message is not None:
        try:
            with open(path, "rb") as handle:
                await message.reply_photo(handle, caption=t("en", "welcome"), parse_mode="HTML")
            return
        except Exception:
            pass
    await reply(update, t("en", "welcome"), None)


async def cmd_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if get_db_user(update) is None:
        return await cmd_start(update, context)
    await reply(update, t(db.user_lang(get_db_user(update)), "what_next"), menu(update))
    await _refresh_commands(context, get_db_user(update))


async def _refresh_commands(context: ContextTypes.DEFAULT_TYPE, user) -> None:
    if user is None or user["telegram_id"] is None:
        return
    await set_role_commands(
        context.bot,
        user["telegram_id"],
        db.user_owns_spot(user["id"]),
        bool(user["is_admin"]),
        db.user_lang(user),
    )


async def cmd_help(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = get_db_user(update)
    lang = db.user_lang(user) if user is not None else "en"
    await reply(update, t(lang, "help"), None)


async def on_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Non-command text: register the user's name, or nudge registered users."""
    if update.effective_user is None or update.message is None:
        return

    if get_db_user(update) is not None:
        await reply(
            update,
            t(db.user_lang(get_db_user(update)), "buttons_only"),
            menu(update),
        )
        return

    name = update.message.text.strip()
    if not (1 <= len(name) <= 40):
        await reply(update, t("en", "name_length"), None)
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
            await reply(update, t("en", "name_taken", name=escape(name)), None)
            return
        else:
            user = db.create_user(tg_id, name, is_admin=True)
        await reply(
            update,
            t("en", "registered_admin", name=escape(user["name"])),
            menu(update),
        )
        await _refresh_commands(context, user)
        return

    req = db.upsert_request(tg_id, name, update.effective_user.username)
    await reply(update, t("en", "waiting"), None)
    try:
        await _notify_new_request(context, tg_id, req)
    except Exception:
        log.warning("Could not notify admins about a new registration", exc_info=True)


async def _notify_new_request(context: ContextTypes.DEFAULT_TYPE, tg_id: int, req) -> None:
    username = f" (@{escape(req['username'])})" if req["username"] else ""
    texts = {
        lang: t(lang, "new_request", name=escape(req["name"]), tg=tg_id, username=username)
        for lang in ("en", "hy")
    }
    kbs = {lang: keyboards.approval_kb(req["id"], lang) for lang in ("en", "hy")}
    await notify_admins(context, texts, kbs)
