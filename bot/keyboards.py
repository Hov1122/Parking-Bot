# -*- coding: utf-8 -*-
from __future__ import annotations

import calendar
from datetime import date
from typing import Iterable, List, Optional

from telegram import InlineKeyboardButton, InlineKeyboardMarkup

from .i18n import month_abbr, month_name, t, weekdays


def _cancel(lang: str) -> InlineKeyboardButton:
    return InlineKeyboardButton(t(lang, "btn_cancel"), callback_data="cancel")


def main_menu(owns_spot: Optional[bool] = None, lang: str = "en") -> InlineKeyboardMarkup:
    """Main menu, tailored to the user's role and language.

    ``owns_spot=True`` shows open/close; ``owns_spot=False`` shows available +
    claim/release; ``None`` shows everything (fallback).
    """
    rows = [
        [
            InlineKeyboardButton(t(lang, "btn_status"), callback_data="status"),
            InlineKeyboardButton(t(lang, "btn_map"), callback_data="map"),
        ],
    ]
    if owns_spot is True:
        rows.append(
            [
                InlineKeyboardButton(t(lang, "btn_open"), callback_data="open"),
                InlineKeyboardButton(t(lang, "btn_close"), callback_data="close"),
            ]
        )
    elif owns_spot is False:
        rows.append([InlineKeyboardButton(t(lang, "btn_avail"), callback_data="avail")])
        rows.append(
            [
                InlineKeyboardButton(t(lang, "btn_claim"), callback_data="claim"),
                InlineKeyboardButton(t(lang, "btn_release"), callback_data="release"),
            ]
        )
    else:
        rows.append([InlineKeyboardButton(t(lang, "btn_avail"), callback_data="avail")])
        rows.append(
            [
                InlineKeyboardButton(t(lang, "btn_open"), callback_data="open"),
                InlineKeyboardButton(t(lang, "btn_close"), callback_data="close"),
            ]
        )
        rows.append(
            [
                InlineKeyboardButton(t(lang, "btn_claim"), callback_data="claim"),
                InlineKeyboardButton(t(lang, "btn_release"), callback_data="release"),
            ]
        )
    rows.append([InlineKeyboardButton(t(lang, "btn_lang"), callback_data="lang")])
    return InlineKeyboardMarkup(rows)


def datepicker_kb(
    selected: Iterable[str],
    year: int,
    month: int,
    min_day: Optional[str] = None,
    max_day: Optional[str] = None,
    lang: str = "en",
) -> InlineKeyboardMarkup:
    """A one-month calendar. Tapping a day toggles it (shown with a dot).

    ``min_day``/``max_day`` are ISO strings; days outside the range are shown
    as dots (disabled). ``cal:day:<iso>`` toggles, ``cal:prev``/``cal:next``
    navigate, ``cal:months`` opens the month picker, ``cal:ok`` confirms the
    selection, ``cal:until`` opens the spot with no end date.
    """
    selected_set = set(selected)
    rows: List[List[InlineKeyboardButton]] = [
        [
            InlineKeyboardButton(
                f"{month_name(month, lang)} {year} ▾", callback_data="cal:months"
            )
        ],
        [InlineKeyboardButton(w, callback_data="cal:ignore") for w in weekdays(lang)],
    ]
    for week in calendar.Calendar(firstweekday=0).monthdayscalendar(year, month):
        row: List[InlineKeyboardButton] = []
        for daynum in week:
            if daynum == 0:
                row.append(InlineKeyboardButton("·", callback_data="cal:ignore"))
                continue
            iso = f"{year:04d}-{month:02d}-{daynum:02d}"
            if (min_day and iso < min_day) or (max_day and iso > max_day):
                row.append(InlineKeyboardButton("·", callback_data="cal:ignore"))
                continue
            mark = "•" if iso in selected_set else ""
            row.append(
                InlineKeyboardButton(f"{mark}{daynum}", callback_data=f"cal:day:{iso}")
            )
        rows.append(row)
    rows.append(
        [
            InlineKeyboardButton("◀", callback_data="cal:prev"),
            InlineKeyboardButton(t(lang, "btn_open_days"), callback_data="cal:ok"),
            InlineKeyboardButton("▶", callback_data="cal:next"),
        ]
    )
    rows.append(
        [
            InlineKeyboardButton(t(lang, "btn_until"), callback_data="cal:until"),
            _cancel(lang),
        ]
    )
    return InlineKeyboardMarkup(rows)


def approval_kb(request_id: int, lang: str = "en") -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(t(lang, "btn_approve"), callback_data=f"appr:{request_id}"),
                InlineKeyboardButton(t(lang, "btn_reject"), callback_data=f"rej:{request_id}"),
            ]
        ]
    )


def map_nav_kb(
    prev_day: str, next_day: str, today: str, view_day: Optional[str] = None,
    lang: str = "en",
) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton("◀", callback_data=f"map:day:{prev_day}"),
                InlineKeyboardButton(t(lang, "btn_today"), callback_data=f"map:day:{today}"),
                InlineKeyboardButton("▶", callback_data=f"map:day:{next_day}"),
            ],
            [InlineKeyboardButton(t(lang, "btn_pick"), callback_data=f"map:pick:{view_day or today}")],
        ]
    )


def map_calendar_kb(
    sel_day: Optional[str],
    year: int,
    month: int,
    min_day: Optional[str] = None,
    max_day: Optional[str] = None,
    today: Optional[str] = None,
    lang: str = "en",
) -> InlineKeyboardMarkup:
    """Single-date calendar used by the map's "Pick a date" screen.

    Tapping the title opens the month picker (``mapcal:months:<YYYY-MM>``).
    """
    rows: List[List[InlineKeyboardButton]] = [
        [
            InlineKeyboardButton(
                f"{month_name(month, lang)} {year} ▾",
                callback_data=f"mapcal:months:{year:04d}-{month:02d}",
            )
        ],
        [InlineKeyboardButton(w, callback_data="mapcal:ignore") for w in weekdays(lang)],
    ]
    for week in calendar.Calendar(firstweekday=0).monthdayscalendar(year, month):
        row: List[InlineKeyboardButton] = []
        for daynum in week:
            if daynum == 0:
                row.append(InlineKeyboardButton("·", callback_data="mapcal:ignore"))
                continue
            iso = f"{year:04d}-{month:02d}-{daynum:02d}"
            if (min_day and iso < min_day) or (max_day and iso > max_day):
                row.append(InlineKeyboardButton("·", callback_data="mapcal:ignore"))
                continue
            mark = "•" if iso == sel_day else ""
            row.append(
                InlineKeyboardButton(f"{mark}{daynum}", callback_data=f"mapcal:day:{iso}")
            )
        rows.append(row)
    rows.append(
        [
            InlineKeyboardButton(
                "◀", callback_data=f"mapcal:nav:{year:04d}-{month:02d}:prev"
            ),
            InlineKeyboardButton(t(lang, "btn_today"), callback_data=f"map:day:{today or sel_day}"),
            InlineKeyboardButton(
                "▶", callback_data=f"mapcal:nav:{year:04d}-{month:02d}:next"
            ),
        ]
    )
    return InlineKeyboardMarkup(rows)


def month_grid_kb(
    year: int,
    prefix: str,
    min_ym: Optional[tuple] = None,
    max_ym: Optional[tuple] = None,
    back_callback: Optional[str] = None,
    lang: str = "en",
) -> InlineKeyboardMarkup:
    """Year view: 12 months plus year navigation. Tapping a month jumps there.

    ``prefix`` is ``"cal"`` (share-spot picker) or ``"mapcal"`` (map picker).
    Months outside ``[min_ym, max_ym]`` render as dots (disabled).
    When ``back_callback`` points at a ``<prefix>:month:<YYYY-MM>`` view, the
    year-navigation buttons carry that month along so "Back to days" still
    returns to the month the grid was opened from.
    """
    back_ym = ""
    if back_callback:
        tail = back_callback.rsplit(":", 1)[-1]
        if len(tail) == 7 and tail[4] == "-":
            back_ym = f":{tail}"
    rows: List[List[InlineKeyboardButton]] = [
        [
            InlineKeyboardButton("◀", callback_data=f"{prefix}:yprev:{year}{back_ym}"),
            InlineKeyboardButton(f"📅 {year}", callback_data=f"{prefix}:ignore"),
            InlineKeyboardButton("▶", callback_data=f"{prefix}:ynext:{year}{back_ym}"),
        ]
    ]
    row: List[InlineKeyboardButton] = []
    for m in range(1, 13):
        if (min_ym and (year, m) < min_ym) or (max_ym and (year, m) > max_ym):
            row.append(InlineKeyboardButton("·", callback_data=f"{prefix}:ignore"))
        else:
            row.append(
                InlineKeyboardButton(
                    month_abbr(m, lang),
                    callback_data=f"{prefix}:month:{year:04d}-{m:02d}",
                )
            )
        if len(row) == 4:
            rows.append(row)
            row = []
    if row:
        rows.append(row)
    if back_callback:
        rows.append(
            [InlineKeyboardButton(t(lang, "btn_back_days"), callback_data=back_callback)]
        )
    return InlineKeyboardMarkup(rows)


def close_days_kb(days: List[str], selected: Iterable[str], lang: str = "en") -> InlineKeyboardMarkup:
    """List the spot's currently-open days as toggles for taking days back."""
    chosen = set(selected)
    rows: List[List[InlineKeyboardButton]] = []
    row: List[InlineKeyboardButton] = []
    for iso in days:
        d = date.fromisoformat(iso)
        mark = "•" if iso in chosen else ""
        if lang == "hy":
            label = f"{mark}{d.day:02d}.{d.month:02d}"
        else:
            label = f"{mark}{d.strftime('%a %d %b')}"
        row.append(
            InlineKeyboardButton(label, callback_data=f"clz:day:{iso}")
        )
        if len(row) == 3:
            rows.append(row)
            row = []
    if row:
        rows.append(row)
    rows.append(
        [InlineKeyboardButton(t(lang, "btn_close_days"), callback_data="clz:ok")]
    )
    rows.append(
        [
            InlineKeyboardButton(t(lang, "btn_close_all"), callback_data="clz:all"),
            _cancel(lang),
        ]
    )
    return InlineKeyboardMarkup(rows)


def claim_menu(available: List[tuple[int, str]], lang: str = "en") -> InlineKeyboardMarkup:
    rows = [
        [InlineKeyboardButton(label, callback_data=f"claim:{number}")]
        for number, label in available
    ]
    rows.append([_cancel(lang)])
    return InlineKeyboardMarkup(rows)


def back_menu(lang: str = "en") -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [[InlineKeyboardButton(t(lang, "btn_menu"), callback_data="menu")]]
    )


def language_kb(lang: str = "en") -> InlineKeyboardMarkup:
    """Explicit language choice: English or Armenian."""
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton("🇬🇧 English", callback_data="lang:set:en"),
                InlineKeyboardButton("🇦🇲 Հայերեն", callback_data="lang:set:hy"),
            ],
            [_cancel(lang)],
        ]
    )
