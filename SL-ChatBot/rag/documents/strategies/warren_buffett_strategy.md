# 워렌버핏 가치투자 전략

## 개요
저평가된 우량 기업을 내재가치 대비 할인된 가격에 매수해 장기 보유하는 가치 투자 전략입니다. 안전마진과 경제적 해자에 집중합니다.

## 핵심 기준
- PBR ≤ 1.0, PER 15 이하 수준의 저평가
- ROE ≥ 15, 안정적 현금흐름, 부채비율 낮음
- 경제적 해자(브랜드, 네트워크 효과, 비용 우위) 보유 여부

## 주요 섹터/특징
- 전통 우량주, 독점력 보유 기업, 현금흐름 안정 산업

## 장점
- 하방 리스크 제한, 검증된 가치 전략, 배당 수익 기대

## 단점
- 가치 함정 위험, 재평가까지 시간 소요, 과열장에서는 기회 감소

## 적합한 투자자
- 장기 투자 성향, 재무제표 분석 선호, 인내심 있는 투자자

## 참고 지표
- PBR, PER, ROE, 부채비율, 배당수익률

## 주의사항
- 내재가치 추정 불확실성, 업종 구조 변화(해자 약화), 가치 함정 여부 확인

## 실수와 교훈

### 1. IBM 투자 실패 (2011-2018)
- **문제**: 기술 변화 속도를 과소평가
- **교훈**: Circle of Competence 벗어남

### 2. 항공주 투자 실패 (2020)
- **문제**: 코로나19로 구조적 변화
- **교훈**: 산업 전망 재평가 중요

### 3. 닷컴 버블 회피 (1999-2000)
- **성공**: 이해할 수 없는 기술주 회피
- **결과**: 버블 붕괴 후 상대적 우위

---

## 한국 시장 적용

### 적합한 종목 예시
- **삼성전자**: 글로벌 브랜드, 기술 우위
- **SK하이닉스**: 메모리 시장 과점
- **NAVER**: 국내 검색 독점, 생태계
- **카카오**: 플랫폼 lock-in 효과

### 주의할 점
1. 한국 시장은 가족 경영 리스크 존재
2. 지배구조 이슈 점검 필요
3. 배당보다 자사주 소각 선호

---

## 백테스트 전략

```json
{
  "strategy_name": "워렌 버핏 스타일",
  "buy_conditions": [
    {"factor": "PER", "operator": "<", "value": 15},
    {"factor": "PBR", "operator": "<", "value": 1.5},
    {"factor": "ROE", "operator": ">", "value": 15},
    {"factor": "부채비율", "operator": "<", "value": 100},
    {"factor": "배당수익률", "operator": ">", "value": 2}
  ],
  "sell_conditions": [
    {"factor": "PER", "operator": ">", "value": 30}
  ],
  "holding_period": "long_term",
  "rebalancing": "yearly"
}
```

---

## 명언

> "Rule No. 1: Never lose money. Rule No. 2: Never forget rule No. 1."
> (규칙 1: 절대 돈을 잃지 마라. 규칙 2: 절대 규칙 1을 잊지 마라)

> "Be fearful when others are greedy, and greedy when others are fearful."
> (남들이 탐욕스러울 때 두려워하고, 남들이 두려워할 때 탐욕스러워라)

> "It's far better to buy a wonderful company at a fair price than a fair company at a wonderful price."
> (평범한 회사를 헐값에 사는 것보다, 훌륭한 회사를 적정가에 사는 것이 훨씬 낫다)

---

## 더 알아보기

- [벤저민 그레이엄 전략](./benjamin_graham_strategy.md)
- [가치투자 기초](./value_strategy.md)
- [ROE 팩터](../factors/profitability.md)
- [PER/PBR 팩터](../factors/valuation.md)
