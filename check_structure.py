import json

# 파일 열기
with open("finto/data/intermediate/structured_chunks.json", "r", encoding="utf-8") as f:
    data = json.load(f)

# 장-조-항 구조 분석
structure = {}

for item in data:
    metadata = item.get("metadata", {})
    chapter_no = metadata.get("chapter_no")
    article_no = metadata.get("article_no")
    paragraph_no = metadata.get("paragraph_no")
    
    # 장 정보가 있는 경우만
    if chapter_no:
        if chapter_no not in structure:
            structure[chapter_no] = {
                "title": metadata.get("chapter_title", ""),
                "articles": {}
            }
        
        # 조문 정보가 있는 경우
        if article_no:
            if article_no not in structure[chapter_no]["articles"]:
                structure[chapter_no]["articles"][article_no] = {
                    "title": metadata.get("article_title", ""),
                    "paragraphs": []
                }
            
            # 항 정보가 있는 경우
            if paragraph_no:
                structure[chapter_no]["articles"][article_no]["paragraphs"].append(paragraph_no)

# 제1장 정보 출력
print("=== 제1장 구조 ===")
if "제1장" in structure:
    chapter1 = structure["제1장"]
    print(f"장 제목: {chapter1['title']}")
    
    print("\n조문 목록:")
    for article_no, article_info in chapter1["articles"].items():
        print(f"- {article_no} ({article_info['title']})")
        if article_info["paragraphs"]:
            print(f"  항 목록: {sorted(article_info['paragraphs'])}")

# 조회 검색 예시 (제1장 제1조 찾기)
print("\n=== 제1장 제1조 검색 결과 ===")
items = [item for item in data if item.get("metadata", {}).get("chapter_no") == "제1장" and 
         item.get("metadata", {}).get("article_no") == "제1조"]

for i, item in enumerate(items):
    print(f"\n[항목 {i+1}]")
    print(f"ID: {item.get('id', '')}")
    print(f"메타데이터: {json.dumps(item.get('metadata', {}), ensure_ascii=False)}")
    print(f"내용: {item.get('cleaned_content', '')[:100]}...") 