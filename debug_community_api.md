# 커뮤니티 API 디버깅 가이드

## 1. 브라우저 개발자 도구에서 확인

### Network 탭
1. F12 키를 눌러 개발자 도구 열기
2. Network 탭 클릭
3. `/community/rankings/top` 요청 찾기
4. 확인할 내용:
   - **Request URL**: `http://localhost:8000/api/v1/community/rankings/top`이 맞는지
   - **Status Code**: 500인지 확인
   - **Response 탭**: 실제 에러 메시지 확인
   - **Preview 탭**: JSON 형식으로 에러 확인

### Console 탭
- "서버 오류:" 메시지와 함께 출력되는 에러 내용 확인

## 2. 백엔드 서버 확인

### 백엔드가 실행 중인지 확인
```bash
# PowerShell에서
curl http://localhost:8000/health
```

예상 응답:
```json
{
  "status": "healthy",
  "environment": "development",
  "database": "connected"
}
```

### 랭킹 API 직접 테스트
```bash
# PowerShell에서 (인증 없이 테스트)
curl http://localhost:8000/api/v1/community/rankings/top
```

## 3. 백엔드 로그 확인

백엔드 터미널에서 실행 중인 로그를 확인:
- 요청이 들어왔는지
- 어떤 에러가 발생했는지

로그에서 찾을 내용:
```
→ GET /api/v1/community/rankings/top
랭킹 조회 실패: [에러 메시지]
```

## 4. 가능한 원인들

### A. 백엔드 서버가 실행 중이 아님
```bash
cd C:\JUNGLE\nmm\Stock-Lab\SL-Back-end
python -m uvicorn app.main:app --reload --port 8000
```

### B. Redis 연결 문제
- 백엔드 로그에 "Redis 캐시 조회 실패" 경고가 있을 수 있음
- 이건 경고일 뿐이고, DB 조회로 넘어가야 함

### C. 데이터베이스 연결 문제
- `asyncpg` 드라이버 문제
- 연결 문자열 문제

### D. 코드 실행 오류
- import 오류
- 타입 변환 오류 (Decimal → float)
- None 값 처리 오류

## 5. 백엔드에서 직접 테스트

### FastAPI Swagger UI에서 테스트
1. 브라우저에서 `http://localhost:8000/docs` 열기
2. `Community` 섹션 찾기
3. `GET /api/v1/community/rankings/top` 엔드포인트 클릭
4. "Try it out" 버튼 클릭
5. "Execute" 버튼 클릭
6. Response 확인

### Python 스크립트로 직접 테스트
```python
import requests

response = requests.get('http://localhost:8000/api/v1/community/rankings/top')
print(f'Status Code: {response.status_code}')
print(f'Response: {response.json()}')
```

## 6. 해결 방법

### 에러 메시지에 따라:

**"relation does not exist"** → 테이블이 없음
- `create_community_tables.sql` 실행 필요

**"column does not exist"** → 컬럼이 없음
- 마이그레이션 필요

**"cannot import name"** → import 오류
- 백엔드 재시작 필요

**"connection refused"** → 서버가 실행 중이 아님
- 백엔드 서버 시작 필요

**"timeout"** → 쿼리가 너무 오래 걸림
- 인덱스 추가 필요
