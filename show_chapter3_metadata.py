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
print(f"{Fore.BLUE}\n[*] 제3장 메타데이터 검색 중...{Style.RESET_ALL}")
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

# 메타데이터 상세 분석
print(f"\n{Fore.YELLOW}=== 제3장 메타데이터 상세 정보 ==={Style.RESET_ALL}")

# 모든 메타데이터 키 추출
all_meta_keys = set()
for point in points:
    all_meta_keys.update(point.payload.keys())

# 메타데이터 키 정렬 (중요한 키 먼저 출력)
priority_keys = ['chapter_no', 'chapter_title', 'article_no', 'article_title', 'item_no', 'law_name', 'effective_date', 'ministry']
sorted_keys = priority_keys + sorted([k for k in all_meta_keys if k not in priority_keys])

# 전체 행렬 데이터 준비 (모든 메타데이터를 포함한 표 데이터)
table_data = []
for i, point in enumerate(points):
    row = [i+1]  # 행 번호
    payload = point.payload
    
    # 각 메타데이터 키에 대한 값 추가
    for key in sorted_keys:
        if key in payload:
            # 긴 콘텐츠는 줄임
            if key in ['content', 'cleaned_content'] and payload[key] and len(payload[key]) > 30:
                row.append(f"{payload[key][:30]}...")
            else:
                row.append(payload[key])
        else:
            row.append('')  # 해당 키가 없으면 빈 값
    
    table_data.append(row)

# 표 헤더 준비
headers = ['No.'] + sorted_keys

# 표 출력
print(tabulate(table_data, headers=headers, tablefmt='grid'))

# 추가 분석: 항목 분포 확인
print(f"\n{Fore.CYAN}=== 조항별 항목 분포 ==={Style.RESET_ALL}")

# 조문별 항목 수 계산
article_stats = {}
for point in points:
    article_no = point.payload.get('article_no', '정보 없음')
    
    if article_no not in article_stats:
        article_stats[article_no] = {
            'count': 0,
            'items': [],
            'title': point.payload.get('article_title', '')
        }
    
    article_stats[article_no]['count'] += 1
    
    # 항목 번호가 있으면 추가
    item_no = point.payload.get('item_no', '')
    if item_no:
        article_stats[article_no]['items'].append(item_no)

# 조문별 통계 출력
stats_table = []
for article_no, data in sorted(article_stats.items()):
    if article_no == '정보 없음':
        continue
        
    stats_table.append([article_no, data['title'], data['count'], ', '.join(data['items']) if data['items'] else ''])

print(tabulate(stats_table, headers=['조문번호', '제목', '항목 수', '항목 목록'], tablefmt='fancy_grid'))

# 추가 분석: 메타데이터 필드별 통계
print(f"\n{Fore.MAGENTA}=== 메타데이터 필드 분석 ==={Style.RESET_ALL}")

meta_stats = {}
for key in sorted_keys:
    # 콘텐츠 필드는 제외
    if key in ['content', 'cleaned_content']:
        continue
        
    values = set()
    count = 0
    
    for point in points:
        if key in point.payload and point.payload[key]:
            count += 1
            values.add(str(point.payload[key]))
    
    meta_stats[key] = {
        'count': count,
        'coverage': f"{count/len(points)*100:.1f}%",
        'unique_values': len(values),
        'examples': ', '.join(list(values)[:3]) + ('...' if len(values) > 3 else '')
    }

# 메타데이터 통계 출력
meta_table = []
for key, stats in meta_stats.items():
    meta_table.append([key, stats['count'], stats['coverage'], stats['unique_values'], stats['examples']])

print(tabulate(meta_table, 
               headers=['메타데이터 필드', '존재 수', '커버리지', '고유값 수', '예시 값'], 
               tablefmt='fancy_grid'))

# ID 구조 분석
print(f"\n{Fore.BLUE}=== ID 구조 분석 ==={Style.RESET_ALL}")

id_structures = []
for point in points:
    chunk_id = point.payload.get('id', '')
    if chunk_id:
        id_parts = chunk_id.split('-')
        structure = f"장-조-항: {'-'.join(id_parts)}"
        id_structures.append([chunk_id, structure, point.payload.get('chapter_no', ''), 
                              point.payload.get('article_no', ''), 
                              point.payload.get('item_no', '')])

if id_structures:
    print(tabulate(id_structures[:10], 
                  headers=['청크 ID', 'ID 구조', '장 정보', '조 정보', '항 정보'], 
                  tablefmt='fancy_grid'))
    if len(id_structures) > 10:
        print(f"\n... 외 {len(id_structures)-10}개 추가 ID")
else:
    print("ID 구조를 분석할 수 없습니다.")

print(f"\n{Fore.GREEN}=== 분석 완료 ==={Style.RESET_ALL}") 