import json

# 파일 열기
with open("finto/data/intermediate/structured_chunks.json", "r", encoding="utf-8") as f:
    data = json.load(f)

# 항목이 있는 데이터 찾기
items_with_item_no = [item for item in data if "item_no" in item.get("metadata", {})]
print(f"항목(item_no)이 있는 데이터 수: {len(items_with_item_no)}")

# 다양한 항목 값 확인
item_nos = set([item["metadata"]["item_no"] for item in items_with_item_no])
print(f"\n고유한 항목 값의 수: {len(item_nos)}")
print(f"항목 값 예시: {sorted(list(item_nos))[:10]}")

# 제3조에 속한 항목 검사 (정의 조항은 항목이 많을 것)
article3_items = [item for item in data if item.get("metadata", {}).get("article_no") == "제3조"]
print(f"\n제3조 관련 데이터 수: {len(article3_items)}")

# 제3조의 항목만 상세히 살펴보기
article3_with_items = [item for item in article3_items if "item_no" in item.get("metadata", {})]
print(f"제3조 중 항목(item_no)이 있는 데이터 수: {len(article3_with_items)}")

if article3_with_items:
    print("\n=== 제3조의 항목 구조 ===")
    for i, item in enumerate(sorted(article3_with_items, key=lambda x: x["metadata"]["item_no"])):
        if i < 5:  # 처음 5개만 출력
            print(f"\n[항목 {i+1}]")
            print(f"ID: {item.get('id', '')}")
            print(f"메타데이터: {json.dumps(item.get('metadata', {}), ensure_ascii=False, indent=2)}")
            print(f"내용 일부: {item.get('cleaned_content', '')[:70]}...")

# ID 체계 분석 (장-조-항 형식인지 확인)
print("\n=== ID 체계 분석 ===")
id_structure = {}

for item in data:
    item_id = item.get("id", "")
    if "-" in item_id:
        parts = item_id.split("-")
        if len(parts) == 2:
            chapter_part, article_part = parts
            
            # 메타데이터와 ID 값의 상관관계 확인
            metadata = item.get("metadata", {})
            chapter_no = metadata.get("chapter_no", "").replace("제", "").replace("장", "")
            article_no = metadata.get("article_no", "").replace("제", "").replace("조", "")
            
            # 장 번호와 ID 첫 부분 일치 여부
            chapter_match = chapter_part == chapter_no if chapter_no else False
            # 조 번호와 ID 두번째 부분 일치 여부
            article_match = article_part == article_no if article_no else False
            
            pattern = f"chapter_match: {'O' if chapter_match else 'X'}, article_match: {'O' if article_match else 'X'}"
            if pattern not in id_structure:
                id_structure[pattern] = []
            
            if len(id_structure[pattern]) < 3:  # 각 패턴별 3개만 저장
                id_structure[pattern].append({
                    "id": item_id,
                    "chapter_no": metadata.get("chapter_no", ""),
                    "article_no": metadata.get("article_no", ""),
                    "item_no": metadata.get("item_no", "")
                })

# ID 구조와 메타데이터 일치 여부 분석 결과 출력
for pattern, examples in id_structure.items():
    print(f"\n[패턴: {pattern}] - {len(examples)} 예시")
    for ex in examples:
        print(f"  ID: {ex['id']}, 장: {ex['chapter_no']}, 조: {ex['article_no']}, 항: {ex['item_no'] if 'item_no' in ex else 'N/A'}") 