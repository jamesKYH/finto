from qdrant_client import QdrantClient
import json

# Qdrant 클라이언트 초기화
client = QdrantClient(host="localhost", port=6333)

# 컬렉션 이름
COLLECTION_NAME = "my-collection"

# 제3장 내용만 필터링하여 검색
search_result = client.scroll(
    collection_name=COLLECTION_NAME,
    scroll_filter={
        "must": [
            {
                "key": "chapter_no",
                "match": {
                    "value": "제3장"
                }
            }
        ]
    },
    limit=100  # 결과 개수 제한
)

# 결과 출력
points = search_result[0]
print(f"총 {len(points)} 개의 결과를 찾았습니다.\n")

for i, point in enumerate(points):
    print(f"=== 결과 {i+1} ===")
    print(f"ID: {point.id}")
    
    # 메타데이터 출력
    chapter_no = point.payload.get('chapter_no', '정보 없음')
    chapter_title = point.payload.get('chapter_title', '정보 없음')
    article_no = point.payload.get('article_no', '정보 없음')
    article_title = point.payload.get('article_title', '정보 없음')
    
    print(f"장: {chapter_no} ({chapter_title})")
    print(f"조: {article_no} ({article_title})")
    
    # 내용 출력
    content = point.payload.get('cleaned_content', point.payload.get('content', '내용 없음'))
    print(f"내용: {content[:200]}{'...' if len(content) > 200 else ''}\n") 