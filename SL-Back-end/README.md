# SL-Back-Test

퀀트 투자 백테스트 시스템 - FastAPI 기반 백엔드

## 프로젝트 구조

```
SL-Back-Test/
├── app/                    # 애플리케이션 소스 코드
│   ├── api/routes/        # API 엔드포인트
│   │   └── backtest.py    # 백테스트 API
│   ├── core/              # 핵심 설정 (config, database, cache)
│   ├── models/            # SQLAlchemy 데이터 모델
│   ├── schemas/           # Pydantic 스키마
│   ├── services/          # 비즈니스 로직
│   │   └── simple_backtest.py
│   └── utils/             # 유틸리티
├── docs/                   # 문서 파일
├── scripts/                # 실행 스크립트
│   ├── init_db.py         # DB 초기화
│   └── run.sh             # 서버 실행
├── tests/                  # 테스트
├── .env                    # 환경 변수
├── docker-compose.yml      # Docker 구성
└── requirements.txt        # Python 의존성
```

## 기술 스택

- **Backend**: FastAPI 0.109.0
- **Database**: PostgreSQL 15
- **Cache**: Redis 7
- **ORM**: SQLAlchemy 2.0.25 (Async)
- **Data**: Pandas 2.2.3, Polars 1.15.0
- **Python**: 3.13

## 빠른 시작

### 1. 환경 설정

```bash
cp .env.example .env
# DATABASE_URL, REDIS_URL 수정
```

### 2. 데이터베이스 시작

```bash
docker start stock-lab-postgres
docker start stock-lab-redis
```

### 3. DB 초기화 및 서버 실행

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python scripts/init_db.py
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 4. API 확인

- Health: http://localhost:8000/
- Docs: http://localhost:8000/docs

## 주요 API

### 백테스트 실행

```bash
POST /api/v1/backtest/run
```

**요청 예시:**
```json
{
  "buy_conditions": [
    {"factor": "PER", "operator": "<", "value": 15},
    {"factor": "ROE", "operator": ">", "value": 10}
  ],
  "sell_conditions": [],
  "start_date": "2025-01-01",
  "end_date": "2025-06-30",
  "initial_capital": 100000000,
  "rebalance_frequency": "MONTHLY",
  "max_positions": 20,
  "position_sizing": "EQUAL_WEIGHT",
  "benchmark": "KOSPI"
}
```

### 백테스트 상태 조회

```bash
GET /api/v1/backtest/{backtestId}/status
```

### 백테스트 결과 조회

```bash
GET /api/v1/backtest/{backtestId}/result
```

## 프론트엔드 연동

- 백엔드: `http://localhost:8000`
- 프론트엔드: `http://localhost:3001`
- 프론트엔드 프로젝트: `SL-Front-End`

## 문서

상세 문서는 `docs/` 디렉토리 참조:
- [설치 가이드](docs/SETUP_GUIDE.md)
- [구현 요약](docs/IMPLEMENTATION_SUMMARY.md)
- [시스템 설계](docs/quant_simulation_design_document.md)

## 트러블슈팅

### 포트 충돌
```bash
lsof -i :8000
kill -9 <PID>
```

### DB 연결 실패
```bash
docker ps | grep postgres
docker restart stock-lab-postgres
```

## 라이선스

Proprietary
