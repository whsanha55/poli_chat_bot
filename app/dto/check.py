from pydantic import BaseModel
from pydantic import Field
from typing import Optional, Dict
class CompletionCheckRequest(BaseModel):
    chat_history: str = Field(..., description="대화 내용",
                              
                            example="""
                            사용자: 인터넷 쇼핑몰에서 사기를 당했어요. 상품을 결제했는데 배송도 안 되고 연락이 두절됐어요.
                            챗봇: 불편을 드려 죄송합니다. 해당 쇼핑몰의 이름과 결제하신 날짜를 알려주시겠어요?
                                
                            사용자: 쇼핑몰 이름은 '스마트마켓'이고 2024년 3월 18일에 결제했어요. 45만원 상당의 전자제품이었어요.
                            챗봇: 네, 확인감사합니다. 결제 방법은 어떻게 되시나요? 그리고 판매자와의 연락 기록이 있으신가요?
                            """)

class CompletionAnalysis(BaseModel):
    fulfilled: bool = Field(description="진정서 작성 가능 여부 (80% 이상일 때 True)")
    percentage: float = Field(description="진정서 작성을 위한 정보 완성도 (0-100)")