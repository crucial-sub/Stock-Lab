#!/bin/bash

# AWS 리소스 정보를 찾아주는 스크립트

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;36m'
NC='\033[0m'

echo -e "${BLUE}================================${NC}"
echo -e "${BLUE}AWS 리소스 정보 찾기${NC}"
echo -e "${BLUE}================================${NC}"
echo ""

# AWS CLI 확인
if ! command -v aws &> /dev/null; then
    echo -e "${RED}AWS CLI가 설치되어 있지 않습니다.${NC}"
    echo -e "${YELLOW}설치 방법:${NC}"
    echo "  macOS: brew install awscli"
    echo "  Linux: https://aws.amazon.com/cli/"
    exit 1
fi

# AWS 자격증명 확인
if ! aws sts get-caller-identity &> /dev/null; then
    echo -e "${RED}AWS 자격증명이 설정되어 있지 않습니다.${NC}"
    echo -e "${YELLOW}설정 방법:${NC}"
    echo "  aws configure"
    exit 1
fi

REGION=${AWS_REGION:-ap-northeast-2}

echo -e "${GREEN}✓ AWS CLI 준비 완료${NC}"
echo -e "${BLUE}리전: ${YELLOW}$REGION${NC}"
echo ""

# Auto Scaling Groups 찾기
echo -e "${BLUE}1. Auto Scaling Groups:${NC}"
ASG_LIST=$(aws autoscaling describe-auto-scaling-groups --region $REGION --query 'AutoScalingGroups[*].[AutoScalingGroupName,DesiredCapacity,MinSize,MaxSize]' --output table 2>/dev/null || echo "")

if [ -n "$ASG_LIST" ]; then
    echo "$ASG_LIST"
    echo ""
    echo -e "${YELLOW}위 목록에서 사용할 ASG 이름을 복사하세요${NC}"
else
    echo -e "${RED}Auto Scaling Group을 찾을 수 없습니다${NC}"
fi
echo ""

# Launch Templates 찾기
echo -e "${BLUE}2. Launch Templates:${NC}"
LT_LIST=$(aws ec2 describe-launch-templates --region $REGION --query 'LaunchTemplates[*].[LaunchTemplateName,LatestVersionNumber,CreateTime]' --output table 2>/dev/null || echo "")

if [ -n "$LT_LIST" ]; then
    echo "$LT_LIST"
    echo ""
    echo -e "${YELLOW}위 목록에서 사용할 Launch Template 이름을 복사하세요${NC}"
else
    echo -e "${RED}Launch Template을 찾을 수 없습니다${NC}"
fi
echo ""

# Application Load Balancers 찾기
echo -e "${BLUE}3. Application Load Balancers:${NC}"
ALB_LIST=$(aws elbv2 describe-load-balancers --region $REGION --query 'LoadBalancers[?Type==`application`].[LoadBalancerName,DNSName,State.Code]' --output table 2>/dev/null || echo "")

if [ -n "$ALB_LIST" ]; then
    echo "$ALB_LIST"
    echo ""
    echo -e "${YELLOW}DNSName 열의 값을 ALB_DNS_URL로 사용하세요 (http:// 붙여서)${NC}"
else
    echo -e "${RED}Application Load Balancer를 찾을 수 없습니다${NC}"
fi
echo ""

# Target Groups 찾기
echo -e "${BLUE}4. Target Groups:${NC}"
TG_LIST=$(aws elbv2 describe-target-groups --region $REGION --query 'TargetGroups[*].[TargetGroupName,TargetGroupArn]' --output table 2>/dev/null || echo "")

if [ -n "$TG_LIST" ]; then
    echo "$TG_LIST"
    echo ""
    echo -e "${YELLOW}TargetGroupArn 열의 값을 TARGET_GROUP_ARN으로 사용하세요${NC}"
else
    echo -e "${RED}Target Group을 찾을 수 없습니다${NC}"
fi
echo ""

# ECR Repositories 확인
echo -e "${BLUE}5. ECR Repositories:${NC}"
ECR_LIST=$(aws ecr describe-repositories --region $REGION --query 'repositories[*].[repositoryName,repositoryUri]' --output table 2>/dev/null || echo "")

if [ -n "$ECR_LIST" ]; then
    echo "$ECR_LIST"
    echo ""
    echo -e "${GREEN}✓ ECR 저장소가 있습니다${NC}"
else
    echo -e "${YELLOW}⚠ ECR 저장소가 없습니다. 생성이 필요합니다${NC}"
fi
echo ""

echo -e "${BLUE}================================${NC}"
echo -e "${GREEN}정보 수집 완료${NC}"
echo -e "${BLUE}================================${NC}"
echo ""
echo -e "${YELLOW}다음 단계:${NC}"
echo "1. 위에서 찾은 값들을 복사"
echo "2. .env.secrets 파일에 붙여넣기"
echo "3. ./scripts/setup-github-secrets.sh 실행"
