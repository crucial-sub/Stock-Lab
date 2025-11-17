# 📙 전략 태그 매핑 문서  
**Version:** 1.0.0  
**Last Update:** 2025-01-16  
**Author:** Stock-Lab AI Team  

본 문서는 전략 추천 알고리즘에서 필수로 사용되는 **전략 → 태그 매핑 정보**를 정의한다.  
LLM은 아래 매핑을 기반으로 매칭 점수를 계산해야 한다.

---

# ## 📌 전략 태그 매핑 JSON

```json
{
  "strategy_tags_mapping": {
    "오늘의 급등 종목": ["short_term", "style_momentum", "risk_high"],
    "꾸준 성장주": ["long_term", "style_growth", "risk_mid_low"],
    "벤저민 그레이엄의 전략": ["long_term", "style_value", "risk_low", "sector_bluechip"],
    "피터린치의 전략": ["long_term", "style_growth", "risk_mid", "prefer_both"],
    "워렌버핏의 전략": ["long_term", "style_value", "risk_low", "prefer_dividend", "sector_bluechip"],
    "윌리엄 오닐의 전략": ["short_term", "style_momentum", "risk_high"],
    "빌 애크먼의 전략": ["long_term", "style_value", "risk_mid", "prefer_both"],
    "찰리 멍거의 전략": ["long_term", "style_value", "risk_low", "sector_bluechip"],
    "글렌 웰링의 전략": ["mid_term", "style_value", "risk_mid", "sector_smallmid"],
    "캐시 우드의 전략": ["long_term", "style_growth", "risk_high", "sector_innovation"],
    "글렌 그린버그의 전략": ["long_term", "style_value", "risk_mid", "sector_any"],
    "저평가 배당주": ["long_term", "style_dividend", "risk_low", "prefer_dividend"],
    "장기 고배당주": ["long_term", "style_dividend", "risk_low", "prefer_dividend", "sector_bluechip"]
  }
}
```

---

# ## 📌 매칭 점수 계산 규칙

```
match_score = (겹치는 태그 수) / (전략 태그 총 수)
match_percentage = match_score * 100
```

---

# 🔒 LLM 규칙
- 전략/태그 수정 금지  
- JSON 구조 고정  
- 전략 ID 생성 금지  

---

# 끝.
