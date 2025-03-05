from fastapi import APIRouter, HTTPException
from app.dto.chat import ChatRequest, ChatResponse
from app.services.chat_service import chat_service
from typing import Dict

router = APIRouter(
    prefix="/api/v1",
    tags=["chat"]
)

@router.post(
    "/chat",
    response_model=ChatResponse,
    summary="채팅 메시지 처리",
    description="""
    사용자의 채팅 메시지를 처리하고 AI 응답을 반환합니다.
    
    - 사기 피해 상담
    - 진정서 작성 지원
    - 법률 정보 제공
    """,
    responses={
        200: {
            "description": "성공적으로 처리된 응답",
            "content": {
                "application/json": {
                    "example": {
                        "messages": [
                            {
                                "role": "user",
                                "content": "저를 아시나요?"
                            },
                            {
                                "role": "assistant",
                                "content": "안녕하세요. 저는 사기 피해 상담을 도와드리는 AI 어시스턴트입니다. 어떤 도움이 필요하신가요?"
                            }
                        ]
                    }
                }
            }
        },
        500: {
            "description": "서버 내부 오류",
            "content": {
                "application/json": {
                    "example": {"detail": "Internal server error"}
                }
            }
        }
    }
)
async def chat_endpoint(request: ChatRequest):
    """
    채팅 메시지를 처리하고 AI 응답을 반환합니다.

    - **request**: 사용자의 채팅 메시지 목록과 세션 ID
    """
    try:
        return await chat_service.process_chat(
            messages=request.messages,
            session_id=request.session_id
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get(
    "/health",
    summary="헬스 체크",
    description="API 서버의 상태를 확인합니다.",
    response_model=Dict[str, str],
    responses={
        200: {
            "description": "서버가 정상적으로 동작 중",
            "content": {
                "application/json": {
                    "example": {"status": "healthy"}
                }
            }
        }
    }
)
async def health_check():
    """API 서버의 상태를 확인합니다."""
    return {"status": "healthy"} 