from qdrant_client import QdrantClient
from qdrant_client.models import PointStruct, Filter, FieldCondition, MatchValue
import os
import requests
import json
from typing import Annotated, List, Dict, Any, Optional
from langchain_core.runnables.config import RunnableConfig
from langgraph.prebuilt.tool_node import InjectedToolArg
from typing import Any
from sentence_transformers import SentenceTransformer
import re
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from langchain_anthropic import ChatAnthropic
from langchain_core.messages import HumanMessage, SystemMessage

QDRANT_URL = os.environ.get("QDRANT_URL", "http://localhost:6333")
COLLECTION_NAME = os.environ.get("COLLECTION_NAME", "my-collection")
EMBEDDING_MODEL = os.environ.get("EMBEDDING_MODEL", "all-MiniLM-L6-v2")

# 임베딩 모델 초기화
model = SentenceTransformer(EMBEDDING_MODEL)
qdrant_client = QdrantClient(url=QDRANT_URL)

async def qdrant_search(
    query: str, 
    top_k: int = 5, 
    initial_k: int = 20,
    reranking_method: str = "hybrid",
    *, 
    config: Annotated[RunnableConfig, InjectedToolArg]
) -> list[dict[str, Any]]:
    """Search Qdrant with a text query and reranking.
    
    Args:
        query: The text query to search for
        top_k: The final number of results to return after reranking
        initial_k: The initial number of results to fetch for reranking
        reranking_method: The reranking method to use ('hybrid', 'tfidf')
        
    Returns:
        A list of search results
    """
    print(f"📌 qdrant_search 함수 호출됨: 쿼리='{query}', top_k={top_k}, initial_k={initial_k}, method={reranking_method}")
    
    try:
        # 법령 구조 관련 키워드 추출 (예: 제1장, 제1조)
        chapter_match = re.search(r'제(\d+)장', query)
        # '제1조'와 '1조' 두 가지 패턴 모두 인식
        article_match = re.search(r'(?:제)?(\d+)조', query)
        
        # REST API 요청 준비
        url = f"{QDRANT_URL}/collections/{COLLECTION_NAME}/points/search"
        
        # 필터 조건 설정
        filter_conditions = None
        if chapter_match or article_match:
            must_conditions = []
            
            if chapter_match:
                chapter_no = f"제{chapter_match.group(1)}장"
                must_conditions.append({
                    "key": "chapter_no",
                    "match": {"value": chapter_no}
                })
                
            if article_match:
                article_no = f"제{article_match.group(1)}조"
                must_conditions.append({
                    "key": "article_no",
                    "match": {"value": article_no}
                })
                
            if must_conditions:
                filter_conditions = {"must": must_conditions}
        
        # 텍스트 쿼리를 벡터로 변환
        query_vector = model.encode(query).tolist()
    
        # REST API 요청 페이로드 구성 - 초기 검색에서 더 많은 수의 결과를 가져옴
        payload = {
            "params": {"hnsw_ef": 128, "exact": False},
            "vector": {"name": EMBEDDING_MODEL, "vector": query_vector},
            "limit": initial_k,  # 초기에 더 많은 결과를 가져오기 위해 initial_k 사용
            "with_payload": True,
            "with_vectors": False,
            "score_threshold": 0.0
        }
        
        # 필터 조건이 있으면 추가
        if filter_conditions:
            payload["filter"] = filter_conditions
            print(f"📌 Qdrant 검색 필터 적용: {json.dumps(filter_conditions)}")
        
        print(f"📌 Qdrant API URL: {url}")
        response = requests.post(url, json=payload)
        print(f"📌 Qdrant API 응답 상태 코드: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            if "result" in data:
                initial_results = data["result"]
                print(f"📌 초기 검색: {len(initial_results)}개 항목 가져옴")
                
                # 결과가 충분하지 않으면 필터 없이 다시 검색
                if len(initial_results) < initial_k / 2 and filter_conditions:
                    print(f"📌 검색 결과가 충분하지 않아 필터 없이 다시 검색합니다.")
                    payload.pop("filter", None)
                    response = requests.post(url, json=payload)
                    
                    if response.status_code == 200:
                        data = response.json()
                        if "result" in data:
                            initial_results = data["result"]
                            print(f"📌 필터 없는 초기 검색: {len(initial_results)}개 항목 가져옴")
                
                # 결과가 없으면 오류 반환
                if not initial_results:
                    return [{"error": "검색 결과가 없습니다."}]
                
                # 리랭킹 진행
                if reranking_method == "tfidf":
                    reranked_results = rerank_with_tfidf(query, initial_results, top_k)
                    print(f"📌 TF-IDF 리랭킹 완료: {len(reranked_results)}개 결과")
                else:  # hybrid 방식 사용
                    reranked_results = rerank_with_hybrid(query, initial_results, top_k)
                    print(f"📌 하이브리드 리랭킹 완료: {len(reranked_results)}개 결과")
                
                # 페이로드만 반환
                return [result["payload"] for result in reranked_results]
            else:
                print(f"📌 Qdrant 검색 오류: 결과에 데이터가 없음 - {response.text}")
                return [{"error": f"검색 결과에 데이터가 없습니다: {response.text}"}]
        else:
            print(f"📌 Qdrant 검색 오류: API 응답 실패 - {response.status_code} - {response.text}")
            return [{"error": f"검색 중 오류 발생: {response.text}"}]
    except Exception as e:
        print(f"📌 Qdrant 검색 예외: {str(e)}")
        import traceback
        print(f"📌 예외 상세 정보: {traceback.format_exc()}")
        return [{"error": f"검색 중 예외 발생: {str(e)}"}]

def rerank_with_tfidf(query, results, top_n=5):
    """TF-IDF 기반으로 결과를 재랭킹합니다."""
    # 결과가 충분하지 않으면 그대로 반환
    if len(results) <= top_n:
        return results
    
    # 결과에서 텍스트 추출
    texts = [result["payload"].get("cleaned_content", "") for result in results]
    
    # 쿼리와 텍스트를 함께 TF-IDF 변환
    tfidf = TfidfVectorizer().fit_transform(texts + [query])
    
    # 마지막 벡터(쿼리)와 다른 모든 텍스트 간의 유사도 계산
    similarities = cosine_similarity(tfidf[-1:], tfidf[:-1])[0]
    
    # 유사도에 따라 정렬
    reranked_indices = similarities.argsort()[::-1][:top_n]
    
    print(f"📌 TF-IDF 리랭킹 상위 점수: {[similarities[i] for i in reranked_indices[:3]]}")
    
    return [results[i] for i in reranked_indices]

def rerank_with_hybrid(query, results, top_n=5, alpha=0.6):
    """벡터 검색 점수와 TF-IDF 점수를 조합하여 하이브리드 재랭킹을 수행합니다."""
    # 결과가 충분하지 않으면 그대로 반환
    if len(results) <= top_n:
        return results
    
    # 벡터 검색 점수 정규화
    vector_scores = np.array([result["score"] for result in results])
    if vector_scores.max() != vector_scores.min():  # 분모가 0이 되지 않도록 체크
        vector_scores = (vector_scores - vector_scores.min()) / (vector_scores.max() - vector_scores.min())
    else:
        vector_scores = np.ones_like(vector_scores)
    
    # 텍스트 기반 유사도 계산
    texts = [result["payload"].get("cleaned_content", "") for result in results]
    
    try:
        tfidf = TfidfVectorizer().fit_transform(texts + [query])
        tfidf_scores = cosine_similarity(tfidf[-1:], tfidf[:-1])[0]
        
        if tfidf_scores.max() != tfidf_scores.min():  # 분모가 0이 되지 않도록 체크
            tfidf_scores = (tfidf_scores - tfidf_scores.min()) / (tfidf_scores.max() - tfidf_scores.min())
        else:
            tfidf_scores = np.ones_like(tfidf_scores)
        
        # 점수 조합
        combined_scores = alpha * vector_scores + (1 - alpha) * tfidf_scores
    except Exception as e:
        print(f"📌 TF-IDF 계산 중 오류, 벡터 점수만 사용합니다: {str(e)}")
        combined_scores = vector_scores
    
    # 조합된 점수로 정렬
    reranked_indices = combined_scores.argsort()[::-1][:top_n]
    
    print(f"📌 하이브리드 리랭킹 상위 점수: {[combined_scores[i] for i in reranked_indices[:3]]}")
    
    return [results[i] for i in reranked_indices]

async def restructure_query_with_llm(query: str) -> str:
    """LLM을 사용하여 법률 검색에 최적화된 형태로 질문을 재구성합니다."""
    model = ChatAnthropic(
        model="claude-3-5-haiku-20241022",
        temperature=0.0,
        max_tokens=1000
    )
    
    system_prompt = """당신은 법률 검색 전문가입니다. 사용자의 질문을 법률 검색에 최적화된 형태로 재구성해주세요.
    다음 사항을 고려하여 재구성해주세요:
    1. 법률 용어를 정확하게 사용
    2. 법률 문서 구조를 고려 (조, 장, 절 등)
    3. 검색 의도를 명확히 표현
    4. 관련 법률 분야를 명시
    5. 구체적인 법률 개념을 포함
    
    재구성된 질문은 검색에 최적화되어야 하며, 원래 의도를 유지해야 합니다."""
    
    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=f"원본 질문: {query}\n\n재구성된 질문:")
    ]
    
    response = await model.ainvoke(messages)
    return response.content.strip()

async def qdrant_search_reranked(
    query: str,
    top_k: int = 5,
    initial_k: int = 20,
    reranking_method: str = "hybrid",
    *, 
    config: Annotated[RunnableConfig, InjectedToolArg]
) -> List[Dict[str, Any]]:
    """법률 문서를 검색하고 결과를 리랭킹합니다."""
    try:
        # 1. LLM을 통한 질문 재구성
        restructured_query = await restructure_query_with_llm(query)
        print(f"원본 질문: {query}")
        print(f"재구성된 질문: {restructured_query}")
        
        # 2. 벡터 검색
        query_vector = model.encode(restructured_query).tolist()
        payload = {
            "vector": {"name": EMBEDDING_MODEL, "vector": query_vector},
            "limit": initial_k
        }
        
        # 3. 검색 실행
        results = await qdrant_search(restructured_query, top_k, initial_k, reranking_method, config=config)
        
        # 4. 리랭킹
        if reranking_method == "hybrid":
            reranked_results = rerank_with_hybrid(restructured_query, results, top_k)
        else:
            reranked_results = rerank_with_tfidf(restructured_query, results, top_k)
            
        return reranked_results
        
    except Exception as e:
        print(f"검색 중 오류 발생: {str(e)}")
        return []

"""This module provides tools for vector search and reranking functionality.

These tools are specialized for legal document search with vector and hybrid reranking capabilities.
"""

from typing import Any, Callable, List, Optional, cast
from langchain_core.runnables import RunnableConfig
from langchain_core.tools import InjectedToolArg
from typing_extensions import Annotated

from react_agent.configuration import Configuration

TOOLS: List[Callable[..., Any]] = [qdrant_search_reranked]
