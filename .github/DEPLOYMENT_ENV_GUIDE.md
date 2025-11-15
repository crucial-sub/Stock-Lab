# 배포 환경 변수 설정 가이드

EC2 Auto Scaling Group으로 배포할 때 환경 변수를 안전하게 관리하는 방법입니다.

## 방법 1: AWS Systems Manager Parameter Store (권장)

가장 안전하고 관리하기 쉬운 방법입니다.

### 1-1. Parameter Store에 환경 변수 저장

AWS Console 또는 CLI로 파라미터 저장:

```bash
# 예시: DATABASE_URL 저장
aws ssm put-parameter \
  --name "/stocklab/prod/DATABASE_URL" \
  --value "postgresql+asyncpg://user:pass@host:5432/db" \
  --type "SecureString" \
  --overwrite

# 예시: SECRET_KEY 저장
aws ssm put-parameter \
  --name "/stocklab/prod/SECRET_KEY" \
  --value "your-generated-secret-key" \
  --type "SecureString" \
  --overwrite

# 모든 환경 변수를 하나씩 저장
aws ssm put-parameter --name "/stocklab/prod/REDIS_URL" --value "redis://host:6379/0" --type "SecureString"
aws ssm put-parameter --name "/stocklab/prod/ALB_DNS_URL" --value "http://your-alb.com" --type "String"
```

### 1-2. EC2 IAM Role에 권한 추가

EC2 인스턴스가 Parameter Store에 접근할 수 있도록 IAM Role에 정책 추가:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "ssm:GetParameter",
        "ssm:GetParameters",
        "ssm:GetParametersByPath"
      ],
      "Resource": "arn:aws:ssm:ap-northeast-2:*:parameter/stocklab/prod/*"
    },
    {
      "Effect": "Allow",
      "Action": [
        "kms:Decrypt"
      ],
      "Resource": "*"
    }
  ]
}
```

### 1-3. Launch Template User Data 스크립트 수정

```bash
#!/bin/bash
set -e

# Systems Manager에서 환경 변수 가져오기
export DATABASE_URL=$(aws ssm get-parameter --name "/stocklab/prod/DATABASE_URL" --with-decryption --query "Parameter.Value" --output text --region ap-northeast-2)
export DATABASE_SYNC_URL=$(aws ssm get-parameter --name "/stocklab/prod/DATABASE_SYNC_URL" --with-decryption --query "Parameter.Value" --output text --region ap-northeast-2)
export SECRET_KEY=$(aws ssm get-parameter --name "/stocklab/prod/SECRET_KEY" --with-decryption --query "Parameter.Value" --output text --region ap-northeast-2)
export REDIS_URL=$(aws ssm get-parameter --name "/stocklab/prod/REDIS_URL" --with-decryption --query "Parameter.Value" --output text --region ap-northeast-2)
export ALB_DNS_URL=$(aws ssm get-parameter --name "/stocklab/prod/ALB_DNS_URL" --query "Parameter.Value" --output text --region ap-northeast-2)

# ECR 로그인
aws ecr get-login-password --region ap-northeast-2 | docker login --username AWS --password-stdin YOUR_ECR_REGISTRY

# 최신 이미지 pull
docker pull YOUR_ECR_REGISTRY/stocklab-backend:latest
docker pull YOUR_ECR_REGISTRY/stocklab-frontend:latest

# 기존 컨테이너 중지 및 제거
docker-compose down || true

# docker-compose.yml에서 환경 변수를 전달하여 컨테이너 시작
docker-compose up -d
```

### 1-4. docker-compose.yml 수정

환경 변수를 컨테이너에 전달:

```yaml
version: '3.8'

services:
  backend:
    image: ${ECR_REGISTRY}/stocklab-backend:latest
    environment:
      - DATABASE_URL=${DATABASE_URL}
      - DATABASE_SYNC_URL=${DATABASE_SYNC_URL}
      - SECRET_KEY=${SECRET_KEY}
      - REDIS_URL=${REDIS_URL}
      - ALGORITHM=HS256
      - ACCESS_TOKEN_EXPIRE_MINUTES=30
      - DEBUG=False
    ports:
      - "8000:8000"

  frontend:
    image: ${ECR_REGISTRY}/stocklab-frontend:latest
    environment:
      - NEXT_PUBLIC_API_BASE_URL=${ALB_DNS_URL}/api/v1
    ports:
      - "3000:3000"
```

## 방법 2: S3에 .env 파일 저장 (간단한 방법)

### 2-1. .env 파일을 S3에 업로드

```bash
# .env 파일 생성 (로컬에서)
cat > .env.production << EOF
DATABASE_URL=postgresql+asyncpg://user:pass@host:5432/db
SECRET_KEY=your-secret-key
REDIS_URL=redis://host:6379/0
EOF

# S3에 업로드 (암호화 사용)
aws s3 cp .env.production s3://your-bucket-name/config/.env.production \
  --sse AES256

# 로컬 파일 삭제
rm .env.production
```

### 2-2. Launch Template User Data에서 다운로드

```bash
#!/bin/bash
set -e

# S3에서 .env 파일 다운로드
aws s3 cp s3://your-bucket-name/config/.env.production /app/.env

# ECR 로그인 및 컨테이너 시작
aws ecr get-login-password --region ap-northeast-2 | docker login --username AWS --password-stdin YOUR_ECR_REGISTRY
docker pull YOUR_ECR_REGISTRY/stocklab-backend:latest
docker pull YOUR_ECR_REGISTRY/stocklab-frontend:latest

# docker-compose로 시작 (.env 파일 자동 로드)
cd /app
docker-compose up -d
```

### 2-3. EC2 IAM Role에 S3 권한 추가

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "s3:GetObject"
      ],
      "Resource": "arn:aws:s3:::your-bucket-name/config/*"
    }
  ]
}
```

## 방법 3: Launch Template에 직접 환경 변수 설정 (간단하지만 덜 안전)

User Data 스크립트에 직접 환경 변수 작성:

```bash
#!/bin/bash
cat > /app/.env << 'EOF'
DATABASE_URL=postgresql+asyncpg://user:pass@host:5432/db
SECRET_KEY=your-secret-key
REDIS_URL=redis://host:6379/0
DEBUG=False
EOF

# 컨테이너 시작
cd /app
docker-compose up -d
```

**주의**: 이 방법은 Launch Template에 민감한 정보가 평문으로 저장되므로 권장하지 않습니다.

## 권장 사항

1. **Production**: Parameter Store (방법 1) 사용
2. **Staging**: Parameter Store 또는 S3 (방법 2)
3. **Development**: .env 파일 직접 사용

## 환경 변수 업데이트 방법

### Parameter Store 사용 시

```bash
# 1. Parameter 업데이트
aws ssm put-parameter \
  --name "/stocklab/prod/SECRET_KEY" \
  --value "new-secret-key" \
  --type "SecureString" \
  --overwrite

# 2. Auto Scaling Group Instance Refresh 트리거
aws autoscaling start-instance-refresh \
  --auto-scaling-group-name your-asg-name
```

### S3 사용 시

```bash
# 1. S3에 새 .env 파일 업로드
aws s3 cp .env.production s3://your-bucket-name/config/.env.production

# 2. Instance Refresh 트리거
aws autoscaling start-instance-refresh \
  --auto-scaling-group-name your-asg-name
```

## 보안 체크리스트

- [ ] Parameter Store 또는 S3에 환경 변수 저장 (평문 X)
- [ ] EC2 IAM Role에 최소 권한만 부여
- [ ] S3 버킷 암호화 활성화
- [ ] Parameter Store SecureString 타입 사용
- [ ] Launch Template에 민감한 정보 평문 저장 금지
- [ ] .env 파일 Git에 커밋 금지
- [ ] 정기적으로 SECRET_KEY 등 중요 키 교체

## 다음 단계

1. Parameter Store에 환경 변수 등록
2. EC2 IAM Role 권한 설정
3. Launch Template User Data 스크립트 업데이트
4. Instance Refresh로 배포 테스트
