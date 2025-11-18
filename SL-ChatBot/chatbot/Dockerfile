FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    curl \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install dependencies
COPY chatbot/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
# 주 코드와 설정, 프롬프트 복사 (컨택스트: SL-ChatBot 루트)
COPY chatbot/src ./src
COPY chatbot/config.yaml .
COPY config ./config
COPY prompts ./prompts

# Expose port
EXPOSE 8003

# Run the application
CMD ["python3", "src/api_server.py"]
