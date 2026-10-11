from __future__ import annotations

import logging
from datetime import time as dtime

from telegram import BotCommandScopeChat
from telegram.ext import (
    Application,
    CallbackQueryHandler,
    CommandHandler,
    MessageHandler,
    filters,
)

from . import config, db
from .handlers import admin, registration, user
from .handlers.common import (
    UNREGISTERED_COMMANDS,
    role_commands,
    set_role_commands,
)


async def _post_init(application: Application) -> None:
    bot = application.bot
    await bot.set_my_commands(UNREGISTERED_COMMANDS)
    for db_user in db.all_users():
        tg_id = db_user["telegram_id"]
        if tg_id is None:
            continue
        await set_role_commands(
            bot,
            tg_id,
            db.user_owns_spot(db_user["id"]),
            bool(db_user["is_admin"]),
        )
    admin_id = config.admin_id()
    if admin_id is not None and db.get_user_by_tg(admin_id) is None:
        try:
            await bot.set_my_commands(
                role_commands(False, True),
                scope=BotCommandScopeChat(chat_id=admin_id),
            )
        except Exception:
            logging.getLogger(__name__).warning(
                "Could not register the admin command menu.", exc_info=True
            )


def _schedule_daily_sweep(app: Application) -> None:
    """Run just after midnight: auto-release yesterday's claims.

    A claim only covers the day it was made, so this is mostly a cleanup +
    notification step. Claimers are only told the spot is free again if the
    owner's opening still covers the new day; otherwise they're told the owner
    is using the spot.
    """
    job_queue = getattr(app, "job_queue", None)
    if job_queue is None:
        logging.getLogger(__name__).warning(
            "JobQueue unavailable (install python-telegram-bot[job-queue]); "
            "claims still auto-expire by date logic, but nobody gets notified."
        )
        return

    async def _expire_yesterday(context) -> None:
        for row in db.expire_old_claims():
            if row["still_open"]:
                text = (
                    "🌅 New day — your claim on spot "
                    f"<b>#{row['spot_number']}</b> is released automatically. "
                    "The owner is still sharing it today, so others can claim it."
                )
            else:
                text = (
                    "🌅 New day — your claim on spot "
                    f"<b>#{row['spot_number']}</b> has ended because the owner "
                    "is using the spot again."
                )
            try:
                await context.bot.send_message(
                    chat_id=row["telegram_id"], text=text, parse_mode="HTML"
                )
            except Exception:
                continue

    job_queue.run_daily(_expire_yesterday, time=dtime(hour=0, minute=5))


def build_application() -> Application:
    db.init_db()

    app = Application.builder().token(config.BOT_TOKEN).post_init(_post_init).build()
    _schedule_daily_sweep(app)

    # Registration / general
    app.add_handler(CommandHandler("start", registration.cmd_start))
    app.add_handler(CommandHandler("menu", registration.cmd_menu))
    app.add_handler(CommandHandler("help", registration.cmd_help))

    # User features
    app.add_handler(CommandHandler("status", user.cmd_status))
    app.add_handler(CommandHandler("available", user.cmd_available))
    app.add_handler(CommandHandler("map", user.cmd_map))
    app.add_handler(CommandHandler("open", user.cmd_open))
    app.add_handler(CommandHandler("close", user.cmd_close))
    app.add_handler(CommandHandler("claim", user.cmd_claim))
    app.add_handler(CommandHandler("release", user.cmd_release))

    # Admin features
    app.add_handler(CommandHandler("admin", admin.cmd_admin))
    app.add_handler(CommandHandler("adduser", admin.cmd_adduser))
    app.add_handler(CommandHandler("deluser", admin.cmd_deluser))
    app.add_handler(CommandHandler("users", admin.cmd_users))
    app.add_handler(CommandHandler("approve", admin.cmd_approve))
    app.add_handler(CommandHandler("reject", admin.cmd_reject))
    app.add_handler(CommandHandler("spots", admin.cmd_spots))
    app.add_handler(CommandHandler("assign", admin.cmd_assign))
    app.add_handler(CommandHandler("rename", admin.cmd_rename))
    app.add_handler(CommandHandler("unassign", admin.cmd_unassign))
    app.add_handler(CommandHandler("settype", admin.cmd_settype))
    app.add_handler(CommandHandler("resetclaims", admin.cmd_resetclaims))
    app.add_handler(CommandHandler("cycle", admin.cmd_cycle))
    app.add_handler(CommandHandler("addcycles", admin.cmd_addcycles))
    app.add_handler(CommandHandler("delcycle", admin.cmd_delcycle))
    app.add_handler(CommandHandler("clearcycles", admin.cmd_clearcycles))

    # Approval buttons (must come before the general callback router)
    app.add_handler(CallbackQueryHandler(admin.on_approval_callback, pattern=r"^(appr|rej):"))

    # Buttons
    app.add_handler(CallbackQueryHandler(user.on_callback))

    # Plain text -> name capture / fallback
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, registration.on_text))

    # Admin "awaiting cycles" paste capture: runs before the registration
    # handler and stops propagation when it consumes the block.
    app.add_handler(MessageHandler(filters.TEXT, admin.on_cycles_text), group=-1)

    return app
