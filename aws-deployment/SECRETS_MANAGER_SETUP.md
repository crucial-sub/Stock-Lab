# AWS Secrets Manager 설정 가이드

AWS Secrets Manager를 사용하여 민감한 정보를 안전하게 관리하는 방법을 설명합니다.

---

## 📋 목차

1. [왜 Secrets Manager를 사용해야 하나요?](#왜-secrets-manager를-사용해야-하나요)
2. [시크릿 생성](#시크릿-생성)
3. [IAM 권한 설정](#iam-권한-설정)
4. [애플리케이션 통합](#애플리케이션-통합)
5. [자동 로테이션 설정](#자동-로테이션-설정)
6. [비용 최적화](#비용-최적화)

---

## 왜 Secrets Manager를 사용해야 하나요?

### 현재 방식의 문제점
```bash
# 환경 변수 파일에 민감 정보 저장 (보안 위험)
DATABASE_PASSWORD=postgres123
REDIS_PASSWORD=redis_pass
API_KEY=sk-xxxxxxxxx
```

### Secrets Manager의 장점
- ✅ **암호화 저장**: AES-256 암호화
- ✅ **자동 로테이션**: 정기적인 비밀번호 변경
- ✅ **접근 제어**: IAM 기반 세밀한 권한 관리
- ✅ **감사 로그**: CloudTrail을 통한 접근 이력 추적
- ✅ **버전 관리**: 이전 버전으로 롤백 가능

---

## 시크릿 생성

### 1. RDS PostgreSQL 비밀번호

**AWS Console** → **Secrets Manager** → **Store a new secret**

#### Step 1: 시크릿 타입 선택
```
Secret type: Credentials for Amazon RDS database
Username: postgres
Password: [생성하거나 자동 생성]
Encryption key: aws/secretsmanager (기본값)
Database: [RDS 인스턴스 선택]
```

**Next** 클릭

#### Step 2: 시크릿 이름 및 설명
```
Secret name: stocklab/production/rds
Description: PostgreSQL database credentials for Stock Lab production
Tags:
  - Key: Environment, Value: production
  - Key: Application, Value: stocklab
```

**Next** 클릭

#### Step 3: 자동 로테이션 설정 (나중에 설정 가능)
```
Disable automatic rotation (처음에는 비활성화)
```

**Next** → **Store**

### 2. Redis 비밀번호

**Store a new secret** 클릭

```
Secret type: Other type of secret
Key/value pairs:
  - password: [Redis 비밀번호]

Secret name: stocklab/production/redis
Description: ElastiCache Redis credentials
```

### 3. 기타 API 키 및 환경 변수

```json
{
  "OPENAI_API_KEY": "sk-xxxxx",
  "JWT_SECRET_KEY": "your-jwt-secret",
  "ENCRYPTION_KEY": "your-encryption-key",
  "SLACK_WEBHOOK_URL": "https://hooks.slack.com/..."
}
```

```
Secret name: stocklab/production/api-keys
```

### AWS CLI로 시크릿 생성

```bash
# RDS 비밀번호 생성
aws secretsmanager create-secret \
  --name stocklab/production/rds \
  --description "PostgreSQL database credentials" \
  --secret-string '{
    "username": "postgres",
    "password": "YourSecurePassword123!",
    "engine": "postgres",
    "host": "your-rds-endpoint.rds.amazonaws.com",
    "port": 5432,
    "dbname": "quant_investment_db"
  }' \
  --region ap-northeast-2

# Redis 비밀번호 생성
aws secretsmanager create-secret \
  --name stocklab/production/redis \
  --description "ElastiCache Redis credentials" \
  --secret-string '{
    "password": "YourRedisPassword123!",
    "host": "your-redis-endpoint.cache.amazonaws.com",
    "port": 6379
  }' \
  --region ap-northeast-2

# API 키 및 기타 환경 변수
aws secretsmanager create-secret \
  --name stocklab/production/api-keys \
  --description "API keys and secrets" \
  --secret-string '{
    "OPENAI_API_KEY": "sk-xxxxx",
    "JWT_SECRET_KEY": "your-jwt-secret",
    "ENCRYPTION_KEY": "your-encryption-key"
  }' \
  --region ap-northeast-2
```

---

## IAM 권한 설정

### EC2 인스턴스 IAM 역할

**IAM Console** → **Roles** → EC2 역할 선택 → **Add permissions** → **Create inline policy**

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "secretsmanager:GetSecretValue",
        "secretsmanager:DescribeSecret"
      ],
      "Resource": [
        "arn:aws:secretsmanager:ap-northeast-2:*:secret:stocklab/production/*"
      ]
    },
    {
      "Effect": "Allow",
      "Action": [
        "kms:Decrypt",
        "kms:DescribeKey"
      ],
      "Resource": "arn:aws:kms:ap-northeast-2:*:key/*",
      "Condition": {
        "StringEquals": {
          "kms:ViaService": "secretsmanager.ap-northeast-2.amazonaws.com"
        }
      }
    }
  ]
}
```

Policy name: `SecretsManagerReadAccess`

---

## 애플리케이션 통합

### Python (Backend) 통합

#### 1. boto3 설치
```bash
pip install boto3
```

#### 2. Secrets Manager 클라이언트 생성

`SL-Back-end/app/core/secrets.py` 생성:

```python
import json
import boto3
from functools import lru_cache
from botocore.exceptions import ClientError

class SecretsManager:
    def __init__(self, region_name="ap-northeast-2"):
        self.client = boto3.client(
            service_name='secretsmanager',
            region_name=region_name
        )

    @lru_cache(maxsize=10)
    def get_secret(self, secret_name: str) -> dict:
        """
        시크릿을 가져오고 캐싱합니다.
        """
        try:
            response = self.client.get_secret_value(SecretId=secret_name)

            if 'SecretString' in response:
                return json.loads(response['SecretString'])
            else:
                # Binary secrets
                return response['SecretBinary']

        except ClientError as e:
            error_code = e.response['Error']['Code']

            if error_code == 'ResourceNotFoundException':
                raise Exception(f"The secret {secret_name} was not found")
            elif error_code == 'InvalidRequestException':
                raise Exception(f"The request was invalid: {e}")
            elif error_code == 'InvalidParameterException':
                raise Exception(f"The request had invalid params: {e}")
            elif error_code == 'DecryptionFailure':
                raise Exception(f"The secret can't be decrypted: {e}")
            else:
                raise

    def get_rds_credentials(self) -> dict:
        """RDS 자격 증명 가져오기"""
        return self.get_secret("stocklab/production/rds")

    def get_redis_credentials(self) -> dict:
        """Redis 자격 증명 가져오기"""
        return self.get_secret("stocklab/production/redis")

    def get_api_keys(self) -> dict:
        """API 키 가져오기"""
        return self.get_secret("stocklab/production/api-keys")

# 싱글톤 인스턴스
secrets_manager = SecretsManager()
```

#### 3. 환경 설정 업데이트

`SL-Back-end/app/core/config.py`:

```python
import os
from pydantic_settings import BaseSettings
from .secrets import secrets_manager

class Settings(BaseSettings):
    # 환경 변수로 Secrets Manager 사용 여부 결정
    USE_SECRETS_MANAGER: bool = os.getenv("USE_SECRETS_MANAGER", "false").lower() == "true"

    # Database settings
    @property
    def DATABASE_URL(self) -> str:
        if self.USE_SECRETS_MANAGER:
            creds = secrets_manager.get_rds_credentials()
            return f"postgresql+asyncpg://{creds['username']}:{creds['password']}@{creds['host']}:{creds['port']}/{creds['dbname']}"
        else:
            # 로컬 개발용 fallback
            return os.getenv("DATABASE_URL", "postgresql+asyncpg://postgres:postgres123@localhost:5432/quant_investment_db")

    # Redis settings
    @property
    def REDIS_URL(self) -> str:
        if self.USE_SECRETS_MANAGER:
            creds = secrets_manager.get_redis_credentials()
            return f"redis://:{creds['password']}@{creds['host']}:{creds['port']}/0"
        else:
            return os.getenv("REDIS_URL", "redis://localhost:6379/0")

    # API Keys
    @property
    def OPENAI_API_KEY(self) -> str:
        if self.USE_SECRETS_MANAGER:
            keys = secrets_manager.get_api_keys()
            return keys.get("OPENAI_API_KEY")
        else:
            return os.getenv("OPENAI_API_KEY", "")

    class Config:
        env_file = ".env"

settings = Settings()
```

#### 4. EC2 User Data 업데이트

`aws-deployment/ec2-user-data-ecr.sh`에 환경 변수 추가:

```bash
# Secrets Manager 사용 활성화
echo "USE_SECRETS_MANAGER=true" >> /app/.env
```

---

## 자동 로테이션 설정

### RDS 비밀번호 자동 로테이션

**Secrets Manager Console** → 시크릿 선택 → **Rotation configuration** → **Edit rotation**

```
Enable automatic rotation: ✓
Rotation schedule: 30 days
Rotation function: Create new Lambda function

Function name: stocklab-rds-rotation
Use separate credentials: No (권장)
```

**Save** 클릭

### Lambda 함수 확인

자동으로 생성된 Lambda 함수가 다음 작업을 수행합니다:
1. 새 비밀번호 생성
2. RDS에서 비밀번호 변경
3. Secrets Manager 업데이트
4. 이전 버전 유지 (롤백용)

---

## 비용 최적화

### 비용 계산

```
시크릿 저장: $0.40/월 per secret
API 호출: $0.05 per 10,000 API calls

예상 비용 (3개 시크릿):
- 저장: 3 × $0.40 = $1.20/월
- API 호출: ~1,000 calls/월 = $0.01/월
─────────────────────────────
Total: ~$1.21/월
```

### 비용 절감 팁

#### 1. 시크릿 그룹화
```bash
# ❌ 나쁜 예: 각각 별도 시크릿
stocklab/production/db-user
stocklab/production/db-password
stocklab/production/db-host

# ✅ 좋은 예: 하나의 시크릿으로 그룹화
stocklab/production/database
```

#### 2. 캐싱 사용
```python
# 캐싱으로 API 호출 횟수 감소
@lru_cache(maxsize=10)
def get_secret(self, secret_name: str) -> dict:
    # ...
```

#### 3. 개발 환경에서는 환경 변수 사용
```python
# 개발: 환경 변수
# 프로덕션: Secrets Manager
USE_SECRETS_MANAGER = os.getenv("ENV") == "production"
```

---

## 모니터링 및 감사

### CloudTrail 로그 확인

```bash
# 시크릿 접근 이력 조회
aws cloudtrail lookup-events \
  --lookup-attributes AttributeKey=ResourceName,AttributeValue=stocklab/production/rds \
  --max-results 50 \
  --region ap-northeast-2
```

### CloudWatch 알람 설정

```bash
# 시크릿 접근 실패 알람
aws cloudwatch put-metric-alarm \
  --alarm-name secrets-manager-access-failures \
  --alarm-description "Alert on Secrets Manager access failures" \
  --metric-name UserErrorCount \
  --namespace AWS/SecretsManager \
  --statistic Sum \
  --period 300 \
  --threshold 5 \
  --comparison-operator GreaterThanThreshold \
  --evaluation-periods 1 \
  --region ap-northeast-2
```

---

## 테스트

### 로컬 테스트 (AWS 자격 증명 필요)

```bash
cd SL-Back-end

# AWS 자격 증명 설정
export AWS_ACCESS_KEY_ID=your-key
export AWS_SECRET_ACCESS_KEY=your-secret
export AWS_REGION=ap-northeast-2
export USE_SECRETS_MANAGER=true

# 애플리케이션 실행
python -c "from app.core.secrets import secrets_manager; print(secrets_manager.get_rds_credentials())"
```

### EC2에서 테스트

```bash
# EC2 인스턴스에 SSH 접속
ssh ec2-user@your-instance-ip

# 시크릿 가져오기 테스트
aws secretsmanager get-secret-value \
  --secret-id stocklab/production/rds \
  --region ap-northeast-2 \
  --query SecretString \
  --output text | jq .
```

---

## 마이그레이션 체크리스트

- [ ] Secrets Manager에 모든 시크릿 생성
- [ ] EC2 IAM 역할에 권한 추가
- [ ] Backend에 `secrets.py` 추가
- [ ] `config.py` 업데이트
- [ ] `requirements.txt`에 `boto3` 추가
- [ ] EC2 User Data에 `USE_SECRETS_MANAGER=true` 추가
- [ ] 로컬에서 테스트
- [ ] Staging 환경에서 테스트
- [ ] Production 배포
- [ ] 자동 로테이션 활성화
- [ ] CloudWatch 알람 설정

---

## 트러블슈팅

### 시크릿을 가져올 수 없음

```bash
# IAM 역할 확인
aws sts get-caller-identity

# 시크릿 존재 확인
aws secretsmanager list-secrets --region ap-northeast-2

# 권한 확인
aws secretsmanager get-secret-value \
  --secret-id stocklab/production/rds \
  --region ap-northeast-2
```

### 복호화 실패

KMS 키 권한 확인:
```bash
aws kms describe-key \
  --key-id alias/aws/secretsmanager \
  --region ap-northeast-2
```

---

## 다음 단계

1. **Parameter Store 비교**: 간단한 설정은 SSM Parameter Store 고려
2. **VPC Endpoint**: Secrets Manager VPC Endpoint로 비용 절감
3. **교차 계정 접근**: 멀티 계정 환경 설정

---

**Secrets Manager 설정 완료! 🔐**
