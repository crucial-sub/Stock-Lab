# 📗 UI Language 질문 세트 문서  
**Version:** 1.0.0  
**Last Update:** 2025-01-16  
**Author:** Stock-Lab AI Team  

본 문서는 LLM이 전략 추천 설문을 구성할 때 반드시 참조해야 하는 **5개 고정 질문 세트**를 정의한다.  
LLM은 질문/옵션/태그를 임의로 수정하거나 변형해서는 안 된다.

---

# ## 📌 전체 질문 JSON 정의

```json
{
  "questions": [
    {
      "question_id": "investment_period",
      "order": 1,
      "text": "보통 얼마 동안 보유할 생각으로 투자하시나요?",
      "options": [
        {
          "id": "short_term",
          "label": "단기 매매 (며칠 ~ 몇 주)",
          "description": "빠르게 사고팔면서 단기 수익을 노립니다.",
          "icon": "⚡",
          "tags": ["short_term", "style_momentum"]
        },
        {
          "id": "mid_term",
          "label": "중기 투자 (몇 개월)",
          "description": "몇 달 정도 흐름을 보면서 가져갑니다.",
          "icon": "📊",
          "tags": ["mid_term"]
        },
        {
          "id": "long_term",
          "label": "장기 투자 (1년 이상)",
          "description": "좋은 기업을 골라 오래 들고 가고 싶어요.",
          "icon": "🏆",
          "tags": ["long_term", "style_value"]
        }
      ]
    },
    {
      "question_id": "investment_style",
      "order": 2,
      "text": "아래 중에서 가장 본인 스타일에 가까운 걸 골라주세요.",
      "options": [
        {
          "id": "value",
          "label": "가치/저평가 위주",
          "description": "싸게 사서 안전마진을 확보하는 게 좋다.",
          "icon": "💎",
          "tags": ["style_value"]
        },
        {
          "id": "growth",
          "label": "성장/실적 위주",
          "description": "매출·이익이 빠르게 커지는 기업이 좋다.",
          "icon": "📈",
          "tags": ["style_growth"]
        },
        {
          "id": "momentum",
          "label": "모멘텀/추세 위주",
          "description": "최근에 많이 오르고 있는 강한 종목이 좋다.",
          "icon": "🚀",
          "tags": ["style_momentum"]
        },
        {
          "id": "dividend",
          "label": "배당 수익 위주",
          "description": "배당을 꾸준히 받으면서 안정적으로 가고 싶다.",
          "icon": "💰",
          "tags": ["style_dividend"]
        }
      ]
    },
    {
      "question_id": "risk_tolerance",
      "order": 3,
      "text": "투자 중에 일시적으로 -20% 같은 큰 손실이 나도 버틸 수 있나요?",
      "options": [
        {
          "id": "risk_high",
          "label": "크게 흔들려도 괜찮아요",
          "description": "수익률만 좋다면 -30% 정도 변동도 감수할 수 있어요.",
          "icon": "🎢",
          "tags": ["risk_high"]
        },
        {
          "id": "risk_mid",
          "label": "어느 정도는 괜찮아요",
          "description": "-10% ~ -20% 수준은 감수할 수 있어요.",
          "icon": "⚖️",
          "tags": ["risk_mid"]
        },
        {
          "id": "risk_low",
          "label": "손실은 최소화하고 싶어요",
          "description": "-10%만 넘어가도 스트레스를 많이 받아요.",
          "icon": "🛡️",
          "tags": ["risk_low"]
        }
      ]
    },
    {
      "question_id": "dividend_preference",
      "order": 4,
      "text": "아래 둘 중, 더 끌리는 쪽은 어디인가요?",
      "options": [
        {
          "id": "prefer_dividend",
          "label": "배당이 중요하다",
          "description": "매년 현금 배당이 들어오는 게 좋고, 배당이 꾸준해야 안심돼요.",
          "icon": "💵",
          "tags": ["prefer_dividend"]
        },
        {
          "id": "prefer_capital_gain",
          "label": "배당보다 시세차익이 중요하다",
          "description": "배당은 없어도 되니, 주가가 많이 오르는 게 더 중요해요.",
          "icon": "📈",
          "tags": ["prefer_capital_gain"]
        },
        {
          "id": "prefer_both",
          "label": "둘 다 적당히 있으면 좋다",
          "description": "배당도 받고, 주가도 오르면 제일 베스트죠.",
          "icon": "🎯",
          "tags": ["prefer_both"]
        }
      ]
    },
    {
      "question_id": "sector_preference",
      "order": 5,
      "text": "어떤 종류의 기업에 더 끌리나요?",
      "options": [
        {
          "id": "innovation",
          "label": "혁신 기술/성장 섹터",
          "description": "AI, 로봇, 바이오, 핀테크 같은 미래 기술 기업이 좋다.",
          "icon": "🚀",
          "tags": ["sector_innovation"]
        },
        {
          "id": "bluechip",
          "label": "전통 산업/우량 대형주",
          "description": "이미 자리가 잡힌 안정적인 대형 기업이 좋다.",
          "icon": "🏢",
          "tags": ["sector_bluechip"]
        },
        {
          "id": "smallmid",
          "label": "중소형/숨은 진주형 종목",
          "description": "아직 덜 알려졌지만, 개선 여지가 큰 중소형주가 좋다.",
          "icon": "💎",
          "tags": ["sector_smallmid"]
        },
        {
          "id": "any",
          "label": "특별히 상관없다",
          "description": "섹터는 상관없고, 조건만 좋으면 된다.",
          "icon": "🎲",
          "tags": ["sector_any"]
        }
      ]
    }
  ]
}
```

---

# 🔒 LLM 규칙
- 질문/옵션/태그는 절대 수정 불가  
- 순서(order)는 항상 1→5  
- 옵션 추가/삭제 금지  

---

# 끝.
