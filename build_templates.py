"""
テンプレートビルダー
templates.json + design.json + template_engine_*.html → template_*.html (生成物)

使い方:
  python build_templates.py
"""

import json
from pathlib import Path

BASE_DIR = Path(__file__).parent
OUT_DIR = BASE_DIR / "templates"
TEMPLATES_FILE = BASE_DIR / "templates.json"
DESIGN_FILE = BASE_DIR / "design.json"


def main():
    if not TEMPLATES_FILE.exists():
        print(f"エラー: {TEMPLATES_FILE.name} が見つかりません")
        return
    if not DESIGN_FILE.exists():
        print(f"エラー: {DESIGN_FILE.name} が見つかりません")
        return

    templates = json.loads(TEMPLATES_FILE.read_text(encoding="utf-8"))
    design = json.loads(DESIGN_FILE.read_text(encoding="utf-8"))

    engines = {}  # キャッシュ

    built = 0
    for name, tmpl in templates.items():
        engine_type = tmpl.get("engine")
        if not engine_type:
            print(f"  スキップ: {name} (engine が未指定)")
            continue

        if engine_type not in engines:
            engine_path = BASE_DIR / f"template_engine_{engine_type}.html"
            if not engine_path.exists():
                print(f"  スキップ: {name} (エンジン '{engine_type}' が見つかりません)")
                continue
            engines[engine_type] = engine_path.read_text(encoding="utf-8")

        slides_js = "const SLIDES = " + json.dumps(tmpl["SLIDES"], ensure_ascii=False, indent=2) + "; // END_SLIDES"
        design_js = "const DESIGN = " + json.dumps(design, ensure_ascii=False, indent=2) + "; // END_DESIGN"

        result = engines[engine_type].replace("// __SLIDES__", slides_js)
        result = result.replace("// __DESIGN__", design_js)

        OUT_DIR.mkdir(exist_ok=True)
        out_path = OUT_DIR / f"template_{name}.html"
        out_path.write_text(result, encoding="utf-8")
        print(f"  {name} → {out_path.name}")
        built += 1

    print(f"\n完了: {built} 件生成")


if __name__ == "__main__":
    main()
