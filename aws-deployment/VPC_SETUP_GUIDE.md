# 🌐 VPC 및 VPC Endpoint 설정 가이드

완전한 네트워크 격리와 보안을 위한 VPC 아키텍처 구성 가이드입니다.

## 📋 목차

1. [VPC 아키텍처 개요](#vpc-아키텍처-개요)
2. [VPC 생성](#vpc-생성)
3. [Subnets 구성](#subnets-구성)
4. [Internet Gateway 설정](#internet-gateway-설정)
5. [NAT Gateway 설정](#nat-gateway-설정)
6. [Route Tables 설정](#route-tables-설정)
7. [VPC Endpoints 설정](#vpc-endpoints-설정)
8. [Network ACLs (선택)](#network-acls-선택)
9. [VPC Flow Logs](#vpc-flow-logs)
10. [비용 최적화](#비용-최적화)

---

## 🏗️ VPC 아키텍처 개요

```
┌─────────────────────────────────────────────────────────────────┐
│                         VPC (10.0.0.0/16)                       │
│                                                                 │
│  ┌───────────────────────────────────────────────────────────┐ │
│  │                   Availability Zone A                     │ │
│  │                                                           │ │
│  │  ┌─────────────────────┐  ┌─────────────────────┐       │ │
│  │  │  Public Subnet A    │  │  Private Subnet A   │       │ │
│  │  │   10.0.1.0/24       │  │   10.0.11.0/24      │       │ │
│  │  │                     │  │                     │       │ │
│  │  │  - ALB              │  │  - EC2 Instances    │       │ │
│  │  │  - NAT Gateway      │  │  - Application      │       │ │
│  │  └─────────────────────┘  └─────────────────────┘       │ │
│  │                                                           │ │
│  │  ┌─────────────────────┐  ┌─────────────────────┐       │ │
│  │  │  Private DB Subnet A│  │  VPC Endpoints      │       │ │
│  │  │   10.0.21.0/24      │  │  - S3               │       │ │
│  │  │                     │  │  - CloudWatch       │       │ │
│  │  │  - RDS              │  │  - SSM              │       │ │
│  │  │  - ElastiCache      │  │  - Secrets Manager  │       │ │
│  │  └─────────────────────┘  └─────────────────────┘       │ │
│  └───────────────────────────────────────────────────────────┘ │
│                                                                 │
│  ┌───────────────────────────────────────────────────────────┐ │
│  │                   Availability Zone B                     │ │
│  │                                                           │ │
│  │  ┌─────────────────────┐  ┌─────────────────────┐       │ │
│  │  │  Public Subnet B    │  │  Private Subnet B   │       │ │
│  │  │   10.0.2.0/24       │  │   10.0.12.0/24      │       │ │
│  │  │                     │  │                     │       │ │
│  │  │  - ALB              │  │  - EC2 Instances    │       │ │
│  │  │  - NAT Gateway      │  │  - Application      │       │ │
│  │  └─────────────────────┘  └─────────────────────┘       │ │
│  │                                                           │ │
│  │  ┌─────────────────────┐                                 │ │
│  │  │  Private DB Subnet B│                                 │ │
│  │  │   10.0.22.0/24      │                                 │ │
│  │  │                     │                                 │ │
│  │  │  - RDS (Standby)    │                                 │ │
│  │  │  - ElastiCache      │                                 │ │
│  │  └─────────────────────┘                                 │ │
│  └───────────────────────────────────────────────────────────┘ │
│                                                                 │
│  Internet Gateway                                              │
└─────────────────────────────────────────────────────────────────┘
```

### 서브넷 유형 설명

- **Public Subnets**: ALB, NAT Gateway 배치 (인터넷 직접 접근)
- **Private Subnets**: EC2 인스턴스 배치 (NAT Gateway를 통해 아웃바운드만)
- **Private DB Subnets**: RDS, ElastiCache 배치 (완전히 격리)

---

## 🌐 VPC 생성

### 방법 1: AWS Console (권장)

**VPC Console → Your VPCs → Create VPC**

```
VPC settings: VPC and more (자동 설정)

Name tag: stacklab-vpc
IPv4 CIDR block: 10.0.0.0/16

Number of Availability Zones: 2
Number of public subnets: 2
Number of private subnets: 2

NAT gateways: 1 per AZ (고가용성)
VPC endpoints: S3 Gateway

Enable DNS hostnames: Yes
Enable DNS resolution: Yes
```

이 방법으로 생성하면 다음이 자동으로 구성됩니다:
- VPC (10.0.0.0/16)
- 2개 AZ에 Public/Private Subnets
- Internet Gateway
- NAT Gateways (각 AZ마다)
- Route Tables
- S3 Gateway Endpoint

### 방법 2: AWS CLI 스크립트

더 세밀한 제어가 필요한 경우 CLI 스크립트를 사용하세요.

---

## 🔧 수동 VPC 구성 (세밀한 제어)

세밀한 제어가 필요한 경우 수동으로 구성합니다.

### 1. VPC 생성

```bash
# VPC 생성
VPC_ID=$(aws ec2 create-vpc \
  --cidr-block 10.0.0.0/16 \
  --tag-specifications 'ResourceType=vpc,Tags=[{Key=Name,Value=stacklab-vpc},{Key=Project,Value=StackLab}]' \
  --region ap-northeast-2 \
  --output text \
  --query 'Vpc.VpcId')

echo "VPC Created: $VPC_ID"

# DNS 설정 활성화
aws ec2 modify-vpc-attribute \
  --vpc-id $VPC_ID \
  --enable-dns-hostnames \
  --region ap-northeast-2

aws ec2 modify-vpc-attribute \
  --vpc-id $VPC_ID \
  --enable-dns-support \
  --region ap-northeast-2
```

### 2. Internet Gateway 생성

```bash
# Internet Gateway 생성
IGW_ID=$(aws ec2 create-internet-gateway \
  --tag-specifications 'ResourceType=internet-gateway,Tags=[{Key=Name,Value=stacklab-igw}]' \
  --region ap-northeast-2 \
  --output text \
  --query 'InternetGateway.InternetGatewayId')

echo "Internet Gateway Created: $IGW_ID"

# VPC에 연결
aws ec2 attach-internet-gateway \
  --internet-gateway-id $IGW_ID \
  --vpc-id $VPC_ID \
  --region ap-northeast-2
```

### 3. Subnets 생성

```bash
# Public Subnet A (AZ-a)
PUBLIC_SUBNET_A=$(aws ec2 create-subnet \
  --vpc-id $VPC_ID \
  --cidr-block 10.0.1.0/24 \
  --availability-zone ap-northeast-2a \
  --tag-specifications 'ResourceType=subnet,Tags=[{Key=Name,Value=stacklab-public-subnet-a},{Key=Type,Value=Public}]' \
  --region ap-northeast-2 \
  --output text \
  --query 'Subnet.SubnetId')

# Public Subnet B (AZ-c)
PUBLIC_SUBNET_B=$(aws ec2 create-subnet \
  --vpc-id $VPC_ID \
  --cidr-block 10.0.2.0/24 \
  --availability-zone ap-northeast-2c \
  --tag-specifications 'ResourceType=subnet,Tags=[{Key=Name,Value=stacklab-public-subnet-b},{Key=Type,Value=Public}]' \
  --region ap-northeast-2 \
  --output text \
  --query 'Subnet.SubnetId')

# Private Subnet A (AZ-a)
PRIVATE_SUBNET_A=$(aws ec2 create-subnet \
  --vpc-id $VPC_ID \
  --cidr-block 10.0.11.0/24 \
  --availability-zone ap-northeast-2a \
  --tag-specifications 'ResourceType=subnet,Tags=[{Key=Name,Value=stacklab-private-subnet-a},{Key=Type,Value=Private}]' \
  --region ap-northeast-2 \
  --output text \
  --query 'Subnet.SubnetId')

# Private Subnet B (AZ-c)
PRIVATE_SUBNET_B=$(aws ec2 create-subnet \
  --vpc-id $VPC_ID \
  --cidr-block 10.0.12.0/24 \
  --availability-zone ap-northeast-2c \
  --tag-specifications 'ResourceType=subnet,Tags=[{Key=Name,Value=stacklab-private-subnet-b},{Key=Type,Value=Private}]' \
  --region ap-northeast-2 \
  --output text \
  --query 'Subnet.SubnetId')

# Private DB Subnet A (AZ-a)
DB_SUBNET_A=$(aws ec2 create-subnet \
  --vpc-id $VPC_ID \
  --cidr-block 10.0.21.0/24 \
  --availability-zone ap-northeast-2a \
  --tag-specifications 'ResourceType=subnet,Tags=[{Key=Name,Value=stacklab-db-subnet-a},{Key=Type,Value=DB}]' \
  --region ap-northeast-2 \
  --output text \
  --query 'Subnet.SubnetId')

# Private DB Subnet B (AZ-c)
DB_SUBNET_B=$(aws ec2 create-subnet \
  --vpc-id $VPC_ID \
  --cidr-block 10.0.22.0/24 \
  --availability-zone ap-northeast-2c \
  --tag-specifications 'ResourceType=subnet,Tags=[{Key=Name,Value=stacklab-db-subnet-b},{Key=Type,Value=DB}]' \
  --region ap-northeast-2 \
  --output text \
  --query 'Subnet.SubnetId')

# Public Subnet에 자동 Public IP 할당
aws ec2 modify-subnet-attribute \
  --subnet-id $PUBLIC_SUBNET_A \
  --map-public-ip-on-launch \
  --region ap-northeast-2

aws ec2 modify-subnet-attribute \
  --subnet-id $PUBLIC_SUBNET_B \
  --map-public-ip-on-launch \
  --region ap-northeast-2

echo "Subnets Created:"
echo "Public A: $PUBLIC_SUBNET_A"
echo "Public B: $PUBLIC_SUBNET_B"
echo "Private A: $PRIVATE_SUBNET_A"
echo "Private B: $PRIVATE_SUBNET_B"
echo "DB A: $DB_SUBNET_A"
echo "DB B: $DB_SUBNET_B"
```

### 4. NAT Gateway 생성

```bash
# Elastic IP 할당 (NAT Gateway A)
EIP_A=$(aws ec2 allocate-address \
  --domain vpc \
  --tag-specifications 'ResourceType=elastic-ip,Tags=[{Key=Name,Value=stacklab-nat-eip-a}]' \
  --region ap-northeast-2 \
  --output text \
  --query 'AllocationId')

# NAT Gateway A 생성
NAT_GW_A=$(aws ec2 create-nat-gateway \
  --subnet-id $PUBLIC_SUBNET_A \
  --allocation-id $EIP_A \
  --tag-specifications 'ResourceType=nat-gateway,Tags=[{Key=Name,Value=stacklab-nat-gw-a}]' \
  --region ap-northeast-2 \
  --output text \
  --query 'NatGateway.NatGatewayId')

# Elastic IP 할당 (NAT Gateway B)
EIP_B=$(aws ec2 allocate-address \
  --domain vpc \
  --tag-specifications 'ResourceType=elastic-ip,Tags=[{Key=Name,Value=stacklab-nat-eip-b}]' \
  --region ap-northeast-2 \
  --output text \
  --query 'AllocationId')

# NAT Gateway B 생성
NAT_GW_B=$(aws ec2 create-nat-gateway \
  --subnet-id $PUBLIC_SUBNET_B \
  --allocation-id $EIP_B \
  --tag-specifications 'ResourceType=nat-gateway,Tags=[{Key=Name,Value=stacklab-nat-gw-b}]' \
  --region ap-northeast-2 \
  --output text \
  --query 'NatGateway.NatGatewayId')

echo "NAT Gateways Created:"
echo "NAT Gateway A: $NAT_GW_A"
echo "NAT Gateway B: $NAT_GW_B"

# NAT Gateway 생성 완료 대기 (약 2-3분)
echo "Waiting for NAT Gateways to become available..."
aws ec2 wait nat-gateway-available --nat-gateway-ids $NAT_GW_A --region ap-northeast-2
aws ec2 wait nat-gateway-available --nat-gateway-ids $NAT_GW_B --region ap-northeast-2
echo "NAT Gateways are now available!"
```

### 5. Route Tables 생성 및 설정

```bash
# Public Route Table
PUBLIC_RT=$(aws ec2 create-route-table \
  --vpc-id $VPC_ID \
  --tag-specifications 'ResourceType=route-table,Tags=[{Key=Name,Value=stacklab-public-rt}]' \
  --region ap-northeast-2 \
  --output text \
  --query 'RouteTable.RouteTableId')

# Internet Gateway 라우트 추가
aws ec2 create-route \
  --route-table-id $PUBLIC_RT \
  --destination-cidr-block 0.0.0.0/0 \
  --gateway-id $IGW_ID \
  --region ap-northeast-2

# Public Subnets 연결
aws ec2 associate-route-table \
  --route-table-id $PUBLIC_RT \
  --subnet-id $PUBLIC_SUBNET_A \
  --region ap-northeast-2

aws ec2 associate-route-table \
  --route-table-id $PUBLIC_RT \
  --subnet-id $PUBLIC_SUBNET_B \
  --region ap-northeast-2

# Private Route Table A
PRIVATE_RT_A=$(aws ec2 create-route-table \
  --vpc-id $VPC_ID \
  --tag-specifications 'ResourceType=route-table,Tags=[{Key=Name,Value=stacklab-private-rt-a}]' \
  --region ap-northeast-2 \
  --output text \
  --query 'RouteTable.RouteTableId')

# NAT Gateway A 라우트 추가
aws ec2 create-route \
  --route-table-id $PRIVATE_RT_A \
  --destination-cidr-block 0.0.0.0/0 \
  --nat-gateway-id $NAT_GW_A \
  --region ap-northeast-2

# Private Subnet A 연결
aws ec2 associate-route-table \
  --route-table-id $PRIVATE_RT_A \
  --subnet-id $PRIVATE_SUBNET_A \
  --region ap-northeast-2

# Private Route Table B
PRIVATE_RT_B=$(aws ec2 create-route-table \
  --vpc-id $VPC_ID \
  --tag-specifications 'ResourceType=route-table,Tags=[{Key=Name,Value=stacklab-private-rt-b}]' \
  --region ap-northeast-2 \
  --output text \
  --query 'RouteTable.RouteTableId')

# NAT Gateway B 라우트 추가
aws ec2 create-route \
  --route-table-id $PRIVATE_RT_B \
  --destination-cidr-block 0.0.0.0/0 \
  --nat-gateway-id $NAT_GW_B \
  --region ap-northeast-2

# Private Subnet B 연결
aws ec2 associate-route-table \
  --route-table-id $PRIVATE_RT_B \
  --subnet-id $PRIVATE_SUBNET_B \
  --region ap-northeast-2

# DB Route Table (인터넷 접근 없음)
DB_RT=$(aws ec2 create-route-table \
  --vpc-id $VPC_ID \
  --tag-specifications 'ResourceType=route-table,Tags=[{Key=Name,Value=stacklab-db-rt}]' \
  --region ap-northeast-2 \
  --output text \
  --query 'RouteTable.RouteTableId')

# DB Subnets 연결
aws ec2 associate-route-table \
  --route-table-id $DB_RT \
  --subnet-id $DB_SUBNET_A \
  --region ap-northeast-2

aws ec2 associate-route-table \
  --route-table-id $DB_RT \
  --subnet-id $DB_SUBNET_B \
  --region ap-northeast-2

echo "Route Tables Created and Associated!"
```

---

## 🔌 VPC Endpoints 설정

VPC Endpoint를 사용하면 인터넷을 거치지 않고 AWS 서비스에 직접 연결할 수 있습니다.

### 장점

1. **보안**: 트래픽이 AWS 내부 네트워크를 통해 전송
2. **성능**: 지연 시간 감소, 대역폭 증가
3. **비용**: NAT Gateway 데이터 전송 비용 절감
4. **네트워크**: 인터넷 게이트웨이 불필요

### 추천 VPC Endpoints

#### 1. S3 Gateway Endpoint (무료)

```bash
# S3 Gateway Endpoint 생성
S3_ENDPOINT=$(aws ec2 create-vpc-endpoint \
  --vpc-id $VPC_ID \
  --service-name com.amazonaws.ap-northeast-2.s3 \
  --route-table-ids $PRIVATE_RT_A $PRIVATE_RT_B $DB_RT \
  --tag-specifications 'ResourceType=vpc-endpoint,Tags=[{Key=Name,Value=stacklab-s3-endpoint}]' \
  --region ap-northeast-2 \
  --output text \
  --query 'VpcEndpoint.VpcEndpointId')

echo "S3 Gateway Endpoint Created: $S3_ENDPOINT"
```

**용도**: 로그 업로드, 백업 저장, 정적 파일 저장

#### 2. CloudWatch Logs Interface Endpoint

```bash
# CloudWatch Logs Endpoint 생성
CLOUDWATCH_LOGS_ENDPOINT=$(aws ec2 create-vpc-endpoint \
  --vpc-id $VPC_ID \
  --vpc-endpoint-type Interface \
  --service-name com.amazonaws.ap-northeast-2.logs \
  --subnet-ids $PRIVATE_SUBNET_A $PRIVATE_SUBNET_B \
  --security-group-ids $VPC_ENDPOINT_SG \
  --tag-specifications 'ResourceType=vpc-endpoint,Tags=[{Key=Name,Value=stacklab-cloudwatch-logs-endpoint}]' \
  --region ap-northeast-2 \
  --output text \
  --query 'VpcEndpoint.VpcEndpointId')

echo "CloudWatch Logs Endpoint Created: $CLOUDWATCH_LOGS_ENDPOINT"
```

**용도**: 애플리케이션 로그 전송

#### 3. Systems Manager (SSM) Endpoints

```bash
# SSM Endpoint
SSM_ENDPOINT=$(aws ec2 create-vpc-endpoint \
  --vpc-id $VPC_ID \
  --vpc-endpoint-type Interface \
  --service-name com.amazonaws.ap-northeast-2.ssm \
  --subnet-ids $PRIVATE_SUBNET_A $PRIVATE_SUBNET_B \
  --security-group-ids $VPC_ENDPOINT_SG \
  --tag-specifications 'ResourceType=vpc-endpoint,Tags=[{Key=Name,Value=stacklab-ssm-endpoint}]' \
  --region ap-northeast-2 \
  --output text \
  --query 'VpcEndpoint.VpcEndpointId')

# SSM Messages Endpoint
SSM_MESSAGES_ENDPOINT=$(aws ec2 create-vpc-endpoint \
  --vpc-id $VPC_ID \
  --vpc-endpoint-type Interface \
  --service-name com.amazonaws.ap-northeast-2.ssmmessages \
  --subnet-ids $PRIVATE_SUBNET_A $PRIVATE_SUBNET_B \
  --security-group-ids $VPC_ENDPOINT_SG \
  --tag-specifications 'ResourceType=vpc-endpoint,Tags=[{Key=Name,Value=stacklab-ssm-messages-endpoint}]' \
  --region ap-northeast-2 \
  --output text \
  --query 'VpcEndpoint.VpcEndpointId')

# EC2 Messages Endpoint
EC2_MESSAGES_ENDPOINT=$(aws ec2 create-vpc-endpoint \
  --vpc-id $VPC_ID \
  --vpc-endpoint-type Interface \
  --service-name com.amazonaws.ap-northeast-2.ec2messages \
  --subnet-ids $PRIVATE_SUBNET_A $PRIVATE_SUBNET_B \
  --security-group-ids $VPC_ENDPOINT_SG \
  --tag-specifications 'ResourceType=vpc-endpoint,Tags=[{Key=Name,Value=stacklab-ec2-messages-endpoint}]' \
  --region ap-northeast-2 \
  --output text \
  --query 'VpcEndpoint.VpcEndpointId')
```

**용도**: SSH 없이 EC2 인스턴스 접근 (Session Manager), Parameter Store 접근

#### 4. Secrets Manager Endpoint

```bash
SECRETS_MANAGER_ENDPOINT=$(aws ec2 create-vpc-endpoint \
  --vpc-id $VPC_ID \
  --vpc-endpoint-type Interface \
  --service-name com.amazonaws.ap-northeast-2.secretsmanager \
  --subnet-ids $PRIVATE_SUBNET_A $PRIVATE_SUBNET_B \
  --security-group-ids $VPC_ENDPOINT_SG \
  --tag-specifications 'ResourceType=vpc-endpoint,Tags=[{Key=Name,Value=stacklab-secrets-manager-endpoint}]' \
  --region ap-northeast-2 \
  --output text \
  --query 'VpcEndpoint.VpcEndpointId')
```

**용도**: DB 비밀번호, API 키 안전하게 가져오기

#### 5. ECR Endpoints (Docker 이미지 사용 시)

```bash
# ECR API Endpoint
ECR_API_ENDPOINT=$(aws ec2 create-vpc-endpoint \
  --vpc-id $VPC_ID \
  --vpc-endpoint-type Interface \
  --service-name com.amazonaws.ap-northeast-2.ecr.api \
  --subnet-ids $PRIVATE_SUBNET_A $PRIVATE_SUBNET_B \
  --security-group-ids $VPC_ENDPOINT_SG \
  --tag-specifications 'ResourceType=vpc-endpoint,Tags=[{Key=Name,Value=stacklab-ecr-api-endpoint}]' \
  --region ap-northeast-2 \
  --output text \
  --query 'VpcEndpoint.VpcEndpointId')

# ECR Docker Endpoint
ECR_DKR_ENDPOINT=$(aws ec2 create-vpc-endpoint \
  --vpc-id $VPC_ID \
  --vpc-endpoint-type Interface \
  --service-name com.amazonaws.ap-northeast-2.ecr.dkr \
  --subnet-ids $PRIVATE_SUBNET_A $PRIVATE_SUBNET_B \
  --security-group-ids $VPC_ENDPOINT_SG \
  --tag-specifications 'ResourceType=vpc-endpoint,Tags=[{Key=Name,Value=stacklab-ecr-dkr-endpoint}]' \
  --region ap-northeast-2 \
  --output text \
  --query 'VpcEndpoint.VpcEndpointId')
```

**용도**: Private Subnet에서 Docker 이미지 pull

### VPC Endpoint Security Group

Interface Endpoint를 위한 Security Group:

```bash
VPC_ENDPOINT_SG=$(aws ec2 create-security-group \
  --group-name sl-vpc-endpoint-sg \
  --description "Security group for VPC Endpoints" \
  --vpc-id $VPC_ID \
  --region ap-northeast-2 \
  --output text \
  --query 'GroupId')

# HTTPS 인바운드 (from Private Subnets)
aws ec2 authorize-security-group-ingress \
  --group-id $VPC_ENDPOINT_SG \
  --protocol tcp \
  --port 443 \
  --cidr 10.0.0.0/16 \
  --region ap-northeast-2

# 태그 추가
aws ec2 create-tags \
  --resources $VPC_ENDPOINT_SG \
  --tags Key=Name,Value=sl-vpc-endpoint-sg \
  --region ap-northeast-2
```

---

## 🔒 Network ACLs (선택사항)

Network ACL은 서브넷 레벨의 방화벽입니다. Security Group과 함께 사용하면 더 강력한 보안을 제공합니다.

### Public Subnet NACL

```bash
PUBLIC_NACL=$(aws ec2 create-network-acl \
  --vpc-id $VPC_ID \
  --tag-specifications 'ResourceType=network-acl,Tags=[{Key=Name,Value=stacklab-public-nacl}]' \
  --region ap-northeast-2 \
  --output text \
  --query 'NetworkAcl.NetworkAclId')

# 인바운드 규칙
aws ec2 create-network-acl-entry \
  --network-acl-id $PUBLIC_NACL \
  --ingress \
  --rule-number 100 \
  --protocol tcp \
  --port-range From=80,To=80 \
  --cidr-block 0.0.0.0/0 \
  --rule-action allow \
  --region ap-northeast-2

aws ec2 create-network-acl-entry \
  --network-acl-id $PUBLIC_NACL \
  --ingress \
  --rule-number 110 \
  --protocol tcp \
  --port-range From=443,To=443 \
  --cidr-block 0.0.0.0/0 \
  --rule-action allow \
  --region ap-northeast-2

# Ephemeral ports (return traffic)
aws ec2 create-network-acl-entry \
  --network-acl-id $PUBLIC_NACL \
  --ingress \
  --rule-number 120 \
  --protocol tcp \
  --port-range From=1024,To=65535 \
  --cidr-block 0.0.0.0/0 \
  --rule-action allow \
  --region ap-northeast-2

# 아웃바운드 규칙 (모두 허용)
aws ec2 create-network-acl-entry \
  --network-acl-id $PUBLIC_NACL \
  --egress \
  --rule-number 100 \
  --protocol -1 \
  --cidr-block 0.0.0.0/0 \
  --rule-action allow \
  --region ap-northeast-2

# Public Subnets 연결
aws ec2 replace-network-acl-association \
  --association-id $(aws ec2 describe-network-acls --filters "Name=association.subnet-id,Values=$PUBLIC_SUBNET_A" --query 'NetworkAcls[0].Associations[0].NetworkAclAssociationId' --output text --region ap-northeast-2) \
  --network-acl-id $PUBLIC_NACL \
  --region ap-northeast-2

aws ec2 replace-network-acl-association \
  --association-id $(aws ec2 describe-network-acls --filters "Name=association.subnet-id,Values=$PUBLIC_SUBNET_B" --query 'NetworkAcls[0].Associations[0].NetworkAclAssociationId' --output text --region ap-northeast-2) \
  --network-acl-id $PUBLIC_NACL \
  --region ap-northeast-2
```

---

## 📊 VPC Flow Logs

네트워크 트래픽을 모니터링하고 디버깅하기 위해 VPC Flow Logs를 활성화합니다.

```bash
# CloudWatch Log Group 생성
aws logs create-log-group \
  --log-group-name /aws/vpc/stacklab-flowlogs \
  --region ap-northeast-2

# IAM Role 생성 (Flow Logs용)
# 먼저 trust policy JSON 생성
cat > /tmp/flowlogs-trust-policy.json <<'EOF'
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Service": "vpc-flow-logs.amazonaws.com"
      },
      "Action": "sts:AssumeRole"
    }
  ]
}
EOF

# IAM Role 생성
FLOWLOGS_ROLE_ARN=$(aws iam create-role \
  --role-name StackLabVPCFlowLogsRole \
  --assume-role-policy-document file:///tmp/flowlogs-trust-policy.json \
  --output text \
  --query 'Role.Arn')

# CloudWatch Logs 권한 추가
cat > /tmp/flowlogs-policy.json <<'EOF'
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "logs:CreateLogGroup",
        "logs:CreateLogStream",
        "logs:PutLogEvents",
        "logs:DescribeLogGroups",
        "logs:DescribeLogStreams"
      ],
      "Resource": "*"
    }
  ]
}
EOF

aws iam put-role-policy \
  --role-name StackLabVPCFlowLogsRole \
  --policy-name CloudWatchLogsPolicy \
  --policy-document file:///tmp/flowlogs-policy.json

# Flow Logs 생성
aws ec2 create-flow-logs \
  --resource-type VPC \
  --resource-ids $VPC_ID \
  --traffic-type ALL \
  --log-destination-type cloud-watch-logs \
  --log-group-name /aws/vpc/stacklab-flowlogs \
  --deliver-logs-permission-arn $FLOWLOGS_ROLE_ARN \
  --tag-specifications 'ResourceType=vpc-flow-log,Tags=[{Key=Name,Value=stacklab-vpc-flowlogs}]' \
  --region ap-northeast-2
```

---

## 💰 비용 최적화

### VPC 관련 비용

| 항목 | 비용 | 비고 |
|------|------|------|
| VPC | 무료 | - |
| Subnets | 무료 | - |
| Internet Gateway | 무료 | 데이터 전송 비용만 |
| NAT Gateway | ~$32/월/개 | + 데이터 전송 비용 ($0.045/GB) |
| VPC Endpoint (Gateway) | 무료 | S3, DynamoDB |
| VPC Endpoint (Interface) | ~$7/월/개 | + 데이터 전송 비용 |
| Elastic IP (사용중) | 무료 | - |
| Elastic IP (미사용) | ~$3.6/월 | - |

### 비용 절감 팁

#### 1. NAT Gateway 최적화

**개발 환경**: NAT Gateway 1개만 사용
```bash
# AZ-A의 Private Subnet만 사용하고 AZ-C는 제거
# 또는 둘 다 같은 NAT Gateway 사용
```

**비용**: $32/월 → $16/월 절약

**프로덕션 환경**: 고가용성을 위해 각 AZ에 NAT Gateway 유지

#### 2. VPC Endpoint 선택적 사용

**필수 Endpoints**:
- S3 Gateway (무료)
- CloudWatch Logs (~$7/월) - 로그 전송 비용 절감

**선택 Endpoints**:
- SSM (~$21/월, 3개) - SSH 대신 Session Manager 사용 시
- Secrets Manager (~$7/월) - 비밀번호 관리 시
- ECR (~$14/월, 2개) - Private 이미지 사용 시

#### 3. Elastic IP 관리

사용하지 않는 Elastic IP는 즉시 릴리스:
```bash
aws ec2 release-address --allocation-id <EIP-ID> --region ap-northeast-2
```

#### 4. Flow Logs 보존 기간 설정

```bash
# 로그 보존 기간을 7일로 설정
aws logs put-retention-policy \
  --log-group-name /aws/vpc/stacklab-flowlogs \
  --retention-in-days 7 \
  --region ap-northeast-2
```

---

## 📝 VPC 설정 완료 체크리스트

- [ ] VPC 생성 (10.0.0.0/16)
- [ ] Internet Gateway 생성 및 연결
- [ ] 2개 AZ에 Public Subnets 생성
- [ ] 2개 AZ에 Private Subnets 생성
- [ ] 2개 AZ에 DB Subnets 생성
- [ ] NAT Gateway 생성 (각 AZ 또는 1개)
- [ ] Public Route Table 설정
- [ ] Private Route Tables 설정
- [ ] DB Route Table 설정
- [ ] S3 Gateway Endpoint 생성
- [ ] CloudWatch Logs Interface Endpoint 생성
- [ ] SSM Interface Endpoints 생성 (선택)
- [ ] VPC Endpoint Security Group 생성
- [ ] VPC Flow Logs 활성화
- [ ] Network ACLs 설정 (선택)

---

## 🎯 다음 단계

VPC 설정이 완료되면:

1. **Security Groups 생성** → `security-groups-setup.sh`
2. **RDS Subnet Group 생성**
   ```bash
   aws rds create-db-subnet-group \
     --db-subnet-group-name sl-db-subnet-group \
     --db-subnet-group-description "Stack Lab DB Subnet Group" \
     --subnet-ids $DB_SUBNET_A $DB_SUBNET_B \
     --region ap-northeast-2
   ```

3. **ElastiCache Subnet Group 생성**
   ```bash
   aws elasticache create-cache-subnet-group \
     --cache-subnet-group-name sl-redis-subnet-group \
     --cache-subnet-group-description "Stack Lab Redis Subnet Group" \
     --subnet-ids $DB_SUBNET_A $DB_SUBNET_B \
     --region ap-northeast-2
   ```

4. **AWS_DEPLOYMENT_GUIDE.md** 계속 진행

---

## 📊 VPC 정보 저장

모든 리소스 ID를 JSON 파일로 저장:

```bash
cat > vpc-resources.json <<EOF
{
  "vpc_id": "$VPC_ID",
  "internet_gateway": "$IGW_ID",
  "subnets": {
    "public_a": "$PUBLIC_SUBNET_A",
    "public_b": "$PUBLIC_SUBNET_B",
    "private_a": "$PRIVATE_SUBNET_A",
    "private_b": "$PRIVATE_SUBNET_B",
    "db_a": "$DB_SUBNET_A",
    "db_b": "$DB_SUBNET_B"
  },
  "nat_gateways": {
    "nat_gw_a": "$NAT_GW_A",
    "nat_gw_b": "$NAT_GW_B"
  },
  "route_tables": {
    "public": "$PUBLIC_RT",
    "private_a": "$PRIVATE_RT_A",
    "private_b": "$PRIVATE_RT_B",
    "db": "$DB_RT"
  },
  "vpc_endpoints": {
    "s3": "$S3_ENDPOINT",
    "cloudwatch_logs": "$CLOUDWATCH_LOGS_ENDPOINT",
    "ssm": "$SSM_ENDPOINT",
    "vpc_endpoint_sg": "$VPC_ENDPOINT_SG"
  }
}
EOF

echo "VPC resources saved to vpc-resources.json"
```

---

**VPC 설정이 완료되었습니다! 🎉**

이제 안전하고 확장 가능한 네트워크 인프라가 준비되었습니다.
