import json
import re

# 파일 열기
with open("finto/data/intermediate/structured_chunks.json", "r", encoding="utf-8") as f:
    data = json.load(f)

# ID 패턴 분석 (3단계 구조 확인 - 장-조-항)
three_level_ids = []
for item in data:
    item_id = item.get("id", "")
    # 장-조-항 형태의 ID (예: 1-3-①) 확인
    if re.match(r'^\d+-\d+-[①-⑮]$', item_id):
        three_level_ids.append(item)

print(f"장-조-항 3단계 ID를 가진 항목 수: {len(three_level_ids)}")

if three_level_ids:
    print("\n=== 3단계 ID 구조 예시 ===")
    for i, item in enumerate(three_level_ids[:3]):
        print(f"\n[예시 {i+1}]")
        print(f"ID: {item.get('id', '')}")
        print(f"메타데이터: {json.dumps(item.get('metadata', {}), ensure_ascii=False, indent=2)}")
        print(f"내용 일부: {item.get('cleaned_content', '')[:70]}...")

# 검색 기능 시뮬레이션
print("\n=== 검색 기능 시뮬레이션 ===")

# 장 번호로 검색
def search_by_chapter(chapter_no):
    return [item for item in data if item.get("metadata", {}).get("chapter_no") == chapter_no]

# 조 번호로 검색
def search_by_article(article_no):
    return [item for item in data if item.get("metadata", {}).get("article_no") == article_no]

# 장-조 조합으로 검색
def search_by_chapter_article(chapter_no, article_no):
    return [item for item in data if 
            item.get("metadata", {}).get("chapter_no") == chapter_no and 
            item.get("metadata", {}).get("article_no") == article_no]

# 장-조-항 조합으로 검색
def search_by_chapter_article_item(chapter_no, article_no, item_no):
    return [item for item in data if 
            item.get("metadata", {}).get("chapter_no") == chapter_no and 
            item.get("metadata", {}).get("article_no") == article_no and
            item.get("metadata", {}).get("item_no") == item_no]

# 제1장 검색
chapter1_items = search_by_chapter("제1장")
print(f"제1장 관련 항목 수: {len(chapter1_items)}")

# 제1조 검색
article1_items = search_by_article("제1조")
print(f"제1조 관련 항목 수: {len(article1_items)}")

# 제1장 제1조 검색
chapter1_article1_items = search_by_chapter_article("제1장", "제1조")
print(f"제1장 제1조 관련 항목 수: {len(chapter1_article1_items)}")

# 제1장 제3조 ① 항 검색
chapter1_article3_item1 = search_by_chapter_article_item("제1장", "제3조", "①")
print(f"제1장 제3조 ① 항 관련 항목 수: {len(chapter1_article3_item1)}")

if chapter1_article3_item1:
    print("\n제1장 제3조 ① 항 내용:")
    for item in chapter1_article3_item1:
        print(f"ID: {item.get('id', '')}")
        print(f"내용: {item.get('cleaned_content', '')[:100]}...")

# 제3장 검색 (외국환평형기금 장)
chapter3_items = search_by_chapter("제3장")
print(f"\n제3장 관련 항목 수: {len(chapter3_items)}")
if chapter3_items:
    print("제3장 조문 목록:")
    article_set = set()
    for item in chapter3_items:
        article_no = item.get("metadata", {}).get("article_no")
        if article_no:
            article_set.add(article_no)
    print(sorted(list(article_set))) 