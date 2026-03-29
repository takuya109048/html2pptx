"""
PPTX から template_flow_4step のスライドをスクリーンショット化
"""
import os
import subprocess
from pathlib import Path

HERE = os.path.dirname(os.path.abspath(__file__))
PPTX_FILE = os.path.join(HERE, "all_templates.pptx")
OUTPUT_DIR = os.path.join(HERE, "screenshots")

# 出力ディレクトリを作成
os.makedirs(OUTPUT_DIR, exist_ok=True)

# LibreOffice を使用して PPTX を PDF に変換
print("[*] Converting PPTX to PDF...")
try:
    subprocess.run([
        "libreoffice", "--headless", "--convert-to", "pdf",
        "--outdir", OUTPUT_DIR, PPTX_FILE
    ], check=True, capture_output=True)
    print("[OK] PDF conversion complete")
except FileNotFoundError:
    print("[!] LibreOffice not found, trying alternative...")
    # Windows の LibreOffice パスを試す
    office_paths = [
        "C:\Program Files\LibreOffice\program\soffice.exe",
        "C:\Program Files (x86)\LibreOffice\program\soffice.exe",
    ]
    for path in office_paths:
        if os.path.exists(path):
            subprocess.run([
                path, "--headless", "--convert-to", "pdf",
                "--outdir", OUTPUT_DIR, PPTX_FILE
            ], check=True)
            print(f"[OK] PDF conversion complete via {path}")
            break

# PDF から PNG に変換
pdf_file = os.path.join(OUTPUT_DIR, "all_templates.pdf")
if os.path.exists(pdf_file):
    print("[*] Converting PDF to PNG...")
    try:
        from pdf2image import convert_from_path
        images = convert_from_path(pdf_file, dpi=150)
        
        # 4番目のスライド（template_flow_4step）をスクリーンショット化
        if len(images) >= 4:
            output_file = os.path.join(OUTPUT_DIR, "template_flow_4step.png")
            images[3].save(output_file, "PNG")
            print(f"[OK] Screenshot saved: {output_file}")
            print(f"[Size] {os.path.getsize(output_file) / 1024:.1f} KB")
        else:
            print(f"[!] Only {len(images)} slides found")
    except Exception as e:
        print(f"[Error] {e}")
else:
    print(f"[!] PDF file not found: {pdf_file}")
