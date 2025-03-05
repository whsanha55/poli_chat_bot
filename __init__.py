# main.py

from supervisoragent import create_supervisor_agent, SupervisorState
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
import json

def main():
    # SupervisorAgent 워크플로우 생성
    supervisor_workflow = create_supervisor_agent()
    
    # 초기 상태 설정
    initial_state: SupervisorState = {
        "messages": [],  # 초기 메시지는 비어있음
        "chat_history": [],  # 초기 대화 기록은 비어있음
        "active_agent": None  # 초기에는 활성화된 에이전트가 없음
    }
    
    print("안녕하세요! 범죄사기피해 상담 시스템입니다.")
    print("원하시는 질문/메시지를 입력해보세요. (종료: exit)")
    
    while True:
        user_input = input("\n사용자: ")
        if user_input.lower() == "exit":
            print("종료합니다. 감사합니다.")
            break
        
        # 사용자 입력을 메시지로 추가
        user_message = HumanMessage(content=user_input)
        initial_state["messages"].append(user_message)
        initial_state["chat_history"].append({"role": "user", "content": user_input})
        
        try:
            # SupervisorAgent 워크플로우 실행
            result = supervisor_workflow(initial_state)
            
            # 시스템 메시지 출력
            for message in result["messages"]:
                if isinstance(message, SystemMessage):
                    print(f"시스템: {message.content}")
                elif isinstance(message, AIMessage):
                    print(f"시스템: {message.content}")
                else:
                    print(f"시스템: {message.content}")
            
            # 대화 기록 업데이트
            for message in result["messages"]:
                if isinstance(message, AIMessage) or isinstance(message, SystemMessage):
                    initial_state["chat_history"].append({"role": "assistant", "content": message.content})
            
            # active_agent 업데이트
            initial_state["active_agent"] = result.get("active_agent", None)
        
        except KeyError as e:
            print(f"시스템: 죄송합니다. 오류가 발생했습니다. 다시 시도해주세요.")
            print(f"로그: {e}")

if __name__ == "__main__":
    main()
