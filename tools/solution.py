from langchain_core.tools import BaseTool
from typing import Type, Optional, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime
from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from langchain_core.callbacks import (
    AsyncCallbackManagerForToolRun,
    CallbackManagerForToolRun,
)
from dotenv import load_dotenv
import asyncio
from tools.output_parser import solution_parser

load_dotenv()

class SolutionInput(BaseModel):
    message: str = Field(description="사용자의 입력 메시지")

class Solution(BaseTool):
    name: str = "solution_tool"
    description: str = "사기유형에 따른 해결방안을 제시하는 도구입니다."
    args_schema: Type[BaseModel] = SolutionInput
    return_direct: bool = False
    llm: ChatOpenAI = Field(
        default_factory=lambda: ChatOpenAI(model="gpt-4o-mini", temperature=0.1)
    )

    def _run(
        self,
        message: str,
        run_manager: Optional[CallbackManagerForToolRun] = None,
    ) -> Dict[str, Any]:
        """동기 실행을 위한 메서드"""
        return asyncio.run(self._arun(message, run_manager))

    async def _arun(
        self,
        message: str,
        run_manager: Optional[AsyncCallbackManagerForToolRun] = None,
    ) -> Dict[str, Any]:
        """비동기 실행을 위한 메서드"""
        try:
            prompt = ChatPromptTemplate.from_template(
                """사용자의 상황을 심층적으로 분석하여 실질적이고 구체적인 해결방안을 제시해주세요.

                다음 사항들을 중점적으로 고려해주세요:
                - 즉각적인 피해 방지를 위한 긴급 조치사항
                - 법적 대응을 위한 단계별 실행 계획
                - 추가 피해 예방을 위한 구체적인 안전장치
                - 필요한 증거자료 확보 및 보관 방법
                - 도움을 받을 수 있는 전문기관 및 법률 지원
                - 심리적 회복을 위한 지원 방안
                - 유사 사기 수법 예방을 위한 교훈과 조언
                - 피해 금액 회수를 위한 전략적 접근
                - 장기적 관점의 재발 방지 대책

                각 해결방안에 대해 구체적인 실행 단계와 예상되는 결과, 주의사항을 포함해 설명해주세요.

                사용자 메시지: {message}
                
                위 요소들을 종합적으로 고려하여 체계적이고 실현 가능한 해결방안을 제시해주세요.
                
                {format_instructions}
                """
            )
            
            chain = prompt | self.llm | solution_parser
            
            response = await chain.ainvoke({
                "message": message,
                "format_instructions": solution_parser.get_format_instructions()
            })
            
            return response
            
        except Exception as e:
            return {"error": f"해결방안 생성 중 오류 발생: {str(e)}"}