# 🚨 Auto Scaling 사용 시 문제점 및 해결 방안

## ❌ 현재 구조로 Auto Scaling 사용 시 발생하는 문제

### 1. **데이터베이스 (PostgreSQL) 문제** 🔴 심각

#### 문제:
```
EC2-1: PostgreSQL (포트 5432) - 사용자 데이터, 전략 데이터
EC2-2: PostgreSQL (포트 5432) - 완전히 다른 데이터
EC2-3: PostgreSQL (포트 5432) - 또 다른 데이터
```

- 각 EC2 인스턴스가 **독립적인 PostgreSQL**을 실행
- 사용자 A가 EC2-1에서 회원가입 → 데이터는 EC2-1의 DB에만 저장
- 다음 요청이 EC2-2로 가면 → "사용자를 찾을 수 없습니다" 에러
- **백테스트 결과, 자동매매 전략, 포트폴리오 모두 인스턴스마다 다름**

#### 실제 시나리오:
```
1. 사용자 로그인 → EC2-1 (성공)
2. 백테스트 실행 → EC2-2 (인증 실패 - 사용자 정보 없음)
3. 포트폴리오 조회 → EC2-3 (빈 데이터 - 전략 정보 없음)
```

---

### 2. **세션/인증 (JWT 토큰) 문제** 🔴 심각

#### 문제:
- 현재: JWT 토큰이 만료되면 **Redis 블랙리스트**에 등록
- Auto Scaling 시: 각 인스턴스가 독립적인 Redis 실행
- EC2-1에서 로그아웃 → EC2-1의 Redis에만 블랙리스트 등록
- EC2-2로 요청 가면 → 로그아웃한 토큰이 여전히 유효함 (보안 취약점!)

---

### 3. **자동매매 스케줄러 문제** 🟡 중요

#### 문제:
```python
# auto_trading_scheduler.py
# 오전 7시: 종목 선정
# 오전 9시: 매수/매도 실행
```

- 각 EC2 인스턴스가 **독립적인 스케줄러** 실행
- 3개 인스턴스면 → 같은 전략이 **3번 실행**됨
- 매수 주문이 3배로 발생! (심각한 버그)

#### 실제 시나리오:
```
EC2-1: 오전 9시 - 삼성전자 10주 매수
EC2-2: 오전 9시 - 삼성전자 10주 매수  ← 중복!
EC2-3: 오전 9시 - 삼성전자 10주 매수  ← 중복!
→ 총 30주 매수 (원래는 10주만 매수해야 함)
```

---

### 4. **파일 업로드 문제** 🟡 중요

#### 문제:
- 사용자가 파일 업로드 → EC2-1의 로컬 디스크에 저장
- 다음 요청이 EC2-2로 가면 → "파일을 찾을 수 없습니다"

---

### 5. **캐시 불일치 문제** 🟡 중요

#### 문제:
- 각 인스턴스가 독립적인 Redis 캐시
- EC2-1에서 전략 A 캐시 → EC2-2는 전략 A를 DB에서 다시 조회
- 캐시 효율 감소, 성능 저하

---

## ✅ 해결 방안

### 1. **데이터베이스 외부화** (필수 🔴)

#### AWS RDS 사용
```bash
# SL-Back-end/.env
DATABASE_URL=postgresql+asyncpg://admin:password@your-rds-endpoint:5432/stocklab_db
```

**장점:**
- ✅ 모든 EC2 인스턴스가 **동일한 데이터** 공유
- ✅ 자동 백업, 복제, 고가용성
- ✅ 확장 가능 (Read Replica)

**비용:**
- RDS t3.micro: ~$15/월 (Free Tier 1년)
- RDS t3.small: ~$30/월

---

### 2. **Redis 외부화** (필수 🔴)

#### AWS ElastiCache 사용
```bash
# SL-Back-end/.env
REDIS_URL=redis://your-elasticache-endpoint:6379/0
```

**장점:**
- ✅ 모든 인스턴스가 동일한 캐시/세션 공유
- ✅ 로그아웃 토큰 블랙리스트 동기화
- ✅ 고가용성 (Multi-AZ)

**비용:**
- ElastiCache t3.micro: ~$15/월

---

### 3. **자동매매 스케줄러 분리** (필수 🔴)

#### 방법 1: AWS EventBridge + Lambda (권장)
```yaml
# Lambda 함수가 스케줄러 역할
# 오전 7시: Lambda 실행 → API Gateway → 백엔드 /auto-trading/schedule-stocks
# 오전 9시: Lambda 실행 → API Gateway → 백엔드 /auto-trading/execute-trades
```

**장점:**
- ✅ 단일 실행 보장 (중복 방지)
- ✅ 서버리스 (EC2 불필요)
- ✅ 자동 확장

**비용:**
- Lambda: ~$0 (Free Tier: 100만 요청/월)

#### 방법 2: 별도 스케줄러 EC2 (간단)
```
EC2-Scheduler (1대): 스케줄러만 실행
EC2-Worker (Auto Scaling): API 요청 처리
```

---

### 4. **파일 스토리지 외부화** (권장 🟡)

#### AWS S3 사용
```python
# 파일 업로드 시
s3.upload_file('local_file.csv', 'bucket-name', 'user123/file.csv')

# 파일 다운로드 시
s3.download_file('bucket-name', 'user123/file.csv', 'local_temp.csv')
```

**비용:**
- S3: ~$0.023/GB/월 (매우 저렴)

---

### 5. **로드 밸런서 설정** (필수 🔴)

#### AWS Application Load Balancer (ALB)
```
사용자 → ALB → EC2-1 (Backend)
              ↓   EC2-2 (Backend)
              ↓   EC2-3 (Backend)
```

**장점:**
- ✅ 자동 트래픽 분산
- ✅ Health Check (죽은 인스턴스 제외)
- ✅ Sticky Session 지원 (선택사항)

**비용:**
- ALB: ~$20/월 + 데이터 전송 비용

---

## 📊 Auto Scaling 가능한 아키텍처 (권장)

```
┌─────────────────────────────────────────────────────┐
│                   Internet Gateway                   │
└─────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────┐
│              Application Load Balancer              │
└─────────────────────────────────────────────────────┘
                          ↓
        ┌─────────────────┼─────────────────┐
        ↓                 ↓                 ↓
┌──────────────┐  ┌──────────────┐  ┌──────────────┐
│   EC2-1      │  │   EC2-2      │  │   EC2-3      │
│   Backend    │  │   Backend    │  │   Backend    │
│   Frontend   │  │   Frontend   │  │   Frontend   │
└──────────────┘  └──────────────┘  └──────────────┘
        │                 │                 │
        └─────────────────┼─────────────────┘
                          ↓
        ┌─────────────────────────────────┐
        │         AWS RDS (PostgreSQL)     │
        └─────────────────────────────────┘
                          ↓
        ┌─────────────────────────────────┐
        │       AWS ElastiCache (Redis)    │
        └─────────────────────────────────┘
                          ↓
        ┌─────────────────────────────────┐
        │    AWS EventBridge + Lambda      │
        │    (자동매매 스케줄러)              │
        └─────────────────────────────────┘
                          ↓
        ┌─────────────────────────────────┐
        │          AWS S3 (파일)           │
        └─────────────────────────────────┘
```

---

## 💰 월 예상 비용 (Auto Scaling 구성)

| 항목 | 스펙 | 비용 |
|------|------|------|
| EC2 (Auto Scaling) | t3.small × 2~5대 | $30~75/월 |
| RDS PostgreSQL | t3.micro | $15/월 |
| ElastiCache Redis | t3.micro | $15/월 |
| ALB | - | $20/월 |
| Lambda + EventBridge | - | ~$0 (Free Tier) |
| S3 | 10GB | ~$0.23/월 |
| **총합** | - | **$80~125/월** |

---

## 🎯 단계별 마이그레이션 가이드

### Phase 1: 데이터베이스 외부화 (최우선 🔴)
```bash
1. AWS RDS PostgreSQL 생성
2. 로컬 DB 백업 → RDS로 마이그레이션
3. .env 파일 수정 (DATABASE_URL)
4. 테스트 후 배포
```

### Phase 2: Redis 외부화 (우선 🔴)
```bash
1. AWS ElastiCache 생성
2. .env 파일 수정 (REDIS_URL)
3. 테스트 후 배포
```

### Phase 3: 스케줄러 분리 (우선 🔴)
```bash
1. Lambda 함수 생성 (자동매매 트리거)
2. EventBridge 규칙 설정 (7시, 9시)
3. 백엔드에서 스케줄러 제거
4. API 엔드포인트 추가 (/auto-trading/trigger)
```

### Phase 4: ALB + Auto Scaling (중요 🟡)
```bash
1. ALB 생성
2. Target Group 설정 (EC2 인스턴스)
3. Auto Scaling Group 생성
4. Health Check 설정
```

### Phase 5: S3 파일 스토리지 (선택 🟢)
```bash
1. S3 버킷 생성
2. 파일 업로드 로직 S3로 변경
3. 기존 파일 마이그레이션
```

---

## 🚦 현재 상태 vs Auto Scaling 가능 상태

### ❌ 현재 (단일 EC2)
```
✅ 간단한 구조
✅ 낮은 비용 (~$10/월)
❌ 트래픽 증가 시 확장 불가
❌ 서버 다운 시 전체 서비스 중단
❌ Auto Scaling 불가능
```

### ✅ Auto Scaling 구성 후
```
✅ 자동 확장 (트래픽 대응)
✅ 고가용성 (서버 다운 시 자동 복구)
✅ 데이터 일관성 보장
✅ 무중단 배포 가능
❌ 비용 증가 (~$100/월)
❌ 구조 복잡도 증가
```

---

## 🤔 언제 Auto Scaling이 필요한가?

### Auto Scaling 필요 ✅
- 사용자 100명 이상
- 동시 접속자 50명 이상
- 백테스트 동시 실행 10개 이상
- 서비스 다운타임 허용 불가
- 투자자 자금 실제 운용 중

### 단일 EC2로 충분 ✅
- 사용자 50명 이하
- 동시 접속자 20명 이하
- MVP/테스트 단계
- 개인 프로젝트/포트폴리오

---

## 💡 결론 및 추천

### 현재 상태 (단일 EC2):
```bash
# 그대로 사용 가능한 경우
- MVP 단계
- 사용자 수 적음 (50명 이하)
- 개발/테스트 환경
```

### 마이그레이션 필요한 경우:
```bash
# 최소한 RDS + ElastiCache는 필수
1. RDS PostgreSQL 전환 (데이터 일관성)
2. ElastiCache Redis 전환 (세션 동기화)
3. 스케줄러 Lambda로 분리 (중복 실행 방지)

# 그 후 Auto Scaling 설정
4. ALB 추가
5. Auto Scaling Group 생성
```

**지금 당장 Auto Scaling 하면?**
→ 🔴 **절대 안됨!** 데이터 불일치, 중복 실행 등 심각한 문제 발생

**먼저 해야 할 것:**
→ 🟢 RDS + ElastiCache + Lambda 스케줄러로 마이그레이션 후 Auto Scaling 설정
