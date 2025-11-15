# 키움증권 API 연동 가이드

## 개요
Stock-Lab-Demo 프로젝트에 키움증권 모의투자 API를 연동하여 실시간 계좌 잔고 조회 및 주식 거래 기능을 구현했습니다.

## 구현된 기능

### 1. 백엔드 (FastAPI)

#### 데이터베이스 스키마
- **파일**: `SL-Back-end/migrations/add_kiwoom_columns.sql`
- **추가된 컬럼**:
  - `kiwoom_app_key`: 키움증권 앱 키
  - `kiwoom_app_secret`: 키움증권 시크릿 키
  - `kiwoom_access_token`: 접근 토큰
  - `kiwoom_token_expires_at`: 토큰 만료 시간

```sql
-- 마이그레이션 실행
psql -h localhost -U your_user -d your_database -f SL-Back-end/migrations/add_kiwoom_columns.sql
```

#### 키움증권 서비스 모듈
- **파일**: `SL-Back-end/app/services/kiwoom_service.py`
- **주요 기능**:
  - `get_access_token()`: 접근 토큰 발급
  - `update_user_kiwoom_credentials()`: 사용자 인증 정보 업데이트
  - `refresh_token_if_needed()`: 토큰 자동 갱신
  - `get_account_balance()`: 계좌 잔고 조회
  - `buy_stock()`: 주식 매수 주문
  - `sell_stock()`: 주식 매도 주문

#### API 엔드포인트
- **파일**: `SL-Back-end/app/api/routes/kiwoom.py`
- **엔드포인트**:

| 메서드 | 경로 | 설명 |
|--------|------|------|
| POST | `/api/v1/kiwoom/credentials` | 키움증권 API KEY 등록 |
| GET | `/api/v1/kiwoom/credentials/status` | 연동 상태 조회 |
| DELETE | `/api/v1/kiwoom/credentials` | 연동 해제 |
| GET | `/api/v1/kiwoom/account/balance` | 계좌 잔고 조회 |
| POST | `/api/v1/kiwoom/order/buy` | 주식 매수 주문 |
| POST | `/api/v1/kiwoom/order/sell` | 주식 매도 주문 |

### 2. 프론트엔드 (Next.js + TypeScript)

#### 키움증권 API 클라이언트
- **파일**: `SL-Front-End/src/lib/api/kiwoom.ts`
- **타입 정의**: `SL-Front-End/src/types/kiwoom.ts`

#### UI 컴포넌트

##### 키움증권 연동 모달
- **파일**: `SL-Front-End/src/components/modal/KiwoomConnectModal.tsx`
- **기능**:
  - 앱 키와 시크릿 키 입력
  - 키움증권 API 인증
  - 연동 성공/실패 처리

##### 메인페이지 연동 버튼
- **파일**: `SL-Front-End/src/app/page.tsx`
- **기능**:
  - 증권사 연동 버튼
  - 연동 상태 표시 (연동됨/미연동)
  - 모달 열기/닫기

##### 나의 잔고 보기 페이지
- **파일**: `SL-Front-End/src/app/mypage/page.tsx`
- **기능**:
  - 연동 상태 확인
  - 실시간 계좌 잔고 조회
  - 자동 새로고침 기능
  - 에러 처리

## 사용 방법

### 1. 데이터베이스 마이그레이션

```bash
cd /Users/a2/Desktop/Stock-Lab-Demo/SL-Back-end
psql -h localhost -U your_user -d stock_lab -f migrations/add_kiwoom_columns.sql
```

### 2. 백엔드 서버 실행

```bash
cd /Users/a2/Desktop/Stock-Lab-Demo/SL-Back-end
python -m uvicorn app.main:app --reload
```

### 3. 프론트엔드 서버 실행

```bash
cd /Users/a2/Desktop/Stock-Lab-Demo/SL-Front-End
npm run dev
```

### 4. 키움증권 연동

1. 메인페이지에서 "증권사 연동하기" 버튼 클릭
2. 키움증권 앱 키와 시크릿 키 입력
3. "등록" 버튼 클릭
4. 연동 성공 메시지 확인

### 5. 잔고 조회

1. "나의 잔고" 메뉴 클릭 (마이페이지)
2. 자동으로 계좌 잔고 조회
3. "새로고침" 버튼으로 수동 갱신 가능

## API 사용 예시

### 키움증권 API KEY 등록

```bash
curl -X POST http://localhost:8000/api/v1/kiwoom/credentials \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -d '{
    "app_key": "YOUR_KIWOOM_APP_KEY",
    "app_secret": "YOUR_KIWOOM_APP_SECRET"
  }'
```

### 계좌 잔고 조회

```bash
curl -X GET http://localhost:8000/api/v1/kiwoom/account/balance \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

### 주식 매수 주문

```bash
curl -X POST http://localhost:8000/api/v1/kiwoom/order/buy \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -d '{
    "stock_code": "005930",
    "quantity": "1",
    "trade_type": "3"
  }'
```

## 주요 특징

### 1. 토큰 자동 갱신
- 토큰 만료 10분 전에 자동으로 갱신
- 사용자가 별도로 관리할 필요 없음

### 2. 모의투자 API 사용
- 호스트: `https://mockapi.kiwoom.com`
- 실제 자금 없이 테스트 가능

### 3. 보안
- 사용자별로 인증 정보 격리 저장
- JWT 토큰으로 API 접근 제어

### 4. 에러 처리
- 상세한 에러 메시지 제공
- 사용자 친화적인 UI 피드백

## 향후 개선 사항

1. **WebSocket 실시간 업데이트**
   - 현재는 REST API 기반
   - WebSocket으로 실시간 잔고 변동 수신 가능

2. **잔고 UI 고도화**
   - 현재는 JSON 원본 데이터 표시
   - 차트와 표로 시각화 필요

3. **거래 내역**
   - 매수/매도 주문 내역 조회
   - 체결 내역 확인

4. **백테스트 연동**
   - 백테스트 결과를 실제 계좌와 연동
   - 자동 매매 활성화/비활성화 기능

## 참고 자료

- 키움증권 API 문서: [키움증권 개발자센터](https://developers.kiwoom.com)
- SL-KIWOOM 디렉토리: `/Users/a2/Desktop/SL-KIWOOM`
  - `accessToken.py`: 토큰 발급 예제
  - `buyStock.py`: 매수 주문 예제
  - `sellStock.py`: 매도 주문 예제
  - `계좌잔고.py`: 잔고 조회 예제

## 문제 해결

### 토큰 발급 실패
- 앱 키와 시크릿 키가 정확한지 확인
- 키움증권 계정이 활성화되어 있는지 확인

### 잔고 조회 실패
- 먼저 증권사 연동이 완료되었는지 확인
- 로그인 상태 확인 (JWT 토큰 유효성)

### 데이터베이스 연결 오류
- PostgreSQL 서버가 실행 중인지 확인
- `.env` 파일의 데이터베이스 설정 확인
