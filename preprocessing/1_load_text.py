# 📁 finto/preprocessing/1_load_text.py
from pathlib import Path

RAW_DIR = Path("/Users/james_kyh/Downloads/finto/data/raw")
TEXT_FILE = RAW_DIR / "sample.txt"
OUTPUT_FILE = Path("finto/data/intermediate/raw_text.txt")

RAW_DIR.mkdir(parents=True, exist_ok=True)
OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)

with open(TEXT_FILE, 'r', encoding='utf-8') as f:
    raw_text = f.read()

with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
    f.write(raw_text)

print(f"✅ 텍스트 로드 완료: {OUTPUT_FILE}")