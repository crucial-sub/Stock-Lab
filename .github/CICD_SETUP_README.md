# CI/CD 환경 변수 설정 완벽 가이드

Stock Lab 프로젝트의 CI/CD 파이프라인에서 환경 변수를 안전하게 관리하는 완벽한 가이드입니다.

## 📋 목차

1. [개요](#개요)
2. [설정 단계](#설정-단계)
3. [필요한 파일](#필요한-파일)
4. [트러블슈팅](#트러블슈팅)

## 개요

CI/CD 파이프라인은 3단계로 구성됩니다:

```
GitHub Actions (CI) → ECR (Image Storage) → EC2 Auto Scaling (CD)
        ↓                      ↓                       ↓
  GitHub Secrets          Docker Images      AWS Parameter Store
```

## 설정 단계

### 1단계: GitHub Secrets 설정

GitHub 저장소에서 민감한 정보를 Secrets로 등록합니다.

#### 방법:
1. GitHub 저장소 → **Settings** → **Secrets and variables** → **Actions**
2. **New repository secret** 클릭
3. 아래 secrets 추가

#### 필수 Secrets:

```bash
# AWS 관련
AWS_ACCESS_KEY_ID=your-key
AWS_SECRET_ACCESS_KEY=your-secret
ASG_NAME=your-auto-scaling-group-name
LAUNCH_TEMPLATE_NAME=your-launch-template-name
TARGET_GROUP_ARN=arn:aws:...
ALB_DNS_URL=http://your-alb-dns-name

# 애플리케이션 관련 (Parameter Store에도 등록 필요)
DATABASE_URL=postgresql+asyncpg://...
SECRET_KEY=your-jwt-secret-key
REDIS_URL=redis://...
```

**상세 목록**: [SECRETS_SETUP_GUIDE.md](./SECRETS_SETUP_GUIDE.md) 참조

### 2단계: AWS Parameter Store 설정

EC2 인스턴스에서 사용할 환경 변수를 AWS Systems Manager Parameter Store에 등록합니다.

#### 방법 1: 스크립트 사용 (권장)

```bash
# 1. 프로덕션용 .env 파일 생성
cp .env.example .env.production
# .env.production 파일을 실제 값으로 수정

# 2. Parameter Store에 업로드
./scripts/upload-env-to-parameter-store.sh prod .env.production

# 3. 로컬의 .env.production 파일 삭제 (보안)
rm .env.production
```

#### 방법 2: 수동 등록

```bash
# 각 환경 변수를 개별적으로 등록
aws ssm put-parameter \
  --name "/stocklab/prod/DATABASE_URL" \
  --value "postgresql+asyncpg://user:pass@host:5432/db" \
  --type "SecureString" \
  --overwrite

aws ssm put-parameter \
  --name "/stocklab/prod/SECRET_KEY" \
  --value "your-secret-key" \
  --type "SecureString" \
  --overwrite

# 나머지 환경 변수도 동일하게 등록...
```

#### 업로드된 파라미터 확인

```bash
aws ssm get-parameters-by-path \
  --path "/stocklab/prod" \
  --region ap-northeast-2 \
  --query "Parameters[*].Name"
```

**상세 가이드**: [DEPLOYMENT_ENV_GUIDE.md](./DEPLOYMENT_ENV_GUIDE.md) 참조

### 3단계: EC2 IAM Role 권한 설정

EC2 인스턴스가 Parameter Store와 ECR에 접근할 수 있도록 IAM Role 설정이 필요합니다.

#### 필요한 권한:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "ParameterStoreAccess",
      "Effect": "Allow",
      "Action": [
        "ssm:GetParameter",
        "ssm:GetParameters",
        "ssm:GetParametersByPath"
      ],
      "Resource": "arn:aws:ssm:ap-northeast-2:*:parameter/stocklab/prod/*"
    },
    {
      "Sid": "KMSDecrypt",
      "Effect": "Allow",
      "Action": ["kms:Decrypt"],
      "Resource": "*"
    },
    {
      "Sid": "ECRAccess",
      "Effect": "Allow",
      "Action": [
        "ecr:GetAuthorizationToken",
        "ecr:BatchCheckLayerAvailability",
        "ecr:GetDownloadUrlForLayer",
        "ecr:BatchGetImage"
      ],
      "Resource": "*"
    }
  ]
}
```

### 4단계: Launch Template 설정

EC2 Launch Template의 User Data에 스크립트를 설정합니다.

#### 방법:
1. AWS Console → EC2 → Launch Templates
2. Launch Template 선택 → **Modify template (Create new version)**
3. **Advanced details** → **User data**에 아래 스크립트 입력

#### User Data 스크립트:

`scripts/ec2-user-data.sh` 파일을 참조하거나, 아래 템플릿 사용:

```bash
#!/bin/bash
set -e

# 환경 설정
export AWS_REGION=ap-northeast-2
export ENVIRONMENT=prod
export ECR_REGISTRY="YOUR_ECR_REGISTRY_ID.dkr.ecr.ap-northeast-2.amazonaws.com"

# Parameter Store에서 환경 변수 가져오기
export DATABASE_URL=$(aws ssm get-parameter --name "/stocklab/prod/DATABASE_URL" --with-decryption --query "Parameter.Value" --output text --region $AWS_REGION)
export SECRET_KEY=$(aws ssm get-parameter --name "/stocklab/prod/SECRET_KEY" --with-decryption --query "Parameter.Value" --output text --region $AWS_REGION)
# ... 나머지 환경 변수

# ECR 로그인 및 컨테이너 시작
aws ecr get-login-password --region $AWS_REGION | docker login --username AWS --password-stdin $ECR_REGISTRY
docker pull $ECR_REGISTRY/stocklab-backend:latest
docker pull $ECR_REGISTRY/stocklab-frontend:latest
docker-compose up -d
```

**전체 스크립트**: [scripts/ec2-user-data.sh](../scripts/ec2-user-data.sh) 참조

### 5단계: GitHub Actions 워크플로우 확인

현재 `.github/workflows/deploy.yml`에 이미 설정되어 있습니다:

- ✅ 테스트 단계에 환경 변수 추가
- ✅ 백엔드/프론트엔드 Docker 이미지 빌드
- ✅ ECR에 이미지 푸시
- ✅ Auto Scaling Group Instance Refresh 트리거

## 필요한 파일

### 설정 파일

- `.github/workflows/deploy.yml` - CI/CD 파이프라인 정의
- `.env.example` - 환경 변수 템플릿
- `docker-compose.yml` - 컨테이너 오케스트레이션

### 문서

- [SECRETS_SETUP_GUIDE.md](./SECRETS_SETUP_GUIDE.md) - GitHub Secrets 설정 가이드
- [DEPLOYMENT_ENV_GUIDE.md](./DEPLOYMENT_ENV_GUIDE.md) - 배포 환경 변수 가이드

### 스크립트

- `scripts/upload-env-to-parameter-store.sh` - Parameter Store 업로드 스크립트
- `scripts/ec2-user-data.sh` - EC2 User Data 템플릿

## CI/CD 플로우

### 전체 흐름

```
1. 코드 푸시 (main 브랜치)
   ↓
2. GitHub Actions 트리거
   ↓
3. 테스트 실행 (환경 변수: GitHub Actions env)
   ↓
4. Docker 이미지 빌드 (프론트엔드: build-arg 사용)
   ↓
5. ECR에 이미지 푸시
   ↓
6. Auto Scaling Group Instance Refresh
   ↓
7. 새 EC2 인스턴스 시작
   ↓
8. User Data 실행
   - Parameter Store에서 환경 변수 가져오기
   - ECR에서 이미지 pull
   - Docker 컨테이너 시작
   ↓
9. Health Check 통과
   ↓
10. 배포 완료
```

### 환경 변수 흐름

```
로컬 개발: .env 파일
    ↓
CI 테스트: GitHub Actions env
    ↓
Parameter Store: 프로덕션 환경 변수 저장
    ↓
EC2 User Data: Parameter Store에서 가져오기
    ↓
Docker Container: 환경 변수 주입
```

## 빠른 시작 체크리스트

- [ ] 1. GitHub Secrets 등록 (AWS credentials, ALB URL 등)
- [ ] 2. `.env.production` 파일 생성
- [ ] 3. Parameter Store에 환경 변수 업로드
- [ ] 4. EC2 IAM Role 권한 설정
- [ ] 5. Launch Template User Data 스크립트 설정
- [ ] 6. Launch Template의 최신 버전을 Default로 설정
- [ ] 7. main 브랜치에 푸시하여 CI/CD 테스트

## 환경 변수 업데이트 방법

### 프로덕션 환경 변수 변경 시

```bash
# 1. Parameter Store 업데이트
aws ssm put-parameter \
  --name "/stocklab/prod/SECRET_KEY" \
  --value "new-secret-key" \
  --type "SecureString" \
  --overwrite

# 2. Instance Refresh 트리거 (자동으로 새 환경 변수 적용)
aws autoscaling start-instance-refresh \
  --auto-scaling-group-name your-asg-name
```

### GitHub Secrets 변경 시

1. GitHub Settings → Secrets → 해당 Secret 선택
2. **Update** 클릭하여 새 값 입력
3. main 브랜치에 푸시하면 새 Secret으로 배포

## 트러블슈팅

### 문제 1: 컨테이너가 시작되지 않음

```bash
# EC2 인스턴스 SSH 접속 후
sudo tail -f /var/log/user-data.log
docker-compose logs
```

### 문제 2: Parameter Store 접근 권한 오류

```bash
# IAM Role 확인
aws sts get-caller-identity

# Parameter 접근 테스트
aws ssm get-parameter --name "/stocklab/prod/DATABASE_URL" --with-decryption
```

### 문제 3: ECR 이미지 pull 실패

```bash
# ECR 로그인 재시도
aws ecr get-login-password --region ap-northeast-2 | \
  docker login --username AWS --password-stdin YOUR_ECR_REGISTRY
```

### 문제 4: 환경 변수가 컨테이너에 전달되지 않음

```bash
# 컨테이너 환경 변수 확인
docker exec stocklab-backend env | grep DATABASE_URL

# .env 파일 확인
cat /opt/stocklab/.env
```

## 보안 모범 사례

1. ✅ **Secrets는 절대 Git에 커밋하지 않기**
   - `.env` 파일은 `.gitignore`에 포함
   - `.env.example`만 커밋

2. ✅ **Parameter Store는 SecureString 사용**
   - 민감한 정보는 암호화 저장

3. ✅ **IAM 최소 권한 원칙**
   - 필요한 권한만 부여

4. ✅ **정기적인 Secret 교체**
   - 특히 SECRET_KEY, 데이터베이스 비밀번호

5. ✅ **환경 분리**
   - dev/staging/prod 환경 변수 분리

## 참고 자료

- [AWS Systems Manager Parameter Store](https://docs.aws.amazon.com/systems-manager/latest/userguide/systems-manager-parameter-store.html)
- [GitHub Actions Encrypted Secrets](https://docs.github.com/en/actions/security-guides/encrypted-secrets)
- [Docker Compose Environment Variables](https://docs.docker.com/compose/environment-variables/)

## 추가 지원

문제가 발생하면:
1. 이 문서의 트러블슈팅 섹션 참조
2. CloudWatch Logs 확인
3. GitHub Actions 로그 확인
4. EC2 User Data 로그 확인 (`/var/log/user-data.log`)
