"""ファイルの文字数を計測するスクリプト。

SKILL設計ルールの文字数上限チェックに使用する:
  SKILL.md  : 5,000文字以内
  context.md: 20,000文字以内

Usage:
    python count_chars.py <file> [<file> ...]
    python count_chars.py .claude/skills/deck-from-source/SKILL.md
    python count_chars.py .claude/skills/deck-from-source/SKILL.md .claude/skills/deck-from-source/context.md
"""

import sys
from pathlib import Path

LIMITS: dict[str, int] = {
    "SKILL.md": 5_000,
    "context.md": 20_000,
}


def count_file(path: Path) -> None:
    text = path.read_text(encoding="utf-8")
    count = len(text)
    limit = LIMITS.get(path.name)

    if limit is not None:
        status = "OK" if count <= limit else "OVER"
        bar = f"{count:,} / {limit:,}文字  [{status}]"
        print(f"{path}  →  {bar}")
    else:
        print(f"{path}  →  {count:,}文字")


def main() -> None:
    if len(sys.argv) < 2:
        print("Usage: python count_chars.py <file> [<file> ...]")
        sys.exit(1)

    has_error = False
    for arg in sys.argv[1:]:
        p = Path(arg)
        if not p.exists():
            print(f"[エラー] ファイルが見つかりません: {p}", file=sys.stderr)
            has_error = True
            continue
        count_file(p)

    if has_error:
        sys.exit(1)


if __name__ == "__main__":
    main()
