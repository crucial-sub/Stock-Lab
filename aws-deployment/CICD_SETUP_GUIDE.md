# CI/CD 파이프라인 구축 가이드

이 가이드는 GitHub Actions + AWS ECR + Auto Scaling을 사용한 CI/CD 파이프라인 구축 방법을 설명합니다.

---

## 📋 목차

1. [전체 아키텍처](#전체-아키텍처)
2. [사전 준비사항](#사전-준비사항)
3. [Step 1: ECR 리포지토리 생성](#step-1-ecr-리포지토리-생성)
4. [Step 2: IAM 설정](#step-2-iam-설정)
5. [Step 3: GitHub Secrets 설정](#step-3-github-secrets-설정)
6. [Step 4: Launch Template 업데이트](#step-4-launch-template-업데이트)
7. [Step 5: 첫 배포 테스트](#step-5-첫-배포-테스트)
8. [배포 프로세스](#배포-프로세스)
9. [트러블슈팅](#트러블슈팅)

---

## 🏗️ 전체 아키텍처

```
Developer
    ↓ git push
GitHub Actions
    ↓ (CI: 테스트, 빌드)
Amazon ECR
    ↓ (Docker 이미지 저장)
Launch Template
    ↓ (User Data에서 ECR 이미지 Pull)
Auto Scaling Group
    ↓ (Instance Refresh)
Application Load Balancer
    ↓
사용자
```

---

## 🔧 사전 준비사항

- ✅ AWS 계정 및 관리자 권한
- ✅ GitHub 리포지토리 (Stock-Lab-Demo)
- ✅ 기존 인프라 구축 완료:
  - VPC
  - RDS PostgreSQL
  - ElastiCache Redis
  - Application Load Balancer
  - Target Groups
  - Auto Scaling Group

---

## Step 1: ECR 리포지토리 생성

### 1-1. AWS Console

**ECR Console** → **Repositories** → **Create repository**

#### Backend 리포지토리:
```
Repository name: stocklab-backend
Tag immutability: Disabled
Scan on push: Enabled (보안 스캔)
Encryption: AES-256
```

**Create repository** 클릭

#### Frontend 리포지토리:
```
Repository name: stocklab-frontend
Tag immutability: Disabled
Scan on push: Enabled
Encryption: AES-256
```

**Create repository** 클릭

### 1-2. URI 확인

생성 후 **URI**를 복사하세요:
```
<AWS_ACCOUNT_ID>.dkr.ecr.ap-northeast-2.amazonaws.com/stocklab-backend
<AWS_ACCOUNT_ID>.dkr.ecr.ap-northeast-2.amazonaws.com/stocklab-frontend
```

---

## Step 2: IAM 설정

### 2-1. EC2 인스턴스 IAM 역할

**IAM Console** → **Roles** → **Create role**

#### Trust relationship:
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Service": "ec2.amazonaws.com"
      },
      "Action": "sts:AssumeRole"
    }
  ]
}
```

#### 정책 연결:
1. **Create policy** → `aws-deployment/iam-policy-ec2-ecr.json` 내용 붙여넣기
2. 정책 이름: `StockLab-EC2-ECR-Policy`
3. 역할에 정책 연결

#### 역할 이름:
```
StockLab-EC2-Role
```

### 2-2. Launch Template에 IAM 역할 연결

**EC2** → **Launch Templates** → 템플릿 선택 → **Modify template (Create new version)**

**Advanced details** → **IAM instance profile**:
```
StockLab-EC2-Role
```

**Create template version**

### 2-3. GitHub Actions IAM 사용자

**IAM Console** → **Users** → **Create user**

#### 사용자 이름:
```
github-actions-stocklab
```

#### 정책 연결:
1. **Create policy** → `aws-deployment/iam-policy-github-actions.json` 내용 붙여넣기
2. 정책 이름: `StockLab-GitHub-Actions-Policy`
3. 사용자에 정책 연결

#### Access Key 생성:
1. 사용자 선택 → **Security credentials** 탭
2. **Create access key**
3. Use case: **Third-party service**
4. **Access key ID**와 **Secret access key** 복사 (한 번만 표시됨!)

---

## Step 3: GitHub Secrets 설정

**GitHub Repository** → **Settings** → **Secrets and variables** → **Actions** → **New repository secret**

### 필수 Secrets:

| Secret Name | Value | 설명 |
|------------|-------|------|
| `AWS_ACCESS_KEY_ID` | `AKIA...` | IAM 사용자 Access Key ID |
| `AWS_SECRET_ACCESS_KEY` | `...` | IAM 사용자 Secret Key |
| `AWS_ACCOUNT_ID` | `123456789012` | AWS 계정 ID |
| `ASG_NAME` | `stacklab-asg` | Auto Scaling Group 이름 |
| `LAUNCH_TEMPLATE_NAME` | `stacklab-launch-template` | Launch Template 이름 |
| `TARGET_GROUP_ARN` | `arn:aws:elasticloadbalancing:...` | Target Group ARN (Backend) |
| `ALB_DNS_URL` | `http://SL-APPLICATION-LB-xxx.elb.amazonaws.com` | ALB DNS 주소 |

### Secrets 값 확인 방법:

#### AWS_ACCOUNT_ID:
```bash
aws sts get-caller-identity --query Account --output text
```

#### ASG_NAME:
```
EC2 Console → Auto Scaling Groups → 이름 확인
```

#### TARGET_GROUP_ARN:
```
EC2 Console → Target Groups → Backend TG 선택 → ARN 복사
```

---

## Step 4: Launch Template 업데이트

### 4-1. User Data 수정

**EC2** → **Launch Templates** → 템플릿 선택 → **Modify template (Create new version)**

**Advanced details** → **User Data**:

`aws-deployment/ec2-user-data-ecr.sh` 파일 내용을 복사하여 붙여넣기

**중요:** 다음 값들을 실제 값으로 변경:
```bash
export AWS_ACCOUNT_ID="123456789012"  # 실제 계정 ID
export RDS_ENDPOINT="..."
export REDIS_ENDPOINT="..."
export SECRET_KEY="..."
export ALB_DNS_NAME="..."
```

**Create template version** 클릭

### 4-2. Auto Scaling Group 업데이트

**EC2** → **Auto Scaling Groups** → ASG 선택 → **Edit**

**Launch template** → **Version**: `Latest`

**Update**

---

## Step 5: 첫 배포 테스트

### 5-1. 로컬에서 첫 이미지 빌드

ECR에 첫 이미지가 있어야 EC2가 Pull할 수 있습니다.

```bash
# AWS CLI 로그인
aws ecr get-login-password --region ap-northeast-2 | \
  docker login --username AWS --password-stdin <AWS_ACCOUNT_ID>.dkr.ecr.ap-northeast-2.amazonaws.com

# Backend 이미지 빌드 및 푸시
cd SL-Back-end
docker build -t <AWS_ACCOUNT_ID>.dkr.ecr.ap-northeast-2.amazonaws.com/stocklab-backend:latest .
docker push <AWS_ACCOUNT_ID>.dkr.ecr.ap-northeast-2.amazonaws.com/stocklab-backend:latest

# Frontend 이미지 빌드 및 푸시
cd ../SL-Front-End
docker build -t <AWS_ACCOUNT_ID>.dkr.ecr.ap-northeast-2.amazonaws.com/stocklab-frontend:latest .
docker push <AWS_ACCOUNT_ID>.dkr.ecr.ap-northeast-2.amazonaws.com/stocklab-frontend:latest
```

### 5-2. GitHub Actions 테스트

```bash
# 코드 수정
git add .
git commit -m "Test CI/CD pipeline"
git push origin main
```

**GitHub** → **Actions** 탭에서 워크플로우 진행 상황 확인

---

## 🚀 배포 프로세스

### 일반 배포 (main 브랜치 push 시)

```
1. Developer: git push origin main
   ↓ (트리거)
2. GitHub Actions - Job: test (3-5분)
   - Python 테스트
   - Lint 검사
   - Frontend 테스트
   ↓ (성공 시)
3. GitHub Actions - Job: build-and-push (5-8분)
   - Backend Docker 이미지 빌드
   - Frontend Docker 이미지 빌드
   - ECR에 푸시 (latest + commit SHA 태그)
   ↓ (성공 시)
4. GitHub Actions - Job: deploy (10-20분)
   - Auto Scaling Group Instance Refresh 트리거
   - 새 EC2 인스턴스 시작
   - User Data 실행 (ECR에서 이미지 Pull)
   - Health Check 통과
   - 구 인스턴스 종료
   ↓
5. 배포 완료!
```

**총 소요 시간:** 약 18-33분

### Rolling Update 전략

Auto Scaling Group은 **50% 최소 Healthy 유지**:

```
초기 상태:     [Old #1] [Old #2]
Step 1:        [Old #1] [New #1]  (Old #2 종료, New #1 시작)
Step 2:        [New #1] [New #2]  (Old #1 종료, New #2 시작)
최종 상태:     [New #1] [New #2]
```

**장점:**
- 다운타임 없음
- 점진적 배포 (문제 발생 시 중단 가능)
- 50% 용량 유지

---

## 🔄 롤백 방법

### 방법 1: 이전 이미지 태그로 재배포

```bash
# 이전 커밋 SHA 확인
git log --oneline

# GitHub Actions에서 이전 커밋 SHA 확인
# 예: abc123def456

# ECR 이미지 태그 변경
aws ecr batch-get-image \
  --repository-name stocklab-backend \
  --image-ids imageTag=abc123def456 \
  --query 'images[].imageManifest' \
  --output text | \
aws ecr put-image \
  --repository-name stocklab-backend \
  --image-tag latest \
  --image-manifest -

# Instance Refresh 트리거
aws autoscaling start-instance-refresh \
  --auto-scaling-group-name stacklab-asg
```

### 방법 2: Git revert

```bash
git revert HEAD
git push origin main
# GitHub Actions가 자동으로 이전 버전 배포
```

---

## 🔍 모니터링

### GitHub Actions 로그

**GitHub** → **Actions** 탭

각 Job의 상세 로그 확인 가능

### EC2 User Data 로그

```bash
# EC2 SSH 접속 후
sudo tail -f /var/log/user-data.log
```

### Docker 로그

```bash
cd /home/ubuntu/app
sudo docker-compose logs -f
```

### Auto Scaling Instance Refresh 상태

```bash
aws autoscaling describe-instance-refreshes \
  --auto-scaling-group-name stacklab-asg \
  --max-records 1
```

---

## ❗ 트러블슈팅

### 문제 1: GitHub Actions에서 ECR 로그인 실패

**증상:**
```
Error: Cannot perform an interactive login from a non TTY device
```

**해결:**
- IAM 사용자 정책 확인
- `ecr:GetAuthorizationToken` 권한 있는지 확인

### 문제 2: EC2에서 ECR 이미지 Pull 실패

**증상:**
```
Error response from daemon: pull access denied
```

**해결:**
- EC2 IAM 역할 확인
- Launch Template에 IAM 역할 연결 확인
- ECR 리포지토리 이름 확인

### 문제 3: Instance Refresh가 실패

**증상:**
```
Status: Failed
```

**해결:**
- User Data 스크립트 오류 확인: `/var/log/user-data.log`
- Health Check 실패: Target Group Health Check 설정 확인
- Docker 컨테이너 로그 확인

### 문제 4: 배포 후 503 에러

**증상:**
ALB DNS 접속 시 503 Service Unavailable

**해결:**
1. Target Group에 Healthy 인스턴스 있는지 확인
2. EC2에서 Docker 컨테이너 상태 확인
3. Backend Health Check 엔드포인트 확인

---

## 📊 성능 최적화

### Docker 이미지 최적화

**.dockerignore 활용:**
```
node_modules/
.git/
*.md
tests/
```

### Multi-stage 빌드:
이미 Dockerfile에 적용됨

### GitHub Actions 캐시:
이미 워크플로우에 적용됨

---

## 🔐 보안 Best Practices

1. ✅ **Secrets 사용**: 민감한 정보는 GitHub Secrets에 저장
2. ✅ **IAM 최소 권한**: 필요한 권한만 부여
3. ✅ **ECR 이미지 스캔**: 보안 취약점 자동 검사
4. ✅ **Private Subnet**: RDS/Redis는 Private에 배치
5. ✅ **Security Group**: 최소한의 포트만 개방

---

## 📈 다음 단계

### 고급 기능 추가:

1. **Blue-Green Deployment**
   - 두 개의 Auto Scaling Group 사용
   - 트래픽을 한 번에 전환

2. **Canary Deployment**
   - 일부 트래픽만 새 버전으로 전달
   - 점진적으로 확대

3. **자동 롤백**
   - Health Check 실패 시 자동 롤백
   - CloudWatch Alarms 연동

4. **Slack/Discord 알림**
   - 배포 성공/실패 알림
   - GitHub Actions webhook 활용

---

## 📞 문의

CI/CD 파이프라인 관련 문제가 있다면:
1. GitHub Issues에 등록
2. `/var/log/user-data.log` 로그 첨부
3. GitHub Actions 로그 첨부

---

**배포 성공을 기원합니다! 🚀**
