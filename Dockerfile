# 베이스 이미지: Python 3.10 슬림 버전
FROM python:3.10-slim

# 필수 패키지 설치 (시스템 종속 항목)
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# 작업 디렉토리 생성 및 설정
WORKDIR /app

# requirements.txt 복사 후 설치
COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

# 앱 소스 전체 복사
COPY . .

# Streamlit 실행 포트 설정
EXPOSE 8501

# 앱 실행 명령
CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.enableCORS=false"]
