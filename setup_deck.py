"""story-to-deck の実行ファイル群を /mnt/data にコピーするセットアップスクリプト。
Colab / Jupyter 等の環境で初回セットアップ時に一度実行する。
"""

import shutil
import sys
from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parent / ".claude" / "skills" / "story-to-deck"
DEST_DIR = Path("/mnt/data")

FILES = [
    "md_to_json.py",
    "to_pptx.py",
    "template_engine_area.html",
    "templates.json",
    "design.json",
    "logo.png",
    "background.png",
]


def main() -> None:
    missing = [f for f in FILES if not (SKILL_DIR / f).exists()]
    if missing:
        print(f"[エラー] スキルフォルダに以下のファイルが見つかりません: {missing}", file=sys.stderr)
        print(f"  スキルフォルダ: {SKILL_DIR}", file=sys.stderr)
        sys.exit(1)

    DEST_DIR.mkdir(parents=True, exist_ok=True)
    for name in FILES:
        src = SKILL_DIR / name
        dst = DEST_DIR / name
        shutil.copy2(src, dst)
        print(f"  copied: {name}")

    print(f"\nセットアップ完了 → {DEST_DIR}")
    print("\nPPTX生成コマンド:")
    print("  python /mnt/data/md_to_json.py deck_YYYYMMDD.md --assets-dir /mnt/data")


if __name__ == "__main__":
    main()
