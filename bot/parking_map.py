from __future__ import annotations

from io import BytesIO

from PIL import Image, ImageDraw, ImageFont

from . import db
from . import layout as L

# Colors (filled spot interiors + darker outlines)
MINE = (59, 130, 246)
MINE_FILL = (219, 234, 254)
OPEN = (34, 197, 94)
OPEN_FILL = (220, 252, 231)
IN_USE = (239, 68, 68)
IN_USE_FILL = (254, 226, 226)
UNASSIGNED = (148, 163, 184)
UNASSIGNED_FILL = (241, 245, 249)
ROAD = (203, 213, 225)
BG = (241, 245, 249)
TEXT = (15, 23, 42)

BOLD_FONTS = [
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    "/usr/share/fonts/dejavu/DejaVuSans-Bold.ttf",
    "C:/Windows/Fonts/arialbd.ttf",
    "/Library/Fonts/Arial Bold.ttf",
]
REGULAR_FONTS = [
    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    "C:/Windows/Fonts/arial.ttf",
    "/Library/Fonts/Arial.ttf",
]


def _font(size: int, bold: bool = True) -> ImageFont.ImageFont:
    candidates = BOLD_FONTS if bold else REGULAR_FONTS
    for path in candidates:
        try:
            return ImageFont.truetype(path, size)
        except OSError:
            continue
    try:
        return ImageFont.load_default(size=size)
    except TypeError:
        return ImageFont.load_default()


def _center(draw: ImageDraw.ImageDraw, x: float, y: float, text: str, font, fill) -> None:
    bbox = draw.textbbox((0, 0), text, font=font)
    w = bbox[2] - bbox[0]
    h = bbox[3] - bbox[1]
    draw.text((x - w / 2, y - h / 2), text, font=font, fill=fill)


def _fit_font(draw: ImageDraw.ImageDraw, text: str, max_w: float, start_size: int, bold: bool = False):
    """Largest font (down to 9px) whose text fits within max_w."""
    size = max(9, start_size)
    while size > 9:
        font = _font(size, bold)
        if draw.textlength(text, font=font) <= max_w:
            return font
        size -= 1
    return _font(9, bold)


def _spot_colors(spot_row, state, owner_user_id, effective_owner_id):
    mine = (
        effective_owner_id is not None
        and owner_user_id is not None
        and effective_owner_id == owner_user_id
    )
    if mine:
        return MINE, MINE_FILL
    if state == db.OPEN:
        return OPEN, OPEN_FILL
    if state in (db.OCCUPIED, db.OWNER):
        return IN_USE, IN_USE_FILL
    return UNASSIGNED, UNASSIGNED_FILL


def render_map(owner_user_id=None, day=None) -> bytes:
    """Render the parking lot as a PNG. Returns raw image bytes."""
    day = day or db.today()
    specs = list(L.SPOTS)
    if not specs:
        raise RuntimeError("layout.SPOTS is empty — nothing to draw.")

    scale = L.SCALE
    margin = 30
    header_h = 64
    footer_h = 64

    max_x = max(s["x"] + s["w"] for s in specs)
    max_y = max(s["y"] + s["h"] for s in specs)
    width = margin * 2 + int(max_x * scale)
    height = header_h + int(max_y * scale) + footer_h

    img = Image.new("RGB", (width, height), BG)
    draw = ImageDraw.Draw(img)

    # Title
    _center(draw, width / 2, header_h / 2 - 6, "Office Parking", _font(28, True), TEXT)
    _center(draw, width / 2, header_h - 14, day, _font(14, False), TEXT)

    # Group spots by floor, keeping layout order (B2 first, then B1).
    by_floor: dict[str, list] = {}
    for s in specs:
        by_floor.setdefault(s["floor"], []).append(s)
    floor_order = list(by_floor)

    # Roads: a band between each floor's bottom edge and the next floor's top.
    road_band: dict[str, tuple[int, int]] = {}
    for i, floor in enumerate(floor_order):
        top = min(s["y"] for s in by_floor[floor])
        bottom = max(s["y"] + s["h"] for s in by_floor[floor])
        if i + 1 < len(floor_order):
            next_top = min(s["y"] for s in by_floor[floor_order[i + 1]])
            road_band[floor] = (bottom, next_top - 8)
        else:
            road_band[floor] = (bottom, bottom + 16)

    drawn_floors: set[str] = set()
    for spec in specs:
        floor = spec["floor"]
        x0 = margin + int(spec["x"] * scale)
        y0 = header_h + int(spec["y"] * scale)
        x1 = margin + int((spec["x"] + spec["w"]) * scale)
        y1 = header_h + int((spec["y"] + spec["h"]) * scale)

        if floor not in drawn_floors:
            draw.text(
                (margin, y0 - 26),
                f"Level {floor}",
                font=_font(18, True),
                fill=TEXT,
            )
        # Road under this floor's row(s).
        band_bottom, band_road_bottom = road_band[floor]
        if floor == floor_order[-1]:
            road_y1 = height - 6
        else:
            road_y1 = header_h + int(band_road_bottom * scale)
        draw.rectangle(
            [margin, header_h + int(band_bottom * scale), x1, road_y1],
            fill=ROAD,
        )

        spot_row = db.get_spot_by_number(spec["number"])
        if spot_row is not None:
            state, other, _ = db.spot_status(spot_row, day)
            eff_owner = db.effective_owner_id(spot_row, day)
            outline, interior = _spot_colors(spot_row, state, owner_user_id, eff_owner)

            draw.rounded_rectangle(
                [x0, y0, x1, y1], radius=10, fill=interior, outline=outline, width=4
            )

            box_w = x1 - x0
            box_h = y1 - y0
            inner_w = box_w - 16

            num_font = _font(max(16, int(box_h * 0.42)), True)
            _center(draw, (x0 + x1) / 2, y0 + box_h * 0.30, str(spec["number"]), num_font, TEXT)

            # Show who is associated with the spot: the person parked there
            # today, else the (cycle-aware) owner, else a helper label.
            label = None
            if state == db.OCCUPIED and other is not None:
                label = other["name"]
            elif eff_owner:
                owner = db.get_user(eff_owner)
                if owner:
                    label = owner["name"]
            elif state == db.OPEN and other is not None:
                label = f"free · {other['name']}"
            if not label:
                label = "no owner"
            name_font = _fit_font(draw, label, inner_w, int(box_h * 0.30))
            _center(draw, (x0 + x1) / 2, y1 - box_h * 0.28, label, name_font, outline)

        drawn_floors.add(floor)

    # Legend
    legend_y = height - footer_h + 18
    items = [
        ("Your spot", MINE),
        ("Free", OPEN),
        ("In use", IN_USE),
        ("No owner", UNASSIGNED),
    ]
    legend_font = _font(14, False)
    lx = margin
    for label, color in items:
        draw.rounded_rectangle([lx, legend_y, lx + 18, legend_y + 18], radius=4, fill=color)
        text_w = draw.textlength(label, font=legend_font)
        draw.text((lx + 26, legend_y), label, font=legend_font, fill=TEXT)
        lx += 26 + text_w + 28

    buf = BytesIO()
    _paste_logo(img, margin, 8, header_h - 16)
    img.save(buf, format="PNG")
    return buf.getvalue()


def _paste_logo(img: Image.Image, x: int, y: int, target_h: int) -> None:
    """Draw the bot logo in the map's header, if a logo.png exists."""
    try:
        from .assets import logo_path

        path = logo_path()
        if path is None:
            return
        logo = Image.open(path).convert("RGBA")
        ratio = target_h / logo.height
        logo = logo.resize((max(1, int(logo.width * ratio)), max(1, target_h)))
        img.paste(logo, (x, y), logo)
    except Exception:
        return


CAPTION = (
    "🅿️ <b>Office Parking</b>\n"
    "Blue = your spot · Green = free · Red = in use · Gray = no owner"
)