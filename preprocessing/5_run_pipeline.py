# 📁 finto/preprocessing/run_pipeline.py
import os
from pathlib import Path

root = Path(__file__).parent

scripts = [
    "1_load_text.py",
    "2_split_chunks.py",
    "3_embed_chunks.py",
    "4_upload_qdrant.py"
]

for script in scripts:
    print(f"\n▶ 실행: {script}")
    os.system(f"python {root / script}")

print("\n✅ 전체 파이프라인 완료")