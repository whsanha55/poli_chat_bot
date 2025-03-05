from typing import List, Dict
from langchain.output_parsers import PydanticOutputParser
from pydantic import BaseModel, Field

class DetailAnalysis(BaseModel):
    incident_time: str = Field(description="사건 발생 시점")
    evidence_list: List[str] = Field(description="증거 자료 목록")
    previous_actions: List[str] = Field(description="기존에 취한 조치들")
    involved_parties: List[str] = Field(description="관련된 당사자들")
    financial_impact: Dict[str, float] = Field(description="금전적 피해 상세(원화, 단위표기)")
    additional_notes: List[str] = Field(description="추가 참고사항")
    fraud_type: str = Field(description="사기 수법의 유형과 특징")
    damage_scale: str = Field(description="피해 규모와 심각성")
    victim_status: str = Field(description="피해자의 현재 상황")
    urgent_actions: List[str] = Field(description="즉각적인 대응이 필요한 사항")
    legal_issues: List[str] = Field(description="관련 법적 이슈와 고려사항") 
    additional_risk: str = Field(description="추가 피해 발생 가능성")

class SolutionInformation(BaseModel):
    immediate_actions: List[str] = Field(description="즉시 필요한 조치 사항")
    legal_actions: List[str] = Field(description="가능한 법적 대응 방안")
    prevention_steps: List[str] = Field(description="추가 피해 예방을 위한 조치")
    required_documents: List[str] = Field(description="필요한 서류나 증빙자료")
    support_resources: List[str] = Field(description="도움을 받을 수 있는 기관이나 리소스")
    timeline: Dict[str, str] = Field(description="해결 과정 타임라인")

class EmotionalResponse(BaseModel):
    emotional_state: str = Field(description="사용자의 현재 감정 상태 (예: 불안, 분노, 슬픔, 절망)")
    speech_style: str = Field(description="사용자의 말투와 어조 특성 (예: 격앙된, 냉정한, 혼란스러운)")
    recommended_tone: str = Field(description="상황에 적절한 대화 톤 (예: 차분한, 공감적인, 전문적인)")
    communication_strategy: Dict[str, str] = Field(description="감정 상태별 의사소통 전략 (어휘 선택, 말의 속도, 어조 등)")
    empathy_points: List[str] = Field(description="사용자의 감정에 공감하고 이해를 표현할 수 있는 핵심 포인트")
    response_guidelines: Dict[str, List[str]] = Field(description="감정 상태에 따른 추천 응답 방식과 피해야 할 표현")
    support_approach: str = Field(description="감정 상태를 고려한 심리적 지원 접근 방식")

# 파서 인스턴스 생성
detail_parser = PydanticOutputParser(pydantic_object=DetailAnalysis)
solution_parser = PydanticOutputParser(pydantic_object=SolutionInformation)
emotion_parser = PydanticOutputParser(pydantic_object=EmotionalResponse)
