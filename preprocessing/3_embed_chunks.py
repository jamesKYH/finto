from sentence_transformers import SentenceTransformer
from pathlib import Path
import json
import numpy as np
import os

model = SentenceTransformer("all-MiniLM-L6-v2")

INPUT_FILE = Path("finto/data/intermediate/structured_chunks.json")
OUTPUT_FILE = Path("finto/data/intermediate/vectors.npy")

import sys
if not INPUT_FILE.exists():
    print(f"❌ 입력 파일이 존재하지 않습니다: {INPUT_FILE}")
    sys.exit(1)
with open(INPUT_FILE, 'r', encoding='utf-8') as f:
    structured_chunks = json.load(f)
print(f"💡 텍스트 청크 임베딩 중... (총 {len(structured_chunks)}개)")
texts = []
for i, chunk in enumerate(structured_chunks):
    # 'content' 키가 없을 경우 'text'를 대체로 사용하며, 줄바꿈 포함한 원문 그대로 사용
    content = chunk.get("content") or chunk.get("text", "")
    if not content.strip():
        print(f"⚠️ [청크 {i}] 비어있는 content. 건너뜁니다.")
        continue
    if not content.startswith("passage:"):
        content = "passage: " + content
    texts.append(content)

vectors = model.encode(texts, show_progress_bar=True)

np.save(OUTPUT_FILE, vectors)
print(f"✅ 임베딩 완료: {vectors.shape} → {OUTPUT_FILE}")
