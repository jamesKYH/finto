from dotenv import load_dotenv
load_dotenv()
from datetime import datetime, timezone
from typing import Dict, List, Literal, cast, Any, Annotated
import os
import sys
import json

from langchain_core.messages import AIMessage, SystemMessage
from langchain_core.runnables import RunnableConfig
from langgraph.graph import StateGraph
from langgraph.prebuilt import ToolNode
from pathlib import Path
from react_agent.configuration import Configuration
from react_agent.state import InputState, State
from react_agent.tools import TOOLS, qdrant_search_reranked
from react_agent import utils
from langgraph.prebuilt import create_react_agent
from langchain_anthropic import ChatAnthropic
from langgraph.checkpoint.memory import MemorySaver
from langchain_core.runnables import RunnableConfig
from langgraph.prebuilt.tool_node import InjectedToolArg


memory = MemorySaver()

async def call_model(
    state: State, config: RunnableConfig
) -> Dict[str, List[AIMessage]]:
    """Call the LLM powering our "agent".

    This function prepares the prompt, initializes the model, and processes the response.

    Args:
        state (State): The current state of the conversation.
        config (RunnableConfig): Configuration for the model run.

    Returns:
        dict: A dictionary containing the model's response message.
    """
    configuration = Configuration.from_runnable_config(config)

    # Format the system prompt. Customize this to change the agent's behavior.
    system_message = configuration.system_prompt.format(
        system_time=datetime.now(tz=timezone.utc).isoformat()
    )

    # 모델 초기화
    model = ChatAnthropic(
        model="claude-3-5-haiku-20241022", temperature=0.0, max_tokens=8192
    )
    
    # 기본 도구 설정
    all_tools = TOOLS
    
    # 에이전트 생성
    agent = create_react_agent(model, all_tools, checkpointer=memory)
    
    # Create the messages list
    messages = [
        SystemMessage(content=system_message),
        *state.messages,
    ]

    # Pass messages with the correct dictionary structure
    response = cast(
        AIMessage,
        await agent.ainvoke(
            {"messages": messages},
            config,
        ),
    )

    # Handle the case when it's the last step and the model still wants to use a tool
    if state.is_last_step and response.tool_calls:
        return {
            "messages": [
                AIMessage(
                    id=response.id,
                    content="죄송합니다. 지정된 단계 수 내에서 질문에 대한 답변을 찾을 수 없었습니다.",
                )
            ]
        }

    # Return the model's response as a list to be added to existing messages
    return {"messages": [response["messages"][-1]]}


# 명시적인 래퍼 함수 정의 (람다 함수 대신 사용)
async def qdrant_search_with_params(
    query: str, *, config: Annotated[RunnableConfig, InjectedToolArg]
) -> list[dict[str, Any]]:
    """Qdrant 벡터 데이터베이스를 검색하는 도구.
    
    LLM을 통한 질문 재구성과 하이브리드 리랭킹을 포함합니다.
    
    Args:
        query: 검색할 텍스트 쿼리
        config: 도구 호출에 필요한 설정
        
    Returns:
        검색 결과 목록
    """
    return await qdrant_search_reranked(query, top_k=10, config=config)


# Define a new graph
builder = StateGraph(State, input=InputState, config_schema=Configuration)

# Define the two nodes we will cycle between
builder.add_node(call_model)

# 도구 설정 시 파라미터 직접 지정
tools_with_params = [
    qdrant_search_with_params
]

# 도구 노드 추가
builder.add_node("tools", ToolNode(tools_with_params))

# Set the entrypoint as `call_model`
# This means that this node is the first one called
builder.add_edge("__start__", "call_model")


def route_model_output(state: State) -> Literal["__end__", "tools"]:
    """Determine the next node based on the model's output.

    This function checks if the model's last message contains tool calls.

    Args:
        state (State): The current state of the conversation.

    Returns:
        str: The name of the next node to call ("__end__" or "tools").
    """
    # Check if the model's last message contains tool calls
    last_message = state.messages[-1]
    if isinstance(last_message, AIMessage) and last_message.tool_calls:
        # If we've reached the maximum number of steps, end the conversation
        if state.is_last_step:
            return "__end__"
        # Otherwise, continue to the tools node
        return "tools"
    # If no tool calls, end the conversation
    return "__end__"


# Add a conditional edge from `call_model` to either `tools` or `__end__`
builder.add_conditional_edges(
    "call_model", route_model_output
)

# Add an edge from `tools` back to `call_model`
builder.add_edge("tools", "call_model")

# Finally, compile the graph
graph = builder.compile()
graph.name = "ReAct Agent"  # This customizes the name in LangSmith
