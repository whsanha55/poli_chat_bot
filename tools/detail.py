# 설명: 사용자 메시지에서 상세 정보를 수집하고 분석하는 도구
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
from tools.output_parser import detail_parser
import asyncio
from dotenv import load_dotenv

load_dotenv()


class FinancialImpact(BaseModel):
    total_loss: float
    currency: str

class DetailCollectorInput(BaseModel):
    message: str = Field(description="사용자의 입력 메시지")
    financial_impact: Optional[FinancialImpact] = Field(default=None)

class Detail(BaseTool):
    name: str = "detail_tool"
    description: str = "사용자 질문에서 정보를 추출하는 도구입니다."
    args_schema: Type[BaseModel] = DetailCollectorInput
    return_direct: bool = False
    llm: ChatOpenAI = Field(
        default_factory=lambda: ChatOpenAI(model="gpt-4o-mini", temperature=0)
    )

    def _run(
        self,
        message: str,
        financial_impact: Optional[FinancialImpact] = None,
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
            # 통합된 상세 정보 및 상황 분석 프롬프트
            detail_prompt = ChatPromptTemplate.from_template(
                """사용자의 메시지를 바탕으로 사기 피해 사건의 상세 정보와 상황을 분석해주세요.

                다음 항목들을 중점적으로 파악해주세요:
                - 사건의 시간적 흐름과 발생 시점을 구체적으로 파악
                - 보유하고 있는 증거자료(통화내역, 문자메시지, 계좌내역, 녹음파일 등) 목록화
                - 지금까지 취한 대응 조치들을 시간순으로 정리
                - 관련된 모든 당사자들(피해자, 가해자, 목격자, 기관 등)의 정보 수집
                - 금전적 피해 내역을 항목별로 구체적으로 산출
                - 법적 대응이나 피해 구제에 도움될 만한 추가 정보들을 수집
                - 사기 수법의 유형과 특징
                - 피해 규모와 심각성
                - 피해자의 현재 상황
                - 즉각적인 대응이 필요한 사항
                - 관련 법적 이슈와 고려사항
                - 추가 피해 발생 가능성

                사용자 메시지: {message}

                위 정보들을 최대한 구체적이고 체계적으로 분류하여 제시해주세요.
                
                {format_instructions}
                """
            )
            
            # 통합된 프롬프트 체인
            detail_chain = detail_prompt | self.llm | detail_parser
            
            # 통합 분석 실행
            detail_response = await detail_chain.ainvoke({
                "message": message,
                "format_instructions": detail_parser.get_format_instructions()
            })

            return detail_response
              
        except Exception as e:
            return {"error": f"상세 정보 수집 중 오류 발생: {str(e)}"}

