# 인증 시스템 (Authentication System)

Stock-Lab 백엔드의 JWT + bcrypt 기반 인증 시스템 문서입니다.

## 목차
1. [사용된 라이브러리](#사용된-라이브러리)
2. [파일 구조](#파일-구조)
3. [데이터베이스 모델](#데이터베이스-모델)
4. [보안 구현](#보안-구현)
5. [API 엔드포인트](#api-엔드포인트)
6. [인증 흐름](#인증-흐름)
7. [사용 예시](#사용-예시)

---

## 사용된 라이브러리

### 1. python-jose[cryptography] (3.3.0)
- **용도**: JWT(JSON Web Token) 생성 및 검증
- **기능**:
  - 토큰 생성 (`jwt.encode`)
  - 토큰 디코딩 (`jwt.decode`)
  - 암호화 알고리즘 지원 (HS256)

### 2. passlib[bcrypt] (1.7.4)
- **용도**: 비밀번호 해싱 및 검증
- **기능**:
  - bcrypt 알고리즘을 사용한 안전한 비밀번호 해싱
  - 해시된 비밀번호와 평문 비밀번호 비교
  - 솔트(salt) 자동 생성

### 3. pydantic (2.5.3)
- **용도**: 데이터 검증 및 직렬화
- **기능**:
  - 요청/응답 스키마 정의
  - 자동 데이터 검증
  - EmailStr 등 특수 타입 지원

### 4. SQLAlchemy (2.0.25)
- **용도**: ORM 및 데이터베이스 관리
- **기능**:
  - 비동기 데이터베이스 작업
  - User 모델 정의

---

## 파일 구조

```
SL-Back-end/
├── app/
│   ├── models/
│   │   └── user.py              # User 데이터베이스 모델
│   ├── schemas/
│   │   └── user.py              # Pydantic 스키마 정의
│   ├── core/
│   │   ├── security.py          # JWT 및 비밀번호 해싱 유틸리티
│   │   ├── dependencies.py      # FastAPI 의존성 함수
│   │   └── config.py            # 설정 관리
│   ├── api/
│   │   └── routes/
│   │       └── auth.py          # 인증 API 엔드포인트
│   └── main.py                  # FastAPI 앱 설정
└── .env                          # 환경 변수 설정
```

---

## 데이터베이스 모델

### User 모델 (`app/models/user.py`)

```python
from sqlalchemy.dialects.postgresql import UUID
import uuid

class User(Base):
    __tablename__ = "users"

    user_id = Column(UUID(as_uuid=True), primary_key=True, index=True, default=uuid.uuid4)
    name = Column(String(100), nullable=False)
    email = Column(String(255), unique=True, index=True, nullable=False)
    phone_number = Column(String(20), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    is_superuser = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
```

**필드 설명:**
- `user_id`: 기본키, UUID 타입 (자동 생성, 유니크)
- `name`: 사용자 이름 (일반 필드, 중복 허용)
- `email`: 이메일 주소 (유니크, 인덱싱)
- `phone_number`: 전화번호 (유니크, 인덱싱, 숫자만 허용)
- `hashed_password`: bcrypt로 해시된 비밀번호
- `is_active`: 계정 활성화 상태
- `is_superuser`: 관리자 권한 여부
- `created_at`: 생성 시각
- `updated_at`: 수정 시각

**Unique 제약조건:**
- `user_id`, `email`, `phone_number`만 unique 설정
- `name`은 중복 허용

**UUID 사용 이유:**
- 보안성 향상: 순차적 ID보다 예측 불가능
- 분산 시스템에서 ID 충돌 방지
- 외부 노출 시 시스템 규모 추정 방지

---

## 보안 구현

### 1. 비밀번호 해싱 (`app/core/security.py`)

#### bcrypt 설정
```python
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
```

#### 비밀번호 해싱
```python
def get_password_hash(password: str) -> str:
    """평문 비밀번호를 bcrypt로 해싱"""
    return pwd_context.hash(password)
```

#### 비밀번호 검증
```python
def verify_password(plain_password: str, hashed_password: str) -> bool:
    """평문 비밀번호와 해시된 비밀번호 비교"""
    return pwd_context.verify(plain_password, hashed_password)
```

### 2. JWT 토큰 관리

#### 토큰 생성
```python
def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    JWT 액세스 토큰 생성
    - 페이로드에 user_id (문자열로 변환된 UUID), email 포함
    - 만료 시간 설정 (기본: 30분)
    - HS256 알고리즘 사용
    """
    to_encode = data.copy()

    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)

    return encoded_jwt

# 로그인 시 토큰 생성 예시
access_token = create_access_token(
    data={"user_id": str(user.user_id), "email": user.email}  # UUID를 문자열로 변환
)
```

#### 토큰 디코딩
```python
def decode_access_token(token: str) -> Optional[dict]:
    """JWT 토큰 디코딩 및 검증"""
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        return payload
    except JWTError:
        return None
```

### 3. 인증 의존성 (`app/core/dependencies.py`)

#### Bearer 토큰 스키마
```python
from fastapi.security import HTTPBearer

security = HTTPBearer()
```

#### 현재 유저 가져오기
```python
from uuid import UUID

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db)
) -> User:
    """
    Authorization 헤더에서 JWT 토큰 추출 및 검증
    1. 토큰 디코딩
    2. user_id (문자열) 추출 및 UUID로 변환
    3. DB에서 유저 조회
    4. 활성화 상태 확인
    """
    token = credentials.credentials
    payload = decode_access_token(token)

    if payload is None:
        raise HTTPException(status_code=401, detail="인증 정보를 확인할 수 없습니다")

    user_id_str = payload.get("user_id")
    if user_id_str is None:
        raise HTTPException(status_code=401, detail="인증 정보를 확인할 수 없습니다")

    try:
        user_id = UUID(user_id_str)  # 문자열을 UUID로 변환
    except (ValueError, AttributeError):
        raise HTTPException(status_code=401, detail="인증 정보를 확인할 수 없습니다")

    result = await db.execute(select(User).where(User.user_id == user_id))
    user = result.scalar_one_or_none()

    if not user or not user.is_active:
        raise HTTPException(status_code=403, detail="비활성화된 계정입니다")

    return user
```

---

## API 엔드포인트

### 1. 회원가입
**POST** `/api/v1/auth/register`

#### 요청 스키마
```json
{
  "name": "홍길동",
  "email": "user@example.com",
  "phone_number": "01012345678",
  "password": "password123"
}
```

**필드 유효성 검증:**
- `name`: 1~100자, 필수
- `email`: 이메일 형식, 필수, 유니크
- `phone_number`: 10~20자, 숫자만 허용, 필수, 유니크
- `password`: 8~100자, 필수

#### 응답 (201 Created)
```json
{
  "user_id": "550e8400-e29b-41d4-a716-446655440000",
  "name": "홍길동",
  "email": "user@example.com",
  "phone_number": "01012345678",
  "is_active": true,
  "is_superuser": false,
  "created_at": "2025-01-05T12:00:00Z"
}
```

#### 에러 응답
- **400 Bad Request**: 이메일 또는 전화번호 중복
- **422 Unprocessable Entity**: 유효성 검증 실패

---

### 2. 로그인
**POST** `/api/v1/auth/login?email=user@example.com&password=password123`

#### 쿼리 파라미터
- `email`: 이메일 주소
- `password`: 비밀번호

#### 응답 (200 OK)
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

#### 에러 응답
- **401 Unauthorized**: 이메일 또는 비밀번호 불일치
- **403 Forbidden**: 비활성화된 계정

---

### 3. 현재 유저 정보 조회
**GET** `/api/v1/auth/me`

#### 헤더
```
Authorization: Bearer <access_token>
```

#### 응답 (200 OK)
```json
{
  "user_id": "550e8400-e29b-41d4-a716-446655440000",
  "name": "홍길동",
  "email": "user@example.com",
  "phone_number": "01012345678",
  "is_active": true,
  "is_superuser": false,
  "created_at": "2025-01-05T12:00:00Z"
}
```

#### 에러 응답
- **401 Unauthorized**: 토큰 없음 또는 유효하지 않음
- **403 Forbidden**: 비활성화된 계정

---

### 4. 특정 유저 정보 조회
**GET** `/api/v1/auth/users/{user_id}`

#### 경로 파라미터
- `user_id`: UUID 형식의 유저 ID (예: `550e8400-e29b-41d4-a716-446655440000`)

#### 헤더
```
Authorization: Bearer <access_token>
```

#### 응답 (200 OK)
```json
{
  "user_id": "550e8400-e29b-41d4-a716-446655440000",
  "name": "홍길동",
  "email": "user@example.com",
  "phone_number": "01012345678",
  "is_active": true,
  "is_superuser": false,
  "created_at": "2025-01-05T12:00:00Z"
}
```

#### 에러 응답
- **401 Unauthorized**: 인증되지 않음
- **404 Not Found**: 유저를 찾을 수 없음

---

## 인증 흐름

### 1. 회원가입 흐름

```mermaid
sequenceDiagram
    participant Client
    participant API
    participant Security
    participant DB

    Client->>API: POST /api/v1/auth/register
    API->>DB: 이메일 중복 확인
    DB-->>API: 결과 반환
    API->>DB: 전화번호 중복 확인
    DB-->>API: 결과 반환
    API->>Security: get_password_hash(password)
    Security-->>API: hashed_password
    API->>DB: User 생성 및 저장 (name, email, phone_number)
    DB-->>API: 생성된 User
    API-->>Client: UserResponse (201)
```

**단계별 설명:**
1. 클라이언트가 회원가입 요청 (이름, 이메일, 전화번호, 비밀번호)
2. 이메일 중복 확인
3. 전화번호 중복 확인
4. 비밀번호 bcrypt 해싱
5. DB에 User 레코드 생성 (name, email, phone_number, hashed_password)
6. 생성된 유저 정보 반환 (비밀번호 제외)

---

### 2. 로그인 흐름

```mermaid
sequenceDiagram
    participant Client
    participant API
    participant Security
    participant DB

    Client->>API: POST /api/v1/auth/login
    API->>DB: 이메일로 User 조회
    DB-->>API: User 또는 None
    API->>Security: verify_password(password, hashed_password)
    Security-->>API: True/False
    API->>API: is_active 확인
    API->>Security: create_access_token({user_id: str(UUID), email})
    Security-->>API: JWT token
    API-->>Client: Token (200)
```

**단계별 설명:**
1. 클라이언트가 로그인 요청 (이메일 + 비밀번호)
2. DB에서 이메일로 유저 조회
3. bcrypt로 비밀번호 검증
4. 계정 활성화 상태 확인
5. JWT 토큰 생성 (user_id를 문자열로 변환, email 포함)
6. 토큰 반환

---

### 3. 인증된 요청 흐름

```mermaid
sequenceDiagram
    participant Client
    participant API
    participant Dependencies
    participant Security
    participant DB

    Client->>API: GET /api/v1/auth/me (Bearer token)
    API->>Dependencies: get_current_user(token)
    Dependencies->>Security: decode_access_token(token)
    Security-->>Dependencies: payload (user_id: str, email)
    Dependencies->>Dependencies: UUID(user_id_str) 변환
    Dependencies->>DB: User 조회 (UUID)
    DB-->>Dependencies: User
    Dependencies->>Dependencies: is_active 확인
    Dependencies-->>API: User
    API-->>Client: UserResponse (200)
```

**단계별 설명:**
1. 클라이언트가 Authorization 헤더에 Bearer 토큰 포함하여 요청
2. FastAPI 의존성 함수 (`get_current_user`) 실행
3. JWT 토큰 디코딩 및 검증
4. 토큰에서 user_id (문자열) 추출
5. 문자열을 UUID로 변환
6. DB에서 유저 조회
7. 계정 활성화 상태 확인
8. 유저 객체 반환
9. 엔드포인트 로직 실행

---

## 사용 예시

### Python (httpx)

```python
import httpx

BASE_URL = "http://localhost:8000/api/v1/auth"

# 1. 회원가입
async def register():
    async with httpx.AsyncClient() as client:
        response = await client.post(f"{BASE_URL}/register", json={
            "name": "홍길동",
            "email": "test@example.com",
            "phone_number": "01012345678",
            "password": "password123"
        })
        print(response.json())

# 2. 로그인
async def login():
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{BASE_URL}/login",
            params={"email": "test@example.com", "password": "password123"}
        )
        token = response.json()["access_token"]
        return token

# 3. 현재 유저 정보 조회
async def get_me(token: str):
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{BASE_URL}/me",
            headers={"Authorization": f"Bearer {token}"}
        )
        print(response.json())
```

### cURL

```bash
# 1. 회원가입
curl -X POST "http://localhost:8000/api/v1/auth/register" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "홍길동",
    "email": "test@example.com",
    "phone_number": "01012345678",
    "password": "password123"
  }'

# 2. 로그인
curl -X POST "http://localhost:8000/api/v1/auth/login?email=test@example.com&password=password123"

# 3. 현재 유저 정보 조회
curl -X GET "http://localhost:8000/api/v1/auth/me" \
  -H "Authorization: Bearer YOUR_TOKEN_HERE"
```

### JavaScript (axios)

```javascript
import axios from 'axios';

const BASE_URL = 'http://localhost:8000/api/v1/auth';

// 1. 회원가입
const register = async () => {
  const response = await axios.post(`${BASE_URL}/register`, {
    name: '홍길동',
    email: 'test@example.com',
    phone_number: '01012345678',
    password: 'password123'
  });
  return response.data;
};

// 2. 로그인
const login = async () => {
  const response = await axios.post(`${BASE_URL}/login`, null, {
    params: {
      email: 'test@example.com',
      password: 'password123'
    }
  });
  return response.data.access_token;
};

// 3. 현재 유저 정보 조회
const getMe = async (token) => {
  const response = await axios.get(`${BASE_URL}/me`, {
    headers: {
      Authorization: `Bearer ${token}`
    }
  });
  return response.data;
};
```

---

## 보안 고려사항

### 1. 비밀번호 보안
- ✅ bcrypt 알고리즘 사용 (솔트 자동 생성)
- ✅ 최소 8자 이상 비밀번호 요구
- ✅ 평문 비밀번호는 절대 저장하지 않음
- ✅ 비밀번호는 응답에 포함되지 않음

### 2. JWT 토큰 보안
- ✅ SECRET_KEY는 환경 변수로 관리
- ✅ 토큰 만료 시간 설정 (기본 30분)
- ✅ HS256 알고리즘 사용
- ⚠️ HTTPS 사용 권장 (프로덕션)
- ⚠️ 리프레시 토큰 구현 고려 (향후 추가)

### 3. 데이터베이스 보안
- ✅ 이메일과 유저명에 유니크 제약 조건
- ✅ 인덱싱을 통한 빠른 조회
- ✅ 비동기 처리로 성능 최적화

### 4. API 보안
- ✅ CORS 설정
- ✅ 에러 메시지에 민감한 정보 노출 방지
- ✅ 로그인 실패 시 구체적인 이유 숨김 (이메일/비밀번호 구분 안 함)

---

## 환경 변수 설정

`.env` 파일:

```env
# Security
SECRET_KEY=your-secret-key-here-change-this-to-a-random-secure-string
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Database
DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/dbname
```

**SECRET_KEY 생성 방법:**

```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

---

## 추가 개선 사항 (향후)

1. **리프레시 토큰**: 액세스 토큰 만료 시 재발급
2. **이메일 인증**: 회원가입 시 이메일 확인
3. **비밀번호 재설정**: 이메일을 통한 비밀번호 찾기
4. **로그인 시도 제한**: Brute-force 공격 방지
5. **OAuth 2.0**: 소셜 로그인 (Google, GitHub 등)
6. **2FA (Two-Factor Authentication)**: 이중 인증
7. **세션 관리**: 동시 로그인 제어
8. **감사 로그**: 로그인 이력 추적

---

## 문제 해결

### 1. 토큰이 유효하지 않음
- SECRET_KEY가 올바른지 확인
- 토큰 만료 시간 확인
- Authorization 헤더 형식: `Bearer <token>`

### 2. 회원가입 실패
- 이메일/전화번호 중복 확인
- 비밀번호 길이 확인 (최소 8자)
- 이메일 형식 확인
- 전화번호 형식 확인 (숫자만, 10~20자)

### 3. 로그인 실패
- 이메일/비밀번호 확인
- 계정 활성화 상태 확인 (`is_active=True`)

---

## 참고 문서

- [FastAPI Security](https://fastapi.tiangolo.com/tutorial/security/)
- [python-jose](https://python-jose.readthedocs.io/)
- [passlib](https://passlib.readthedocs.io/)
- [JWT.io](https://jwt.io/)
- [bcrypt](https://en.wikipedia.org/wiki/Bcrypt)
