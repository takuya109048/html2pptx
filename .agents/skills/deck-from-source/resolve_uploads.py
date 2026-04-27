"""resolve_uploads.py

カスタムGPTsのcode interpreter環境で、`/mnt/data` 直下にある
`assistant-{ユニークID}-{元のファイル名}` 形式のアップロードファイルを、
プレフィックスを除いた元のファイル名でコピー配置するユーティリティ。

チャット開始直後に code interpreter で1回だけ実行することを想定。
実行後は、以降のスクリプト・ユーザー操作は `/mnt/data/{元のファイル名}`
でアップロードファイルに安定してアクセスできる。

典型的な使い方（code interpreter 側）::

    import glob
    matches = glob.glob("/mnt/data/*resolve_uploads.py")
    if matches:
        exec(open(matches[0]).read())

glob を使うのは、本スクリプト自体もカスタムGPTs環境では
`assistant-{id}-resolve_uploads.py` にリネームされる可能性があるため。
"""

from __future__ import annotations

import re
import shutil
from pathlib import Path

DATA_DIR = Path("/mnt/data")

# assistant- の直後のユニークIDは英数字のみを想定。
# 元のファイル名にハイフンが含まれても正しく残すため、IDの範囲を明示する。
PREFIX_RE = re.compile(r"^assistant-[A-Za-z0-9]+-(.+)$")


def resolve_uploads(data_dir: Path = DATA_DIR) -> list[tuple[str, str]]:
    """プレフィックス付きファイルを検出し、プレフィックスなしの名前でコピー配置する。

    既に同名ファイルが存在する場合は上書きしない（二重実行時の安全策）。

    Returns:
        実際にコピーした (元ファイル名, コピー先ファイル名) のリスト。
    """
    copied: list[tuple[str, str]] = []

    if not data_dir.exists():
        print(f"[resolve_uploads] {data_dir} が存在しません")
        return copied

    for src in sorted(data_dir.iterdir()):
        if not src.is_file():
            continue
        m = PREFIX_RE.match(src.name)
        if not m:
            continue
        stripped_name = m.group(1)
        dst = data_dir / stripped_name
        if dst.exists():
            continue
        shutil.copy2(src, dst)
        copied.append((src.name, dst.name))

    return copied


def main() -> None:
    results = resolve_uploads()
    if not results:
        print("[resolve_uploads] プレフィックス付きファイルは見つかりませんでした")
        return
    print("[resolve_uploads] 以下のファイルをコピー配置しました:")
    for src_name, dst_name in results:
        print(f"  - {src_name} -> {dst_name}")


if __name__ == "__main__":
    main()
