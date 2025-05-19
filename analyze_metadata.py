import json
from collections import Counter

# 파일 열기
with open("finto/data/intermediate/structured_chunks.json", "r", encoding="utf-8") as f:
    data = json.load(f)

# 메타데이터 키 분석
metadata_keys = Counter()
for item in data:
    for key in item.get("metadata", {}).keys():
        metadata_keys[key] += 1

print("=== 메타데이터 키 사용 빈도 ===")
for key, count in metadata_keys.most_common():
    print(f"{key}: {count}/{len(data)} ({count/len(data)*100:.1f}%)")

# ID 체계 분석
print("\n=== ID 체계 분석 ===")
id_patterns = Counter()
for item in data:
    item_id = item.get("id", "")
    if item_id:
        id_patterns[item_id.split("-")[0] if "-" in item_id else item_id] += 1

print("\nID 패턴 빈도:")
for pattern, count in id_patterns.most_common():
    print(f"{pattern}: {count}")

# 다양한 메타데이터 조합 확인
print("\n=== 메타데이터 조합 패턴 ===")
metadata_patterns = Counter()
for item in data:
    metadata = item.get("metadata", {})
    pattern = (
        f"chapter_no: {'O' if 'chapter_no' in metadata else 'X'}, "
        f"article_no: {'O' if 'article_no' in metadata else 'X'}, "
        f"paragraph_no: {'O' if 'paragraph_no' in metadata else 'X'}"
    )
    metadata_patterns[pattern] += 1

for pattern, count in metadata_patterns.most_common():
    print(f"{pattern}: {count}")

# 구체적인 예시 출력
print("\n=== 메타데이터 예시 ===")
examples = {}

# 다양한 패턴의 예시 찾기
for item in data:
    metadata = item.get("metadata", {})
    pattern = (
        f"chapter_no: {'O' if 'chapter_no' in metadata else 'X'}, "
        f"article_no: {'O' if 'article_no' in metadata else 'X'}, "
        f"paragraph_no: {'O' if 'paragraph_no' in metadata else 'X'}"
    )
    
    if pattern not in examples:
        examples[pattern] = item

# 예시 출력
for pattern, item in examples.items():
    print(f"\n[패턴: {pattern}]")
    print(f"ID: {item.get('id', '')}")
    print(f"메타데이터: {json.dumps(item.get('metadata', {}), ensure_ascii=False, indent=2)}")
    print(f"내용 일부: {item.get('cleaned_content', '')[:50]}...") 