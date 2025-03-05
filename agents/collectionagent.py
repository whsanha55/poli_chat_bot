from typing import Annotated, Sequence, TypedDict, Dict, Any, List
import json
import asyncio
from langchain_openai import ChatOpenAI
from langchain_core.messages import BaseMessage, ToolMessage, SystemMessage, HumanMessage
from langchain_core.runnables import RunnableConfig
from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages
from tools.perplexity_tool import PerplexityQATool
from langchain_community.tools import TavilySearchResults
#
from utils.logging_utils import log_tool_usage



class CollectionAgentState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], add_messages]
    chat_history: Sequence[BaseMessage]  # Dict 형식에서 BaseMessage로 변경

def create_collection_agent():

    tools = [PerplexityQATool(), TavilySearchResults()]
    tools_by_name = {tool.name: tool for tool in tools}
    

    model = ChatOpenAI(model="gpt-4o-mini")
    model = model.bind_tools(tools)
    
    # 도구 노드
    def tool_node(state: CollectionAgentState) -> Dict:
        outputs = []    
        for tool_call in state["messages"][-1].tool_calls:
            # 도구 사용 로깅
            log_tool_usage("collection_agent", tool_call["name"], json.dumps(tool_call["args"]))
            
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
        state: CollectionAgentState,
        config: RunnableConfig,
    ) -> Dict:
        system_prompt = SystemMessage(content="""
        당신은 「Collection Agent」입니다.  
        역할: 사기 피해 진정서 작성을 위한 정보를 수집하고, 작성 양식을 안내합니다.
                                      
        사용가능한 도구:
        1. perplexity_tool: 
           - Perplexity AI 기반의 심층 검색 도구
           - 복잡한 법률 정보나 진정서 작성 관련 상세 내용 검색에 활용
           - 정확하고 신뢰성 있는 정보가 필요한 경우 사용

        2. tavily_search_results:
           - 실시간 웹 검색 기반의 빠른 검색 도구
           - 최신 사기 사례나 간단한 정보 조회에 활용
           - 신속한 결과가 필요한 경우 사용

        당신이 해야 할 일:
        1. 사용자에게 진정서 작성을 위해 필요한 필수 정보를 확인하세요:
        - 신청인 정보 (성명, 생년월일, 주소, 연락처)
        - 피진정인 정보 (상대방 닉네임/이름/아이디, 사이트/플랫폼명, 가능한 연락처, 계좌번호 등)
        - 피해 내용 (사기 유형, 날짜/시간, 금액, 진행 과정, 입금 방식 등)
        - 증거자료 (대화 캡처, 이체 기록, 송금증, 택배 송장 등)
        2. 아직 누락된 정보가 있다면 정중하게 요청하세요.
        3. 모든 내용이 충분해지면, **진정서 양식**(문서 내용 예시)을 안내하거나 작성에 필요한 초안을 제공합니다.
        4. 추가로 궁금한 사항(서류 제출처, 절차, 소요시간 등)에 대해 안내해 주세요.
        5. 사기 피해로 심려가 큰 사용자에게 적절한 공감 문장을 포함하면서, 단순히 반복 멘트만 하지 말고 **사용자가 제공한 정보**를 구체적으로 반영해 대화를 진행하세요.
        6. 정보가 충분하다면, 진정서 양식을 안내하거나, 진정서 작성 버튼을 눌러서 진정서를 작성하라고 사용자에게 안내해 주세요.
                                      
        상세 유의사항:
        - 사용자 대답을 들어보고, 누락된 부분(예: 사건 발생 시점, 정확한 금액, 상대방 계좌번호 등)이 있다면 꼼꼼히 물어보세요.
        - "혹시 거래하시던 플랫폼 이름과 상대방 아이디는 어떻게 되나요?" 처럼 구체적인 추가 질문을 하세요.
        - 상대방이 원한다면, 최종적으로 "진정서 서식"을 함께 만들어주는 단계로 안내하세요.
        - 이미 Poli Agent에게서 받은 정보가 있다면, 중복으로 요구하지 않도록 유의하세요(동일한 프로젝트라면 chat_history를 참고)
        
        필수사항:
        진정서에 제공되는 정보가 충분하다면, 진정서 버튼을 누르라고 제안하세요. Chat History에 내용을 보고 80% 이상 채워졌다면 진정서 버튼을 누르라고 제안하세요.
        """)
        
        # chat_history가 이미 BaseMessage 형식이므로 직접 사용
        all_messages = [system_prompt] + list(state["chat_history"]) + list(state["messages"])
        
        response = model.invoke(all_messages, config)
        return {"messages": [response], "chat_history": state["chat_history"]}
    
    # 그래프 구성
    workflow = StateGraph(CollectionAgentState)
    
    workflow.add_node("agent", call_model)
    workflow.add_node("tools", tool_node)
    workflow.set_entry_point("agent")
    
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
    
    # 체크포인터 설정과 함께 컴파일
    return workflow.compile()