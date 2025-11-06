#!/bin/bash
#==============================================================================
# AWS Security Groups Setup Script
# 이 스크립트는 AWS CLI를 사용하여 필요한 Security Groups를 생성합니다.
#==============================================================================

set -e

# 설정
AWS_REGION="ap-northeast-2"
VPC_ID="vpc-xxxxxxxxx"  # TODO: 실제 VPC ID로 변경
YOUR_IP="xxx.xxx.xxx.xxx/32"  # TODO: 본인의 IP 주소로 변경

echo "Creating Security Groups in region: $AWS_REGION"
echo "VPC ID: $VPC_ID"

#==============================================================================
# 1. ALB Security Group
#==============================================================================

echo "Creating ALB Security Group..."

ALB_SG_ID=$(aws ec2 create-security-group \
    --group-name sl-alb-sg \
    --description "Security group for Stack Lab Application Load Balancer" \
    --vpc-id "$VPC_ID" \
    --region "$AWS_REGION" \
    --output text \
    --query 'GroupId')

echo "ALB Security Group created: $ALB_SG_ID"

# HTTP 인바운드
aws ec2 authorize-security-group-ingress \
    --group-id "$ALB_SG_ID" \
    --protocol tcp \
    --port 80 \
    --cidr 0.0.0.0/0 \
    --region "$AWS_REGION"

# HTTPS 인바운드
aws ec2 authorize-security-group-ingress \
    --group-id "$ALB_SG_ID" \
    --protocol tcp \
    --port 443 \
    --cidr 0.0.0.0/0 \
    --region "$AWS_REGION"

# 태그 추가
aws ec2 create-tags \
    --resources "$ALB_SG_ID" \
    --tags Key=Name,Value=sl-alb-sg Key=Project,Value=StackLab \
    --region "$AWS_REGION"

#==============================================================================
# 2. EC2 Instance Security Group
#==============================================================================

echo "Creating EC2 Instance Security Group..."

EC2_SG_ID=$(aws ec2 create-security-group \
    --group-name sl-ec2-sg \
    --description "Security group for Stack Lab EC2 instances" \
    --vpc-id "$VPC_ID" \
    --region "$AWS_REGION" \
    --output text \
    --query 'GroupId')

echo "EC2 Security Group created: $EC2_SG_ID"

# Backend 포트 (from ALB)
aws ec2 authorize-security-group-ingress \
    --group-id "$EC2_SG_ID" \
    --protocol tcp \
    --port 8000 \
    --source-group "$ALB_SG_ID" \
    --region "$AWS_REGION"

# Frontend 포트 (from ALB)
aws ec2 authorize-security-group-ingress \
    --group-id "$EC2_SG_ID" \
    --protocol tcp \
    --port 3000 \
    --source-group "$ALB_SG_ID" \
    --region "$AWS_REGION"

# SSH (from your IP only)
aws ec2 authorize-security-group-ingress \
    --group-id "$EC2_SG_ID" \
    --protocol tcp \
    --port 22 \
    --cidr "$YOUR_IP" \
    --region "$AWS_REGION"

# 태그 추가
aws ec2 create-tags \
    --resources "$EC2_SG_ID" \
    --tags Key=Name,Value=sl-ec2-sg Key=Project,Value=StackLab \
    --region "$AWS_REGION"

#==============================================================================
# 3. RDS Security Group
#==============================================================================

echo "Creating RDS Security Group..."

RDS_SG_ID=$(aws ec2 create-security-group \
    --group-name sl-rds-sg \
    --description "Security group for Stack Lab RDS PostgreSQL" \
    --vpc-id "$VPC_ID" \
    --region "$AWS_REGION" \
    --output text \
    --query 'GroupId')

echo "RDS Security Group created: $RDS_SG_ID"

# PostgreSQL 포트 (from EC2)
aws ec2 authorize-security-group-ingress \
    --group-id "$RDS_SG_ID" \
    --protocol tcp \
    --port 5432 \
    --source-group "$EC2_SG_ID" \
    --region "$AWS_REGION"

# 태그 추가
aws ec2 create-tags \
    --resources "$RDS_SG_ID" \
    --tags Key=Name,Value=sl-rds-sg Key=Project,Value=StackLab \
    --region "$AWS_REGION"

#==============================================================================
# 4. ElastiCache Redis Security Group
#==============================================================================

echo "Creating ElastiCache Redis Security Group..."

REDIS_SG_ID=$(aws ec2 create-security-group \
    --group-name sl-redis-sg \
    --description "Security group for Stack Lab ElastiCache Redis" \
    --vpc-id "$VPC_ID" \
    --region "$AWS_REGION" \
    --output text \
    --query 'GroupId')

echo "Redis Security Group created: $REDIS_SG_ID"

# Redis 포트 (from EC2)
aws ec2 authorize-security-group-ingress \
    --group-id "$REDIS_SG_ID" \
    --protocol tcp \
    --port 6379 \
    --source-group "$EC2_SG_ID" \
    --region "$AWS_REGION"

# 태그 추가
aws ec2 create-tags \
    --resources "$REDIS_SG_ID" \
    --tags Key=Name,Value=sl-redis-sg Key=Project,Value=StackLab \
    --region "$AWS_REGION"

#==============================================================================
# Summary
#==============================================================================

echo ""
echo "========================================"
echo "Security Groups Created Successfully!"
echo "========================================"
echo "ALB SG ID:    $ALB_SG_ID"
echo "EC2 SG ID:    $EC2_SG_ID"
echo "RDS SG ID:    $RDS_SG_ID"
echo "Redis SG ID:  $REDIS_SG_ID"
echo "========================================"
echo ""
echo "Save these IDs for use in other AWS services!"
echo ""

# JSON 파일로 저장
cat > security-groups-ids.json <<EOF
{
  "alb_security_group": "$ALB_SG_ID",
  "ec2_security_group": "$EC2_SG_ID",
  "rds_security_group": "$RDS_SG_ID",
  "redis_security_group": "$REDIS_SG_ID"
}
EOF

echo "Security Group IDs saved to: security-groups-ids.json"
