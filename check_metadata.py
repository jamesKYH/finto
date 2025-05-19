import json

# 파일 열기
with open("finto/data/intermediate/structured_chunks.json", "r", encoding="utf-8") as f:
    data = json.load(f)

# 전체 데이터 개수 출력
print(f"총 데이터 개수: {len(data)}")

# 첫 번째 항목의 메타데이터 출력
print("\n첫 번째 항목 메타데이터:")
print(json.dumps(data[0].get("metadata", {}), ensure_ascii=False, indent=2))

# 제1조 검색
article1_items = [item for item in data if item.get("metadata", {}).get("article_no") == "제1조"]
if article1_items:
    print("\n제1조 항목 메타데이터:")
    print(json.dumps(article1_items[0].get("metadata", {}), ensure_ascii=False, indent=2))
else:
    print("\n제1조 항목을 찾을 수 없습니다.")

# 모든 장과 조문의 유니크한 값 확인
chapters = set()
articles = set()

for item in data:
    metadata = item.get("metadata", {})
    if "chapter_no" in metadata:
        chapters.add(metadata["chapter_no"])
    if "article_no" in metadata:
        articles.add(metadata["article_no"])

print("\n유니크한 장 개수:", len(chapters))
print("유니크한 조문 개수:", len(articles))
print("\n장 목록:", sorted(list(chapters)))
print("\n조문 목록 (일부):", sorted(list(articles))[:10]) 