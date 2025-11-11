# 개발 환경 설정 완료 요약 📋

## 완료된 작업

### 1. 백테스트 시스템 설계 ✅

**생성된 파일:**
- `/SL-Back-end/docs/FACTOR_TABLE_DESIGN.md` - 팩터 테이블 설계
- `/SL-Back-end/app/schemas/backtest.py` - 스타일 스키마
- `/SL-Back-end/app/services/backtest__engine.py` - 백테스트 엔진
- `/SL-Back-end/docs/API_SPECIFICATION.md` - 새로운 API 명세서

**핵심 내용:**
- 스크린샷 기반 UI 요구사항 분석 완료
- 16개 팩터 지원 (PER, PBR, ROE, 모멘텀 등)
- 월별/연도별 성과 집계 기능
- 벤치마크 비교 기능
- 상세 거래 내역 및 포트폴리오 추적

### 2. SSH 터널링 시스템 구축 ✅

**생성된 파일:**
- `/aws-deployment/SSH_TUNNEL_SETUP.md` - 상세 SSH 터널링 가이드
- `/SL-Back-end/TUNNEL_QUICK_START.md` - 빠른 시작 가이드
- `/SL-Back-end/scripts/start-tunnel.sh` - 터널 시작 스크립트
- `/SL-Back-end/scripts/stop-tunnel.sh` - 터널 중지 스크립트
- `/SL-Back-end/scripts/check-tunnel.sh` - 터널 상태 확인 스크립트
- `/SL-Back-end/scripts/switch-env.sh` - 환경 전환 스크립트
- `/SL-Back-end/.env.tunnel.template` - 터널 환경 변수 템플릿

**핵심 내용:**
- EC2를 점프 서버로 사용하여 VPC 내부 RDS 접근
- 로컬 포트 5433을 통한 RDS 연결
- 배포 없이 로컬에서 프로덕션 DB 테스트 가능

---

## 사용 방법

### ⚠️ 백테스트 실행 시 주의사항

백테스트는 백그라운드 Task로 실행되므로, **실행 중에 코드 파일을 저장하면 앱이 재시작되어 백테스트가 중단됩니다.**

**해결 방법:**

1. **백테스트 실행 중에는 파일 저장하지 않기** (가장 간단)
   - 백테스트 완료까지 약 5분 소요
   - 코드 수정 → 저장 → 백테스트 실행 순서로 진행

2. **백테스트 파일을 reload 감지에서 제외**
   ```bash
   cd SL-Back-end
   uvicorn app.main:app --reload \
     --reload-exclude "app/services/backtest.py" \
     --reload-exclude "app/services/advanced_backtest.py"
   ```

3. **테스트 시에만 reload 끄기**
   ```bash
   # 백테스트 테스트용 (reload 없음)
   uvicorn app.main:app --port 8000

   # 일반 개발용 (reload 있음)
   uvicorn app.main:app --reload --port 8000
   ```

### 첫 설정 (최초 1회)

1. **SSH 키와 EC2 정보 설정**

   `SL-Back-end/scripts/start-tunnel.sh` 파일 수정:
   ```bash
   SSH_KEY="$HOME/.ssh/stock-lab-ec2.pem"
   EC2_HOST="ec2-xx-xx-xx-xx.ap-northeast-2.compute.amazonaws.com"
   RDS_ENDPOINT="stock-lab-rds.xxxxx.ap-northeast-2.rds.amazonaws.com"
   ```

2. **RDS 비밀번호 설정**

   ```bash
   cd /Users/a2/Desktop/Stack-Lab-Demo/SL-Back-end
   cp .env.tunnel.template .env.tunnel
   vim .env.tunnel  # YOUR_RDS_PASSWORD를 실제 비밀번호로 변경
   ```

### 일일 개발 워크플로우

**아침에 작업 시작:**
```bash
cd /Users/a2/Desktop/Stack-Lab-Demo/SL-Back-end

# 1. 터널 시작
./scripts/start-tunnel.sh

# 2. 환경 전환
./scripts/switch-env.sh tunnel

# 3. 서버 실행
uvicorn app.main:app --reload
```

**저녁에 작업 종료:**
```bash
# 1. 서버 중지 (Ctrl+C)

# 2. 터널 중지
./scripts/stop-tunnel.sh
```

---

## 기존 방식 vs 새로운 방식

### ❌ 기존 방식 (비효율적)

```
코드 수정
  ↓
커밋
  ↓
푸시
  ↓
배포 (2-5분)
  ↓
테스트
  ↓
에러 발견
  ↓
다시 처음부터 반복... 😫
```

**문제점:**
- 배포 대기 시간이 너무 김
- 사소한 수정도 전체 배포 필요
- 디버깅이 어려움

### ✅ 새로운 방식 (효율적)

```
SSH 터널 시작 (1회)
  ↓
로컬에서 개발 & 테스트 (실시간)
  ↓
프로덕션 DB로 즉시 테스트
  ↓
테스트 완료 후 배포
  ↓
배포 1회로 완료! 🎉
```

**장점:**
- 실시간 개발 & 테스트
- 프로덕션 데이터로 로컬 테스트
- 빠른 반복 개발
- 배포 전 충분한 테스트 가능

---

## 환경 모드

### 1. Local Mode (로컬 Docker)
```bash
./scripts/switch-env.sh local
```
- 용도: 초기 개발, 격리된 테스트
- DB: localhost:5432 (Docker PostgreSQL)
- 장점: 완전히 독립적, 프로덕션 영향 없음

### 2. Tunnel Mode (SSH 터널링) ⭐ 추천
```bash
./scripts/switch-env.sh tunnel
```
- 용도: 프로덕션 DB로 개발 & 테스트
- DB: localhost:5433 (RDS via SSH)
- 장점: 실제 데이터로 테스트, 배포 전 검증

### 3. Production Mode (직접 연결)
```bash
./scripts/switch-env.sh production
```
- 용도: 긴급 프로덕션 접근 (신중하게 사용)
- DB: 직접 RDS 연결
- 주의: 프로덕션 직접 연결, 매우 조심!

---

## 유용한 명령어

### 터널 관리
```bash
# 터널 시작
./scripts/start-tunnel.sh

# 터널 상태 확인
./scripts/check-tunnel.sh

# 터널 중지
./scripts/stop-tunnel.sh
```

### 환경 전환
```bash
./scripts/switch-env.sh local     # 로컬 모드
./scripts/switch-env.sh tunnel    # 터널 모드
```

### DB 연결 테스트
```bash
# psql로 연결
psql -h localhost -p 5433 -U postgres -d quant_investment_db

# 테이블 목록 확인
psql -h localhost -p 5433 -U postgres -d quant_investment_db -c "\dt"

# 백테스트 결과 조회
psql -h localhost -p 5433 -U postgres -d quant_investment_db -c "SELECT * FROM backtests LIMIT 5;"
```

---

## 필요한 AWS 정보 찾기

### EC2 Public DNS
```bash
aws ec2 describe-instances \
    --filters "Name=tag:Name,Values=stock-lab-*" \
    --query 'Reservations[0].Instances[0].PublicDnsName' \
    --output text
```

### RDS 엔드포인트
```bash
aws rds describe-db-instances \
    --db-instance-identifier stock-lab-rds \
    --query 'DBInstances[0].Endpoint.Address' \
    --output text
```

---

## 트러블슈팅

### "Permission denied (publickey)"
```bash
chmod 400 ~/.ssh/stock-lab-ec2.pem
```

### "Port 5433 already in use"
```bash
./scripts/stop-tunnel.sh
```

### "Could not connect to server"
```bash
# EC2 실행 중인지 확인
aws ec2 describe-instances --instance-ids i-xxxxx

# Security Group 확인
```

---

## 보안 체크리스트

- [x] SSH 키 파일 권한이 400으로 설정됨
- [x] `.gitignore`에 `*.pem`, `.env.tunnel` 추가됨
- [ ] EC2 SSH 키를 안전한 곳에 보관
- [ ] RDS 비밀번호를 `.env.tunnel`에만 저장
- [ ] 작업 완료 후 터널 종료 습관화

---

## 다음 단계

1. **팩터 테이블 구현**
   - DB 마이그레이션 완료 후 팩터 테이블 생성
   - 팩터 계산 배치 작업 구현

2. **백테스트 엔진 완성**
   - 더미 메서드들 실제 구현
   - 벤치마크 비교 로직 추가
   - 월별/연도별 성과 집계 완성

3. **API 엔드포인트 연결**
   - 엔진과 API 연결
   - WebSocket 실시간 업데이트 구현

4. **프론트엔드 통합**
   - 팀원과 API 응답 형식 검증
   - 차트 데이터 최적화

---

## 참고 문서

- [SSH 터널링 상세 가이드](aws-deployment/SSH_TUNNEL_SETUP.md)
- [SSH 터널링 빠른 시작](SL-Back-end/TUNNEL_QUICK_START.md)
- [팩터 테이블 설계](SL-Back-end/docs/FACTOR_TABLE_DESIGN.md)
- [API 명세서](SL-Back-end/docs/API_SPECIFICATION.md)
- [백테스트 분석 문서](BACKTEST_ANALYSIS.md)

---

## 요약

이제 다음과 같은 작업이 가능합니다:

1. ✅ **로컬에서 프로덕션 RDS 접근** - SSH 터널링으로 VPC 우회
2. ✅ **빠른 개발 & 테스트** - 배포 없이 실시간 테스트
3. ✅ **환경 쉽게 전환** - local/tunnel/production 모드 전환

**개발 속도가 10배 빨라집니다!** 🚀

문제가 있으면 언제든지 팀 채널에 문의하세요.