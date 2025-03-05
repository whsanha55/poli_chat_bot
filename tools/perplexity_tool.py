import asyncio
from typing import Any, Dict, Optional
from langchain_core.tools import BaseTool
from langchain_teddynote.models import ChatPerplexity
from pydantic import BaseModel, Field
from dotenv import load_dotenv
from langchain_core.callbacks import AsyncCallbackManagerForToolRun

load_dotenv()

class PerplexityQAToolInput(BaseModel):
    query: str = Field(..., description="사용자의 질의 내용")

class PerplexityQATool(BaseTool):
    name: str = "perplexity_qa_tool"
    description: str = "사용자 질의에 맞는 진정서 관련 정보를 검색 후 제공하는 도구"
    perplexity: ChatPerplexity = Field(default=None, exclude=True)

    def __init__(self, **data):
        super().__init__(**data)
        self.perplexity = ChatPerplexity(
            model="llama-3.1-sonar-large-128k-online",
            temperature=0.2,
            top_p=0.9,
            search_domain_filter=["perplexity.ai"],
            return_images=False,
            return_related_questions=True,
            top_k=0,
            streaming=False,
            presence_penalty=0,
            frequency_penalty=1,
        )

    def _run(self, query: str) -> Dict[str, Any]:
        """동기 실행 메서드"""
        return asyncio.run(self._arun(query))

    async def _arun(self, query: str, run_manager: Optional[AsyncCallbackManagerForToolRun] = None) -> Dict[str, Any]:
        """비동기 실행 메서드"""
        response = await self.perplexity.ainvoke(query)
        return {"content": response.content}

    async def ainvoke(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """args를 dict로 받고, "query" 키만 뽑아서 비동기 실행"""
        query = args.get("query", "")
        return await self._arun(query)