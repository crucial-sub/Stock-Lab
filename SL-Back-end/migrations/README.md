# Stock Universe History 설정 가이드

## 개요

stock_universe_history 테이블은 시간에 따른 종목의 유니버스 분류를 추적합니다.
백테스트 시 각 시점의 정확한 유니버스 분류를 사용하여 정확한 시뮬레이션을 제공합니다.

## 설치 순서

### 1단계: 테이블 생성

```bash
# PostgreSQL 접속
psql -U stocklabadmin -d stock_lab_investment_db

# 또는 Docker를 통해
docker exec -it sl_postgres_dev psql -U stocklabadmin -d stock_lab_investment_db

# SQL 파일 실행
\i /path/to/migrations/001_create_stock_universe_history.sql
```

**또는 직접 SQL 실행:**
```bash
cd /Users/a2/Desktop/Stock-Lab-Demo/SL-Back-end
psql -U stocklabadmin -d stock_lab_investment_db -f migrations/001_create_stock_universe_history.sql
```

### 2단계: 초기 데이터 채우기

```bash
# 기존 stock_prices 데이터로부터 유니버스 히스토리 생성
psql -U stocklabadmin -d stock_lab_investment_db -f migrations/002_populate_stock_universe_history.sql
```

**예상 소요 시간:** 데이터 양에 따라 5-30분

**진행 상황 확인:**
```sql
-- 처리된 레코드 수 확인
SELECT COUNT(*) FROM stock_universe_history;

-- 최신 데이터 확인
SELECT trade_date, COUNT(*) as stock_count
FROM stock_universe_history
GROUP BY trade_date
ORDER BY trade_date DESC
LIMIT 10;

-- 유니버스별 분포 확인
SELECT universe_id, COUNT(DISTINCT stock_code) as unique_stocks
FROM stock_universe_history
WHERE trade_date = (SELECT MAX(trade_date) FROM stock_universe_history)
GROUP BY universe_id
ORDER BY universe_id;
```

### 3단계: 일일 배치 설정 (선택)

매일 자동으로 최신 데이터를 업데이트하려면 cron job을 설정하세요.

**crontab 설정:**
```bash
# crontab 편집
crontab -e

# 매일 밤 10시에 실행
0 22 * * * cd /Users/a2/Desktop/Stock-Lab-Demo/SL-Back-end && python3 scripts/update_universe_history.py >> /var/log/universe_update.log 2>&1
```

**수동 실행:**
```bash
cd /Users/a2/Desktop/Stock-Lab-Demo/SL-Back-end
python3 scripts/update_universe_history.py
```

## 동작 방식

### 시스템 아키텍처

```
┌─────────────────┐
│  stock_prices   │  ← 원본 데이터 (market_cap 포함)
│   (매일 업데이트)  │
└────────┬────────┘
         │
         │ 배치 작업 (매일 밤 10시)
         ↓
┌───────────────────────┐
│ stock_universe_history│  ← 유니버스 분류 히스토리
│  (stock_code, date)   │
└───────────┬───────────┘
            │
            │ API 조회
            ↓
    ┌──────────────┐
    │ 백테스트 엔진  │
    └──────────────┘
```

### 유니버스 분류 기준

**KOSPI:**
- 초대형주 (MEGA): 시총 10조 이상
- 대형주 (LARGE): 시총 2조 ~ 10조
- 중형주 (MID): 시총 5천억 ~ 2조
- 소형주 (SMALL): 시총 5천억 이하

**KOSDAQ:**
- 초대형주 (MEGA): 시총 2조 이상
- 대형주 (LARGE): 시총 5천억 ~ 2조
- 중형주 (MID): 시총 2천억 ~ 5천억
- 소형주 (SMALL): 시총 2천억 이하

### 백테스트 작동 방식

```python
# 예: 2020-01-01부터 2023-12-31까지 백테스트
# 사용자가 "KOSPI_MEGA" 유니버스 선택

# 2020-01-01 시점
- 히스토리 테이블에서 2020-01-01의 KOSPI_MEGA 종목 조회
- 당시 삼성전자, SK하이닉스 등 포함

# 2021-01-01 시점 (리밸런싱)
- 히스토리 테이블에서 2021-01-01의 KOSPI_MEGA 종목 조회
- 시총 변화로 카카오가 새로 포함될 수 있음

# 각 시점의 정확한 유니버스 구성 반영!
```

## 검증

### 데이터 품질 체크

```sql
-- 1. 전체 데이터 건수
SELECT COUNT(*) as total_records FROM stock_universe_history;

-- 2. 날짜 범위 확인
SELECT MIN(trade_date) as start_date, MAX(trade_date) as end_date
FROM stock_universe_history;

-- 3. 누락된 날짜 확인 (거래일 기준)
SELECT sp.trade_date, COUNT(DISTINCT suh.stock_code) as stock_count
FROM (SELECT DISTINCT trade_date FROM stock_prices WHERE market_cap IS NOT NULL) sp
LEFT JOIN stock_universe_history suh ON sp.trade_date = suh.trade_date
GROUP BY sp.trade_date
HAVING COUNT(DISTINCT suh.stock_code) = 0
ORDER BY sp.trade_date;

-- 4. 유니버스별 종목 수 추이
SELECT
    trade_date,
    universe_id,
    COUNT(*) as stock_count
FROM stock_universe_history
WHERE trade_date IN (
    SELECT DISTINCT trade_date
    FROM stock_universe_history
    ORDER BY trade_date DESC
    LIMIT 5
)
GROUP BY trade_date, universe_id
ORDER BY trade_date DESC, universe_id;

-- 5. 특정 종목의 유니버스 변화 추적
SELECT trade_date, universe_id, market_cap
FROM stock_universe_history
WHERE stock_code = '005930'  -- 삼성전자
ORDER BY trade_date DESC
LIMIT 20;
```

### API 테스트

```bash
# 최신 날짜의 KOSPI_MEGA 종목 수 조회
curl -X POST "http://localhost:8000/api/v1/universes/stock-count" \
  -H "Content-Type: application/json" \
  -d '{"universeIds": ["KOSPI_MEGA"]}'

# 응답 예시
# {"stockCount":52,"universeIds":["KOSPI_MEGA"]}
```

## 문제 해결

### 문제 1: 데이터가 0개로 조회됨

**원인:** stock_prices에 market_cap 데이터가 없음

**해결:**
```sql
-- market_cap 데이터 확인
SELECT COUNT(*) as with_market_cap
FROM stock_prices
WHERE market_cap IS NOT NULL AND market_cap > 0;

-- market_cap이 0이면 데이터 수집 필요
```

### 문제 2: 히스토리 테이블 업데이트 실패

**원인:** 배치 스크립트 권한 문제

**해결:**
```bash
# 스크립트 실행 권한 부여
chmod +x /Users/a2/Desktop/Stock-Lab-Demo/SL-Back-end/scripts/update_universe_history.py

# 수동 실행 테스트
python3 scripts/update_universe_history.py
```

### 문제 3: 백테스트가 히스토리를 사용하지 않음

**원인:** 히스토리 테이블에 해당 날짜 데이터가 없음

**동작:** 자동으로 동적 계산으로 폴백됨 (로그 확인)

```bash
# 백엔드 로그 확인
docker logs sl-backend | grep "히스토리"
```

## 성능 최적화

### 인덱스 확인
```sql
-- 인덱스 목록 확인
\d stock_universe_history

-- 인덱스 사용 통계
SELECT * FROM pg_stat_user_indexes WHERE tablename = 'stock_universe_history';
```

### 쿼리 성능 분석
```sql
-- EXPLAIN ANALYZE로 쿼리 플랜 확인
EXPLAIN ANALYZE
SELECT stock_code
FROM stock_universe_history
WHERE universe_id = 'KOSPI_MEGA'
  AND trade_date = '2025-11-13';
```

## 유지보수

### 정기 점검 (월 1회)

1. **데이터 무결성 검증**
   ```sql
   -- 중복 레코드 확인
   SELECT stock_code, trade_date, COUNT(*)
   FROM stock_universe_history
   GROUP BY stock_code, trade_date
   HAVING COUNT(*) > 1;
   ```

2. **스토리지 사용량 확인**
   ```sql
   SELECT pg_size_pretty(pg_total_relation_size('stock_universe_history'));
   ```

3. **오래된 데이터 정리 (선택)**
   ```sql
   -- 3년 이상 된 데이터 삭제 (필요시)
   DELETE FROM stock_universe_history
   WHERE trade_date < CURRENT_DATE - INTERVAL '3 years';
   ```

## 참고 자료

- [Universe Service 소스코드](../app/services/universe_service.py)
- [배치 스크립트](../scripts/update_universe_history.py)
- [API 문서](http://localhost:8000/docs#/Universes)
