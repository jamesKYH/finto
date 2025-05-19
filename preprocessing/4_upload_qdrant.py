from qdrant_client import QdrantClient
from qdrant_client.models import PointStruct, VectorParams, Distance
from pathlib import Path
import numpy as np
import json

COLLECTION_NAME = "my-collection"
client = QdrantClient(host="localhost", port=6333)

chunks_file = Path("finto/data/intermediate/structured_chunks.json")
vectors_file = Path("finto/data/intermediate/vectors.npy")

with open(chunks_file, 'r', encoding='utf-8') as f:
    structured_chunks = json.load(f)

vectors = np.load(vectors_file)

# 컬렉션 없으면 생성
if client.collection_exists(COLLECTION_NAME):
    client.delete_collection(COLLECTION_NAME)
client.create_collection(
    collection_name=COLLECTION_NAME,
    vectors_config={
        "all-MiniLM-L6-v2": VectorParams(
            size=vectors.shape[1],
            distance=Distance.COSINE
        )
    }
)

# 유효한 청크만 필터링
valid_chunks = [
    (i, chunk) for i, chunk in enumerate(structured_chunks)
    if (chunk.get("content") or chunk.get("text"))
]

if len(valid_chunks) == 0:
    raise ValueError("❌ 유효한 청크가 없습니다. 업로드 중단.")

if vectors.shape[0] != len(valid_chunks):
    raise ValueError(f"❌ 벡터 수({vectors.shape[0]})와 유효 청크 수({len(valid_chunks)})가 일치하지 않습니다.")

# 벡터 업로드
points = [
    PointStruct(
        id=i,
        vector={"all-MiniLM-L6-v2": vectors[idx]},
        payload={
            "content": chunk.get("content") or chunk.get("text"),
            "cleaned_content": chunk.get("cleaned_content", ""),
            "id": chunk.get("id", str(i)),
            **chunk.get("metadata", {})
        }
    )
    for i, (idx, chunk) in enumerate(valid_chunks)
]

client.upsert(
    collection_name=COLLECTION_NAME,
    points=points,
    wait=True
)
print(f"✅ Qdrant 적재 완료: {len(points)}개")
