from fastapi import APIRouter, HTTPException
from app.dto.check import CompletionCheckRequest, CompletionAnalysis
from app.services.check import check_service
from typing import Dict

router = APIRouter(
    prefix="/api/v1",
    tags=["check"]
)

@router.post(
    "/check-completion",
    response_model=CompletionAnalysis,
    summary="대화 내용 기반 진정서 작성 가능 여부 분석",
    description="""
    대화 내용을 분석하여 진정서 작성에 필요한 정보의 완성도를 반환합니다.
    
    - 신청인 정보 (25%)
    - 피진정인 정보 (25%)
    - 피해 내용 (35%)
    - 증거자료 (15%)
    
    총 80% 이상일 경우 진정서 작성이 가능합니다.
    """,
    responses={
        200: {
            "description": "성공적으로 분석된 결과",
            "content": {
                "application/json": {
                    "example": {
                        "fulfilled": True,
                        "percentage": 85.0
                    }
                }
            }
        },
        422: {
            "description": "잘못된 요청 형식",
            "content": {
                "application/json": {
                    "example": {"detail": "대화 내용이 비어있습니다."}
                }
            }
        },
        500: {
            "description": "서버 내부 오류",
            "content": {
                "application/json": {
                    "example": {"detail": "대화 내용 분석 중 오류가 발생했습니다."}
                }
            }
        }
    }
)
async def check_completion(request: CompletionCheckRequest) -> CompletionAnalysis:
    """
    대화 내용을 분석하여 진정서 작성 가능 여부와 완성도를 반환합니다.
    
    Args:
        request (CompletionCheckRequest): 분석할 대화 내용
        
    Returns:
        CompletionAnalysis: 진정서 작성 가능 여부와 완성도 정보
    """
    try:
        return await check_service.check_completion(request)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"대화 내용 분석 중 오류가 발생했습니다: {str(e)}"
        )