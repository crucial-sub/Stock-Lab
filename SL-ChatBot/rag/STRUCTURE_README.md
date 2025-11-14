# SL-Chatbot RAG 문서 구조 가이드

## 📊 현재 구조

```
SL-Chatbot/rag/documents/
├── metadata.json                    # 📌 전체 카탈로그 인덱스
│
├── 📁 factors/                      # A. 팩터 설명 (⭐⭐⭐⭐⭐)
│   ├── metadata.json                # 팩터 메타데이터
│   ├── value.md                     # 가치 팩터
│   ├── growth.md                    # 성장 팩터
│   ├── quality.md                   # 퀄리티 팩터
│   ├── momentum.md                  # 모멘텀 팩터
│   ├── dividend.md                  # 배당 팩터
│   └── risk.md                      # 리스크 팩터 (기존)
│
├── 📁 strategies/                   # A. 전략 설명 (⭐⭐⭐⭐⭐)
│   ├── metadata.json                # 전략 메타데이터
│   ├── value_strategy.md            # 가치투자 전략 (작성 예정)
│   ├── growth_strategy.md           # 성장투자 전략 (작성 예정)
│   ├── dividend_strategy.md         # 배당투자 전략 (작성 예정)
│   ├── quality_strategy.md          # 퀄리티 투자 전략 (작성 예정)
│   └── momentum_strategy.md         # 모멘텀 투자 전략 (작성 예정)
│
├── 📁 indicators/                   # A. 금융지표 설명 (⭐⭐⭐⭐⭐)
│   ├── metadata.json                # 지표 메타데이터
│   ├── per.md                       # PER (작성 예정)
│   ├── roe.md                       # ROE (작성 예정)
│   ├── debt_ratio.md                # 부채비율 (작성 예정)
│   ├── roa.md                       # ROA (작성 예정)
│   ├── pbr.md                       # PBR (작성 예정)
│   └── dividend_yield.md            # 배당수익률 (작성 예정)
│
├── 📁 beginner_guide/               # C. 초심자 가이드 (⭐⭐⭐⭐⭐)
│   ├── metadata.json                # 가이드 메타데이터
│   ├── what_is_factor.md            # 팩터란? (작성 예정)
│   ├── financial_basics.md          # 금융 기본 (작성 예정)
│   ├── investment_types.md          # 투자 타입 비교 (작성 예정)
│   └── how_to_start.md              # 투자 시작하기 (작성 예정)
│
└── 📁 policies/                     # D. 정책 및 안전 (⭐⭐⭐⭐⭐)
    ├── metadata.json                # 정책 메타데이터
    ├── investment_advisory.md       # 투자 조언 금지 (작성 예정)
    ├── risk_warnings.md             # 리스크 안내 (작성 예정)
    ├── prohibited_phrases.txt       # 금지 문구 (작성 예정)
    └── user_protection.md           # 사용자 보호 (작성 예정)
```

---

## 📝 문서 형식

### Metadata.json (메타데이터)

**위치**: 각 카테고리 폴더 내 `metadata.json`

**용도**:
- RAG 검색 인덱싱
- 카테고리 관리
- 문서 속성 (우선순위, 키워드, 버전 등)

**구조**:
```json
{
  "category": "factors",
  "category_name": "팩터 설명",
  "documents": [
    {
      "id": "factor_value",
      "name": "가치 팩터",
      "file": "value.md",
      "priority": "⭐⭐⭐⭐⭐",
      "keywords": ["PER", "저평가", ...],
      "summary": "짧은 요약",
      "last_updated": "2025-11-14"
    }
  ]
}
```

### 마크다운 (.md) 문서

**위치**: 각 카테고리 폴더 내

**용도**:
- 실제 콘텐츠 저장
- 벡터 임베딩용 원본
- 사용자에게 보여줄 설명

**구조**:
```markdown
# 제목

## 개념
...

## 핵심 지표
...

## 장점
...

## 단점
...

## 주의사항 ⚠️
...

## FAQ
...
```

### 텍스트 (.txt) 문서

**위치**: 정책 폴더 (`policies/`)

**용도**:
- 금지 문구 목록
- 정책 체크리스트
- 단순 텍스트 정보

---

## 🔍 RAG 검색 프로세스

```
사용자 질문
  ↓
1️⃣ 메타데이터 검색 (metadata.json)
   └─ keywords 매칭
   └─ category 필터링
  ↓
2️⃣ 문서 식별
   └─ 해당 .md 파일 경로 확인
  ↓
3️⃣ 문서 로드
   └─ 마크다운 콘텐츠 메모리로 로드
  ↓
4️⃣ 벡터 임베딩
   └─ Chroma 또는 유사 벡터DB에 임베딩
  ↓
5️⃣ 유사도 검색
   └─ 상위 3개 문서 선택
  ↓
6️⃣ 정책 검증
   └─ 정책 폴더 문서 확인
  ↓
7️⃣ LLM 응답 생성
   └─ 컨텍스트 + 프롬프트 → 응답
```

---

## 📌 각 카테고리별 우선순위

| # | 카테고리 | 우선순위 | 설명 |
|---|---------|--------|------|
| 1 | **policies** | ⭐⭐⭐⭐⭐ | 안전성 최우선 |
| 2 | **factors** | ⭐⭐⭐⭐⭐ | 기본 교육 자료 |
| 3 | **indicators** | ⭐⭐⭐⭐⭐ | 팩터 설명 참조 |
| 4 | **strategies** | ⭐⭐⭐⭐⭐ | 팩터 조합 설명 |
| 5 | **beginner_guide** | ⭐⭐⭐⭐⭐ | 초심자 응답용 |

---

## ✅ 작성 현황

### Factors (5/5 완료)
- ✅ value.md (완료)
- ✅ growth.md (완료)
- ✅ quality.md (완료)
- ✅ momentum.md (완료)
- ✅ dividend.md (완료)

### Strategies (0/5)
- ⏳ value_strategy.md
- ⏳ growth_strategy.md
- ⏳ dividend_strategy.md
- ⏳ quality_strategy.md
- ⏳ momentum_strategy.md

### Indicators (0/6)
- ⏳ per.md
- ⏳ roe.md
- ⏳ debt_ratio.md
- ⏳ roa.md
- ⏳ pbr.md
- ⏳ dividend_yield.md

### Beginner Guide (4/4 완료)
- ✅ what_is_factor.md (완료)
- ✅ financial_basics.md (완료)
- ✅ investment_types.md (완료)
- ✅ how_to_start.md (완료)

### Policies (4/4 완료)
- ✅ investment_advisory.md (완료)
- ✅ risk_warnings.md (완료)
- ✅ prohibited_phrases.txt (완료)
- ✅ user_protection.md (완료)

---

## 🛠️ 다음 단계

### 1단계: 마크다운 문서 완성
- [ ] Strategies 5개 문서 작성
- [ ] Indicators 6개 문서 작성
- [ ] Beginner Guide 4개 문서 작성
- [ ] Policies 4개 문서 작성

### 2단계: 데이터 기반 기능 (B 카테고리)
- [ ] 감성 점수 데이터 처리
- [ ] 백테스트 결과 해석
- [ ] 시장 브리핑 생성

### 3단계: Themes 추가 (선택)
- [ ] 산업별 가이드
- [ ] 테마별 분석

### 4단계: RAG 검색 엔진 구현
- [ ] 벡터DB 연동 (Chroma)
- [ ] 검색 함수 구현
- [ ] 정책 검증 로직

---

## 📚 문서 작성 가이드

### 일관된 구조 유지
```markdown
# 제목

## 개념
핵심 개념 설명 (1~2문장)

> 💡 **핵심 아이디어**: ...

---

## 핵심 지표
### 1. 지표명
**의미**:
**수식**:
**해석**:
**예시**:

---

## 장점 ✅
| 항목 | 설명 |

---

## 단점 ❌
| 항목 | 설명 |

---

## 언제 사용할까?
### ✅ 좋은 경우
### ❌ 피해야 할 경우

---

## 실전 분석 예시
코드 블록으로 예시 제시

---

## 주의사항 ⚠️
### 1. 함정명
**문제**:
**해결책**:

---

## FAQ
Q: ...
A: ...
```

### 메타데이터 작성 가이드
```json
{
  "id": "고유ID",
  "name": "문서 제목",
  "type": "카테고리",
  "file": "filename.md",
  "priority": "⭐⭐⭐⭐⭐",
  "keywords": ["키워드1", "키워드2", ...],
  "summary": "한 문장 요약",
  "difficulty": "beginner|intermediate|advanced",
  "last_updated": "YYYY-MM-DD",
  "version": "1.0"
}
```

---

## 🎯 RAG 활용 예시

### 사례 1: 초심자 "PER이 뭐예요?"

```
질문 → "PER" 키워드 검색
↓
메타 검색: indicators/metadata.json
  → indicator_per 매칭
↓
문서 로드: indicators/per.md
↓
벡터 임베딩 + 유사도 검색
↓
정책 검증: 교육적 설명만 하기
↓
응답: "PER은 주가를 주당순이익으로 나눈 값으로..."
```

### 사례 2: "배당주 투자는?"

```
질문 → "배당" 키워드 검색
↓
메타 검색:
  - factors/metadata.json → factor_dividend
  - strategies/metadata.json → strategy_dividend
  - indicators/metadata.json → indicator_dividend_yield
↓
문서 로드: 3개 문서 모두
↓
유사도 검색: 상위 3개 순서대로
↓
정책 검증: 특정 종목 추천 금지
↓
응답: "배당주 전략은... (장점) ... (단점) ... 주의사항..."
```

---

## 🔐 정책 검증

**모든 응답 전에 확인**:
- ✅ policies/prohibited_phrases.txt에 해당 문구 없음?
- ✅ policies/investment_advisory.md - 종목 추천 없음?
- ✅ policies/risk_warnings.md - 리스크 안내 포함?
- ✅ policies/user_protection.md - 개인정보 수집 없음?

---

## 📞 문의 및 업데이트

- **마크다운 추가**: 해당 폴더에 `.md` 파일 추가 + metadata.json 업데이트
- **메타데이터 변경**: 해당 폴더의 `metadata.json` 수정
- **전체 카탈로그 변경**: `metadata.json` 수정

---

## 버전 이력

| 버전 | 날짜 | 변경 사항 |
|------|------|---------|
| 1.0 | 2025-11-14 | 초기 구조 완성 (factors 완료) |

