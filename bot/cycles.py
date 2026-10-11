from __future__ import annotations

"""Parse a pasted rotation-cycle plan.

Expected block (names may contain spaces)::

    Cycle 1 12/10/26-31/12/26
    1 - Test
    2 - Test2
    Cycle 2 01/01/27-31/03/27
    1 - test3
    2 - test2

Dates are day-first: ``DD/MM/YY`` (a 4-digit year also works). A line is a
header when it starts with ``cycle`` or contains two dates; everything else
that looks like ``<number> - <name>`` is an assignment.
"""

import re
from dataclasses import dataclass, field
from datetime import date
from typing import List, Tuple

_DATE_RE = re.compile(r"(\d{1,2})[/.\-](\d{1,2})[/.\-](\d{2,4})")
_HEADER_RE = re.compile(r"(?i)^\s*cycle\b")
_ASSIGN_RE = re.compile(r"^\s*(\d{1,3})\s*[\-\u2013\u2014:.)]*\s*(\S.*)$")


class CycleParseError(ValueError):
    """Raised when the pasted block can't be understood."""


@dataclass
class ParsedCycle:
    label: str
    start: str  # ISO date
    end: str  # ISO date
    assignments: List[Tuple[int, str]] = field(default_factory=list)


def _parse_date(day: str, month: str, year: str) -> str:
    d, m, y = int(day), int(month), int(year)
    if y < 100:
        y += 2000
    try:
        return date(y, m, d).isoformat()
    except ValueError as exc:
        raise CycleParseError(f"Invalid date {day}/{month}/{year}.") from exc


def parse_cycles(text: str) -> List[ParsedCycle]:
    """Parse the pasted block into cycles, or raise :class:`CycleParseError`."""
    cycles: List[ParsedCycle] = []
    current: ParsedCycle | None = None

    for lineno, raw in enumerate(text.splitlines(), start=1):
        line = raw.strip()
        if not line:
            continue

        dates = _DATE_RE.findall(line)
        is_header = bool(_HEADER_RE.match(line)) or len(dates) >= 2

        if is_header:
            if len(dates) != 2:
                raise CycleParseError(
                    f"Line {lineno}: a cycle header needs a start and end date "
                    f"(e.g. \"Cycle 1 12/10/26-31/12/26\")."
                )
            start = _parse_date(*dates[0])
            end = _parse_date(*dates[1])
            if end < start:
                raise CycleParseError(
                    f"Line {lineno}: the end date ({end}) is before the start "
                    f"date ({start})."
                )
            label = line[: _DATE_RE.search(line).start()].strip() or None
            current = ParsedCycle(label=label, start=start, end=end)
            cycles.append(current)
            continue

        match = _ASSIGN_RE.match(line)
        if not match:
            raise CycleParseError(f"Line {lineno}: I couldn't read \"{line}\".")
        number = int(match.group(1))
        name = match.group(2).strip()
        if current is None:
            raise CycleParseError(
                f"Line {lineno}: \"{line}\" appears before any cycle header."
            )
        if not name:
            raise CycleParseError(f"Line {lineno}: missing a name after the spot.")
        current.assignments.append((number, name))

    if not cycles:
        raise CycleParseError("No cycles found. Send at least one cycle block.")

    for cycle in cycles:
        if not cycle.assignments:
            label = cycle.label or f"{cycle.start}–{cycle.end}"
            raise CycleParseError(f"Cycle \"{label}\" has no spots assigned.")

    return cycles
