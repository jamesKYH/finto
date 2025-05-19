from qdrant_client import QdrantClient

client = QdrantClient(host="localhost", port=6333)
collection = "my-collection"

client.delete_collection(collection)
print("🗑️ 기존 my-collection 삭제 완료")