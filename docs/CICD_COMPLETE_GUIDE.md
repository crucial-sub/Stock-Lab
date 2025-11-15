# Stock Lab CI/CD 완벽 가이드

GitHub Actions와 AWS를 활용한 프로덕션급 CI/CD 파이프라인 구축 가이드입니다.

---

## 개요

이 프로젝트는 다음과 같은 CI/CD 파이프라인을 구축합니다:

- **Staging 환경**: `staging` 브랜치 푸시 시 자동 배포
- **Production 환경**: `main` 브랜치 푸시 시 수동 승인 후 배포
- **보안 스캔**: Trivy를 통한 코드 및 컨테이너 취약점 스캔
- **자동 롤백**: 배포 실패 시 이전 버전으로 자동 복구
- **실시간 알림**: Slack을 통한 배포 상태 알림
- **모니터링**: CloudWatch를 통한 종합 모니터링

---

## 아키텍처

```
Developer
    ↓
GitHub (staging/main branch)
    ↓
GitHub Actions
    ├─ Tests & Linting
    ├─ Security Scan (Trivy)
    ├─ Docker Build
    └─ Push to ECR
    ↓
AWS Infrastructure
    ├─ Auto Scaling Group
    ├─ Application Load Balancer
    ├─ RDS PostgreSQL
    ├─ ElastiCache Redis
    └─ CloudWatch Monitoring
    ↓
Slack Notification
```

---

## 빠른 시작

### 1단계: AWS 인프라 구축 (이미 완료된 경우 건너뛰기)

기존 인프라가 있다면 [2단계](#2단계-github-secrets-설정)로 이동하세요.

새로 구축하는 경우:
```bash
# VPC 및 네트워크 설정
cd aws-deployment
./vpc-setup.sh

# Security Groups 설정
# VPC ID를 vpc-resources.json에서 확인 후
nano security-groups-setup.sh  # VPC_ID 수정
./security-groups-setup.sh
```

자세한 내용: [aws-deployment/README.md](../aws-deployment/README.md)

### 2단계: GitHub Secrets 설정

필수 Secrets를 GitHub Repository에 추가합니다.

**Repository** → **Settings** → **Secrets and variables** → **Actions**

#### AWS 자격 증명
```
AWS_ACCESS_KEY_ID: AKIAIOSFODNN7EXAMPLE
AWS_SECRET_ACCESS_KEY: wJalrXUtnFEMI/K7MDENG/...
```

#### Production 환경
```
ASG_NAME: stocklab-prod-asg
LAUNCH_TEMPLATE_NAME: stocklab-prod-template
TARGET_GROUP_ARN: arn:aws:elasticloadbalancing:...
ALB_DNS_URL: http://your-alb-dns.elb.amazonaws.com
```

#### Staging 환경
```
STAGING_ASG_NAME: stocklab-staging-asg
STAGING_LAUNCH_TEMPLATE_NAME: stocklab-staging-template
STAGING_TARGET_GROUP_ARN: arn:aws:elasticloadbalancing:...
STAGING_ALB_DNS_URL: http://your-staging-alb-dns.elb.amazonaws.com
```

#### Slack 알림
```
SLACK_WEBHOOK_URL: https://hooks.slack.com/services/...
SLACK_ONCALL_WEBHOOK_URL: https://hooks.slack.com/services/...
```

자세한 설정 방법: [GITHUB_SECRETS_SETUP.md](./GITHUB_SECRETS_SETUP.md)

### 3단계: ECR 리포지토리 생성

```bash
# Production 환경
aws ecr create-repository \
  --repository-name stocklab-backend \
  --region ap-northeast-2

aws ecr create-repository \
  --repository-name stocklab-frontend \
  --region ap-northeast-2

# Staging 환경
aws ecr create-repository \
  --repository-name stocklab-backend-staging \
  --region ap-northeast-2

aws ecr create-repository \
  --repository-name stocklab-frontend-staging \
  --region ap-northeast-2
```

### 4단계: Slack Webhook 설정

1. https://api.slack.com/apps 방문
2. **Create New App** → **From scratch**
3. **Incoming Webhooks** 활성화
4. Webhook URL을 GitHub Secrets에 추가

자세한 내용: [GITHUB_SECRETS_SETUP.md#slack-webhook-설정](./GITHUB_SECRETS_SETUP.md#slack-webhook-설정)

### 5단계: Production Environment 설정 (수동 승인)

**Repository** → **Settings** → **Environments** → **New environment**

```
Name: production
Required reviewers: [팀원 선택]
Deployment branches: main only
```

### 6단계: 첫 배포 테스트

#### Staging 배포
```bash
# staging 브랜치 생성 (없는 경우)
git checkout -b staging
git push origin staging
```

GitHub Actions에서 자동으로 배포가 시작됩니다.

#### Production 배포
```bash
# main 브랜치에 병합
git checkout main
git merge staging
git push origin main
```

지정된 승인자가 승인하면 배포가 진행됩니다.

---

## 워크플로우 상세

### Staging 워크플로우 (.github/workflows/staging.yml)

```yaml
trigger: push to staging branch
jobs:
  1. quality-checks    # 린팅, 테스트, 타입 체크
  2. security-scan     # Trivy 보안 스캔
  3. build-and-scan    # Docker 빌드 및 이미지 스캔
  4. deploy-staging    # Auto Scaling Group 배포
  5. notify            # Slack 알림
```

**특징:**
- 자동 배포 (승인 불필요)
- 빠른 피드백 사이클
- 실패 시 자동 롤백

### Production 워크플로우 (.github/workflows/production.yml)

```yaml
trigger: push to main branch
jobs:
  1. quality-checks    # 린팅, 테스트, 커버리지
  2. security-scan     # 보안 스캔
  3. build-and-scan    # Docker 빌드 및 스캔
  4. approval          # 수동 승인 대기
  5. deploy-production # 단계별 배포
  6. notify            # Slack 알림 (성공/실패)
```

**특징:**
- 수동 승인 필요
- 단계별 배포 (25%, 50%, 75%, 100%)
- 배포 후 smoke test
- 실패 시 자동 롤백
- 긴급 알림 채널 별도 운영

---

## 배포 프로세스

### 1. 코드 푸시
```bash
git add .
git commit -m "feat: new feature"
git push origin staging  # 또는 main
```

### 2. GitHub Actions 실행
- 테스트 및 보안 스캔 자동 실행
- Docker 이미지 빌드 및 ECR 푸시

### 3. 배포 (Staging)
- Auto Scaling Group Instance Refresh 시작
- 새 인스턴스가 헬스 체크 통과 후 트래픽 전환
- 이전 인스턴스 종료

### 4. 배포 (Production)
- 승인자가 GitHub에서 수동 승인
- 단계별 배포 (25% → 50% → 75% → 100%)
- 각 단계에서 5분 대기 및 헬스 체크

### 5. 알림
- Slack으로 배포 상태 알림
- 실패 시 긴급 알림 채널로 별도 알림

---

## 추가 AWS 서비스 설정

### AWS Secrets Manager

민감한 정보를 안전하게 관리합니다.

```bash
# RDS 비밀번호 저장
aws secretsmanager create-secret \
  --name stocklab/production/rds \
  --secret-string '{
    "username": "postgres",
    "password": "YourSecurePassword",
    "host": "your-rds-endpoint",
    "port": 5432
  }'
```

자세한 내용: [aws-deployment/SECRETS_MANAGER_SETUP.md](../aws-deployment/SECRETS_MANAGER_SETUP.md)

### CloudWatch 모니터링

종합 모니터링 및 알람 설정

#### CloudWatch Agent 설치
```bash
# EC2 인스턴스에서
sudo yum install -y amazon-cloudwatch-agent
```

#### 대시보드 생성
- CPU, 메모리, 디스크 사용률
- API 응답 시간
- 에러 로그
- ALB 메트릭

#### 알람 설정
- CPU > 80% 경고
- 메모리 > 85% 경고
- 5xx 에러 발생 시 긴급 알림

자세한 내용: [aws-deployment/CLOUDWATCH_MONITORING_SETUP.md](../aws-deployment/CLOUDWATCH_MONITORING_SETUP.md)

### AWS WAF + CloudFront (선택)

보안 및 성능 향상

```bash
# WAF Web ACL 생성
aws wafv2 create-web-acl \
  --name stocklab-prod-waf \
  --scope REGIONAL \
  --default-action Allow={} \
  --rules file://waf-rules.json
```

---

## 모니터링 및 로그

### CloudWatch Logs

로그 그룹:
- `/stocklab/production/backend/application`
- `/stocklab/production/backend/errors`
- `/stocklab/production/frontend/application`
- `/stocklab/production/docker`

### Log Insights 쿼리

#### 최근 에러 조회
```sql
fields @timestamp, @message
| filter @message like /ERROR/
| sort @timestamp desc
| limit 50
```

#### API 응답 시간 분석
```sql
fields @timestamp, endpoint, duration
| filter duration > 1000
| stats avg(duration), max(duration), count() by endpoint
| sort avg(duration) desc
```

### CloudWatch Dashboards

**StockLab-Production** 대시보드:
- 실시간 시스템 메트릭
- API 성능 지표
- 에러 추이
- 헬스 체크 상태

---

## 트러블슈팅

### 배포 실패

#### 1. 이미지 빌드 실패
```bash
# 로컬에서 테스트
cd SL-Back-end
docker build -t test-backend .

cd SL-Front-End
docker build -t test-frontend .
```

#### 2. 보안 스캔 실패
```bash
# Trivy로 로컬 스캔
trivy fs ./SL-Back-end
trivy fs ./SL-Front-End
```

#### 3. Instance Refresh 실패
```bash
# Instance Refresh 상태 확인
aws autoscaling describe-instance-refreshes \
  --auto-scaling-group-name stocklab-prod-asg

# 취소 (필요한 경우)
aws autoscaling cancel-instance-refresh \
  --auto-scaling-group-name stocklab-prod-asg
```

#### 4. 헬스 체크 실패
```bash
# Target Group 헬스 확인
aws elbv2 describe-target-health \
  --target-group-arn YOUR_TARGET_GROUP_ARN

# EC2 인스턴스 로그 확인
ssh ec2-user@instance-ip
sudo docker logs sl_backend
sudo docker logs sl_frontend
```

### GitHub Actions 오류

#### Secrets 오류
```
Error: AWS credentials not configured
```

**해결:** GitHub Secrets 확인 및 재설정

#### 권한 오류
```
Error: AccessDenied
```

**해결:** IAM 사용자 권한 확인 및 정책 업데이트

---

## 비용 예상

### 개발/Staging 환경
```
EC2 (t3.medium × 2):           $60/월
RDS (db.t3.micro):             $25/월
ElastiCache (cache.t3.micro):  $15/월
ALB:                           $20/월
NAT Gateway:                   $32/월
ECR:                           $1/월
CloudWatch:                    $5/월
Secrets Manager:               $1/월
──────────────────────────────────
Total:                         ~$159/월
```

### Production 환경
```
EC2 (t3.large × 2-4):          $120-240/월
RDS (db.t3.medium, Multi-AZ):  $90/월
ElastiCache (cache.t3.medium): $50/월
ALB:                           $25/월
NAT Gateway (2개):             $64/월
ECR:                           $2/월
CloudWatch:                    $15/월
Secrets Manager:               $2/월
WAF (선택):                    $15/월
CloudFront (선택):             $20/월
──────────────────────────────────
Total:                         ~$403-523/월
```

---

## 체크리스트

### 초기 설정
- [ ] AWS 인프라 구축 (VPC, RDS, Redis, ALB, ASG)
- [ ] ECR 리포지토리 생성 (backend, frontend × 2환경)
- [ ] GitHub Secrets 설정
- [ ] Slack Webhook 설정
- [ ] Production Environment 설정

### Staging 환경
- [ ] staging 브랜치 생성
- [ ] Staging 워크플로우 테스트
- [ ] 배포 성공 확인
- [ ] Slack 알림 확인

### Production 환경
- [ ] Production 워크플로우 테스트
- [ ] 수동 승인 프로세스 테스트
- [ ] 롤백 프로세스 테스트
- [ ] Smoke test 확인

### 모니터링
- [ ] CloudWatch Agent 설치
- [ ] 대시보드 생성
- [ ] 알람 설정
- [ ] 로그 확인

### 보안
- [ ] Secrets Manager 설정
- [ ] IAM 권한 최소화
- [ ] 보안 스캔 활성화
- [ ] WAF 설정 (선택)

---

## 다음 단계

1. **성능 최적화**
   - CDN (CloudFront) 설정
   - Redis 캐싱 전략 개선
   - 데이터베이스 인덱스 최적화

2. **고급 모니터링**
   - AWS X-Ray 분산 추적
   - Custom metrics 추가
   - APM (Application Performance Monitoring)

3. **재해 복구**
   - 멀티 리전 배포
   - 자동 백업 및 복구
   - DR (Disaster Recovery) 계획

4. **보안 강화**
   - 침입 탐지 시스템 (IDS)
   - 정기 보안 감사
   - Compliance 인증

---

## 참고 문서

- [GitHub Secrets 설정](./GITHUB_SECRETS_SETUP.md)
- [AWS Secrets Manager 설정](../aws-deployment/SECRETS_MANAGER_SETUP.md)
- [CloudWatch 모니터링 설정](../aws-deployment/CLOUDWATCH_MONITORING_SETUP.md)
- [AWS 배포 가이드](../aws-deployment/README.md)
- [CI/CD 설정 가이드](../aws-deployment/CICD_SETUP_GUIDE.md)

---

## 지원

문제가 발생하면:
1. [트러블슈팅](#트러블슈팅) 섹션 확인
2. GitHub Issues 등록
3. 팀 채널에서 질문

---

**CI/CD 파이프라인 구축 완료!**

Happy Deploying! 🚀
