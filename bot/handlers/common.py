from __future__ import annotations

import logging
from typing import Optional

from telegram import BotCommand, BotCommandScopeChat, Update
from telegram.error import BadRequest
from telegram.ext import ContextTypes

from .. import config, db
from ..i18n import t
from ..keyboards import main_menu

log = logging.getLogger(__name__)

# --- Role-based Telegram command menus ------------------------------------- #
_BASE = ["start", "menu", "status", "map"]
_OWNER = ["open", "close"]
_NONOWNER = ["available", "claim", "release"]
_HELPTAIL = ["help", "language"]
_ADMIN = [
    "admin", "adduser", "deluser", "makeadmin", "demote", "users", "approve",
    "reject", "spots", "assign", "unassign", "settype", "rename",
    "resetclaims", "cycle", "addcycles", "delcycle", "clearcycles",
]
_CMD_KEY = {
    "start": "cmd_start", "menu": "cmd_menu", "status": "cmd_status",
    "map": "cmd_map", "open": "cmd_open", "close": "cmd_close",
    "available": "cmd_available", "claim": "cmd_claim", "release": "cmd_release",
    "help": "cmd_help", "language": "cmd_language", "admin": "cmd_admin",
    "adduser": "cmd_adduser", "deluser": "cmd_deluser",
    "makeadmin": "cmd_makeadmin", "demote": "cmd_demote", "users": "cmd_users",
    "approve": "cmd_approve", "reject": "cmd_reject", "spots": "cmd_spots",
    "assign": "cmd_assign", "unassign": "cmd_unassign", "settype": "cmd_settype",
    "rename": "cmd_rename", "resetclaims": "cmd_resetclaims", "cycle": "cmd_cycle",
    "addcycles": "cmd_addcycles", "delcycle": "cmd_delcycle",
    "clearcycles": "cmd_clearcycles",
}

UNREGISTERED_COMMANDS = [
    BotCommand("start", "Register / main menu"),
    BotCommand("help", "Help"),
    BotCommand("language", "Switch language"),
]

ADMIN_COMMANDS = [
    BotCommand("admin", "Admin help"),
    BotCommand("adduser", "Pre-create a user account"),
    BotCommand("deluser", "Delete a user"),
    BotCommand("makeadmin", "Grant admin rights"),
    BotCommand("demote", "Remove admin rights"),
    BotCommand("users", "Users and pending requests"),
    BotCommand("approve", "Approve a registration (by telegram id)"),
    BotCommand("reject", "Reject a registration (by telegram id)"),
    BotCommand("spots", "List all spots"),
    BotCommand("assign", "Assign a spot to a user"),
    BotCommand("unassign", "Remove a spot owner"),
    BotCommand("settype", "Set spot type"),
    BotCommand("rename", "Fix a user's display name"),
    BotCommand("resetclaims", "Clear today's claims"),
    BotCommand("cycle", "Show rotation cycles"),
    BotCommand("addcycles", "Add rotation cycles (paste a plan)"),
    BotCommand("delcycle", "Delete a rotation cycle by id"),
    BotCommand("clearcycles", "Remove all rotation cycles"),
]


def _cmd(name: str, lang: str) -> BotCommand:
    return BotCommand(name, t(lang, _CMD_KEY[name]))


def role_commands(owns_spot: bool, is_admin: bool = False, lang: str = "en") -> list[BotCommand]:
    """The command list a user should see, based on role and language."""
    names = list(_BASE)
    names += _OWNER if owns_spot else _NONOWNER
    names += _HELPTAIL
    if is_admin:
        names += _ADMIN
    return [_cmd(n, lang) for n in names]


async def set_role_commands(
    bot, chat_id: int, owns_spot: bool, is_admin: bool = False, lang: str = "en"
) -> None:
    """Refresh the per-chat ``/`` command menu so it matches the user's role."""
    try:
        await bot.set_my_commands(
            role_commands(owns_spot, is_admin, lang), scope=BotCommandScopeChat(chat_id=chat_id)
        )
    except BadRequest as exc:
        if "chat not found" in str(exc).lower():
            # Approved but never opened the bot (or blocked/deleted it).
            # The menu is set on their next /start instead.
            log.info("No Telegram chat yet for %s, command menu skipped.", chat_id)
        else:
            log.warning("Could not set the command menu for chat %s", chat_id, exc_info=True)
    except Exception:
        log.warning("Could not set the command menu for chat %s", chat_id, exc_info=True)


async def clear_role_commands(bot, chat_id: int) -> None:
    """Reset a chat's command menu to the unregistered default."""
    try:
        await bot.set_my_commands(
            UNREGISTERED_COMMANDS, scope=BotCommandScopeChat(chat_id=chat_id)
        )
    except Exception:
        log.warning("Could not reset the command menu for chat %s", chat_id, exc_info=True)



def get_db_user(update: Update):
    if update.effective_user is None:
        return None
    return db.get_user_by_tg(update.effective_user.id)


def lang_of(user) -> str:
    return db.user_lang(user)


def menu(update: Update):
    """The main menu, tailored to ownership and language."""
    user = get_db_user(update)
    owns = bool(user and db.user_owns_spot(user["id"]))
    return main_menu(owns, db.user_lang(user))


def is_admin(update: Update) -> bool:
    user = get_db_user(update)
    return bool(user and user["is_admin"])


def is_bootstrap_admin(tg_id: int) -> bool:
    """The configured admin, or the very first user if no admin is configured."""
    configured = config.admin_id()
    if configured is not None:
        return tg_id == configured
    return db.count_admins() == 0


def is_admin_tg(tg_id: int) -> bool:
    """True when a bare telegram id belongs to the configured/admin user."""
    if config.admin_id() is not None and tg_id == config.admin_id():
        return True
    user = db.get_user_by_tg(tg_id)
    return bool(user and user["is_admin"])


def admin_tg_ids() -> list[int]:
    """Every telegram id that should receive admin notifications (deduplicated)."""
    ids: list[int] = []
    configured = config.admin_id()
    if configured is not None:
        ids.append(configured)
    for user in db.all_users():
        if user["is_admin"] and user["telegram_id"] is not None:
            ids.append(user["telegram_id"])
    seen: set[int] = set()
    unique: list[int] = []
    for tg_id in ids:
        if tg_id not in seen:
            seen.add(tg_id)
            unique.append(tg_id)
    return unique


def _pick(localized, lang: str):
    if isinstance(localized, dict):
        return localized.get(lang) or localized.get("en")
    return localized


async def notify_admins(context: ContextTypes.DEFAULT_TYPE, text, keyboard=None) -> None:
    """Best-effort broadcast to every admin.

    ``text``/``keyboard`` may be plain values (same for everyone) or
    ``{"en": ..., "hy": ...}`` dicts — each admin gets their own language.
    """
    ids = admin_tg_ids()
    if not ids:
        log.warning("notify_admins: no admins configured/found, message dropped.")
        return
    for tg_id in ids:
        lang = db.user_lang(db.get_user_by_tg(tg_id))
        try:
            await context.bot.send_message(
                chat_id=tg_id, text=_pick(text, lang),
                reply_markup=_pick(keyboard, lang), parse_mode="HTML",
            )
        except Exception:
            log.warning("notify_admins: could not message admin %s", tg_id, exc_info=True)


async def reply(
    update: Update,
    text: str,
    keyboard=None,
    parse_mode: Optional[str] = "HTML",
) -> None:
    """Reply to either a message or a callback query, editing in place when possible."""
    if update.callback_query is not None:
        try:
            await update.callback_query.edit_message_text(
                text, reply_markup=keyboard, parse_mode=parse_mode
            )
            return
        except BadRequest as exc:
            if "not modified" in str(exc).lower():
                return
            await update.callback_query.message.reply_text(
                text, reply_markup=keyboard, parse_mode=parse_mode
            )
            return
        except Exception:
            await update.callback_query.message.reply_text(
                text, reply_markup=keyboard, parse_mode=parse_mode
            )
            return
    await update.effective_message.reply_text(
        text, reply_markup=keyboard, parse_mode=parse_mode
    )


async def need_registration(update: Update) -> bool:
    """Returns True (and nudges the user) when they haven't registered yet."""
    if get_db_user(update) is None:
        await reply(
            update,
            t("en", "not_registered"),
            None,
        )
        return True
    return False


def mention(user) -> str:
    name = user["name"] if user is not None else "someone"
    return f"<b>{escape(name)}</b>"


def escape(text: str) -> str:
    return (
        str(text)
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
    )


__all__ = [
    "get_db_user",
    "is_admin",
    "is_admin_tg",
    "is_bootstrap_admin",
    "admin_tg_ids",
    "notify_admins",
    "menu",
    "reply",
    "need_registration",
    "mention",
    "escape",
    "lang_of",
    "ContextTypes",
    "role_commands",
    "set_role_commands",
    "clear_role_commands",
    "UNREGISTERED_COMMANDS",
    "ADMIN_COMMANDS",
]
