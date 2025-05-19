from qdrant_client import QdrantClient
import json
from tabulate import tabulate
import pandas as pd
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
    limit=100  # 결과 개수 제한
)

# 결과 추출
points = search_result[0]
print(f"{Fore.GREEN}\n✓ 총 {len(points)} 개의 결과를 찾았습니다.{Style.RESET_ALL}")

# 기본 대표 정보 출력
if points:
    sample = points[0].payload
    print(f"\n{Fore.YELLOW}== 법령 기본 정보 =={Style.RESET_ALL}")
    print(f"법령명: {sample.get('law_name', '정보 없음')}")
    print(f"시행일: {sample.get('effective_date', '정보 없음')}")
    print(f"소관부처: {sample.get('ministry', '정보 없음')}")
    print(f"장 정보: {sample.get('chapter_no', '정보 없음')} ({sample.get('chapter_title', '정보 없음')})")

# 출력할 데이터 준비
results = []
for point in points:
    payload = point.payload
    item = {
        "id": point.id,
        "chunk_id": payload.get('id', str(point.id)),
        "article_no": payload.get('article_no', '정보 없음'),
        "article_title": payload.get('article_title', '정보 없음'),
        "item_no": payload.get('item_no', ''),
        "content": payload.get('cleaned_content', payload.get('content', '내용 없음')),
        "amendment_date": payload.get('amendment_date', ''),
        "full_amendment_date": payload.get('full_amendment_date', '')
    }
    results.append(item)

# 조문 별로 그룹화
article_groups = {}
for item in results:
    article_no = item["article_no"]
    if article_no not in article_groups:
        article_groups[article_no] = []
    article_groups[article_no].append(item)

# 조문 별로 상세 내용 출력
for article_no, items in sorted(article_groups.items(), key=lambda x: x[0]):
    if article_no == '정보 없음':
        continue
        
    article_title = items[0]["article_title"] if items else ""
    print(f"\n{Fore.CYAN}=================================================={Style.RESET_ALL}")
    print(f"{Fore.CYAN}● {article_no} ({article_title}){Style.RESET_ALL}")
    print(f"{Fore.CYAN}=================================================={Style.RESET_ALL}")
    
    # 항목 정보 출력
    for item in sorted(items, key=lambda x: x['item_no'] if x['item_no'] else '0'):
        item_prefix = f"{Fore.YELLOW}{item['item_no']}{Style.RESET_ALL}" if item['item_no'] else ""
        print(f"\n{item_prefix} {item['content']}")
        
        # 개정 정보 출력
        amendment_info = []
        if item.get('amendment_date'):
            amendment_info.append(f"개정일: {item['amendment_date']}")
        if item.get('full_amendment_date'):
            amendment_info.append(f"전문개정일: {item['full_amendment_date']}")
            
        if amendment_info:
            print(f"\n{Fore.RED}[개정정보] {', '.join(amendment_info)}{Style.RESET_ALL}")

# 전체 구조 요약
print(f"\n{Fore.GREEN}=================================================={Style.RESET_ALL}")
print(f"{Fore.GREEN}● 제3장 구조 요약{Style.RESET_ALL}")
print(f"{Fore.GREEN}=================================================={Style.RESET_ALL}\n")

# 요약 테이블 데이터 준비
summary_data = []
for article_no, items in sorted(article_groups.items(), key=lambda x: x[0]):
    if article_no == '정보 없음':
        continue
        
    article_title = items[0]["article_title"] if items else ""
    item_count = len(items)
    item_nos = ", ".join([i["item_no"] for i in items if i["item_no"]])
    summary_data.append([article_no, article_title, item_count, item_nos])

# 테이블 출력
if summary_data:
    df = pd.DataFrame(summary_data, columns=["조문번호", "제목", "항목 수", "항목 목록"])
    print(tabulate(df, headers='keys', tablefmt='fancy_grid', showindex=False))
else:
    print("요약할 데이터가 없습니다.") 