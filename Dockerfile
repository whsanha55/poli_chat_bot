# Python 3.11 이미지를 기반으로 사용
FROM python:3.11-slim

# 작업 디렉토리 설정
WORKDIR /app

# 시스템 패키지 업데이트 및 필요한 패키지 설치
RUN apt-get update && apt-get install -y \
    build-essential \
    git \
    && rm -rf /var/lib/apt/lists/*

# requirements.txt 파일 복사 및 의존성 설치
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 애플리케이션 코드 복사
COPY . .

# 환경 변수 설정
ENV PYTHONPATH=/app
ENV AWS_DEFAULT_REGION=${AWS_REGION}
ENV AWS_ACCESS_KEY_ID=${AWS_ACCESS_KEY_ID}
ENV AWS_SECRET_ACCESS_KEY=${AWS_SECRET_ACCESS_KEY}
ENV OPENAI_API_KEY=${OPENAI_API_KEY}
ENV YOUTUBE_API_KEY=${YOUTUBE_API_KEY}
ENV TAVILY_API_KEY=${TAVILY_API_KEY}
ENV PPLX_API_KEY=${PPLX_API_KEY}
ENV ALPHAVANTAGE_API_KEY=${ALPHAVANTAGE_API_KEY}
ENV PSQL_USERNAME=${PSQL_USERNAME}
ENV PSQL_PASSWORD=${PSQL_PASSWORD}
ENV PSQL_HOST=${PSQL_HOST}
ENV PSQL_PORT=${PSQL_PORT}
ENV PSQL_DATABASE=${PSQL_DATABASE}
ENV PSQL_SSLMODE=${PSQL_SSLMODE}
ENV NCP_CLOVASTUDIO_API_KEY=${NCP_CLOVASTUDIO_API_KEY}
ENV NCP_APIGW_API_KEY=${NCP_APIGW_API_KEY}

# 포트 설정
EXPOSE 8000

# 애플리케이션 실행
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"] 