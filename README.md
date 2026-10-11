# 🅿️ Office Parking Bot

A small Telegram bot for a shared office parking lot. It keeps track of who
owns which spot and lets people **share a spot** on days they don't drive, so
colleagues without a spot can use it.

Designed for ~10 users today and scales comfortably to 40+ (SQLite, no server
needed). Built with [`python-telegram-bot`](https://github.com/python-telegram-bot/python-telegram-bot).

## How it works

- **Auth by Telegram ID.** No passwords. On first `/start` the bot asks for a
  name; the request is sent to the admin, who taps **Approve** (or **Reject**)
  before the name is bound to the user's Telegram ID. The admin can also
  pre-create accounts by name with `/adduser`. The name is shown everywhere.
- **9 spots in two basement levels** (see `bot/layout.py`): **B1** — 1,2,3 in
  a row + 4 closing their front; **B2** — 5 (standalone, reserved), 6+7 side
  by side (6 reserved), 8 closing the front of 6 & 7, 9 (standalone).
  Reserved = `1,2,5,6`; rotating = `3,4,7,8,9`. The admin assigns owners by
  hand — for the 3-month rotation just reassign the rotating spots with
  `/assign`.
- **Live map:** every user runs `/map` and sees a generated PNG of the lot:
  **blue** = their own spot, **green** = free, **red** = in use, **gray** = no
  owner. Each box shows the spot number plus the owner's name (or who is
  parked there today). Use the **◀ / ▶ / Today** buttons or **📅 Pick a date**
  to browse the lot day by day — the caption lists which spots are free that
  day. Layout/positions are one editable file: `bot/layout.py`.
- **Share a spot:** an owner who won't drive runs `/open` and taps the day(s)
  they're away on a calendar, then **Open these days** — or **Until I close
  it**. Rotating spots can only be opened up to `ROTATION_END`. The spot shows
  up as available to everyone on those days.
- **Take a spot:** a user **without any spot** (no reserved, no rotating) runs
  `/claim`, taps the free spot they physically parked in, and is recorded as
  occupying it for the day. Owners can never claim someone else's spot.
  The main menu is tailored: **spot owners** see *Open/Close my spot* (no
  available/claim), while **everyone without a spot** sees *Available spots /
  I parked / I left* instead.
- **Give it back:** the taker runs `/release` when they leave — or it's
  **auto-released at midnight** (a claim only covers the day it was made). A
  nightly sweep notifies the taker: the spot is announced as free again only
  *if the owner is still sharing it*; otherwise the taker is told the owner is
  using the spot.

### Spot states (per day)

| State | Meaning |
|-------|---------|
| 🔒 owner | assigned and not shared |
| 🔓 open | owner shared it — free for others |
| 🚗 occupied | someone without a spot claimed it |
| ⚪ unassigned | no owner (free, e.g. during rotation gaps) |

## Quick start (local test)

```bash
cd parking-bot
python -m venv .venv
# Windows:  .venv\Scripts\activate
# Linux:    source .venv/bin/activate
pip install -r requirements.txt

cp .env.example .env      # then edit .env (see below)
python main.py
```

Run the logic self-test (no token needed):

```bash
python tests/selftest.py
```

## Configuration (`.env`)

| Variable | Description |
|----------|-------------|
| `BOT_TOKEN` | Token from [@BotFather](https://t.me/BotFather). **Required.** |
| `ADMIN_TELEGRAM_ID` | Your numeric Telegram ID (from [@userinfobot](https://t.me/userinfobot)). If left empty, the **first** person to register becomes admin. |
| `DB_PATH` | SQLite file path (default `parking.db`). |
| `ROTATION_END` | Last valid day of the rotation (`YYYY-MM-DD`). Rotating-spot owners can only open days up to this date. Empty = no limit. |

The spot layout (numbers, reserved/rotating type, physical positions) lives in
`bot/layout.py` — one editable file. `pip install -r requirements.txt` includes
`Pillow`, which the map feature needs.

## Commands

**Everyone**
| Command | Action |
|---------|--------|
| `/start`, `/menu` | Register (admin approval required) / open the main menu |
| `/map` | PNG map, browsable day by day (◀ / ▶ / Today / pick a date) |
| `/status` | Your spot and today's situation |
| `/available` | Spots that are free today |
| `/open` | Share your spot — tap the day(s) on a calendar, or "until closed" |
| `/close` | Take back specific day(s) from your shared spot, or stop sharing entirely |
| `/claim` | Record that you parked in a free spot |
| `/release` | Record that you left that spot |
| `/help` | Help text |

**Admin only**
| Command | Action |
|---------|--------|
| `/adduser <name>` | Pre-create a user account (they bind on approval) |
| `/deluser <name or tg-id>` | Delete a user (frees their spot, drops their data) |
| `/makeadmin <name or tg-id>` | Grant admin rights (approvals, admin commands) |
| `/demote <name or tg-id>` | Remove admin rights (last admin is protected) |
| `/users` | List registered users and pending approval requests |
| `/approve <tg-id>` / `/reject <tg-id>` | Resolve a request without the buttons |
| `/spots` | List every spot, owner and today's state |
| `/assign <spot#> <name or telegram-id>` | Give a spot to a user |
| `/unassign <spot#>` | Remove a spot's owner |
| `/settype <spot#> reserved\|rotating` | Change a spot's type |
| `/rename <name\|tg-id> <new name>` | Fix a user's display name |
| `/resetclaims` | Clear today's "I parked" marks |

New users who message the bot are shown as buttons in the admin's chat; the
admin taps **Approve** to let them in. The Telegram command menu (`/`) is
registered automatically, with the admin commands visible only to the admin.

## Deploy on your Ubuntu server

```bash
sudo apt update && sudo apt install -y python3 python3-venv
cd /opt/parking-bot          # or wherever you copied the project
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env && nano .env     # set BOT_TOKEN and ADMIN_TELEGRAM_ID
```

Create a systemd service `/etc/systemd/system/parking-bot.service`
(see `parking-bot.service` in this repo — adjust `User` and `WorkingDirectory`):

```bash
sudo cp parking-bot.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now parking-bot
sudo systemctl status parking-bot
journalctl -u parking-bot -f          # live logs
```

### First-run checklist

1. In Telegram, open your bot and send `/start`.
2. Send your name → you're approved and registered (the first user, or the
   `ADMIN_TELEGRAM_ID` account, becomes admin automatically). Everyone else
   waits for you to tap **Approve** (or run `/adduser <name>` first and
   approve when they join).
3. `/assign` the reserved spots (1, 2, 5, 6) to their owners.
4. `/assign` the rotating spots (3, 4, 7, 8, 9).
5. Check the map with `/map` — if positions look wrong, tweak `bot/layout.py`.
6. Every 3 months, repeat step 4 with the new rotation.

> **Notes / boundaries**
> - "Today" uses the server's local date. Set the server timezone
>   (`sudo timedatectl set-timezone ...`) to your office's timezone.
> - `reserved` vs `rotating` is just a label + config; owners are always set
>   manually, so the rotation logic is intentionally yours to control.
> - Unassigned spots are treated as always free and can be claimed.
