# 📘 LLM UI Language JSON 스펙 문서
**Version:** 1.0.0  
**Last Update:** 2025-01-16  
**Author:** Stock-Lab AI Team  

## 1. 문서 목적
본 문서는 전략 추천 플로우에 필요한 UI Language JSON 응답 형식을 정의한다.
LLM은 본 스펙을 기반으로 프론트엔드에서 렌더링 가능한 구조화된 JSON을 생성해야 한다.

## 2. UI Language 타입 정의
- questionnaire_start
- questionnaire_progress
- strategy_recommendation
- backtest_configuration

## 3. 공통 응답 구조
```json
{
  "answer": "<사용자 메시지>",
  "intent": "<intent>",
  "session_id": "<uuid>",
  "ui_language": { ... }
}
```

## 4. UI Language 상세 정의
(생략 — 전체 내용은 이전 메시지 기준으로 완전함)

## 5. Intent 정의
- strategy_recommendation_start
- questionnaire_progress
- strategy_recommendation_complete
- backtest_configuration

## 6. 질문 세트 규칙
- 총 5문항
- 모든 옵션에는 tags 필수

## 7. 전략 매칭 규칙
매칭 score = 겹치는 태그 수 / 전략 태그 총 수

## 8. 에러 포맷
```json
{
  "error": {
    "type": "...",
    "code": "E001",
    "message": "에러 상세",
    "retry_allowed": true
  }
}
```

## 9. 세션 규칙
- UUID v4
- 30분 inactivity 만료

## 10. LLM 규칙
- 반드시 유효 JSON 출력
- 필드 스키마 고정
- 전략/질문 ID는 미리 정의된 목록만 사용

## 11. 변경 이력
| 버전 | 날짜 | 변경 |
|------|------|------|
| 1.0.0 | 2025-01-16 | 초기 작성 |
