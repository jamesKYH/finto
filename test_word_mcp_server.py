#!/usr/bin/env python3
"""
Office-Word-MCP-Server 테스트 스크립트

이 스크립트는 Office-Word-MCP-Server가 제대로 작동하는지 확인합니다.
HTTP 모드로 서버를 실행하고 문서 생성, 단락 추가 등의 기본 기능을 테스트합니다.
"""

import os
import sys
import subprocess
import asyncio
import json
import time
import httpx
from mcp.client.session import ClientSession

# Office-Word-MCP-Server 경로
OFFICE_WORD_MCP_PATH = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "src", "react_agent", "Office-Word-MCP-Server", "word_mcp_server.py"
)

# Word MCP 서버 URL
SERVER_URL = "http://localhost:8080"

async def main():
    print(f"Office-Word-MCP-Server 경로: {OFFICE_WORD_MCP_PATH}")
    
    # Word MCP 서버 프로세스 시작
    server_process = subprocess.Popen(
        [sys.executable, OFFICE_WORD_MCP_PATH],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    
    # 서버가 시작될 때까지 대기
    print("Word MCP 서버 시작 중...")
    max_retries = 10
    retry_count = 0
    server_ready = False
    
    while retry_count < max_retries and not server_ready:
        try:
            # 서버에 연결 시도
            async with httpx.AsyncClient(timeout=2.0) as client:
                response = await client.get(SERVER_URL)
                if response.status_code == 200:
                    server_ready = True
                    print("Word MCP 서버 응답 확인됨!")
                    break
        except Exception:
            pass
        
        retry_count += 1
        print(f"서버 연결 시도 중... ({retry_count}/{max_retries})")
        await asyncio.sleep(1)
    
    if not server_ready:
        print("Word MCP 서버 시작 실패")
        server_process.terminate()
        return
    
    try:
        # ClientSession 초기화
        session = ClientSession(SERVER_URL)
        
        # 사용 가능한 도구 가져오기
        tools = await session.list_tools()
        print(f"사용 가능한 도구 수: {len(tools)}")
        for i, tool in enumerate(tools):
            print(f"{i+1}. {tool.name}: {tool.description}")
        
        # 문서 생성 테스트
        print("\n1. 문서 생성 테스트")
        create_document_tool = next((tool for tool in tools if "create_document" in tool.name), None)
        if create_document_tool:
            result = await session.call_tool(create_document_tool.name, {"title": "테스트 문서"})
            print(f"결과: {json.dumps(result, ensure_ascii=False, indent=2)}")
        else:
            print("create_document 도구를 찾을 수 없습니다.")
        
        # 문서 목록 확인
        print("\n2. 문서 목록 확인")
        list_documents_tool = next((tool for tool in tools if "list_available_documents" in tool.name), None)
        if list_documents_tool:
            result = await session.call_tool(list_documents_tool.name, {})
            print(f"결과: {json.dumps(result, ensure_ascii=False, indent=2)}")
        else:
            print("list_available_documents 도구를 찾을 수 없습니다.")
        
        # 새 단락 추가 테스트
        print("\n3. 단락 추가 테스트")
        add_paragraph_tool = next((tool for tool in tools if "add_paragraph" in tool.name), None)
        if add_paragraph_tool:
            result = await session.call_tool(add_paragraph_tool.name, {
                "document_title": "테스트 문서",
                "text": "이것은 테스트 문서입니다. Office-Word-MCP-Server 연동 테스트 중입니다.",
                "style": "Normal"
            })
            print(f"결과: {json.dumps(result, ensure_ascii=False, indent=2)}")
        else:
            print("add_paragraph 도구를 찾을 수 없습니다.")
        
        # 문서 내용 확인
        print("\n4. 문서 내용 확인")
        get_document_text_tool = next((tool for tool in tools if "get_document_text" in tool.name), None)
        if get_document_text_tool:
            result = await session.call_tool(get_document_text_tool.name, {"document_title": "테스트 문서"})
            print(f"결과: {json.dumps(result, ensure_ascii=False, indent=2)}")
        else:
            print("get_document_text 도구를 찾을 수 없습니다.")
            
    except Exception as e:
        print(f"오류 발생: {str(e)}")
        import traceback
        print(traceback.format_exc())
    finally:
        # 프로세스 종료
        print("\n서버 프로세스 종료 중...")
        server_process.terminate()
        try:
            server_process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            server_process.kill()

if __name__ == "__main__":
    asyncio.run(main()) 