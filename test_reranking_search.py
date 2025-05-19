from qdrant_client import QdrantClient
from qdrant_client.models import Filter, FieldCondition, MatchValue, models
from sentence_transformers import SentenceTransformer
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

# 연결 설정
QDRANT_URL = "http://localhost:6333"
COLLECTION_NAME = "my-collection"
EMBEDDING_MODEL = "all-MiniLM-L6-v2"

# 클라이언트 및 임베딩 모델 초기화
client = QdrantClient(url=QDRANT_URL)
model = SentenceTransformer(EMBEDDING_MODEL)

def search_with_filter(query, filter_dict=None, top_k=20):
    """
    필터를 적용하여 검색을 수행합니다.
    
    Args:
        query: 검색할 텍스트
        filter_dict: 필터 조건 딕셔너리
        top_k: 반환할 결과 개수 (기본값 20으로 증가)
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

def rerank_with_tfidf(query, results, top_n=5):
    """
    TF-IDF 기반으로 결과를 재랭킹합니다.
    
    Args:
        query: 원본 검색 쿼리
        results: Qdrant 검색 결과
        top_n: 최종적으로 반환할 결과 수
    """
    # 결과가 충분하지 않으면 그대로 반환
    if len(results) <= top_n:
        return results
    
    # 결과에서 텍스트 추출
    texts = [result.payload.get("cleaned_content", "") for result in results]
    
    # 쿼리와 텍스트를 함께 TF-IDF 변환
    tfidf = TfidfVectorizer().fit_transform(texts + [query])
    
    # 마지막 벡터(쿼리)와 다른 모든 텍스트 간의 유사도 계산
    similarities = cosine_similarity(tfidf[-1:], tfidf[:-1])[0]
    
    # 유사도에 따라 정렬
    reranked_indices = similarities.argsort()[::-1][:top_n]
    
    return [results[i] for i in reranked_indices]

def rerank_with_hybrid(query, results, top_n=5, alpha=0.7):
    """
    벡터 검색 점수와 TF-IDF 점수를 조합하여 하이브리드 재랭킹을 수행합니다.
    
    Args:
        query: 원본 검색 쿼리
        results: Qdrant 검색 결과
        top_n: 최종적으로 반환할 결과 수
        alpha: 벡터 검색 점수의 가중치 (0~1), 1-alpha는 TF-IDF 점수의 가중치
    """
    # 결과가 충분하지 않으면 그대로 반환
    if len(results) <= top_n:
        return results
    
    # 벡터 검색 점수 정규화
    vector_scores = np.array([result.score for result in results])
    vector_scores = (vector_scores - vector_scores.min()) / (vector_scores.max() - vector_scores.min() + 1e-8)
    
    # 텍스트 기반 유사도 계산
    texts = [result.payload.get("cleaned_content", "") for result in results]
    tfidf = TfidfVectorizer().fit_transform(texts + [query])
    tfidf_scores = cosine_similarity(tfidf[-1:], tfidf[:-1])[0]
    tfidf_scores = (tfidf_scores - tfidf_scores.min()) / (tfidf_scores.max() - tfidf_scores.min() + 1e-8)
    
    # 점수 조합
    combined_scores = alpha * vector_scores + (1 - alpha) * tfidf_scores
    
    # 조합된 점수로 정렬
    reranked_indices = combined_scores.argsort()[::-1][:top_n]
    
    return [results[i] for i in reranked_indices]

def search_with_reranking(query, filter_dict=None, final_top_k=5, reranking_method="hybrid"):
    """
    두 단계 검색: 우선 많은 결과를 가져온 후 재랭킹합니다.
    
    Args:
        query: 검색 쿼리
        filter_dict: 필터 조건
        final_top_k: 최종적으로 반환할 결과 수
        reranking_method: 재랭킹 방법 ('tfidf' 또는 'hybrid')
    """
    # 첫 번째 단계: 충분한 수의 결과를 가져옴 (final_top_k의 4배)
    initial_top_k = final_top_k * 4
    initial_results = search_with_filter(query, filter_dict, top_k=initial_top_k)
    
    print(f"첫 번째 검색 단계: {len(initial_results)}개 항목 찾음")
    
    # 두 번째 단계: 재랭킹
    if reranking_method == "tfidf":
        reranked_results = rerank_with_tfidf(query, initial_results, final_top_k)
    else:  # hybrid 방식이 기본
        reranked_results = rerank_with_hybrid(query, initial_results, final_top_k)
    
    return reranked_results

def print_results(results, title):
    """검색 결과를 출력합니다."""
    print("=" * 80)
    print(f"🔍 {title} (총 {len(results)}개)")
    print("=" * 80)
    
    for i, result in enumerate(results):
        payload = result.payload
        
        # 메타데이터 접근
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

print("리랭킹 검색 테스트 시작...")

# 테스트 1: 일반 검색 vs 리랭킹 검색 (제1장)
print("\n*** 테스트 1: 일반 검색 vs 리랭킹 검색 (제1장) ***")
regular_results = search_with_filter("외국환거래법 제1장", {"chapter_no": "제1장"}, top_k=5)
print_results(regular_results, "일반 검색 결과 (제1장)")

reranked_results = search_with_reranking("외국환거래법 제1장", {"chapter_no": "제1장"}, final_top_k=5)
print_results(reranked_results, "리랭킹 검색 결과 (제1장)")

# 테스트 2: 제1조 목적 검색
print("\n*** 테스트 2: 제1조 목적 검색 ***")
regular_results = search_with_filter("외국환거래법 제1조 목적", {"article_no": "제1조"}, top_k=3)
print_results(regular_results, "일반 검색 결과 (제1조 목적)")

reranked_results = search_with_reranking("외국환거래법 제1조 목적", {"article_no": "제1조"}, final_top_k=3)
print_results(reranked_results, "리랭킹 검색 결과 (제1조 목적)")

# 테스트 3: 필터 없는 검색 - 해외송금 규정
print("\n*** 테스트 3: 필터 없는 검색 - 해외송금 규정 ***")
regular_results = search_with_filter("외국환거래법 해외송금 신고 의무", None, top_k=5)
print_results(regular_results, "일반 검색 결과 (해외송금 신고 의무)")

reranked_results = search_with_reranking("외국환거래법 해외송금 신고 의무", None, final_top_k=5)
print_results(reranked_results, "리랭킹 검색 결과 (해외송금 신고 의무)")

# 테스트 4: TF-IDF 기반 리랭킹 vs 하이브리드 리랭킹
print("\n*** 테스트 4: TF-IDF vs 하이브리드 리랭킹 ***")
tfidf_results = search_with_reranking("외국환거래법 자금세탁방지", None, final_top_k=5, reranking_method="tfidf")
print_results(tfidf_results, "TF-IDF 리랭킹 결과 (자금세탁방지)")

hybrid_results = search_with_reranking("외국환거래법 자금세탁방지", None, final_top_k=5, reranking_method="hybrid")
print_results(hybrid_results, "하이브리드 리랭킹 결과 (자금세탁방지)") 