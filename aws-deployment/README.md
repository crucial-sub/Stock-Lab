# 🚀 AWS 배포 가이드 모음

Stack Lab Demo 프로젝트를 AWS에 배포하기 위한 완전한 가이드와 자동화 스크립트 모음입니다.

## 📚 문서 구성

### 1. 📖 [VPC_SETUP_GUIDE.md](./VPC_SETUP_GUIDE.md)
**VPC 및 네트워크 인프라 구성**

- 완전한 VPC 아키텍처 (Public/Private/DB Subnets)
- Internet Gateway, NAT Gateway 설정
- Route Tables 구성
- **VPC Endpoints** 설정 (S3, CloudWatch, SSM, Secrets Manager 등)
- Network ACLs, VPC Flow Logs
- 비용 최적화 팁

**자동화 스크립트**: [`vpc-setup.sh`](./vpc-setup.sh)

### 2. 📖 [AWS_DEPLOYMENT_GUIDE.md](../AWS_DEPLOYMENT_GUIDE.md)
**완전한 AWS 배포 가이드** (메인 가이드)

- 전체 아키텍처 다이어그램
- Security Groups 설정
- RDS PostgreSQL 상세 설정
- ElastiCache Redis 설정
- Auto Scaling Group 설정
- Application Load Balancer 설정
- CloudWatch 모니터링
- 추가 권장 AWS 서비스 11가지

### 3. 📖 [QUICK_DEPLOY.md](./QUICK_DEPLOY.md)
**60-90분 빠른 배포 가이드**

- 단계별 체크리스트
- 복사/붙여넣기 가능한 명령어
- 예상 소요 시간 표시
- 문제 해결 가이드

---

## 🛠️ 자동화 스크립트

### 1. [`vpc-setup.sh`](./vpc-setup.sh)
**VPC 전체 인프라 자동 생성**

```bash
# 실행
./vpc-setup.sh

# 생성되는 리소스:
# - VPC (10.0.0.0/16)
# - 6개 Subnets (Public x2, Private x2, DB x2)
# - Internet Gateway
# - NAT Gateway (1개 또는 2개)
# - Route Tables
# - VPC Endpoints (S3, CloudWatch Logs, SSM)
# - RDS/ElastiCache Subnet Groups
```

**소요 시간**: 약 5-7분

### 2. [`security-groups-setup.sh`](./security-groups-setup.sh)
**Security Groups 자동 생성**

```bash
# 먼저 VPC ID 수정
nano security-groups-setup.sh
# VPC_ID="vpc-xxxxxxxxx" 실제 값으로 변경

# 실행
./security-groups-setup.sh

# 생성되는 Security Groups:
# - ALB Security Group (HTTP/HTTPS)
# - EC2 Security Group (8000, 3000, 22)
# - RDS Security Group (5432)
# - Redis Security Group (6379)
```

**소요 시간**: 약 2분

### 3. [`ec2-user-data.sh`](./ec2-user-data.sh)
**EC2 인스턴스 초기화 스크립트**

Launch Template의 User Data로 사용:
- Docker/Docker Compose 자동 설치
- 프로젝트 자동 클론
- 환경 변수 자동 설정
- CloudWatch Agent 설정
- 애플리케이션 자동 시작

---

## 🗺️ 배포 로드맵

### Phase 1: 네트워크 인프라 (10분)
```bash
# 1. VPC 생성
cd aws-deployment
./vpc-setup.sh

# 2. Security Groups 생성
# VPC ID를 vpc-resources.json에서 확인
cat vpc-resources.json
nano security-groups-setup.sh  # VPC_ID 수정
./security-groups-setup.sh
```

### Phase 2: 데이터베이스 (25분)
```
1. RDS PostgreSQL 생성 (15분)
2. ElastiCache Redis 생성 (10분)
```
[AWS_DEPLOYMENT_GUIDE.md](../AWS_DEPLOYMENT_GUIDE.md#rds-postgresql-설정) 참조

### Phase 3: 컴퓨팅 리소스 (30분)
```
1. EC2 인스턴스 수동 설정 (15분)
2. AMI 생성 (5분)
3. Launch Template 생성 (5분)
4. ALB + Target Groups 생성 (5분)
```

### Phase 4: Auto Scaling (15분)
```
1. Auto Scaling Group 생성 (10분)
2. 환경 변수 업데이트 (5분)
3. 테스트 및 확인
```

**총 소요 시간**: 60-90분

---

## 🏗️ 전체 아키텍처

```
Internet
   ↓
Route 53 (DNS)
   ↓
Application Load Balancer (ALB)
   ↓
┌─────────────────────────────────────────┐
│        Auto Scaling Group               │
│  ┌──────┐  ┌──────┐  ┌──────┐          │
│  │ EC2  │  │ EC2  │  │ EC2  │  ...     │
│  │  1   │  │  2   │  │  3   │          │
│  └──────┘  └──────┘  └──────┘          │
│  Min: 2, Max: 4                         │
└─────────────────────────────────────────┘
   ↓                     ↓
┌──────────────┐   ┌─────────────────┐
│RDS PostgreSQL│   │ElastiCache Redis│
│  (Multi-AZ)  │   │  (Cluster Mode) │
└──────────────┘   └─────────────────┘
```

### VPC 네트워크 구조

```
VPC (10.0.0.0/16)
├── Public Subnets (10.0.1.0/24, 10.0.2.0/24)
│   ├── ALB
│   └── NAT Gateways
├── Private Subnets (10.0.11.0/24, 10.0.12.0/24)
│   └── EC2 Instances (Auto Scaling Group)
└── DB Subnets (10.0.21.0/24, 10.0.22.0/24)
    ├── RDS PostgreSQL
    └── ElastiCache Redis
```

---

## 🔐 Security Groups 포트 설정

| Security Group | 인바운드 규칙 | 소스 |
|----------------|---------------|------|
| ALB SG | HTTP (80), HTTPS (443) | 0.0.0.0/0 |
| EC2 SG | 8000, 3000 | ALB SG |
| EC2 SG | SSH (22) | Your IP |
| RDS SG | PostgreSQL (5432) | EC2 SG |
| Redis SG | Redis (6379) | EC2 SG |
| VPC Endpoint SG | HTTPS (443) | VPC CIDR |

---

## 🔌 VPC Endpoints

### Gateway Endpoints (무료)
- **S3**: 로그 업로드, 백업 저장

### Interface Endpoints
- **CloudWatch Logs** (~$7/월): 로그 전송
- **SSM** (~$21/월, 3개): Session Manager (SSH 불필요)
- **Secrets Manager** (~$7/월): 비밀번호 관리
- **ECR** (~$14/월, 2개): Private Docker 이미지

**총 비용**: ~$49/월 (NAT Gateway 데이터 전송 비용 절감으로 상쇄 가능)

---

## 💰 예상 비용

### 개발 환경
```
EC2 (t3.medium × 2):        $60/월
RDS (db.t3.micro):          $25/월
ElastiCache (cache.t3.micro): $15/월
ALB:                        $20/월
NAT Gateway (1개):          $32/월
VPC Endpoints:              $7/월 (CloudWatch Logs만)
─────────────────────────────────
Total:                      ~$159/월
```

### 프로덕션 환경
```
EC2 (t3.medium × 2-4):      $60-120/월
RDS (db.t3.medium, Multi-AZ): $90/월
ElastiCache (cache.t3.medium): $50/월
ALB:                        $25/월
NAT Gateway (2개):          $64/월
VPC Endpoints:              $49/월
─────────────────────────────────
Total:                      ~$338-398/월
```

### 비용 절감 팁
- **Reserved Instances**: 1년 약정 시 40% 절약
- **NAT Gateway**: 개발 환경에서 1개만 사용
- **VPC Endpoints**: 필수 항목만 선택
- **Auto Scaling**: 사용량에 따라 자동 조절

---

## 📊 배포 체크리스트

### 1️⃣ VPC 설정
- [ ] VPC 생성 (10.0.0.0/16)
- [ ] Subnets 생성 (Public x2, Private x2, DB x2)
- [ ] Internet Gateway 연결
- [ ] NAT Gateway 생성
- [ ] Route Tables 설정
- [ ] S3 Gateway Endpoint 생성
- [ ] CloudWatch Logs Endpoint 생성
- [ ] SSM Endpoints 생성 (선택)

### 2️⃣ Security Groups
- [ ] ALB Security Group
- [ ] EC2 Security Group
- [ ] RDS Security Group
- [ ] Redis Security Group
- [ ] VPC Endpoint Security Group

### 3️⃣ 데이터베이스
- [ ] RDS PostgreSQL 생성
- [ ] RDS Endpoint 저장
- [ ] ElastiCache Redis 생성
- [ ] Redis Endpoint 저장

### 4️⃣ 컴퓨팅
- [ ] EC2 인스턴스 수동 설정
- [ ] 환경 변수 설정
- [ ] 애플리케이션 테스트
- [ ] AMI 생성
- [ ] Launch Template 생성

### 5️⃣ Load Balancing
- [ ] Target Groups 생성 (Backend, Frontend)
- [ ] ALB 생성
- [ ] Listener Rules 설정
- [ ] HTTPS 인증서 설정 (ACM)

### 6️⃣ Auto Scaling
- [ ] Auto Scaling Group 생성
- [ ] Scaling Policies 설정
- [ ] CloudWatch Alarms 설정

### 7️⃣ 모니터링
- [ ] CloudWatch Logs 설정
- [ ] CloudWatch Alarms 설정
- [ ] VPC Flow Logs 활성화

### 8️⃣ DNS (선택)
- [ ] Route 53 Hosted Zone
- [ ] A Record (ALB 연결)

---

## 🔧 유용한 명령어

### VPC 리소스 확인
```bash
# VPC ID 확인
aws ec2 describe-vpcs --filters "Name=tag:Name,Values=stacklab-vpc" --query 'Vpcs[0].VpcId' --output text

# Subnet IDs 확인
aws ec2 describe-subnets --filters "Name=vpc-id,Values=<VPC-ID>" --query 'Subnets[*].[SubnetId,Tags[?Key==`Name`].Value|[0],CidrBlock]' --output table

# NAT Gateway 상태 확인
aws ec2 describe-nat-gateways --filter "Name=vpc-id,Values=<VPC-ID>" --query 'NatGateways[*].[NatGatewayId,State,SubnetId]' --output table

# VPC Endpoints 확인
aws ec2 describe-vpc-endpoints --filters "Name=vpc-id,Values=<VPC-ID>" --query 'VpcEndpoints[*].[VpcEndpointId,ServiceName,State]' --output table
```

### 저장된 설정 파일 활용
```bash
# VPC 리소스 정보
cat vpc-resources.json | jq .

# Security Group IDs
cat security-groups-ids.json | jq .

# 특정 값 추출
VPC_ID=$(cat vpc-resources.json | jq -r '.vpc_id')
PRIVATE_SUBNET_A=$(cat vpc-resources.json | jq -r '.subnets.private_a')
```

---

## 🆘 문제 해결

### VPC 생성 실패
```bash
# 리전 확인
aws configure get region

# 권한 확인
aws sts get-caller-identity

# VPC 할당량 확인
aws service-quotas get-service-quota \
  --service-code vpc \
  --quota-code L-F678F1CE \
  --region ap-northeast-2
```

### NAT Gateway 생성 실패
```bash
# Elastic IP 할당량 확인
aws ec2 describe-account-attributes \
  --attribute-names max-elastic-ips \
  --region ap-northeast-2

# NAT Gateway 상태 확인
aws ec2 describe-nat-gateways \
  --nat-gateway-ids <NAT-GW-ID> \
  --region ap-northeast-2
```

### VPC Endpoint 연결 실패
```bash
# Endpoint 상태 확인
aws ec2 describe-vpc-endpoints \
  --vpc-endpoint-ids <ENDPOINT-ID> \
  --region ap-northeast-2

# DNS 설정 확인
aws ec2 describe-vpc-attribute \
  --vpc-id <VPC-ID> \
  --attribute enableDnsHostnames \
  --region ap-northeast-2
```

---

## 📞 추가 지원

- **AWS 문서**: https://docs.aws.amazon.com/
- **AWS Well-Architected**: https://aws.amazon.com/architecture/well-architected/
- **AWS Pricing Calculator**: https://calculator.aws/

---

## 🎯 다음 단계

배포가 완료되면:

1. **HTTPS 설정**: ACM 인증서 + ALB HTTPS Listener
2. **도메인 연결**: Route 53
3. **CI/CD 구축**: GitHub Actions + CodeDeploy
4. **WAF 설정**: SQL Injection, XSS 차단
5. **CloudFront**: CDN + DDoS 보호
6. **백업 설정**: AWS Backup

---

**배포를 시작하세요! 🚀**

질문이 있으시면 [QUICK_DEPLOY.md](./QUICK_DEPLOY.md)의 문제 해결 섹션을 참조하세요.
