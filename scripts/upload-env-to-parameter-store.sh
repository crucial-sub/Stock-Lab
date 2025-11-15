#!/bin/bash

# AWS Systems Manager Parameter Store에 환경 변수를 업로드하는 스크립트
# Usage: ./upload-env-to-parameter-store.sh [environment] [env-file]
# Example: ./upload-env-to-parameter-store.sh prod .env.production

set -e

# 색상 정의
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 인자 확인
if [ "$#" -ne 2 ]; then
    echo -e "${RED}Usage: $0 [environment] [env-file]${NC}"
    echo -e "${YELLOW}Example: $0 prod .env.production${NC}"
    exit 1
fi

ENVIRONMENT=$1
ENV_FILE=$2
REGION=${AWS_REGION:-ap-northeast-2}
PREFIX="/stocklab/${ENVIRONMENT}"

# 파일 존재 확인
if [ ! -f "$ENV_FILE" ]; then
    echo -e "${RED}Error: Environment file '$ENV_FILE' not found${NC}"
    exit 1
fi

echo -e "${GREEN}=== Uploading environment variables to Parameter Store ===${NC}"
echo -e "Environment: ${YELLOW}${ENVIRONMENT}${NC}"
echo -e "Prefix: ${YELLOW}${PREFIX}${NC}"
echo -e "Region: ${YELLOW}${REGION}${NC}"
echo -e "File: ${YELLOW}${ENV_FILE}${NC}"
echo ""

# 민감한 정보를 포함하는 키 목록 (SecureString으로 저장)
SECURE_KEYS=(
    "DATABASE_URL"
    "DATABASE_SYNC_URL"
    "SECRET_KEY"
    "POSTGRES_PASSWORD"
    "REDIS_PASSWORD"
    "AWS_SECRET_ACCESS_KEY"
)

# SecureString인지 확인하는 함수
is_secure_key() {
    local key=$1
    for secure_key in "${SECURE_KEYS[@]}"; do
        if [[ "$key" == "$secure_key" ]]; then
            return 0
        fi
    done
    return 1
}

# .env 파일 파싱 및 업로드
SUCCESS_COUNT=0
FAIL_COUNT=0

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

        # 빈 값 체크
        if [[ -z "$VALUE" ]]; then
            echo -e "${YELLOW}⚠ Skipping $KEY (empty value)${NC}"
            continue
        fi

        # SecureString 여부 결정
        if is_secure_key "$KEY"; then
            PARAM_TYPE="SecureString"
        else
            PARAM_TYPE="String"
        fi

        PARAM_NAME="${PREFIX}/${KEY}"

        # Parameter Store에 업로드
        echo -n "Uploading ${KEY} (${PARAM_TYPE})... "
        if aws ssm put-parameter \
            --name "$PARAM_NAME" \
            --value "$VALUE" \
            --type "$PARAM_TYPE" \
            --overwrite \
            --region "$REGION" \
            > /dev/null 2>&1; then
            echo -e "${GREEN}✓${NC}"
            ((SUCCESS_COUNT++))
        else
            echo -e "${RED}✗${NC}"
            ((FAIL_COUNT++))
        fi
    fi
done < "$ENV_FILE"

echo ""
echo -e "${GREEN}=== Upload Complete ===${NC}"
echo -e "Success: ${GREEN}${SUCCESS_COUNT}${NC}"
echo -e "Failed: ${RED}${FAIL_COUNT}${NC}"
echo ""

# 업로드된 파라미터 확인
echo -e "${GREEN}=== Uploaded Parameters ===${NC}"
aws ssm get-parameters-by-path \
    --path "$PREFIX" \
    --region "$REGION" \
    --query "Parameters[*].Name" \
    --output table

echo ""
echo -e "${YELLOW}Note: SecureString values are encrypted and cannot be viewed in plain text${NC}"
echo -e "${YELLOW}To view a parameter: aws ssm get-parameter --name '$PREFIX/KEY' --with-decryption${NC}"
