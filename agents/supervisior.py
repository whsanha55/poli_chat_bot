from typing import Annotated, Sequence, TypedDict, Dict, List, Literal
from pydantic import BaseModel
from langchain_openai import ChatOpenAI
from langchain_core.messages import BaseMessage, SystemMessage, HumanMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages

from agents.poliagent import create_poli_agent, PoliAgentState
from agents.collectionagent import create_collection_agent, CollectionAgentState
from utils.logging_utils import log_agent_routing

import os
from dotenv import load_dotenv

load_dotenv()

class SupervisorState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], add_messages]
    chat_history: Sequence[BaseMessage]  # Dict 형식에서 BaseMessage로 변경
    next: str

class RouteResponse(BaseModel):
    next: Literal["POLIAGENT", "COLLECTIONAGENT", "CHAT", "FINISH"]

def create_supervisor_agent():
    """슈퍼바이저 에이전트를 생성하는 메인 함수"""
    
    # 하위 에이전트들 초기화
    poli_agent = create_poli_agent()
    collection_agent = create_collection_agent()
    # GPT-4 모델 초기화
    model = ChatOpenAI(model="gpt-4o-mini", temperature=0.7)
    
    # 슈퍼바이저의 메인 프롬프트 설정
    supervisor_prompt = ChatPromptTemplate.from_messages([
        ("system", """
        당신은 친절하고 전문적인 AI 어시스턴트입니다.
        
        입력을 정확히 분석하여 다음과 같이 라우팅하세요:
        
        1. 사용자가 사기 피해 신고를 원하는 경우, POLIAGENT로 라우팅하세요.
        2. 사용자가 진정서 작성을 원하는 경우, 진정서 작성하는방법을 물어보는 경우, 대화내용을 보고 정보를 수집중이라면, COLLECTIONAGENT로 라우팅하세요.
        3. 사용자가 일반적인 대화를 원하는 경우, CHAT로 라우팅하세요.
        
        명확하지 않은 경우, 사용자에게 구체적인 의도를 물어보세요.
        """),
        MessagesPlaceholder(variable_name="chat_history"),
        MessagesPlaceholder(variable_name="messages"),
        ("system", "다음 중 하나를 선택하세요: POLIAGENT, LETTERAGENT, WRITERAGENT, CHAT")
    ])
    
    def supervisor_node(state: SupervisorState) -> Dict:
        try:
            # 라우팅 결정 (이미 BaseMessage 형식이므로 변환 불필요)
            route_chain = supervisor_prompt | model.with_structured_output(RouteResponse)
            result = route_chain.invoke({
                "messages": state["messages"],
                "chat_history": state["chat_history"]
            })
            
            log_agent_routing("supervisor", result.next)
            
            if result.next == "CHAT":
                chat_model = ChatOpenAI(
                    model="gpt-4o-mini",
                    temperature=0.1,
                )
                
                chat_prompt = ChatPromptTemplate.from_messages([
                    ("system", "당신은 POlI Agent 로 사기피해 진정서에 관련된 특화에이전트입니다. 유저의 질문을 받아서, 관련내용이 아니라면 해당 Task 를 수행할 수 있도록 유도를 하세요."),
                    MessagesPlaceholder(variable_name="chat_history"),
                    MessagesPlaceholder(variable_name="messages")
                ])
                
                # 응답 생성 (이미 BaseMessage 형식)
                response = chat_model.invoke(chat_prompt.format_messages(
                    messages=state["messages"],
                    chat_history=state["chat_history"]
                ))
                
                # 메시지와 채팅 기록 업데이트
                new_messages = list(state["messages"]) + [response]
                chat_history = list(state["chat_history"]) + [state["messages"][-1], response] if state["messages"] else []
                
                return {
                    "messages": new_messages,
                    "chat_history": chat_history,
                    "next": "FINISH"
                }
            
            return {
                "messages": state["messages"],
                "chat_history": state["chat_history"],
                "next": result.next
            }
            
        except Exception as e:
            return {
                "messages": [SystemMessage(content="죄송합니다. 일시적인 오류가 발생했습니다.")],
                "chat_history": state["chat_history"],
                "next": "FINISH"
            }
    
    def collection_node(state: SupervisorState) -> Dict:
        """정보 수집 에이전트 노드"""
        try:
            collection_state = CollectionAgentState(
                messages=state["messages"],
                chat_history=state["chat_history"]
            )
            result = collection_agent.invoke(collection_state)
            
            # 응답이 있는지 확인
            if result and "messages" in result and result["messages"]:
                # 채팅 기록 업데이트
                new_chat_history = result.get("chat_history", state["chat_history"])
                
                # 응답 메시지 확인 및 변환
                response_message = result["messages"][-1]
                if hasattr(response_message, 'content'):
                    return {
                        "messages": result["messages"],
                        "chat_history": new_chat_history,
                        "next": "FINISH"
                    }
            
            raise ValueError("정보 수집 에이전트로부터 유효한 응답을 받지 못했습니다")

        except Exception as e:
            error_message = SystemMessage(content="죄송합니다. 금융 정보 처리 중 오류가 발생했습니다.")
            return {
                "messages": [error_message],
                "chat_history": state["chat_history"],
                "next": "FINISH"
            }
        
    def poli_node(state: SupervisorState) -> Dict:
        """사기 피해 신고 에이전트 노드
        
        Args:
            state: 현재 대화 상태
            
        Returns:
            Dict: 사기 피해 신고 결과와 업데이트된 대화 기록
        """
        poli_state = PoliAgentState(
            messages=state["messages"],
            chat_history=state["chat_history"]
        )
        result = poli_agent.invoke(poli_state)
        return {
            "messages": result["messages"],
            "chat_history": result["chat_history"],
            "next": "FINISH"
        }
    
    # 워크플로우 그래프 구성
    workflow = StateGraph(SupervisorState)
    
    # 각 에이전트 노드 추가
    workflow.add_node("supervisor", supervisor_node)
    workflow.add_node("poliagent", poli_node)
    workflow.add_node("collectionagent", collection_node)
    
    # 시작점을 슈퍼바이저로 설정    
    workflow.set_entry_point("supervisor")
    
    # 조건부 라우팅 규칙 설정
    conditional_map = {
        "POLIAGENT": "poliagent",
        "COLLECTIONAGENT": "collectionagent",
        "CHAT": "supervisor",
        "FINISH": END
    }
    
    def get_next(state):
        return state["next"]
    
    # 조건부 엣지 추가
    workflow.add_conditional_edges("supervisor", get_next, conditional_map)
    
    return workflow.compile()