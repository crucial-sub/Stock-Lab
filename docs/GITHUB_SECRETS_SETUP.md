# GitHub Secrets 설정 가이드

CI/CD 파이프라인에 필요한 GitHub Secrets 설정 가이드입니다.

---

## 📋 목차

1. [필수 Secrets 목록](#필수-secrets-목록)
2. [AWS Secrets 설정](#aws-secrets-설정)
3. [Slack Webhook 설정](#slack-webhook-설정)
4. [Staging 환경 Secrets](#staging-환경-secrets)
5. [Production 환경 Secrets](#production-환경-secrets)
6. [Environment 설정](#environment-설정)
7. [보안 모범 사례](#보안-모범-사례)

---

## 필수 Secrets 목록

### AWS 관련

| Secret 이름 | 설명 | 예시 |
|-------------|------|------|
| `AWS_ACCESS_KEY_ID` | AWS IAM 사용자 Access Key | `AKIAIOSFODNN7EXAMPLE` |
| `AWS_SECRET_ACCESS_KEY` | AWS IAM 사용자 Secret Key | `wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY` |

### Production 환경

| Secret 이름 | 설명 | 예시 |
|-------------|------|------|
| `ASG_NAME` | Auto Scaling Group 이름 | `stocklab-prod-asg` |
| `LAUNCH_TEMPLATE_NAME` | Launch Template 이름 | `stocklab-prod-template` |
| `TARGET_GROUP_ARN` | Target Group ARN | `arn:aws:elasticloadbalancing:...` |
| `ALB_DNS_URL` | ALB DNS 주소 | `http://stocklab-alb-123456.ap-northeast-2.elb.amazonaws.com` |
| `DOMAIN_NAME` | 도메인 이름 (선택) | `stocklab.example.com` |

### Staging 환경

| Secret 이름 | 설명 | 예시 |
|-------------|------|------|
| `STAGING_ASG_NAME` | Staging ASG 이름 | `stocklab-staging-asg` |
| `STAGING_LAUNCH_TEMPLATE_NAME` | Staging Launch Template | `stocklab-staging-template` |
| `STAGING_TARGET_GROUP_ARN` | Staging Target Group ARN | `arn:aws:elasticloadbalancing:...` |
| `STAGING_ALB_DNS_URL` | Staging ALB DNS | `http://stocklab-staging-alb-123456.ap-northeast-2.elb.amazonaws.com` |

### Slack 알림

| Secret 이름 | 설명 | 예시 |
|-------------|------|------|
| `SLACK_WEBHOOK_URL` | Slack Incoming Webhook URL | `https://hooks.slack.com/services/...` |
| `SLACK_ONCALL_WEBHOOK_URL` | 긴급 알림용 Webhook (선택) | `https://hooks.slack.com/services/...` |

---

## AWS Secrets 설정

### 1. IAM 사용자 생성

**IAM Console** → **Users** → **Create user**

```
User name: github-actions-deploy
```

**Next** 클릭

### 2. 권한 설정

**Attach policies directly** 선택

필요한 권한:
- `AmazonEC2ContainerRegistryPowerUser` (ECR 푸시용)
- 커스텀 정책 (Auto Scaling, ELB 관리)

**Create policy** → **JSON** 탭:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "autoscaling:DescribeAutoScalingGroups",
        "autoscaling:StartInstanceRefresh",
        "autoscaling:DescribeInstanceRefreshes",
        "autoscaling:CancelInstanceRefresh",
        "autoscaling:UpdateAutoScalingGroup"
      ],
      "Resource": "*"
    },
    {
      "Effect": "Allow",
      "Action": [
        "ec2:DescribeLaunchTemplates",
        "ec2:DescribeLaunchTemplateVersions",
        "ec2:CreateLaunchTemplateVersion",
        "ec2:ModifyLaunchTemplate"
      ],
      "Resource": "*"
    },
    {
      "Effect": "Allow",
      "Action": [
        "elasticloadbalancing:DescribeTargetGroups",
        "elasticloadbalancing:DescribeTargetHealth",
        "elasticloadbalancing:DescribeLoadBalancers"
      ],
      "Resource": "*"
    },
    {
      "Effect": "Allow",
      "Action": [
        "ecr:GetAuthorizationToken",
        "ecr:BatchCheckLayerAvailability",
        "ecr:GetDownloadUrlForLayer",
        "ecr:BatchGetImage",
        "ecr:PutImage",
        "ecr:InitiateLayerUpload",
        "ecr:UploadLayerPart",
        "ecr:CompleteLayerUpload"
      ],
      "Resource": "*"
    }
  ]
}
```

Policy name: `GitHubActionsDeployPolicy`

**Create policy** → 사용자에게 연결

### 3. Access Key 생성

**Security credentials** 탭 → **Create access key**

```
Use case: Application running outside AWS
```

**Access key** 및 **Secret access key** 복사 (한 번만 표시됨)

### 4. GitHub에 Secrets 추가

**GitHub Repository** → **Settings** → **Secrets and variables** → **Actions** → **New repository secret**

```
Name: AWS_ACCESS_KEY_ID
Secret: [복사한 Access Key]
```

```
Name: AWS_SECRET_ACCESS_KEY
Secret: [복사한 Secret Key]
```

---

## Slack Webhook 설정

### 1. Slack App 생성

1. https://api.slack.com/apps 방문
2. **Create New App** 클릭
3. **From scratch** 선택
4. App Name: `StockLab CI/CD Notifications`
5. Workspace 선택

### 2. Incoming Webhooks 활성화

1. **Incoming Webhooks** 클릭
2. **Activate Incoming Webhooks** 토글 ON
3. **Add New Webhook to Workspace** 클릭
4. 알림을 받을 채널 선택 (예: `#deployments`)
5. **Allow** 클릭

### 3. Webhook URL 복사

```
Webhook URL: https://hooks.slack.com/services/T00000000/B00000000/XXXXXXXXXXXXXXXXXXXX
```

### 4. GitHub에 Secret 추가

```
Name: SLACK_WEBHOOK_URL
Secret: [복사한 Webhook URL]
```

### 5. (선택) 긴급 알림용 Webhook

프로덕션 배포 실패 시 별도 채널로 알림을 보내려면:

1. 추가 Webhook 생성 (채널: `#incidents` 또는 `#alerts`)
2. GitHub Secret 추가:

```
Name: SLACK_ONCALL_WEBHOOK_URL
Secret: [긴급 알림용 Webhook URL]
```

---

## Staging 환경 Secrets

### AWS 리소스 정보 수집

```bash
# Staging ASG 이름 확인
aws autoscaling describe-auto-scaling-groups \
  --query 'AutoScalingGroups[?contains(AutoScalingGroupName, `staging`)].AutoScalingGroupName' \
  --output text

# Staging Launch Template 이름 확인
aws ec2 describe-launch-templates \
  --query 'LaunchTemplates[?contains(LaunchTemplateName, `staging`)].LaunchTemplateName' \
  --output text

# Staging Target Group ARN 확인
aws elbv2 describe-target-groups \
  --query 'TargetGroups[?contains(TargetGroupName, `staging`)].TargetGroupArn' \
  --output text

# Staging ALB DNS 확인
aws elbv2 describe-load-balancers \
  --query 'LoadBalancers[?contains(LoadBalancerName, `staging`)].DNSName' \
  --output text
```

### GitHub Secrets 추가

```
STAGING_ASG_NAME: stocklab-staging-asg
STAGING_LAUNCH_TEMPLATE_NAME: stocklab-staging-template
STAGING_TARGET_GROUP_ARN: arn:aws:elasticloadbalancing:ap-northeast-2:ACCOUNT_ID:targetgroup/stocklab-staging-tg/xxxxx
STAGING_ALB_DNS_URL: http://stocklab-staging-alb-123456.ap-northeast-2.elb.amazonaws.com
```

---

## Production 환경 Secrets

### AWS 리소스 정보 수집

```bash
# Production ASG 이름 확인
aws autoscaling describe-auto-scaling-groups \
  --query 'AutoScalingGroups[?contains(AutoScalingGroupName, `prod`)].AutoScalingGroupName' \
  --output text

# Production Launch Template 이름 확인
aws ec2 describe-launch-templates \
  --query 'LaunchTemplates[?contains(LaunchTemplateName, `prod`)].LaunchTemplateName' \
  --output text

# Production Target Group ARN 확인
aws elbv2 describe-target-groups \
  --query 'TargetGroups[?contains(TargetGroupName, `prod`)].TargetGroupArn' \
  --output text

# Production ALB DNS 확인
aws elbv2 describe-load-balancers \
  --query 'LoadBalancers[?contains(LoadBalancerName, `prod`)].DNSName' \
  --output text
```

### GitHub Secrets 추가

```
ASG_NAME: stocklab-prod-asg
LAUNCH_TEMPLATE_NAME: stocklab-prod-template
TARGET_GROUP_ARN: arn:aws:elasticloadbalancing:ap-northeast-2:ACCOUNT_ID:targetgroup/stocklab-prod-tg/xxxxx
ALB_DNS_URL: http://stocklab-prod-alb-123456.ap-northeast-2.elb.amazonaws.com
DOMAIN_NAME: stocklab.example.com
```

---

## Environment 설정

GitHub Environments를 사용하여 수동 승인 프로세스를 추가할 수 있습니다.

### Production Environment 생성

**Repository Settings** → **Environments** → **New environment**

```
Name: production
```

**Configure environment** 클릭

### 보호 규칙 설정

#### Required reviewers
```
Required reviewers: ✓
Reviewers: [팀원 선택]
```

프로덕션 배포 시 지정된 사람의 승인이 필요합니다.

#### Wait timer
```
Wait timer: 5 (선택사항)
```

배포 전 5분 대기 (취소 가능한 시간)

#### Deployment branches
```
Selected branches: main
```

main 브랜치에서만 프로덕션 배포 가능

### Environment Secrets

Environment별로 다른 시크릿을 설정할 수도 있습니다:

**production environment** → **Environment secrets** → **Add secret**

이렇게 하면 워크플로우에서 환경별로 다른 값을 사용할 수 있습니다.

---

## 보안 모범 사례

### 1. Secrets 로테이션

```bash
# 정기적으로 (3-6개월마다) Access Key 교체
aws iam create-access-key --user-name github-actions-deploy

# 이전 키 비활성화
aws iam update-access-key \
  --user-name github-actions-deploy \
  --access-key-id OLD_ACCESS_KEY \
  --status Inactive

# 새 키로 GitHub Secrets 업데이트

# 이전 키 삭제
aws iam delete-access-key \
  --user-name github-actions-deploy \
  --access-key-id OLD_ACCESS_KEY
```

### 2. 최소 권한 원칙

IAM 정책에서 필요한 최소한의 권한만 부여:

```json
{
  "Effect": "Allow",
  "Action": [
    "autoscaling:StartInstanceRefresh"
  ],
  "Resource": "arn:aws:autoscaling:ap-northeast-2:ACCOUNT_ID:autoScalingGroup:*:autoScalingGroupName/stocklab-*"
}
```

### 3. IP 제한 (선택)

GitHub Actions의 IP 범위로 제한:

```json
{
  "Condition": {
    "IpAddress": {
      "aws:SourceIp": [
        "192.30.252.0/22",
        "185.199.108.0/22",
        "140.82.112.0/20",
        "143.55.64.0/20"
      ]
    }
  }
}
```

### 4. CloudTrail 모니터링

GitHub Actions IAM 사용자의 활동 모니터링:

```bash
# 최근 활동 확인
aws cloudtrail lookup-events \
  --lookup-attributes AttributeKey=Username,AttributeValue=github-actions-deploy \
  --max-results 50
```

### 5. Secrets 암호화 확인

GitHub Secrets는 자동으로 암호화되지만, 워크플로우 로그에 출력되지 않도록 주의:

```yaml
# ❌ 나쁜 예
- name: Debug
  run: echo "Secret: ${{ secrets.AWS_SECRET_ACCESS_KEY }}"

# ✅ 좋은 예
- name: Debug
  run: echo "AWS credentials configured"
```

---

## 체크리스트

### AWS 설정
- [ ] IAM 사용자 생성
- [ ] 필요한 권한 정책 생성 및 연결
- [ ] Access Key 생성 및 안전하게 보관
- [ ] CloudTrail 모니터링 설정

### GitHub Secrets 설정
- [ ] `AWS_ACCESS_KEY_ID` 추가
- [ ] `AWS_SECRET_ACCESS_KEY` 추가
- [ ] `SLACK_WEBHOOK_URL` 추가
- [ ] `SLACK_ONCALL_WEBHOOK_URL` 추가 (선택)

### Staging 환경
- [ ] `STAGING_ASG_NAME` 추가
- [ ] `STAGING_LAUNCH_TEMPLATE_NAME` 추가
- [ ] `STAGING_TARGET_GROUP_ARN` 추가
- [ ] `STAGING_ALB_DNS_URL` 추가

### Production 환경
- [ ] `ASG_NAME` 추가
- [ ] `LAUNCH_TEMPLATE_NAME` 추가
- [ ] `TARGET_GROUP_ARN` 추가
- [ ] `ALB_DNS_URL` 추가
- [ ] `DOMAIN_NAME` 추가 (선택)

### GitHub Environments
- [ ] Production environment 생성
- [ ] Required reviewers 설정
- [ ] Deployment branches 제한

### 테스트
- [ ] Staging 워크플로우 테스트
- [ ] Production 워크플로우 테스트
- [ ] Slack 알림 테스트
- [ ] 수동 승인 프로세스 테스트

---

## 트러블슈팅

### Secrets가 인식되지 않음

```yaml
# Secrets 이름 대소문자 확인
${{ secrets.AWS_ACCESS_KEY_ID }}  # ✅
${{ secrets.aws_access_key_id }}  # ❌
```

### 권한 오류

```bash
# IAM 사용자 권한 확인
aws iam list-attached-user-policies --user-name github-actions-deploy

# 정책 내용 확인
aws iam get-policy-version \
  --policy-arn arn:aws:iam::ACCOUNT_ID:policy/GitHubActionsDeployPolicy \
  --version-id v1
```

### Slack 알림이 오지 않음

1. Webhook URL 확인
2. Slack App이 채널에 추가되었는지 확인
3. Webhook 테스트:

```bash
curl -X POST $SLACK_WEBHOOK_URL \
  -H 'Content-Type: application/json' \
  -d '{"text":"Test notification from GitHub Actions"}'
```

---

**GitHub Secrets 설정 완료! 🔐**

다음 단계: [Staging 워크플로우 테스트](../.github/workflows/staging.yml)
