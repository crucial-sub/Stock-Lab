#!/bin/bash
#==============================================================================
# VPC 전체 구성 자동화 스크립트
# Stack Lab Demo - Complete VPC Setup
#==============================================================================

set -e

# 색상 정의
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 설정
AWS_REGION="${AWS_REGION:-ap-northeast-2}"
VPC_CIDR="10.0.0.0/16"
PROJECT_NAME="stacklab"

# 개발/프로덕션 모드 선택
echo -e "${YELLOW}Select deployment mode:${NC}"
echo "1) Development (1 NAT Gateway - saves money)"
echo "2) Production (2 NAT Gateways - high availability)"
read -p "Enter choice [1-2]: " DEPLOY_MODE

if [ "$DEPLOY_MODE" = "1" ]; then
    echo -e "${GREEN}Development mode selected${NC}"
    USE_SINGLE_NAT=true
else
    echo -e "${GREEN}Production mode selected${NC}"
    USE_SINGLE_NAT=false
fi

echo ""
echo "========================================"
echo "Stack Lab VPC Setup"
echo "========================================"
echo "Region: $AWS_REGION"
echo "VPC CIDR: $VPC_CIDR"
echo "Mode: $([ "$USE_SINGLE_NAT" = true ] && echo 'Development' || echo 'Production')"
echo "========================================"
echo ""

read -p "Continue? (y/n): " CONFIRM
if [ "$CONFIRM" != "y" ]; then
    echo "Aborted."
    exit 1
fi

#==============================================================================
# 1. VPC 생성
#==============================================================================

echo -e "${GREEN}[1/12] Creating VPC...${NC}"

VPC_ID=$(aws ec2 create-vpc \
  --cidr-block $VPC_CIDR \
  --tag-specifications "ResourceType=vpc,Tags=[{Key=Name,Value=${PROJECT_NAME}-vpc},{Key=Project,Value=StackLab}]" \
  --region $AWS_REGION \
  --output text \
  --query 'Vpc.VpcId')

echo "VPC Created: $VPC_ID"

# DNS 설정 활성화
aws ec2 modify-vpc-attribute --vpc-id $VPC_ID --enable-dns-hostnames --region $AWS_REGION
aws ec2 modify-vpc-attribute --vpc-id $VPC_ID --enable-dns-support --region $AWS_REGION

#==============================================================================
# 2. Internet Gateway 생성
#==============================================================================

echo -e "${GREEN}[2/12] Creating Internet Gateway...${NC}"

IGW_ID=$(aws ec2 create-internet-gateway \
  --tag-specifications "ResourceType=internet-gateway,Tags=[{Key=Name,Value=${PROJECT_NAME}-igw}]" \
  --region $AWS_REGION \
  --output text \
  --query 'InternetGateway.InternetGatewayId')

echo "Internet Gateway Created: $IGW_ID"

aws ec2 attach-internet-gateway \
  --internet-gateway-id $IGW_ID \
  --vpc-id $VPC_ID \
  --region $AWS_REGION

#==============================================================================
# 3. Subnets 생성
#==============================================================================

echo -e "${GREEN}[3/12] Creating Subnets...${NC}"

# Public Subnet A
PUBLIC_SUBNET_A=$(aws ec2 create-subnet \
  --vpc-id $VPC_ID \
  --cidr-block 10.0.1.0/24 \
  --availability-zone ${AWS_REGION}a \
  --tag-specifications "ResourceType=subnet,Tags=[{Key=Name,Value=${PROJECT_NAME}-public-subnet-a},{Key=Type,Value=Public}]" \
  --region $AWS_REGION \
  --output text \
  --query 'Subnet.SubnetId')

# Public Subnet B
PUBLIC_SUBNET_B=$(aws ec2 create-subnet \
  --vpc-id $VPC_ID \
  --cidr-block 10.0.2.0/24 \
  --availability-zone ${AWS_REGION}c \
  --tag-specifications "ResourceType=subnet,Tags=[{Key=Name,Value=${PROJECT_NAME}-public-subnet-b},{Key=Type,Value=Public}]" \
  --region $AWS_REGION \
  --output text \
  --query 'Subnet.SubnetId')

# Private Subnet A
PRIVATE_SUBNET_A=$(aws ec2 create-subnet \
  --vpc-id $VPC_ID \
  --cidr-block 10.0.11.0/24 \
  --availability-zone ${AWS_REGION}a \
  --tag-specifications "ResourceType=subnet,Tags=[{Key=Name,Value=${PROJECT_NAME}-private-subnet-a},{Key=Type,Value=Private}]" \
  --region $AWS_REGION \
  --output text \
  --query 'Subnet.SubnetId')

# Private Subnet B
PRIVATE_SUBNET_B=$(aws ec2 create-subnet \
  --vpc-id $VPC_ID \
  --cidr-block 10.0.12.0/24 \
  --availability-zone ${AWS_REGION}c \
  --tag-specifications "ResourceType=subnet,Tags=[{Key=Name,Value=${PROJECT_NAME}-private-subnet-b},{Key=Type,Value=Private}]" \
  --region $AWS_REGION \
  --output text \
  --query 'Subnet.SubnetId')

# DB Subnet A
DB_SUBNET_A=$(aws ec2 create-subnet \
  --vpc-id $VPC_ID \
  --cidr-block 10.0.21.0/24 \
  --availability-zone ${AWS_REGION}a \
  --tag-specifications "ResourceType=subnet,Tags=[{Key=Name,Value=${PROJECT_NAME}-db-subnet-a},{Key=Type,Value=DB}]" \
  --region $AWS_REGION \
  --output text \
  --query 'Subnet.SubnetId')

# DB Subnet B
DB_SUBNET_B=$(aws ec2 create-subnet \
  --vpc-id $VPC_ID \
  --cidr-block 10.0.22.0/24 \
  --availability-zone ${AWS_REGION}c \
  --tag-specifications "ResourceType=subnet,Tags=[{Key=Name,Value=${PROJECT_NAME}-db-subnet-b},{Key=Type,Value=DB}]" \
  --region $AWS_REGION \
  --output text \
  --query 'Subnet.SubnetId')

# Public Subnet에 자동 Public IP 할당
aws ec2 modify-subnet-attribute --subnet-id $PUBLIC_SUBNET_A --map-public-ip-on-launch --region $AWS_REGION
aws ec2 modify-subnet-attribute --subnet-id $PUBLIC_SUBNET_B --map-public-ip-on-launch --region $AWS_REGION

echo "Subnets Created:"
echo "  Public A: $PUBLIC_SUBNET_A"
echo "  Public B: $PUBLIC_SUBNET_B"
echo "  Private A: $PRIVATE_SUBNET_A"
echo "  Private B: $PRIVATE_SUBNET_B"
echo "  DB A: $DB_SUBNET_A"
echo "  DB B: $DB_SUBNET_B"

#==============================================================================
# 4. NAT Gateway 생성
#==============================================================================

echo -e "${GREEN}[4/12] Creating NAT Gateway(s)...${NC}"

# Elastic IP A
EIP_A=$(aws ec2 allocate-address \
  --domain vpc \
  --tag-specifications "ResourceType=elastic-ip,Tags=[{Key=Name,Value=${PROJECT_NAME}-nat-eip-a}]" \
  --region $AWS_REGION \
  --output text \
  --query 'AllocationId')

# NAT Gateway A
NAT_GW_A=$(aws ec2 create-nat-gateway \
  --subnet-id $PUBLIC_SUBNET_A \
  --allocation-id $EIP_A \
  --tag-specifications "ResourceType=nat-gateway,Tags=[{Key=Name,Value=${PROJECT_NAME}-nat-gw-a}]" \
  --region $AWS_REGION \
  --output text \
  --query 'NatGateway.NatGatewayId')

echo "NAT Gateway A Created: $NAT_GW_A"

if [ "$USE_SINGLE_NAT" = false ]; then
    # Elastic IP B
    EIP_B=$(aws ec2 allocate-address \
      --domain vpc \
      --tag-specifications "ResourceType=elastic-ip,Tags=[{Key=Name,Value=${PROJECT_NAME}-nat-eip-b}]" \
      --region $AWS_REGION \
      --output text \
      --query 'AllocationId')

    # NAT Gateway B
    NAT_GW_B=$(aws ec2 create-nat-gateway \
      --subnet-id $PUBLIC_SUBNET_B \
      --allocation-id $EIP_B \
      --tag-specifications "ResourceType=nat-gateway,Tags=[{Key=Name,Value=${PROJECT_NAME}-nat-gw-b}]" \
      --region $AWS_REGION \
      --output text \
      --query 'NatGateway.NatGatewayId')

    echo "NAT Gateway B Created: $NAT_GW_B"
else
    NAT_GW_B=$NAT_GW_A
    echo "Using single NAT Gateway for both AZs (Development mode)"
fi

echo "Waiting for NAT Gateway(s) to become available (this may take 2-3 minutes)..."
aws ec2 wait nat-gateway-available --nat-gateway-ids $NAT_GW_A --region $AWS_REGION

if [ "$USE_SINGLE_NAT" = false ]; then
    aws ec2 wait nat-gateway-available --nat-gateway-ids $NAT_GW_B --region $AWS_REGION
fi

echo -e "${GREEN}NAT Gateway(s) ready!${NC}"

#==============================================================================
# 5. Route Tables 생성
#==============================================================================

echo -e "${GREEN}[5/12] Creating Route Tables...${NC}"

# Public Route Table
PUBLIC_RT=$(aws ec2 create-route-table \
  --vpc-id $VPC_ID \
  --tag-specifications "ResourceType=route-table,Tags=[{Key=Name,Value=${PROJECT_NAME}-public-rt}]" \
  --region $AWS_REGION \
  --output text \
  --query 'RouteTable.RouteTableId')

aws ec2 create-route \
  --route-table-id $PUBLIC_RT \
  --destination-cidr-block 0.0.0.0/0 \
  --gateway-id $IGW_ID \
  --region $AWS_REGION > /dev/null

aws ec2 associate-route-table --route-table-id $PUBLIC_RT --subnet-id $PUBLIC_SUBNET_A --region $AWS_REGION > /dev/null
aws ec2 associate-route-table --route-table-id $PUBLIC_RT --subnet-id $PUBLIC_SUBNET_B --region $AWS_REGION > /dev/null

echo "Public Route Table Created: $PUBLIC_RT"

# Private Route Table A
PRIVATE_RT_A=$(aws ec2 create-route-table \
  --vpc-id $VPC_ID \
  --tag-specifications "ResourceType=route-table,Tags=[{Key=Name,Value=${PROJECT_NAME}-private-rt-a}]" \
  --region $AWS_REGION \
  --output text \
  --query 'RouteTable.RouteTableId')

aws ec2 create-route \
  --route-table-id $PRIVATE_RT_A \
  --destination-cidr-block 0.0.0.0/0 \
  --nat-gateway-id $NAT_GW_A \
  --region $AWS_REGION > /dev/null

aws ec2 associate-route-table --route-table-id $PRIVATE_RT_A --subnet-id $PRIVATE_SUBNET_A --region $AWS_REGION > /dev/null

echo "Private Route Table A Created: $PRIVATE_RT_A"

# Private Route Table B
PRIVATE_RT_B=$(aws ec2 create-route-table \
  --vpc-id $VPC_ID \
  --tag-specifications "ResourceType=route-table,Tags=[{Key=Name,Value=${PROJECT_NAME}-private-rt-b}]" \
  --region $AWS_REGION \
  --output text \
  --query 'RouteTable.RouteTableId')

aws ec2 create-route \
  --route-table-id $PRIVATE_RT_B \
  --destination-cidr-block 0.0.0.0/0 \
  --nat-gateway-id $NAT_GW_B \
  --region $AWS_REGION > /dev/null

aws ec2 associate-route-table --route-table-id $PRIVATE_RT_B --subnet-id $PRIVATE_SUBNET_B --region $AWS_REGION > /dev/null

echo "Private Route Table B Created: $PRIVATE_RT_B"

# DB Route Table
DB_RT=$(aws ec2 create-route-table \
  --vpc-id $VPC_ID \
  --tag-specifications "ResourceType=route-table,Tags=[{Key=Name,Value=${PROJECT_NAME}-db-rt}]" \
  --region $AWS_REGION \
  --output text \
  --query 'RouteTable.RouteTableId')

aws ec2 associate-route-table --route-table-id $DB_RT --subnet-id $DB_SUBNET_A --region $AWS_REGION > /dev/null
aws ec2 associate-route-table --route-table-id $DB_RT --subnet-id $DB_SUBNET_B --region $AWS_REGION > /dev/null

echo "DB Route Table Created: $DB_RT"

#==============================================================================
# 6. S3 Gateway Endpoint 생성
#==============================================================================

echo -e "${GREEN}[6/12] Creating S3 Gateway Endpoint...${NC}"

S3_ENDPOINT=$(aws ec2 create-vpc-endpoint \
  --vpc-id $VPC_ID \
  --service-name com.amazonaws.${AWS_REGION}.s3 \
  --route-table-ids $PRIVATE_RT_A $PRIVATE_RT_B $DB_RT \
  --tag-specifications "ResourceType=vpc-endpoint,Tags=[{Key=Name,Value=${PROJECT_NAME}-s3-endpoint}]" \
  --region $AWS_REGION \
  --output text \
  --query 'VpcEndpoint.VpcEndpointId')

echo "S3 Gateway Endpoint Created: $S3_ENDPOINT"

#==============================================================================
# 7. VPC Endpoint Security Group 생성
#==============================================================================

echo -e "${GREEN}[7/12] Creating VPC Endpoint Security Group...${NC}"

VPC_ENDPOINT_SG=$(aws ec2 create-security-group \
  --group-name ${PROJECT_NAME}-vpc-endpoint-sg \
  --description "Security group for VPC Endpoints" \
  --vpc-id $VPC_ID \
  --region $AWS_REGION \
  --output text \
  --query 'GroupId')

aws ec2 authorize-security-group-ingress \
  --group-id $VPC_ENDPOINT_SG \
  --protocol tcp \
  --port 443 \
  --cidr $VPC_CIDR \
  --region $AWS_REGION > /dev/null

aws ec2 create-tags \
  --resources $VPC_ENDPOINT_SG \
  --tags Key=Name,Value=${PROJECT_NAME}-vpc-endpoint-sg \
  --region $AWS_REGION

echo "VPC Endpoint Security Group Created: $VPC_ENDPOINT_SG"

#==============================================================================
# 8. CloudWatch Logs Interface Endpoint
#==============================================================================

echo -e "${GREEN}[8/12] Creating CloudWatch Logs Endpoint...${NC}"

CLOUDWATCH_LOGS_ENDPOINT=$(aws ec2 create-vpc-endpoint \
  --vpc-id $VPC_ID \
  --vpc-endpoint-type Interface \
  --service-name com.amazonaws.${AWS_REGION}.logs \
  --subnet-ids $PRIVATE_SUBNET_A $PRIVATE_SUBNET_B \
  --security-group-ids $VPC_ENDPOINT_SG \
  --tag-specifications "ResourceType=vpc-endpoint,Tags=[{Key=Name,Value=${PROJECT_NAME}-cloudwatch-logs-endpoint}]" \
  --region $AWS_REGION \
  --output text \
  --query 'VpcEndpoint.VpcEndpointId')

echo "CloudWatch Logs Endpoint Created: $CLOUDWATCH_LOGS_ENDPOINT"

#==============================================================================
# 9. SSM Endpoints (for Session Manager)
#==============================================================================

echo -e "${GREEN}[9/12] Creating SSM Endpoints...${NC}"

SSM_ENDPOINT=$(aws ec2 create-vpc-endpoint \
  --vpc-id $VPC_ID \
  --vpc-endpoint-type Interface \
  --service-name com.amazonaws.${AWS_REGION}.ssm \
  --subnet-ids $PRIVATE_SUBNET_A $PRIVATE_SUBNET_B \
  --security-group-ids $VPC_ENDPOINT_SG \
  --tag-specifications "ResourceType=vpc-endpoint,Tags=[{Key=Name,Value=${PROJECT_NAME}-ssm-endpoint}]" \
  --region $AWS_REGION \
  --output text \
  --query 'VpcEndpoint.VpcEndpointId')

SSM_MESSAGES_ENDPOINT=$(aws ec2 create-vpc-endpoint \
  --vpc-id $VPC_ID \
  --vpc-endpoint-type Interface \
  --service-name com.amazonaws.${AWS_REGION}.ssmmessages \
  --subnet-ids $PRIVATE_SUBNET_A $PRIVATE_SUBNET_B \
  --security-group-ids $VPC_ENDPOINT_SG \
  --tag-specifications "ResourceType=vpc-endpoint,Tags=[{Key=Name,Value=${PROJECT_NAME}-ssm-messages-endpoint}]" \
  --region $AWS_REGION \
  --output text \
  --query 'VpcEndpoint.VpcEndpointId')

EC2_MESSAGES_ENDPOINT=$(aws ec2 create-vpc-endpoint \
  --vpc-id $VPC_ID \
  --vpc-endpoint-type Interface \
  --service-name com.amazonaws.${AWS_REGION}.ec2messages \
  --subnet-ids $PRIVATE_SUBNET_A $PRIVATE_SUBNET_B \
  --security-group-ids $VPC_ENDPOINT_SG \
  --tag-specifications "ResourceType=vpc-endpoint,Tags=[{Key=Name,Value=${PROJECT_NAME}-ec2-messages-endpoint}]" \
  --region $AWS_REGION \
  --output text \
  --query 'VpcEndpoint.VpcEndpointId')

echo "SSM Endpoints Created"

#==============================================================================
# 10. RDS Subnet Group 생성
#==============================================================================

echo -e "${GREEN}[10/12] Creating RDS Subnet Group...${NC}"

aws rds create-db-subnet-group \
  --db-subnet-group-name ${PROJECT_NAME}-db-subnet-group \
  --db-subnet-group-description "Stack Lab DB Subnet Group" \
  --subnet-ids $DB_SUBNET_A $DB_SUBNET_B \
  --tags Key=Name,Value=${PROJECT_NAME}-db-subnet-group \
  --region $AWS_REGION > /dev/null

echo "RDS Subnet Group Created: ${PROJECT_NAME}-db-subnet-group"

#==============================================================================
# 11. ElastiCache Subnet Group 생성
#==============================================================================

echo -e "${GREEN}[11/12] Creating ElastiCache Subnet Group...${NC}"

aws elasticache create-cache-subnet-group \
  --cache-subnet-group-name ${PROJECT_NAME}-redis-subnet-group \
  --cache-subnet-group-description "Stack Lab Redis Subnet Group" \
  --subnet-ids $DB_SUBNET_A $DB_SUBNET_B \
  --region $AWS_REGION > /dev/null

echo "ElastiCache Subnet Group Created: ${PROJECT_NAME}-redis-subnet-group"

#==============================================================================
# 12. VPC 정보 저장
#==============================================================================

echo -e "${GREEN}[12/12] Saving VPC configuration...${NC}"

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
    "ssm_messages": "$SSM_MESSAGES_ENDPOINT",
    "ec2_messages": "$EC2_MESSAGES_ENDPOINT",
    "vpc_endpoint_sg": "$VPC_ENDPOINT_SG"
  },
  "subnet_groups": {
    "rds": "${PROJECT_NAME}-db-subnet-group",
    "elasticache": "${PROJECT_NAME}-redis-subnet-group"
  }
}
EOF

#==============================================================================
# 완료 요약
#==============================================================================

echo ""
echo "========================================"
echo -e "${GREEN}VPC Setup Complete!${NC}"
echo "========================================"
echo ""
echo "Resources Created:"
echo "  VPC ID: $VPC_ID"
echo "  Internet Gateway: $IGW_ID"
echo "  Public Subnets: $PUBLIC_SUBNET_A, $PUBLIC_SUBNET_B"
echo "  Private Subnets: $PRIVATE_SUBNET_A, $PRIVATE_SUBNET_B"
echo "  DB Subnets: $DB_SUBNET_A, $DB_SUBNET_B"
echo "  NAT Gateways: $NAT_GW_A$([ "$USE_SINGLE_NAT" = false ] && echo ", $NAT_GW_B" || echo " (shared)")"
echo "  VPC Endpoints: S3, CloudWatch Logs, SSM (3 endpoints)"
echo "  Subnet Groups: RDS, ElastiCache"
echo ""
echo "Configuration saved to: vpc-resources.json"
echo ""
echo "Next steps:"
echo "  1. Create Security Groups: ./security-groups-setup.sh"
echo "  2. Update VPC_ID in security-groups-setup.sh"
echo "  3. Continue with AWS_DEPLOYMENT_GUIDE.md"
echo ""
echo "========================================"
