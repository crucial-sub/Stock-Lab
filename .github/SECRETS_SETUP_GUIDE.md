# GitHub Secrets 설정 가이드

CI/CD 파이프라인에서 사용할 환경 변수를 GitHub Secrets로 등록하는 방법입니다.

## 1. GitHub Secrets 등록 방법

1. GitHub 저장소 페이지로 이동
2. **Settings** → **Secrets and variables** → **Actions** 클릭
3. **New repository secret** 버튼 클릭
4. Name과 Value를 입력하고 **Add secret** 클릭

## 2. 필수 Secrets 목록

### AWS 관련 (현재 설정됨)
```
AWS_ACCESS_KEY_ID=your-aws-access-key-id
AWS_SECRET_ACCESS_KEY=your-aws-secret-access-key
ASG_NAME=your-auto-scaling-group-name
LAUNCH_TEMPLATE_NAME=your-launch-template-name
TARGET_GROUP_ARN=your-target-group-arn
ALB_DNS_URL=http://your-alb-dns-name
```

### Database 관련
```
DATABASE_URL=postgresql+asyncpg://username:password@host:port/database
DATABASE_SYNC_URL=postgresql://username:password@host:port/database
POSTGRES_USER=your-postgres-user
POSTGRES_PASSWORD=your-postgres-password
POSTGRES_DB=stock_lab_investment_db
POSTGRES_PORT=5432
```

### Redis 관련
```
REDIS_URL=redis://your-redis-host:6379/0
REDIS_HOST=your-redis-host
REDIS_PORT=6379
REDIS_PASSWORD=your-redis-password (없으면 빈 값)
```

### Backend API 관련
```
SECRET_KEY=your-jwt-secret-key-min-32-characters
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
```

### CORS 설정
```
BACKEND_CORS_ORIGINS=["http://localhost:3000","https://your-production-domain.com"]
```

### Frontend 관련
```
NEXT_PUBLIC_API_BASE_URL=https://your-alb-dns-name/api/v1
```

### 선택적 설정
```
LOG_LEVEL=INFO
DEBUG=False
ENABLE_CACHE=True
CACHE_TTL_SECONDS=3600
```

## 3. Secret Key 생성 방법

JWT SECRET_KEY는 강력한 랜덤 문자열이어야 합니다:

```bash
# Python 사용
python -c "import secrets; print(secrets.token_hex(32))"

# OpenSSL 사용
openssl rand -hex 32
```

## 4. 환경별 Secrets (선택사항)

개발/스테이징/프로덕션 환경을 분리하려면 Environment Secrets 사용:

1. **Settings** → **Environments** → **New environment**
2. 환경 이름 입력 (예: production, staging)
3. 해당 환경에 특화된 secrets 추가

워크플로우에서 사용:
```yaml
jobs:
  deploy:
    runs-on: ubuntu-latest
    environment: production  # 여기서 환경 지정
    steps:
      - name: Use environment secret
        run: echo ${{ secrets.DATABASE_URL }}
```

## 5. 보안 주의사항

- Secrets는 절대 로그에 출력되지 않도록 주의
- Production 환경의 secrets는 개발 환경과 다른 값 사용
- 정기적으로 secrets 교체 (특히 SECRET_KEY)
- `.env` 파일은 절대 Git에 커밋하지 않기 (이미 .gitignore에 포함됨)

## 6. Secrets 확인

설정된 Secrets는 값을 확인할 수 없습니다. 이름만 확인 가능합니다.
**Settings** → **Secrets and variables** → **Actions**에서 목록 확인

## 7. 다음 단계

Secrets 설정 후:
1. GitHub Actions 워크플로우 파일에서 secrets 사용
2. Docker 컨테이너에 환경 변수 전달
3. EC2 인스턴스 User Data나 ECS Task Definition에 환경 변수 설정
