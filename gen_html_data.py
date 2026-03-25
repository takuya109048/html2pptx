"""Generate slide-data.json from slide_data.py for HTML consumption."""
import json, os
from slide_data import (
    SLIDE_W, SLIDE_H, COLORS, FONTS,
    HEADER, BODY, CARDS, CARD_PAD, CARD_DIVIDER_OFFSET_Y,
    FOOTER, LOGO_H, SLIDES,
)

data = {
    "SLIDE_W": SLIDE_W, "SLIDE_H": SLIDE_H,
    "COLORS": COLORS, "FONTS": FONTS,
    "HEADER": HEADER, "BODY": BODY,
    "CARDS": CARDS, "CARD_PAD": CARD_PAD,
    "CARD_DIVIDER_OFFSET_Y": CARD_DIVIDER_OFFSET_Y,
    "FOOTER": FOOTER, "LOGO_H": LOGO_H,
    "SLIDES": SLIDES,
}

out = os.path.join(os.path.dirname(os.path.abspath(__file__)), "slide-data.json")
with open(out, "w", encoding="utf-8") as f:
    json.dump(data, f, ensure_ascii=False, indent=2)
print(f"Saved: {out}")
