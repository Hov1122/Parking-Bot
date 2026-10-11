from __future__ import annotations

import logging
from typing import Optional

from telegram import BotCommand, BotCommandScopeChat, Update
from telegram.error import BadRequest
from telegram.ext import ContextTypes

from .. import config, db
from ..keyboards import main_menu

log = logging.getLogger(__name__)

# --- Role-based Telegram command menus ------------------------------------- #
_BASE_COMMANDS = [
    BotCommand("start", "Register / main menu"),
    BotCommand("menu", "Main menu"),
    BotCommand("status", "My spot and today"),
    BotCommand("map", "Parking map"),
]
_OWNER_COMMANDS = [
    BotCommand("open", "Share my spot"),
    BotCommand("close", "Stop sharing my spot"),
]
_NONOWNER_COMMANDS = [
    BotCommand("available", "Free spots today"),
    BotCommand("claim", "I parked in a free spot"),
    BotCommand("release", "I left my claimed spot"),
]
_HELP_COMMAND = [BotCommand("help", "Help")]

UNREGISTERED_COMMANDS = [
    BotCommand("start", "Register / main menu"),
    BotCommand("help", "Help"),
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


def role_commands(owns_spot: bool, is_admin: bool = False) -> list[BotCommand]:
    """The command list a user should see, based on their role."""
    commands = list(_BASE_COMMANDS)
    commands += _OWNER_COMMANDS if owns_spot else _NONOWNER_COMMANDS
    commands += _HELP_COMMAND
    if is_admin:
        commands += ADMIN_COMMANDS
    return commands


async def set_role_commands(
    bot, chat_id: int, owns_spot: bool, is_admin: bool = False
) -> None:
    """Refresh the per-chat ``/`` command menu so it matches the user's role."""
    try:
        await bot.set_my_commands(
            role_commands(owns_spot, is_admin), scope=BotCommandScopeChat(chat_id=chat_id)
        )
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


def menu(update: Update):
    """The main menu, tailored to whether the user owns a spot."""
    user = get_db_user(update)
    owns = bool(user and db.user_owns_spot(user["id"]))
    return main_menu(owns)


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


async def notify_admins(context: ContextTypes.DEFAULT_TYPE, text: str, keyboard=None) -> None:
    """Best-effort broadcast of a message to every admin."""
    ids = admin_tg_ids()
    if not ids:
        log.warning("notify_admins: no admins configured/found, message dropped.")
        return
    for tg_id in ids:
        try:
            await context.bot.send_message(
                chat_id=tg_id, text=text, reply_markup=keyboard, parse_mode="HTML"
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
            "You're not registered yet. Send /start and tell me your name first.",
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
    "ContextTypes",
    "role_commands",
    "set_role_commands",
    "clear_role_commands",
    "UNREGISTERED_COMMANDS",
    "ADMIN_COMMANDS",
]
