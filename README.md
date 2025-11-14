# Stock Lab - 퀀트 투자 시뮬레이션 플랫폼

고성능 백테스팅 엔진과 54개 금융 팩터를 활용한 퀀트 투자 전략 시뮬레이션 플랫폼

---

## 🚀 빠른 시작

**백테스트 실행:**
```bash
cd Stock-Lab-Demo
docker-compose up -d
```

자세한 내용은 [QUICK_START.md](./QUICK_START.md)를 참고하세요.

---

## 📚 문서

### 핵심 문서
- **[백테스트 아키텍처](./BACKTEST_ARCHITECTURE_FINAL.md)** - 최적화된 백테스트 시스템 구조
- **[빠른 시작 가이드](./QUICK_START.md)** - 프로젝트 실행 방법

### 설정 가이드
- [도커 설정 가이드](./docs/setup/DOCKER_SETUP.md)
- [도커 vs SSH 터널 가이드](./docs/setup/DOCKER_VS_TUNNEL_GUIDE.md)
- [개발 환경 설정](./docs/setup/DEVELOPMENT_SETUP_SUMMARY.md)
- [AWS 배포 가이드](./docs/setup/AWS_DEPLOYMENT_GUIDE.md)

### 통합 가이드
- [백엔드-프론트엔드 통합](./docs/integration/INTEGRATION_GUIDE.md)
- [Next.js + FastAPI 통합](./docs/integration/NEXTJS_FASTAPI_INTEGRATION_GUIDE.md)
- [54개 팩터 계산기](./docs/integration/FACTOR_CALCULATOR_54_COMPLETE_REPORT.md)

### 프론트엔드
- [회사 정보 페이지 가이드](./docs/frontend/COMPANY_INFO_FRONTEND_GUIDE.md)
- [대시보드 구조](./docs/frontend/front-dashboard.md)

---

## 🏗️ 프로젝트 구조

```
Stock-Lab-Demo/
├── SL-Back-end/              # FastAPI 백엔드
│   ├── app/
│   │   ├── api/              # API 라우트
│   │   ├── services/         # 비즈니스 로직
│   │   │   ├── backtest.py                      # 백테스트 엔진
│   │   │   ├── backtest_integration.py          # 최적화 통합
│   │   │   ├── factor_integration.py            # 팩터 + 조건 평가
│   │   │   ├── condition_evaluator_vectorized.py # 🚀 벡터화 평가
│   │   │   └── backtest_extreme_optimized.py    # 멀티프로세싱
│   │   ├── models/           # DB 모델
│   │   └── schemas/          # Pydantic 스키마
│   └── requirements.txt
│
├── SL-Front-end/             # Next.js 프론트엔드
│   ├── src/
│   │   ├── app/              # Next.js 13 app router
│   │   ├── components/       # React 컴포넌트
│   │   └── lib/              # 유틸리티
│   └── package.json
│
├── scripts/                  # 배포/실행 스크립트
├── docs/                     # 문서
│   ├── setup/                # 설정 가이드
│   ├── integration/          # 통합 가이드
│   ├── frontend/             # 프론트엔드 가이드
│   └── archive/              # 이전 문서 보관
│
├── docker-compose.yml        # 도커 컴포즈 설정
└── README.md                 # 이 파일
```

---

## ⚡ 성능

### 백테스트 속도 (최적화 적용 후)
- **1개월 백테스트:** 3-5초 (기존 대비 7-10배 개선)
- **1년 백테스트:** 25-35초 (기존 대비 10-14배 개선)

### 적용된 최적화
1. 병렬 데이터 로드 (40% 개선)
2. 멀티프로세싱 팩터 계산 (10배 개선)
3. 포트폴리오 벡터화 (10-20배 개선)
4. DB UPSERT 최적화 (10배 개선)
5. 재무 팩터 캐싱 (244배 절감)
6. **벡터화 조건 평가 (500-1000배 개선)** ⚡⚡⚡

자세한 내용은 [백테스트 아키텍처](./BACKTEST_ARCHITECTURE_FINAL.md)를 참고하세요.

---

## 🔧 기술 스택

### Backend
- **FastAPI** - 고성능 Python 웹 프레임워크
- **PostgreSQL** - 데이터베이스
- **Redis** - 캐싱
- **Pandas/Polars** - 데이터 처리
- **Numba** - JIT 컴파일 최적화
- **SQLAlchemy** - ORM

### Frontend
- **Next.js 13** - React 프레임워크 (App Router)
- **TypeScript** - 타입 안전성
- **Tailwind CSS** - 스타일링
- **Recharts** - 차트 라이브러리

### DevOps
- **Docker** - 컨테이너화
- **Docker Compose** - 오케스트레이션
- **AWS EC2** - 배포

---

## 📊 주요 기능

### 1. 백테스트 엔진
- 논리식 기반 매수/매도 조건
- 리밸런싱 (일간/월간)
- 목표가/손절가 관리
- 포지션 추적 및 체결 시뮬레이션

### 2. 팩터 시스템
- **54개 금융 팩터** 자동 계산
  - 기술적 지표 (RSI, MACD, Bollinger Bands 등)
  - 재무 지표 (PER, PBR, ROE, ROA 등)
  - 모멘텀 지표 (1M, 3M, 6M, 12M)
- 팩터 랭킹 및 스코어링

### 3. 성능 분석
- 일간/월간/연간 수익률
- MDD (Maximum Drawdown)
- Sharpe Ratio
- 승률 및 손익비
- 벤치마크 대비 성과

---

## 🚀 배포

### 개발 환경
```bash
docker-compose up -d
```

### 프로덕션 환경
자세한 내용은 [AWS 배포 가이드](./docs/setup/AWS_DEPLOYMENT_GUIDE.md)를 참고하세요.

---

## 📝 라이센스

이 프로젝트는 비공개 프로젝트입니다.

---

## 🤝 기여

내부 프로젝트로 외부 기여는 받지 않습니다.

---

## 📮 문의

프로젝트 관련 문의사항이 있으시면 팀에 문의해주세요.
