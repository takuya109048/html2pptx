"""Shared slide definition — single source of truth for HTML & PPTX.
All positions/sizes in inches (LAYOUT_16x9: 10" x 5.625").
"""

SLIDE_W = 10.0
SLIDE_H = 5.625

COLORS = {
    "bg":         "FFFFFF",
    "surface":    "F5F5F5",
    "border":     "E0E0E0",
    "text":       "333333",
    "textMuted":  "888888",
    "headerBg":   "4A4A4A",
    "headerText": "FFFFFF",
}

FONTS = {
    "family": "Segoe UI",
    "title":     {"size": 24, "bold": True},
    "message":   {"size": 12, "bold": False},
    "cardTitle": {"size": 15, "bold": True},
    "cardBody":  {"size": 11, "bold": False},
    "footer":    {"size": 10, "bold": False},
}

MARGIN_X = 0.25
CARD_GAP = 0.15

HEADER = {"x": 0, "y": 0, "w": SLIDE_W, "h": 0.85, "padX": MARGIN_X, "padY": 0.08}

BODY = {
    "x": MARGIN_X,
    "y": 0.95,
    "w": SLIDE_W - MARGIN_X * 2,
    "h": 4.15,
}

_card_w = (BODY["w"] - CARD_GAP) / 2
CARDS = [
    {"x": BODY["x"],                          "y": BODY["y"], "w": _card_w, "h": BODY["h"]},
    {"x": BODY["x"] + _card_w + CARD_GAP,     "y": BODY["y"], "w": _card_w, "h": BODY["h"]},
]
CARD_PAD = {"x": 0.2, "y": 0.15}
CARD_DIVIDER_OFFSET_Y = 0.5

FOOTER = {"x": 0, "y": SLIDE_H - 0.4, "w": SLIDE_W, "h": 0.4, "padX": MARGIN_X}
LOGO_H = 0.25

SLIDES = [
    {
        "header": {
            "title": "スライドタイトルをここに入力",
            "message": "補足メッセージやサブタイトルをここに記載します",
        },
        "cards": [
            {
                "title": "左カード見出し",
                "bullets": ["ポイント1の説明テキスト", "ポイント2の説明テキスト", "ポイント3の説明テキスト"],
            },
            {
                "title": "右カード見出し",
                "bullets": ["ポイント1の説明テキスト", "ポイント2の説明テキスト", "ポイント3の説明テキスト"],
            },
        ],
        "page": "1 / 1",
        "logo": "logo.png",
    },
]
