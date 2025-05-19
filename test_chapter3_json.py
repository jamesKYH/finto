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

# 결과를 JSON 형식으로 변환
points = search_result[0]
print(f"총 {len(points)} 개의 결과를 찾았습니다.\n")

# 컬렉션 정보 출력
print("\n=== 제3장 컬렉션 정보 ===\n")

# 출력할 데이터 준비
results = []
for point in points:
    # 메타데이터 추출
    payload = point.payload
    
    item = {
        "id": point.id,
        "chapter_no": payload.get('chapter_no', '정보 없음'),
        "chapter_title": payload.get('chapter_title', '정보 없음'),
        "article_no": payload.get('article_no', '정보 없음'),
        "article_title": payload.get('article_title', '정보 없음'),
        "content": payload.get('cleaned_content', payload.get('content', '내용 없음')),
        "law_name": payload.get('law_name', '정보 없음'),
        "effective_date": payload.get('effective_date', '정보 없음'),
        "ministry": payload.get('ministry', '정보 없음'),
        "item_no": payload.get('item_no', ''),
        "chunk_id": payload.get('id', str(point.id))
    }
    
    results.append(item)

# JSON 형식으로 출력
print(json.dumps(results, ensure_ascii=False, indent=2))

# 전체 구조를 파악하기 위한 요약 정보 출력
print("\n=== 제3장 구조 요약 ===\n")

# 조문 별로 그룹화
article_groups = {}
for item in results:
    article_no = item["article_no"]
    if article_no not in article_groups:
        article_groups[article_no] = []
    article_groups[article_no].append(item)

# 요약 정보 출력
for article_no, items in article_groups.items():
    if article_no == '정보 없음':
        continue
        
    article_title = items[0]["article_title"] if items else ""
    print(f"{article_no} ({article_title}) - {len(items)}개 항목")
    
    # 항목 정보 출력 (있는 경우)
    for item in items:
        content_preview = item["content"][:30].replace("\n", " ") + "..." if len(item["content"]) > 30 else item["content"]
        item_info = f"  - {item['item_no']}" if item['item_no'] else "  - "
        print(f"{item_info} {content_preview}") 