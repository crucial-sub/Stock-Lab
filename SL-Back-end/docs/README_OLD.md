# 🚀 Quant Investment API

퀀트 투자 시뮬레이션을 위한 고성능 FastAPI 백엔드

[![FastAPI](https://img.shields.io/badge/FastAPI-0.109.0-009688?logo=fastapi)](https://fastapi.tiangolo.com/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-15-336791?logo=postgresql)](https://www.postgresql.org/)
[![Polars](https://img.shields.io/badge/Polars-0.20.3-CD792C?logo=polars)](https://www.pola.rs/)
[![Python](https://img.shields.io/badge/Python-3.11+-3776AB?logo=python)](https://www.python.org/)

---

## 📋 목차

1. [프로젝트 개요](#-프로젝트-개요)
2. [주요 기능](#-주요-기능)
3. [기술 스택](#-기술-스택)
4. [시작하기](#-시작하기)
5. [API 문서](#-api-문서)
6. [팩터 목록](#-팩터-목록)
7. [백테스팅 가이드](#-백테스팅-가이드)
8. [성능 최적화](#-성능-최적화)
9. [프로젝트 구조](#-프로젝트-구조)

---

## 🎯 프로젝트 개요

한국 주식시장(KOSPI/KOSDAQ)의 **10GB+ 대용량 금융 데이터**를 효율적으로 처리하여, 퀀트 투자 팩터 계산 및 백테스팅 시뮬레이션을 제공하는 FastAPI 기반 REST API입니다.

### 특징
- ✅ **22개 퀀트 팩터** 실시간 계산 (20개 구현 완료)
- ✅ **대용량 데이터 처리**: Polars + 비동기 PostgreSQL
- ✅ **백테스팅 엔진**: 전략 검증 및 성과 분석
- ✅ **멀티 팩터 조합**: 가중치 기반 스코어링

---

## 🎨 주요 기능

### 1. 팩터 계산 API

22개의 퀀트 팩터를 계산하여 종목 순위 제공:

| 카테고리 | 팩터 (총 22개) | 상태 |
|---------|--------------|-----|
| **가치 (Value)** | PER, PBR, PSR, PCR | ✅ 4/4 |
| **퀄리티 (Quality)** | ROE, ROA, 매출총이익률, 부채비율, 유동비율 | ✅ 5/5 |
| **성장 (Growth)** | 매출증가율, 영업이익증가율, EPS증가율, 자산증가율 | ✅ 4/4 |
| **모멘텀 (Momentum)** | 3개월/12개월 수익률, 거래량, 거래대금, 52주 최고가 대비 | ✅ 5/5 |
| **규모 (Size)** | 시가총액, 매출액, 총자산 | ✅ 3/3 |
| **배당** | 배당수익률 | ❌ 0/1 (자본변동표 필요) |

### 2. 백테스팅 시뮬레이션

- **전략 구성**: 팩터 조합 + 매매 규칙
- **리밸런싱**: 일별/주별/월별/분기별
- **성과 지표**: CAGR, MDD, Sharpe Ratio, 승률 등
- **포지션 관리**: 동일가중/시가총액가중/리스크패리티

---

## 🛠️ 기술 스택

### Backend
- **FastAPI** 0.109.0 - 비동기 REST API 프레임워크
- **Uvicorn** - ASGI 서버

### Database
- **PostgreSQL** 15 (Docker) - 금융 데이터 저장
- **AsyncPG** - 비동기 PostgreSQL 드라이버
- **SQLAlchemy** 2.0 (Async) - ORM

### Data Processing (대용량 최적화)
- **Polars** 0.20.3 - Pandas 대비 10-100배 빠른 DataFrame (Rust 기반)
- **NumPy** 1.26 - 수치 계산
- **PyArrow** - 컬럼형 데이터 처리

### Caching & Performance
- **Redis** - 팩터 계산 결과 캐싱
- **Connection Pooling** - 20 base + 40 overflow

### Testing & QA
- **Pytest** - 테스트 프레임워크
- **Black** - 코드 포맷팅
- **MyPy** - 타입 체킹

---

## 🚀 시작하기

### 1. 사전 요구사항

- **Python 3.11+**
- **Docker** (PostgreSQL용)
- **Git**

### 2. 설치

```bash
# 1. 저장소 클론
git clone https://github.com/yourusername/quant-investment-api.git
cd quant-investment-api

# 2. 가상환경 생성
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 3. 의존성 설치
pip install -r requirements.txt

# 4. 환경변수 설정
cp .env.example .env
# .env 파일 수정 (DATABASE_URL, SECRET_KEY 등)
```

### 3. 데이터베이스 실행

```bash
# Docker Compose로 PostgreSQL 실행
cd /path/to/Stock-Lab
docker-compose up -d postgres

# 연결 확인
psql -h localhost -U postgres -d quant_investment_db
```

### 4. API 서버 실행

```bash
# 개발 모드 (Hot Reload)
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# 프로덕션 모드
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
```

### 5. API 문서 확인

브라우저에서 접속:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

---

## 📚 API 문서

### 기본 구조

**Base URL**: `http://localhost:8000/api/v1`

### 주요 엔드포인트

#### 1. 팩터 계산

```http
POST /api/v1/factors/{factor_id}
Content-Type: application/json

{
  "stock_codes": ["005930", "000660"],  // Optional
  "base_date": "2024-11-04",
  "market_type": "KOSPI"  // KOSPI/KOSDAQ/ALL
}
```

**Response:**
```json
{
  "factor_id": "PER",
  "factor_name": "주가수익비율",
  "base_date": "2024-11-04",
  "data": [
    {
      "stock_code": "005930",
      "company_name": "삼성전자",
      "value": 12.5,
      "rank": 1
    }
  ],
  "total_count": 2500,
  "calculation_time_ms": 1234.56
}
```

#### 2. 멀티 팩터 조합

```http
POST /api/v1/factors/multi
Content-Type: application/json

{
  "factor_ids": ["PER", "PBR", "ROE"],
  "weights": {
    "PER": 0.4,
    "PBR": 0.3,
    "ROE": 0.3
  },
  "base_date": "2024-11-04",
  "market_type": "ALL"
}
```

#### 3. 백테스팅 실행

```http
POST /api/v1/simulation/run
Content-Type: application/json

{
  "strategy_id": "uuid-here",
  "session_name": "2020-2024 저PER 전략",
  "start_date": "2020-01-01",
  "end_date": "2024-12-31",
  "initial_capital": 100000000,
  "benchmark": "KOSPI"
}
```

---

## 📊 팩터 목록

자세한 팩터 정보는 [FACTOR_IMPLEMENTATION_STATUS.md](./FACTOR_IMPLEMENTATION_STATUS.md) 참조

### 구현된 팩터 (20개)

#### 가치 팩터
1. **PER** - 주가수익비율
2. **PBR** - 주가순자산비율
3. **PSR** - 주가매출비율
4. **PCR** - 주가현금흐름비율

#### 퀄리티 팩터
5. **ROE** - 자기자본이익률
6. **ROA** - 총자산이익률
7. **매출총이익률**
8. **부채비율**
9. **유동비율**

#### 성장 팩터
10. **매출액증가율**
11. **영업이익증가율**
12. **EPS증가율**
13. **자산증가율**

#### 모멘텀 팩터
14. **3개월 수익률**
15. **12개월 수익률**
16. **거래량** (20일 평균)
17. **거래대금** (20일 평균)
18. **52주 최고가 대비**

#### 규모 팩터
19. **시가총액**
20. **매출액**
21. **총자산**

### 구현 불가 팩터 (1개)

22. **배당수익률** - 자본변동표 테이블 필요

---

## 🔍 백테스팅 가이드

### 1. 전략 생성

```python
import requests

strategy = {
    "strategy_name": "저PER + 고ROE 전략",
    "strategy_type": "VALUE",
    "backtest_start_date": "2020-01-01",
    "backtest_end_date": "2023-12-31",
    "universe_type": "KOSPI",
    "market_cap_filter": "ALL",
    "initial_capital": 100000000,
    "strategy_factors": [
        {
            "factor_id": "PER",
            "usage_type": "SCREENING",
            "operator": "LT",
            "threshold_value": 10
        },
        {
            "factor_id": "ROE",
            "usage_type": "RANKING",
            "operator": "TOP_N",
            "threshold_value": 30,
            "weight": 1.0
        }
    ],
    "trading_rule": {
        "rebalance_frequency": "MONTHLY",
        "position_sizing": "EQUAL_WEIGHT",
        "max_positions": 20,
        "commission_rate": 0.00015,
        "tax_rate": 0.0023
    }
}

response = requests.post("http://localhost:8000/api/v1/strategies", json=strategy)
strategy_id = response.json()["strategy_id"]
```

### 2. 시뮬레이션 실행

```python
simulation = {
    "strategy_id": strategy_id,
    "session_name": "2020-2023 백테스트",
    "start_date": "2020-01-01",
    "end_date": "2023-12-31",
    "initial_capital": 100000000,
    "benchmark": "KOSPI"
}

response = requests.post("http://localhost:8000/api/v1/simulation/run", json=simulation)
session_id = response.json()["session_id"]
```

### 3. 결과 조회

```python
# 통계
stats = requests.get(f"http://localhost:8000/api/v1/simulation/{session_id}/statistics")
print(stats.json())

# 일별 수익률
daily = requests.get(f"http://localhost:8000/api/v1/simulation/{session_id}/daily-values")

# 거래 내역
trades = requests.get(f"http://localhost:8000/api/v1/simulation/{session_id}/trades")
```

---

## ⚡ 성능 최적화

### 1. 대용량 데이터 처리

- **Polars DataFrame**: Pandas 대비 10-100배 빠름
- **청크 처리**: 10,000건 단위 배치
- **비동기 쿼리**: AsyncPG 사용

### 2. 데이터베이스 최적화

```sql
-- 복합 인덱스 (주가 조회)
CREATE INDEX idx_stock_prices_company_date_close
ON stock_prices(company_id, trade_date, close_price);

-- 재무제표 조회
CREATE INDEX idx_income_statements_stmt_account
ON income_statements(stmt_id, account_nm);
```

### 3. 커넥션 풀링

```python
# .env
DATABASE_POOL_SIZE=20
DATABASE_MAX_OVERFLOW=40
DATABASE_POOL_TIMEOUT=30
```

### 4. Redis 캐싱

```python
# 팩터 계산 결과 1시간 캐싱
REDIS_CACHE_TTL=3600
ENABLE_QUERY_CACHE=True
```

---

## 📁 프로젝트 구조

```
quant/
├── app/
│   ├── main.py                 # FastAPI 앱
│   ├── core/
│   │   ├── config.py          # 설정
│   │   └── database.py        # DB 연결
│   ├── models/                # SQLAlchemy 모델
│   │   ├── company.py
│   │   ├── stock_price.py
│   │   ├── financial_statement.py
│   │   └── simulation.py
│   ├── schemas/               # Pydantic 스키마
│   │   ├── factor.py
│   │   └── simulation.py
│   ├── services/              # 비즈니스 로직
│   │   ├── factor_calculator.py
│   │   └── backtest_engine.py
│   └── api/
│       └── routes/            # API 라우터
│           ├── factors.py
│           └── simulation.py
├── tests/                     # 테스트
├── requirements.txt           # 의존성
├── .env.example              # 환경변수 예시
├── README.md                 # 이 파일
└── FACTOR_IMPLEMENTATION_STATUS.md  # 팩터 상세 문서
```

---

## 🧪 테스트

```bash
# 전체 테스트
pytest

# 커버리지 포함
pytest --cov=app tests/

# 특정 테스트
pytest tests/test_factors.py -v
```

---

## 📊 데이터 요구사항

### ERD 구조

1. **companies** - 기업 마스터 (~2,500개)
2. **stock_prices** - 일별 시세 (~3,125,000개)
3. **disclosures** - 공시 정보 (~450,000개)
4. **financial_statements** - 재무제표 메타 (~12,500개)
5. **balance_sheets** - 재무상태표 (~625,000개)
6. **income_statements** - 손익계산서 (~625,000개)
7. **cashflow_statements** - 현금흐름표 (~625,000개)

자세한 ERD는 [ERD_GUIDE.md](/Users/a2/Desktop/StockLab/Stock-Lab/documents/ERD_GUIDE.md) 참조

---

## 🔮 로드맵

### v1.0.0 (현재)
- [x] 20개 팩터 API 구현
- [x] 백테스팅 엔진
- [x] 대용량 데이터 최적화

### v1.1.0 (예정)
- [ ] 배당수익률 팩터 (자본변동표 추가)
- [ ] WebSocket 실시간 스트리밍
- [ ] Grafana 대시보드 연동

### v2.0.0 (계획)
- [ ] 머신러닝 기반 팩터 조합 최적화
- [ ] 리스크 패리티 포트폴리오
- [ ] 틱 데이터 처리

---

## 🤝 기여하기

1. Fork the Project
2. Create your Feature Branch (`git checkout -b feature/AmazingFeature`)
3. Commit your Changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the Branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

---

## 📝 라이센스

MIT License - 자유롭게 사용하세요

---

## 📧 문의

프로젝트 관련 문의: [이슈 등록](https://github.com/yourusername/quant-investment-api/issues)

---

**Built with ❤️ using FastAPI & Polars**
