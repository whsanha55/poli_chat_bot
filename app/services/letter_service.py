from langchain_openai import ChatOpenAI
from langchain.schema import SystemMessage, HumanMessage
from typing import Dict
from datetime import datetime

class LetterService:
    def __init__(self):
        self.llm = ChatOpenAI(model="gpt-4", temperature=0.2)
        
    async def generate_letter(self, chat_content: str) -> Dict[str, str]:
        """진정서를 생성하는 서비스 메소드"""
        
        # 현재 날짜 생성
        current_date = datetime.now().strftime("%Y년 %m월 %d일")
        
        system_prompt = SystemMessage(content=f"""
        당신은 진정서 작성 전문가입니다. 제공된 대화 내용을 분석하여 아래 형식의 진정서를 작성해주세요.
        현재 날짜는 {current_date} 입니다. 이 날짜를 진정서 말미에 사용하세요.


        '''
        [진 정 서]
        접수기관: ○○경찰서(또는 ○○지방경찰청 사이버수사대)

        신청인(피해자)
            성명: (대화에서 추출)
            주민등록번호(또는 생년월일): (대화에서 추출)
            주소: (대화에서 추출)
            연락처: (대화에서 추출)

        피진정인(피의자)
            성명(또는 닉네임/아이디): (대화에서 추출 또는 '불상')
            아이디/사이트명: (대화에서 추출)
            기타 가능한 신원정보 및 특이사항: (대화에서 추출)

        진정 내용
            사건 유형 정보
            범죄 유형: (대화 내용 기반 판단)
            세부 유형: (구체적인 사기 유형)

        상세 피해 상황
            피해장소: (플랫폼/사이트 정보)
            진정취지: (대화 내용 기반 작성)
            피해상황: (구체적인 피해 내용)
            피해 발생 일시: (대화에서 추출)
            피해 발생 경로: (구체적인 사건 경위)
            해당 행위로 인한 피해: (금전/정신적 피해 등)
            확보 증거 자료: (대화에서 언급된 증거)

        결론: (진정 의견 정리)

        {current_date}
        신청인: ○○○ (서명 또는 인)
        '''
        
        주의사항:
        1. 대화 내용에서 언급된 모든 구체적인 정보를 최대한 활용하세요.
        2. 언급되지 않은 정보는 "불상" 또는 "미상"으로 처리하세요.
        3. 시간, 금액, 계좌번호 등 구체적인 정보는 정확히 기재하세요.
        4. 진정서 어투는 공식적이고 격식있게 작성하세요.
        5. 진정서 날짜는 반드시 오늘 날짜({current_date})를 사용하세요.
        """)
        
        human_prompt = HumanMessage(content=f"다음 대화 내용을 바탕으로 진정서를 작성해주세요:\n\n{chat_content}")
        
        response = await self.llm.ainvoke([system_prompt, human_prompt])
        
        return {"content": response.content}

letter_service = LetterService() 