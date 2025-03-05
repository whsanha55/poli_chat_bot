from typing import Annotated, Sequence, TypedDict, Dict, Any, List
import json
import asyncio
import re
from langchain_openai import ChatOpenAI
from langchain_core.messages import BaseMessage, ToolMessage, SystemMessage, HumanMessage, AIMessage
from langchain_core.runnables import RunnableConfig
from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages

from tools.perplexity_tool import PerplexityQATool
from langchain_community.tools import TavilySearchResults

class WriterAgentState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], add_messages]
    chat_history: List[Dict[str, str]]
    completion_ratio: float  # 0.0 ~ 1.0 (진정서 정보 충족도)
    finalize_requested: bool # 사용자가 "yes"라고 답했는지 여부

# 진정서 양식 JSON 스키마
LETTER_FORM_SCHEMA = {
    "title": "진 정 서",
    "fields": [
        {
            "section": "신청인(피해자)",
            "fields": [
                {"label": "성명", "type": "text", "required": True},
                {"label": "주민등록번호(또는 생년월일)", "type": "text", "required": True},
                {"label": "주소", "type": "text", "required": True},
                {"label": "연락처", "type": "text", "required": True}
            ]
        },
        {
            "section": "피진정인(피의자)",
            "fields": [
                {"label": "성명(또는 닉네임/아이디)", "type": "text", "required": False},
                {"label": "아이디/사이트명", "type": "text", "required": True},
                {"label": "기타 가능한 신원정보", "type": "text", "required": False}
            ]
        },
        {
            "section": "진정 내용",
            "fields": [
                {
                    "label": "범죄 유형",
                    "type": "dropdown",
                    "options": ["사이버 사기", "명예훼손", "불법 촬영물 유포"],
                    "required": True
                },
                {"label": "세부 유형", "type": "text", "required": True},
                {"label": "피해 장소", "type": "text", "required": True},
                {"label": "피해 발생 일시", "type": "text", "required": True},
                {"label": "피해 발생 경로", "type": "text", "required": True},
                {"label": "피해 사실", "type": "text", "required": True}
            ]
        },
        {
            "section": "첨부 증거 자료",
            "fields": [
                {"label": "관련 대화 내역", "type": "file", "required": False},
                {"label": "거래 영수증 또는 입금 내역", "type": "file", "required": False},
                {"label": "명예훼손 게시물 캡처 및 URL", "type": "file", "required": False}
            ]
        },
        {
            "section": "결 론",
            "fields": [
                {"label": "결론 문장", "type": "text", "required": True}
            ]
        }
    ]
}

def create_writer_agent():
    """WriterAgent를 생성하는 함수"""
    
    tools = [PerplexityQATool(), TavilySearchResults()]
    tools_by_name = {tool.name: tool for tool in tools}
    
    # LLM 초기화
    model = ChatOpenAI(model="gpt-4o-mini")
    model = model.bind_tools(tools)
    
    def writer_agent_node(state: WriterAgentState, config: RunnableConfig) -> Dict:
        """
        단일 에이전트 노드:
        - 대화 내역을 바탕으로 진정서 작성 가능 여부를 판단
        - 가능하면 작성
        - 부족하면 추가 정보 요청
        """
        messages_out = []
        
        # 진정서 작성 완료 요청이 있으면 작성
        if state["finalize_requested"]:
            finalize_model = ChatOpenAI(model="gpt-4o-mini", temperature=0.2)
            system_prompt = SystemMessage(content=f"""
            당신은 최종 '진정서' 문안을 작성해주는 역할입니다.
        
            [진정서 양식 JSON]
            {json.dumps(LETTER_FORM_SCHEMA, ensure_ascii=False, indent=2)}
        
            지금까지 사용자(신청인)이 제공한 내용을 최대한 반영하여,
            아래와 같은 템플릿으로 작성해주세요:
        
            [진 정 서]
            접수기관: ○○경찰서(또는 ○○지방경찰청 사이버수사대)
        
            1. 신청인(피해자):
               - 성명: ...
               - 주민등록번호(생년월일): ...
               - 주소: ...
               - 연락처: ...
            2. 피진정인(피의자):
               - 성명(닉네임/아이디): ...
               - 아이디/사이트명: ...
               - 기타 가능한 신원정보: ...
            3. 진정 내용:
               - 범죄 유형: ...
               - 세부 유형: ...
               - 피해 장소: ...
               - 피해 발생 일시: ...
               - 피해 발생 경로: ...
               - 피해 사실: ...
               - (필요시) 첨부 증거 자료: ...
            4. 결론:
               - 결론 문장
        
            마지막에:
            ○○○○년 ○○월 ○○일
            신청인: ○○○ (서명 또는 인)
        
            대화내용에서 사용자가 말한 정보를 최대한 추려서 반영하세요.
            누락된 부분은 "불상" "미상" 등으로 처리하셔도 됩니다.
            """)
            
            # 대화 전체를 넣어서 최종 문안 구성
            chat_msgs = []
            for h in state["chat_history"]:
                if h["role"] == "user":
                    chat_msgs.append(HumanMessage(content=h["content"]))
                else:
                    chat_msgs.append(SystemMessage(content=h["content"]))
            
            for msg in state["messages"]:
                if isinstance(msg, HumanMessage):
                    chat_msgs.append(HumanMessage(content=msg.content))
                elif isinstance(msg, SystemMessage) or isinstance(msg, AIMessage):
                    chat_msgs.append(SystemMessage(content=msg.content))
            
            all_msgs = [system_prompt] + chat_msgs
            final_resp = finalize_model.invoke(all_msgs, config)
            
            messages_out.append(final_resp)
            return {
                "messages": messages_out,
                "chat_history": state["chat_history"],
                "completion_ratio": state["completion_ratio"],
                "finalize_requested": True
            }
        
        # 진정서 작성 여부 판단
        elif state["completion_ratio"] >= 0.8:
            # 진정서 작성 요청
            msg = SystemMessage(
                content="진정서에 필요한 정보가 거의 준비된 것 같습니다. 작성하시겠습니까? (yes/no)"
            )
            messages_out.append(msg)
            return {
                "messages": messages_out,
                "chat_history": state["chat_history"],
                "completion_ratio": state["completion_ratio"],
                "finalize_requested": False
            }
        
        else:
            # 추가 정보 수집
            system_prompt = SystemMessage(content=f"""
            당신은 「Writer Agent」입니다.
            역할: 사기 피해 진정서를 작성하기 위한 정보를 수집하고, 작성 양식을 안내합니다.
        
            아래 '진정서 양식 JSON'의 스키마에 따라, 필수 필드를 사용자로부터 최대한 구체적으로 받아주세요.
            JSON 스키마:
            {json.dumps(LETTER_FORM_SCHEMA, ensure_ascii=False, indent=2)}
        
            주의사항:
            - 아직 사용자에게서 충분한 정보가 나오지 않았다면, 어떤 항목이 누락되었는지 구체적으로 묻고 안내하세요.
            - 이미 답변 받은 내용은 중복으로 물어보지 말고, chat_history를 잘 활용하세요.
            - 80% 이상 정보가 모이면, 곧 최종 진정서 초안을 작성해줄 수 있다고 제안하세요.
            """)
            
            all_messages = [system_prompt]
            for history in state["chat_history"]:
                if history["role"] == "user":
                    all_messages.append(HumanMessage(content=history["content"]))
                elif history["role"] == "assistant":
                    all_messages.append(SystemMessage(content=history["content"]))
            # 현재 턴에서 들어온 messages
            all_messages.extend(state["messages"])
            
            response = model.invoke(all_messages, config)
            messages_out.append(response)
            
            return {
                "messages": messages_out,
                "chat_history": state["chat_history"],
                "completion_ratio": state.get("completion_ratio", 0.0),
                "finalize_requested": state.get("finalize_requested", False)
            }
    
    def tool_node(state: WriterAgentState) -> Dict:
        outputs = []
        for tool_call in state["messages"][-1].tool_calls:
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
        return {
            "messages": outputs, 
            "chat_history": state["chat_history"],
            "completion_ratio": state["completion_ratio"],
            "finalize_requested": state.get("finalize_requested", False)
        }
    
    def update_completion_ratio(state: WriterAgentState, config: RunnableConfig) -> Dict:
        """
        현재까지의 대화 내역을 바탕으로 진정서 정보 충족도를 계산
        """
        ratio_model = ChatOpenAI(model="gpt-4o-mini", temperature=0.0)
        
        system_prompt = SystemMessage(content=f"""
        당신은 '진정서 정보 충족도'를 평가하는 역할입니다.
    
        [진정서 양식 JSON]
        {json.dumps(LETTER_FORM_SCHEMA, ensure_ascii=False, indent=2)}
    
        위 양식을 기준으로, 지금까지의 대화를 보고 필수 필드 중 몇 %가 채워졌는지 0.0 ~ 1.0 사이 숫자로 추정해주세요.
        답변 마지막에 '##COMPLETION:0.XX##' 형태로 기재해주세요.
        """)
    
        # 모든 대화(채팅) + 마지막 agent 응답을 합쳐서 모델에 전달
        chat_history_msgs = []
        for h in state["chat_history"]:
            if h["role"] == "user":
                chat_history_msgs.append(HumanMessage(content=h["content"]))
            else:
                chat_history_msgs.append(SystemMessage(content=h["content"]))
        
        # 이번 턴에 생성된 메시지들도 포함
        for msg in state["messages"]:
            if isinstance(msg, HumanMessage):
                chat_history_msgs.append(HumanMessage(content=msg.content))
            elif isinstance(msg, SystemMessage) or isinstance(msg, AIMessage):
                chat_history_msgs.append(SystemMessage(content=msg.content))
    
        messages = [system_prompt] + chat_history_msgs
        ratio_response = ratio_model.invoke(messages, config)
    
        # 예: "... ##COMPLETION:0.72##"
        text = ratio_response.content
        match = re.search(r'##COMPLETION:(0\.\d+)##', text)
        ratio = 0.0
        if match:
            try:
                ratio = float(match.group(1))
            except:
                ratio = 0.0
    
        return {
            "messages": [],  # 사용자에게 보여줄 메시지는 없음
            "chat_history": state["chat_history"],
            "completion_ratio": ratio,
            "finalize_requested": state.get("finalize_requested", False)
        }
    
    def finalize_decision_node(state: WriterAgentState) -> Dict:
        """
        사용자의 응답에 따라 진정서 작성 여부 결정
        """
        messages_out = []
        if state["completion_ratio"] >= 0.8 and not state["finalize_requested"]:
            # 사용자의 마지막 메시지를 확인
            if state["messages"]:
                user_content = state["messages"][-1].content.lower()
                if "yes" in user_content or "네" in user_content:
                    return {
                        "messages": [],
                        "chat_history": state["chat_history"],
                        "completion_ratio": state["completion_ratio"],
                        "finalize_requested": True
                    }
                elif "no" in user_content or "아니오" in user_content:
                    messages_out.append(SystemMessage(content="진정서 작성을 취소하였습니다. 추가로 도와드릴 사항이 있으면 말씀해주세요."))
            else:
                # 정보가 충분하나 사용자의 응답이 없는 경우
                msg = SystemMessage(
                    content="진정서에 필요한 정보가 거의 준비된 것 같습니다. 작성하시겠습니까? (yes/no)"
                )
                messages_out.append(msg)
        
        return {
            "messages": messages_out,
            "chat_history": state["chat_history"],
            "completion_ratio": state["completion_ratio"],
            "finalize_requested": state["finalize_requested"]
        }
    
    # 그래프(워크플로우) 구성
    workflow = StateGraph(WriterAgentState)
    
    # 노드 등록
    workflow.add_node("writer_agent", writer_agent_node)
    workflow.add_node("tools", tool_node)
    workflow.add_node("update_ratio", update_completion_ratio)
    workflow.add_node("finalize_decision", finalize_decision_node)
    
    # 시작점 설정
    workflow.set_entry_point("writer_agent")
    
    # writer_agent -> tools 또는 update_ratio
    def next_step_after_writer(state: WriterAgentState) -> str:
        if hasattr(state["messages"][-1], "tool_calls") and state["messages"][-1].tool_calls:
            return "tools"
        elif state["finalize_requested"]:
            return "writer_agent"
        else:
            return "update_ratio"
    
    workflow.add_conditional_edges(
        "writer_agent",
        next_step_after_writer,
        {
            "tools": "tools",
            "update_ratio": "update_ratio",
            "writer_agent": "writer_agent"
        }
    )
    
    # tools -> writer_agent
    workflow.add_edge("tools", "writer_agent")
    
    # update_ratio -> finalize_decision
    workflow.add_edge("update_ratio", "finalize_decision")
    
    # finalize_decision -> writer_agent 또는 END
    workflow.add_conditional_edges(
        "finalize_decision",
        lambda x: "writer_agent" if not x["finalize_requested"] else "writer_agent",
        {
            "writer_agent": "writer_agent",
            "END": END
        }
    )
    
    return workflow.compile()
