from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from app.dto.check import CompletionCheckRequest, CompletionAnalysis
from typing import Dict
import json


class CheckService:
    def __init__(self):
        # JSON 출력 파서 설정
        self.parser = JsonOutputParser(pydantic_object=CompletionAnalysis)
        
        # 프롬프트 템플릿 정의
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", """
            당신은 사기 피해 진정서 작성에 필요한 정보를 분석하는 전문가입니다.
            제공된 대화 내용에서 다음 필수 항목들의 존재 여부를 확인하고 완성도를 평가해주세요:

            필수 항목:
            1. 신청인 정보 (성명, 생년월일, 주소, 연락처) - 25%
            2. 피진정인 정보 (상대방 정보, 계좌번호 등) - 25%
            3. 피해 내용 (사기 유형, 날짜, 금액, 경위) - 35%
            4. 증거자료 존재 여부 - 15%

            각 항목의 존재 여부와 구체성을 검토하여 백분율로 평가하세요.
            총점이 80% 이상이면 fulfilled를 true로 설정하세요.

            대화 내용을 분석하여 각 항목의 존재 여부와 완성도를 평가한 후,
            다음 형식의 JSON으로 응답해주세요:
            {{
                "fulfilled": boolean,
                "percentage": float (0-100)
            }}

            {format_instructions}
            """),
            ("human", "다음 대화 내용을 분석해주세요:\n\n{chat_history}")
        ])
        
        # LLM 모델 설정
        self.model = ChatOpenAI(
            model="gpt-4o-mini",
            temperature=0
        )
        
        # 체인 구성
        self.chain = self.prompt | self.model | self.parser

    async def check_completion(self, request: CompletionCheckRequest) -> CompletionAnalysis:
        """
        대화 내용을 분석하여 진정서 작성 가능 여부와 완성도를 반환합니다.
        
        Args:
            request (CompletionCheckRequest): 분석할 대화 내용을 포함한 요청 객체
            
        Returns:
            CompletionAnalysis: fulfilled(bool)와 percentage(float) 포함
        """
        try:
            # 프롬프트에 파서 지침 추가
            format_instructions = self.parser.get_format_instructions()
            
            # 프롬프트 실행
            response = await self.model.ainvoke(
                self.prompt.format_messages(
                    chat_history=request.chat_history,
                    format_instructions=format_instructions
                )
            )
            
            # JSON 응답 파싱
            try:
                result = json.loads(response.content)
                
                # CompletionAnalysis 객체 생성 및 반환
                return CompletionAnalysis(
                    fulfilled=bool(result.get("fulfilled", False)),
                    percentage=float(result.get("percentage", 0.0))
                )
                
            except json.JSONDecodeError as e:
                raise ValueError(f"JSON 파싱 실패: {str(e)}")
            
        except Exception as e:
            raise ValueError(f"대화 내용 분석 중 오류 발생: {str(e)}")

check_service = CheckService()