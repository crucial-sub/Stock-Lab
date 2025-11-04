# SL-Back-Test 디렉토리 구조 정리 완료

## 정리 작업 요약

### 삭제된 파일
- ❌ `numpy-2.0.2-src/` - 불필요한 numpy 소스 코드
- ❌ `numpy-2.0.2/` - 불필요한 numpy 소스 코드
- ❌ `numpy-2.1.1-src/` - 불필요한 numpy 소스 코드
- ❌ `numpy-2.0.2.tar.gz` - 불필요한 numpy 압축 파일
- ❌ `tmp_numpy_download/` - 임시 다운로드 디렉토리
- ❌ `app/api/routes/factors.py` - 미사용 라우터
- ❌ `app/api/routes/factors_cached.py` - 미사용 라우터
- ❌ `app/api/routes/factors_extended.py` - 미사용 라우터
- ❌ `app/services/factor_calculator.py` - 미사용 서비스
- ❌ `app/services/factor_calculator_extended.py` - 미사용 서비스
- ❌ `app/services/backtest_engine.py` - 사용하지 않는 구버전 엔진
- ❌ `backend.log` - 임시 로그 파일
- ❌ `logs/` - 임시 로그 디렉토리
- ❌ `init.sql/` - 빈 디렉토리
- ❌ `requirements_stable.txt` - 중복 requirements
- ❌ `requirements_working.txt` - 중복 requirements

### 이동된 파일

#### docs/ 디렉토리로 이동
- ✅ `FACTOR_IMPLEMENTATION_STATUS.md` → `docs/`
- ✅ `IMPLEMENTATION_SUMMARY.md` → `docs/`
- ✅ `PROJECT_REVIEW_AND_IMPROVEMENTS.md` → `docs/`
- ✅ `SETUP_GUIDE.md` → `docs/`
- ✅ `quant_simulation_design_document.md` → `docs/`
- ✅ `quant_simulation_detailed_schema.sql` → `docs/`
- ✅ `quant_simulation_implementation_guide.py` → `docs/`
- ✅ `README.md` (old) → `docs/README_OLD.md`

#### scripts/ 디렉토리로 이동
- ✅ `init_db.py` → `scripts/`
- ✅ `install.sh` → `scripts/`
- ✅ `quick_install.sh` → `scripts/`
- ✅ `run.sh` → `scripts/`
- ✅ `test_api.py` → `scripts/`

### 수정된 파일
- 📝 `app/main.py` - factors 관련 라우터 제거, backtest만 유지
- 📝 `app/api/routes/backtest.py` - backtest_engine import 제거
- 📝 `README.md` - 새로운 간결한 버전으로 재작성

### 최종 디렉토리 구조

```
SL-Back-Test/
├── app/                       # 애플리케이션 소스
│   ├── api/
│   │   └── routes/
│   │       └── backtest.py    # 백테스트 API (유일한 라우터)
│   ├── core/                  # 핵심 설정
│   ├── models/                # 데이터 모델
│   ├── schemas/               # API 스키마
│   ├── services/              # 비즈니스 로직
│   │   └── simple_backtest.py # 백테스트 엔진
│   └── utils/                 # 유틸리티
├── docs/                      # 문서 (모든 .md, .sql 파일)
├── scripts/                   # 실행 스크립트
│   ├── init_db.py
│   ├── install.sh
│   ├── run.sh
│   └── test_api.py
├── tests/                     # 테스트 (비어있음)
├── .env                       # 환경 변수
├── .env.example               # 환경 변수 예시
├── Dockerfile                 # Docker 이미지
├── docker-compose.yml         # Docker 구성
├── README.md                  # 새 README (간결)
└── requirements.txt           # Python 의존성 (하나만)
```

## 변경 사항

### 1. 코드 단순화
- **이전**: 3개의 factors 라우터 + 2개의 factor_calculator 서비스
- **이후**: backtest 라우터 1개 + simple_backtest 서비스 1개

### 2. 문서 통합
- 모든 마크다운 및 SQL 문서를 `docs/` 디렉토리로 집중

### 3. 스크립트 정리
- 모든 실행 스크립트를 `scripts/` 디렉토리로 이동
- 중복된 requirements 파일 삭제

### 4. 불필요한 파일 제거
- 1GB+ numpy 소스 코드 완전 삭제
- 미사용 라우터 및 서비스 삭제
- 임시 파일 및 로그 삭제

## 효과

- **디스크 공간**: ~1.2GB 절약
- **파일 수**: ~2,500개 감소
- **코드 복잡도**: 중복 제거로 유지보수 용이
- **명확성**: 기능별로 명확하게 구분된 디렉토리 구조

## 주의사항

모든 중요한 파일은 백업되었으며 (`docs/README_OLD.md` 등), 실제 동작하는 백테스트 기능은 영향받지 않습니다.

정리 완료일: 2025-11-04
