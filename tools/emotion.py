from pydantic import BaseModel, Field
from typing import Dict, Any, Optional, Type
from datetime import datetime
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.tools import BaseTool
from langchain_core.callbacks import (
    AsyncCallbackManagerForToolRun,
    CallbackManagerForToolRun,
)
from langchain_openai import ChatOpenAI
from tools.output_parser import emotion_parser
from dotenv import load_dotenv
import asyncio

load_dotenv()

class EmotionInput(BaseModel):
    message: str = Field(description="사용자의 입력 메시지")

class Emotion(BaseTool):
    name: str = "emotion_tool"
    description: str = "사용자 질문에서 감정 상태를 분석하는 도구입니다."
    args_schema: Type[BaseModel] = EmotionInput
    return_direct: bool = False
    llm: ChatOpenAI = Field(
        default_factory=lambda: ChatOpenAI(model="gpt-4o-mini", temperature=0)
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
            emotion_prompt = ChatPromptTemplate.from_template(
                """사용자의 메시지를 바탕으로 감정 상태를 분석해주세요.

                사용자 메시지: {message}

                감정 상태를 최대한 구체적이고 체계적으로 분석하여 제시해주세요.
                
                {format_instructions}
                """
            )
            
            emotion_chain = emotion_prompt | self.llm | emotion_parser
            
            emotion_response = await emotion_chain.ainvoke({
                "message": message,
                "format_instructions": emotion_parser.get_format_instructions()
            })

            return emotion_response
              
        except Exception as e:
            return {"error": f"감정 분석 중 오류 발생: {str(e)}"}

