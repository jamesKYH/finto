from qdrant_client import QdrantClient
import json

client = QdrantClient(host="localhost", port=6333)
collection = "my-collection"

scroll_offset = None
all_results = []
batch_size = 100
total_fetched = 0

print("📦 Qdrant에서 모든 문서 조회 시작...\n")

count_response = client.count(collection_name=collection, exact=True)
total_fetched = count_response.count

scroll_offset = None
fetched = 0

while fetched < total_fetched:
    result, scroll_offset = client.scroll(
        collection_name=collection,
        offset=scroll_offset,
        limit=batch_size,
        with_payload=True
    )
    for doc in result:
        print(f"📌 문서 ID: {doc.id}")
        payload = doc.payload or {}
        for key, value in payload.items():
            print(f"{key}: {value}")
        print("=" * 60)

    fetched += len(result)

print(f"\n✅ Qdrant에 저장된 총 문서 수: {total_fetched}개\n")