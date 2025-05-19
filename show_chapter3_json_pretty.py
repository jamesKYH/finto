from qdrant_client import QdrantClient
import json
from colorama import init, Fore, Style

# 색상 초기화
init()

# Qdrant 클라이언트 초기화
client = QdrantClient(host="localhost", port=6333)

# 컬렉션 이름
COLLECTION_NAME = "my-collection"

# 제3장 내용만 필터링하여 검색
print(f"{Fore.BLUE}\n[*] 제3장 데이터 검색 중...{Style.RESET_ALL}")
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
    limit=100,  # 결과 개수 제한
    with_payload=True,  # 모든 메타데이터 가져오기
    with_vectors=False  # 벡터는 필요 없음
)

# 결과 추출
points = search_result[0]
print(f"{Fore.GREEN}\n✓ 총 {len(points)} 개의 결과를 찾았습니다.{Style.RESET_ALL}")

if not points:
    print("검색 결과가 없습니다.")
    exit()

# 데이터 구조화
result_data = {
    "법령정보": {},
    "장정보": {},
    "조문목록": []
}

# 기본 법령 정보 추출 (첫 번째 항목에서 추출)
first_item = points[0].payload
result_data["법령정보"] = {
    "법령명": first_item.get("law_name", ""),
    "시행일": first_item.get("effective_date", ""),
    "소관부처": first_item.get("ministry", ""),
    "공포정보": first_item.get("publication_info", "")
}

# 장 정보 추출
result_data["장정보"] = {
    "장번호": first_item.get("chapter_no", ""),
    "장제목": first_item.get("chapter_title", "")
}

# 조문별로 그룹화
article_groups = {}
for point in points:
    payload = point.payload
    article_no = payload.get("article_no", "정보 없음")
    
    if article_no not in article_groups:
        article_groups[article_no] = {
            "조번호": article_no,
            "조제목": payload.get("article_title", ""),
            "항목목록": []
        }
    
    # 항목 정보 추가
    item_info = {
        "항번호": payload.get("item_no", ""),
        "내용": payload.get("cleaned_content", payload.get("content", "")),
        "ID": payload.get("id", ""),
        "개정정보": {}
    }
    
    # 개정 정보 추가
    if payload.get("amendment_date"):
        item_info["개정정보"]["개정일"] = payload.get("amendment_date")
    if payload.get("full_amendment_date"):
        item_info["개정정보"]["전문개정일"] = payload.get("full_amendment_date")
    
    article_groups[article_no]["항목목록"].append(item_info)

# 조문 정보를 목록에 추가 (정렬 후)
for article_no in sorted(article_groups.keys()):
    if article_no != "정보 없음":
        # 항목 번호로 항목 목록 정렬
        article_groups[article_no]["항목목록"].sort(
            key=lambda x: x["항번호"] if x["항번호"] else "0"
        )
        result_data["조문목록"].append(article_groups[article_no])

# 결과 출력
print(f"\n{Fore.YELLOW}=== 제3장 JSON 데이터 ==={Style.RESET_ALL}\n")
print(json.dumps(result_data, ensure_ascii=False, indent=2))

# 파일로도 저장
output_file = "chapter3_data.json"
with open(output_file, "w", encoding="utf-8") as f:
    json.dump(result_data, f, ensure_ascii=False, indent=2)

print(f"\n{Fore.GREEN}✓ JSON 데이터를 {output_file} 파일로 저장했습니다.{Style.RESET_ALL}") 