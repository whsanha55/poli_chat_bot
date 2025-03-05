# state.py (수정된 예시)

from typing import TypedDict, Annotated, Union, Sequence
from langchain_core.agents import AgentAction, AgentFinish
from langchain.agents.output_parsers.tools import ToolAgentAction
from langchain_core.messages import BaseMessage
import operator

class AgentState(TypedDict):
    # 최종 LLM에 전달할(또는 참조할) 전체 메시지
    messages: list[BaseMessage]

    # 사용자로부터의 입력 문자열
    input: str

    # 과거 대화 기록 (폴리/레터 내부적으로 사용할 수 있음)
    chat_history: list[BaseMessage]
    
    # 에이전트 실행 결과 (도구 액션, 최종 출력 등)
    agent_outcome: Union[AgentAction, list, ToolAgentAction, AgentFinish, None]
    
    # 중간 단계의 액션과 관찰 결과 리스트
    intermediate_steps: Annotated[
        list[Union[tuple[AgentAction, str], tuple[ToolAgentAction, str]]], 
        operator.add
    ]
