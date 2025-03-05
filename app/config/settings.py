from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    APP_TITLE: str = "Poli Agent API"
    APP_DESCRIPTION: str = "사기 피해 신고 및 진정서 작성을 도와주는 AI 어시스턴트 API"
    APP_VERSION: str = "1.0.0"

settings = Settings()