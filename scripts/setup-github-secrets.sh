#!/bin/bash

# GitHub Secrets 자동 설정 스크립트
# 사용법: ./setup-github-secrets.sh

set -e

# 색상 정의
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;36m'
NC='\033[0m' # No Color

echo -e "${BLUE}================================${NC}"
echo -e "${BLUE}GitHub Secrets 자동 설정${NC}"
echo -e "${BLUE}================================${NC}"
echo ""

# GitHub CLI 설치 확인
if ! command -v gh &> /dev/null; then
    echo -e "${RED}GitHub CLI (gh)가 설치되어 있지 않습니다.${NC}"
    echo -e "${YELLOW}설치 방법:${NC}"
    echo "  macOS: brew install gh"
    echo "  Linux: https://github.com/cli/cli#installation"
    exit 1
fi

# GitHub 로그인 확인
if ! gh auth status &> /dev/null; then
    echo -e "${YELLOW}GitHub에 로그인해주세요:${NC}"
    gh auth login
fi

echo -e "${GREEN}✓ GitHub CLI 준비 완료${NC}"
echo ""

# 저장소 정보 확인
REPO=$(gh repo view --json nameWithOwner -q .nameWithOwner 2>/dev/null || echo "")
if [ -z "$REPO" ]; then
    echo -e "${RED}GitHub 저장소를 찾을 수 없습니다.${NC}"
    echo "현재 디렉토리가 Git 저장소인지 확인해주세요."
    exit 1
fi

echo -e "${BLUE}저장소: ${YELLOW}$REPO${NC}"
echo ""

# .env 파일에서 값 읽기
ENV_FILE=".env.secrets"

if [ ! -f "$ENV_FILE" ]; then
    echo -e "${YELLOW}.env.secrets 파일이 없습니다. 생성하시겠습니까? (y/n)${NC}"
    read -r CREATE_FILE

    if [ "$CREATE_FILE" = "y" ]; then
        cat > "$ENV_FILE" << 'EOF'
# GitHub Secrets 설정 파일
# 아래 값들을 실제 값으로 채워주세요

# AWS Credentials
AWS_ACCESS_KEY_ID=AKIA25BJTVF74YCFN6UL
AWS_SECRET_ACCESS_KEY=Ecm6TTid0fJ30eHTcH7+7xZ+GqR2pGtvZIT+WUHq

# AWS Resources (아래 값들을 실제 값으로 변경하세요)
ASG_NAME=your-auto-scaling-group-name
LAUNCH_TEMPLATE_NAME=your-launch-template-name
TARGET_GROUP_ARN=arn:aws:elasticloadbalancing:ap-northeast-2:123456789012:targetgroup/your-target-group/abc123
ALB_DNS_URL=http://your-alb-dns-name.ap-northeast-2.elb.amazonaws.com

# Application Secrets
SECRET_KEY=287f9da66a0d902c68afad72c7955407a26aab76c2eec17130b8a0458773e7f8
DATABASE_URL=postgresql+asyncpg://stocklabadmin:nmmteam05@your-rds-endpoint:5432/stock_lab_investment_db
REDIS_URL=redis://master.sl-redis-cluster.lvbc9o.apn2.cache.amazonaws.com:6379/0
EOF
        echo -e "${GREEN}✓ .env.secrets 파일을 생성했습니다${NC}"
        echo -e "${YELLOW}파일을 열어서 실제 값으로 수정한 후 다시 실행해주세요:${NC}"
        echo "  vi $ENV_FILE"
        exit 0
    else
        exit 1
    fi
fi

echo -e "${BLUE}================================${NC}"
echo -e "${BLUE}Secrets 등록 시작${NC}"
echo -e "${BLUE}================================${NC}"
echo ""

# 필수 Secrets 목록
REQUIRED_SECRETS=(
    "AWS_ACCESS_KEY_ID"
    "AWS_SECRET_ACCESS_KEY"
    "ASG_NAME"
    "LAUNCH_TEMPLATE_NAME"
    "TARGET_GROUP_ARN"
    "ALB_DNS_URL"
)

# 선택적 Secrets
OPTIONAL_SECRETS=(
    "SECRET_KEY"
    "DATABASE_URL"
    "REDIS_URL"
)

SUCCESS_COUNT=0
FAIL_COUNT=0
SKIP_COUNT=0

# 함수: Secret 등록
set_secret() {
    local key=$1
    local value=$2

    if [ -z "$value" ] || [[ "$value" == "your-"* ]]; then
        echo -e "${YELLOW}⚠ Skipping $key (placeholder value)${NC}"
        ((SKIP_COUNT++))
        return
    fi

    echo -n "Setting $key... "
    if echo "$value" | gh secret set "$key" -R "$REPO" 2>/dev/null; then
        echo -e "${GREEN}✓${NC}"
        ((SUCCESS_COUNT++))
    else
        echo -e "${RED}✗${NC}"
        ((FAIL_COUNT++))
    fi
}

# .env.secrets 파일에서 값 읽어서 등록
while IFS= read -r line || [ -n "$line" ]; do
    # 빈 줄과 주석 무시
    if [[ -z "$line" ]] || [[ "$line" =~ ^[[:space:]]*# ]]; then
        continue
    fi

    # KEY=VALUE 파싱
    if [[ "$line" =~ ^[[:space:]]*([A-Za-z_][A-Za-z0-9_]*)=(.*)$ ]]; then
        KEY="${BASH_REMATCH[1]}"
        VALUE="${BASH_REMATCH[2]}"

        # 따옴표 제거
        VALUE=$(echo "$VALUE" | sed -e 's/^"//' -e 's/"$//' -e "s/^'//" -e "s/'$//")

        set_secret "$KEY" "$VALUE"
    fi
done < "$ENV_FILE"

echo ""
echo -e "${BLUE}================================${NC}"
echo -e "${BLUE}완료${NC}"
echo -e "${BLUE}================================${NC}"
echo -e "성공: ${GREEN}${SUCCESS_COUNT}${NC}"
echo -e "실패: ${RED}${FAIL_COUNT}${NC}"
echo -e "건너뜀: ${YELLOW}${SKIP_COUNT}${NC}"
echo ""

if [ $SKIP_COUNT -gt 0 ]; then
    echo -e "${YELLOW}⚠ 일부 값이 placeholder입니다. .env.secrets 파일을 수정 후 다시 실행하세요.${NC}"
fi

echo -e "${GREEN}GitHub Secrets 설정이 완료되었습니다!${NC}"
echo ""
echo -e "${BLUE}다음 단계:${NC}"
echo "1. AWS 콘솔에서 실제 ASG_NAME, LAUNCH_TEMPLATE_NAME 등을 찾기"
echo "2. .env.secrets 파일 업데이트"
echo "3. 이 스크립트 다시 실행"
echo "4. git push로 배포 테스트"
