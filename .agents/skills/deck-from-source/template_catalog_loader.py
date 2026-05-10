"""Print one compact template-catalog entry for Custom GPTs."""

from __future__ import annotations

import glob
import json
import sys
import tempfile
from pathlib import Path
from typing import Any

MAX_OUTPUT_CHARS = 400


def runtime_dir() -> Path:
    mnt = Path("/mnt/data")
    if mnt.exists():
        return mnt
    path = Path(tempfile.gettempdir()) / "deck_from_source_context"
    path.mkdir(parents=True, exist_ok=True)
    return path


def find_catalog_path() -> Path:
    base = runtime_dir()
    candidates = [
        base / "template_catalog.json",
        Path(__file__).resolve().with_name("template_catalog.json"),
    ]
    candidates.extend(Path(p) for p in glob.glob(str(base / "*template_catalog.json")))
    for path in candidates:
        if path.exists():
            return path
    raise SystemExit("ERROR template_catalog.json not found")


def load_catalog() -> dict[str, Any]:
    return json.loads(find_catalog_path().read_text(encoding="utf-8"))


def emit(text: str) -> None:
    if len(text) > MAX_OUTPUT_CHARS:
        raise SystemExit(f"ERROR output too long len={len(text)}")
    print(text)


def describe_kind(catalog: dict[str, Any], kind: str) -> str:
    data = catalog.get("slide_kinds", {}).get(kind)
    if not data:
        known = ",".join(sorted(catalog.get("slide_kinds", {})))
        return f"ERROR unknown kind. kinds={known}"
    slots = ",".join(data.get("slots", []))
    variant_items = [str(v.get("id", "")) for v in data.get("variants", [])]
    variants = ",".join(variant_items)
    return (
        f"[{kind}]\n{data.get('purpose', '')}\n"
        f"slots={slots}\nvariants({len(variant_items)})={variants}"
    )


def validate(catalog: dict[str, Any]) -> str:
    kinds = catalog.get("slide_kinds", {})
    errors: list[str] = []
    for kind, data in kinds.items():
        if not data.get("variants"):
            errors.append(f"no variants:{kind}")
        text = describe_kind(catalog, kind)
        if len(text) > MAX_OUTPUT_CHARS:
            errors.append(f"output>400:{kind}:{len(text)}")
        for variant in data.get("variants", []):
            if not variant.get("layout"):
                errors.append(f"missing layout:{kind}:{variant.get('id')}")
    if errors:
        return f"ERROR {len(errors)} issue(s): {'; '.join(errors[:3])}"
    return f"OK kinds={len(kinds)} max_output={MAX_OUTPUT_CHARS}"


def main(argv: list[str]) -> None:
    catalog = load_catalog()
    if len(argv) < 2:
        emit("USAGE list | get <slide_kind> | validate")
        return
    cmd = argv[1]
    if cmd == "list":
        kinds = ",".join(sorted(catalog.get("slide_kinds", {})))
        emit(f"KINDS {kinds}")
    elif cmd == "get":
        if len(argv) != 3:
            raise SystemExit("ERROR usage: get <slide_kind>")
        emit(describe_kind(catalog, argv[2]))
    elif cmd == "validate":
        emit(validate(catalog))
    else:
        raise SystemExit(f"ERROR unknown command {cmd}")


if __name__ == "__main__":
    main(sys.argv)
