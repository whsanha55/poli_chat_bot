#!/bin/bash

# 실행할 컨테이너 & 이미지 이름 설정
CONTAINER_NAME="poli_chat_bot"
IMAGE_NAME="poli_chat_bot_python"

# 현재 디렉토리의 변경 사항을 추적하기 위한 해시값 저장
HASH_FILE=".last_build_hash"
CURRENT_HASH=$(find . -type f -not -path "./.git/*" -not -name "$HASH_FILE" -exec sha256sum {} \; | sort | sha256sum | awk '{print $1}')

# 1️⃣ 최신 코드 가져오기 (GitHub Pull)
echo "📥 Git에서 최신 코드 가져오는 중..."
git pull origin main

# 2️⃣ 기존 컨테이너가 실행 중이면 중지 후 삭제
if [ "$(docker ps -q -f name=$CONTAINER_NAME)" ]; then
    echo "⚠ 기존 컨테이너 ($CONTAINER_NAME) 중지 중..."
    docker stop $CONTAINER_NAME
    docker rm $CONTAINER_NAME
fi

# 3️⃣ 파일 변경이 없으면 Docker Build 생략
if [ -f "$HASH_FILE" ] && [ "$(cat $HASH_FILE)" == "$CURRENT_HASH" ]; then
    echo "✅ 파일 변경 없음 → 기존 이미지 그대로 사용"
else
    echo "🚀 변경 감지됨 → Docker 이미지 빌드 중..."
    docker build -t $IMAGE_NAME .
    echo "$CURRENT_HASH" > "$HASH_FILE"  # 새 해시 저장
fi

# 4️⃣ 새로운 컨테이너 실행
echo "✅ 새로운 컨테이너 실행: $CONTAINER_NAME"
docker run -it -d  --rm --env-file /home/poli_chat_bot/.env -p 9000:8000 --name $CONTAINER_NAME $IMAGE_NAME


# 실행된 컨테이너 로그 출력
echo "📜 실행된 컨테이너 로그 확인:"
docker logs -f $CONTAINER_NAME