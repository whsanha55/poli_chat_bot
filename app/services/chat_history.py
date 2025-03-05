from typing import Dict, List
from app.dto.chat import ChatMessage

class ChatHistory:
    def __init__(self):
        self.histories: Dict[str, List[ChatMessage]] = {}
    
    def add_message(self, session_id: str, message: ChatMessage):
        if session_id not in self.histories:
            self.histories[session_id] = []
        self.histories[session_id].append(message)
    
    def get_history(self, session_id: str) -> List[ChatMessage]:
        return self.histories.get(session_id, [])
    
    def clear_history(self, session_id: str):
        if session_id in self.histories:
            del self.histories[session_id]

chat_history = ChatHistory() 