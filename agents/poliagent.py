from typing import Annotated, Sequence, TypedDict, Dict, Any, List
import json
import asyncio
from langchain_openai import ChatOpenAI
from langchain_core.messages import BaseMessage, SystemMessage, HumanMessage, ToolMessage
from langchain_core.runnables import RunnableConfig
from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages
from prompt.system import poli_agent_system_prompt
from langchain_community.tools import TavilySearchResults
from utils.logging_utils import log_tool_usage

class PoliAgentState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], add_messages]
    chat_history: Sequence[BaseMessage]

def create_poli_agent():
    # 도구 초기화
    tavily_tool = TavilySearchResults(k=5)
   
    tools = [tavily_tool]
    tools_by_name = {tool.name: tool for tool in tools}
    
    # LLM 초기화 (도구 바인딩 추가)
    model = ChatOpenAI(model="gpt-4o-mini")
    model = model.bind_tools(tools)
    
    # 도구 실행 노드 추가
    def tool_node(state: PoliAgentState) -> Dict:
        outputs = []    
        for tool_call in state["messages"][-1].tool_calls:
            # 도구 사용 로깅
            log_tool_usage("poli_agent", tool_call["name"], json.dumps(tool_call["args"]))
            
            tool_result = tools_by_name[tool_call["name"]].invoke(tool_call["args"])
            if asyncio.iscoroutine(tool_result):
                tool_result = asyncio.run(tool_result)
            outputs.append(
                ToolMessage(
                    content=json.dumps(tool_result),
                    name=tool_call["name"],
                    tool_call_id=tool_call["id"],
                )
            )
        return {"messages": outputs, "chat_history": state["chat_history"]}
    
    # LLM 노드
    def call_model(
        state: PoliAgentState,
        config: RunnableConfig,
    ) -> Dict:
        system_prompt = SystemMessage(content=poli_agent_system_prompt)
        
        all_messages = [system_prompt] + list(state["chat_history"]) + list(state["messages"])
        
        response = model.invoke(all_messages, config)
        return {"messages": [response], "chat_history": state["chat_history"]}
    
    # 그래프 구성 수정
    workflow = StateGraph(PoliAgentState)
    
    workflow.add_node("agent", call_model)
    workflow.add_node("tools", tool_node)
    workflow.set_entry_point("agent")
    
    # 조건부 엣지 추가
    workflow.add_conditional_edges(
        "agent",
        lambda x: "end" if not hasattr(x["messages"][-1], "tool_calls") 
                 or not x["messages"][-1].tool_calls else "continue",
        {
            "continue": "tools",
            "end": END,
        },
    )
    workflow.add_edge("tools", "agent")
    
    # 컴파일 및 반환
    return workflow.compile()