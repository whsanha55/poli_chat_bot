from langchain_core.messages import HumanMessage, SystemMessage
from typing import List, Dict
from app.dto.chat import ChatMessage, ChatResponse
from agents.supervisior import create_supervisor_agent
from app.services.chat_history import chat_history
from uuid import uuid4

class ChatService:
    def __init__(self):
        self.supervisor = create_supervisor_agent()
    
    async def process_chat(self, messages: List[ChatMessage], session_id: str = None) -> ChatResponse:
        if session_id is None:
            session_id = str(uuid4())
            
        # 이전 채팅 기록 가져오기
        history = chat_history.get_history(session_id)
        
        # 새 메시지 추가
        for message in messages:
            chat_history.add_message(session_id, message)
        
        # 모든 메시지를 LangChain 형식으로 직접 변환
        langchain_messages = []
        for msg in history + messages:
            message_type = HumanMessage if msg.role.lower() == "user" else SystemMessage
            langchain_messages.append(message_type(content=msg.content))
        
        # 슈퍼바이저 에이전트 실행
        result = self.supervisor.invoke({
            "messages": langchain_messages,
            "chat_history": langchain_messages,  # 동일한 형식 사용
            "next": "supervisor"
        })
        
        # 응답 변환 및 히스토리에 추가
        response_message = ChatMessage(
            role="assistant",
            content=result["messages"][-1].content  # 마지막 메시지만 사용
        )
        chat_history.add_message(session_id, response_message)
            
        return ChatResponse(
            messages=[response_message],  # 단일 응답 메시지만 반환
            session_id=session_id
        )

chat_service = ChatService()