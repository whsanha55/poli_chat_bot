from fastapi import APIRouter, HTTPException
from app.dto.letter import LetterRequest, LetterResponse
from app.services.letter_service import letter_service

router = APIRouter(
    prefix="/api/v1",
    tags=["letter"]
)
@router.post(
    "/letter/generate",
    response_model=LetterResponse,
    summary="진정서 생성",
    description="대화 내용을 바탕으로 진정서를 생성합니다.",
    responses={
        200: {
            "description": "성공적으로 생성된 진정서",
            "content": {
                "application/json": {
                    "example": {"content": "[진 정 서]\n접수기관: ○○경찰서..."}
                }   
            }
        },
        500: {
            "description": "서버 내부 오류",
            "content": {
                "application/json": {
                    "example": {"detail": "진정서 생성 중 오류가 발생했습니다."}
                }
            }
        }
    }
)
async def generate_letter(request: LetterRequest):
    """
    대화 내용을 바탕으로 진정서를 생성합니다.

    - **request**: 대화 내용과 세션 ID
    """
    try:
        return await letter_service.generate_letter(request.chat_content)
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"진정서 생성 중 오류가 발생했습니다: {str(e)}"
        ) 