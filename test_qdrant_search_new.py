from qdrant_client import QdrantClient
from qdrant_client.models import Filter, FieldCondition, MatchValue, models
from sentence_transformers import SentenceTransformer
import json

# 연결 설정
QDRANT_URL = "http://localhost:6333"
COLLECTION_NAME = "my-collection"
EMBEDDING_MODEL = "all-MiniLM-L6-v2"

# 클라이언트 및 임베딩 모델 초기화
client = QdrantClient(url=QDRANT_URL)
model = SentenceTransformer(EMBEDDING_MODEL)

def search_with_filter(query, filter_dict=None, top_k=5):
    """
    필터를 적용하여 검색을 수행합니다.
    
    Args:
        query: 검색할 텍스트
        filter_dict: 필터 조건 딕셔너리
        top_k: 반환할 결과 개수
    """
    query_vector = model.encode(query).tolist()
    filter_obj = None
    
    if filter_dict:
        must_conditions = []
        for key, value in filter_dict.items():
            must_conditions.append(
                models.FieldCondition(
                    key=key,
                    match=models.MatchValue(value=value)
                )
            )
        filter_obj = models.Filter(must=must_conditions)
    
    # Qdrant API 호출
    search_results = client.search(
        collection_name=COLLECTION_NAME,
        query_vector=(EMBEDDING_MODEL, query_vector),
        limit=top_k,
        query_filter=filter_obj,
        with_payload=True
    )
    
    return search_results

def print_results(results, title):
    """검색 결과를 출력합니다."""
    print("=" * 80)
    print(f"🔍 {title} (총 {len(results)}개)")
    print("=" * 80)
    
    for i, result in enumerate(results):
        payload = result.payload
        
        # 메타데이터 접근 방식 수정
        chapter_no = payload.get("chapter_no", "장 정보 없음")
        chapter_title = payload.get("chapter_title", "")
        article_no = payload.get("article_no", "조 정보 없음")
        article_title = payload.get("article_title", "")
        item_no = payload.get("item_no", "")
        
        content = payload.get("cleaned_content", "내용 없음")
        
        print(f"{i+1}. {chapter_no} {chapter_title} > {article_no} {article_title} {item_no}")
        print(f"   점수: {result.score:.4f}")
        print(f"   ID: {payload.get('id', 'ID 없음')}")
        print(f"   내용: {content[:150]}...")
        print()

print("Qdrant 검색 테스트 시작...")

# 테스트 1: 제1장 검색 (메타데이터 필터 수정)
results_chapter1 = search_with_filter("외국환거래법 제1장", {"chapter_no": "제1장"}, top_k=10)
print_results(results_chapter1, "제1장 검색 결과")

# 테스트 2: 제1장 제1조 검색
results_chapter1_article1 = search_with_filter("외국환거래법 제1장 제1조", {
    "chapter_no": "제1장",
    "article_no": "제1조"
}, top_k=3)
print_results(results_chapter1_article1, "제1장 제1조 검색 결과")

# 테스트 3: '1조' 형식으로 검색 (제1조와 동일한 결과가 나와야 함)
results_article1 = search_with_filter("외국환거래법 1조", {"article_no": "제1조"}, top_k=3)
print_results(results_article1, "'1조' 형식으로 검색 (제1조)")

# 테스트 4: 제3조 검색
results_article3 = search_with_filter("외국환거래법 제3조 정의", {"article_no": "제3조"}, top_k=5)
print_results(results_article3, "제3조(정의) 검색 결과")

# 테스트 5: 메타데이터 필터 없이 검색
results_without_filter = search_with_filter("외국환거래법 목적", None, top_k=3)
print_results(results_without_filter, "필터 없이 '목적' 검색 결과") 