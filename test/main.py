import asyncio
from agents.supervisior import create_supervisor_agent
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from utils.logging_utils import log_agent_routing, log_tool_usage
import logging

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

async def chat_loop(app):
    """대화 루프를 실행하는 비동기 함수"""
    print("안녕하세요! 범죄사기피해 상담 시스템입니다.")
    print("원하시는 질문/메시지를 입력해보세요. (종료: exit)")

    # 초기 상태 설정
    state = {
        "messages": [],
        "chat_history": [],
        "next": "START"
    }

    while True:
        try:
            user_input = input("\n사용자: ").strip()
            if user_input.lower() in ["exit", "quit"]:
                print("대화를 종료합니다.")
                break

            # 사용자 메시지 추가
            state["messages"].append(HumanMessage(content=user_input))

            # 에이전트 실행
            new_state = await app.ainvoke(state)
            state.update(new_state)

            # 응답 출력
            if state["messages"]:
                last_message = state["messages"][-1]
                if isinstance(last_message, (HumanMessage, AIMessage, SystemMessage)):
                    sender = getattr(last_message, "name", "assistant")
                    content = last_message.content
                else:
                    sender = last_message.get("role", "assistant")
                    content = last_message.get("content", "")
                print(f"\n{sender}: {content}")

        except Exception as e:
            logger.error(f"Error during chat: {e}")
            print("\n시스템: 죄송합니다. 오류가 발생했습니다. 다시 시도해주세요.")

def main():
    """메인 함수"""
    app = create_supervisor_agent()
    asyncio.run(chat_loop(app))

if __name__ == "__main__":
    main()
