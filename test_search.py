import asyncio
from react_agent.tools import qdrant_search_reranked
from langchain_core.runnables import RunnableConfig

async def test_search():
    # 자연어 질문 + 키워드 위주 쿼리 혼합 (외국환거래법 중심)
    test_queries = [
        "외국환거래법 신고의무",
        "외국환거래법 제18조",
        "외국환중개업무 규제",
        "외국환거래법 처벌",
        "외국환거래법상 신고의무가 발생하는 경우는?",
        "외국환거래법 위반 시 처벌 규정은?",
        "외국환거래법상 외국환중개업무의 규제는 어떻게 되나요?"
    ]
    
    # 기본 설정 생성
    config = RunnableConfig()
    
    for query in test_queries:
        print("\n" + "="*50)
        print(f"원본 질문: {query}")
        
        try:
            # 검색 실행
            results = await qdrant_search_reranked(
                query=query,
                top_k=3,  # 상위 3개 결과만 확인
                initial_k=10,
                reranking_method="hybrid",
                config=config  # config 파라미터 추가
            )
            
            # 결과 출력
            print("\n검색 결과:")
            for i, result in enumerate(results, 1):
                payload = result.get('payload', {})
                print(f"\n{i}번째 결과 payload 전체: {payload}")
                print(f"제목: {payload.get('title', 'N/A')}")
                print(f"내용: {payload.get('content', 'N/A')[:200]}...")  # 내용은 200자까지만 출력
                
        except Exception as e:
            print(f"검색 중 오류 발생: {str(e)}")
            continue

if __name__ == "__main__":
    asyncio.run(test_search()) 