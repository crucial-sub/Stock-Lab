"""UI Language JSON 데이터 모델 및 응답 생성"""
from dataclasses import dataclass, asdict, field
from typing import List, Optional, Dict, Any
from enum import Enum


class UILanguageType(str, Enum):
    """UI 렌더링 타입"""
    QUESTIONNAIRE_START = "questionnaire_start"
    QUESTIONNAIRE_PROGRESS = "questionnaire_progress"
    STRATEGY_RECOMMENDATION = "strategy_recommendation"
    BACKTEST_CONFIGURATION = "backtest_configuration"


@dataclass
class OptionCard:
    """선택지 카드"""
    id: str
    label: str
    description: str
    icon: str
    tags: List[str]

    def to_dict(self):
        return asdict(self)


@dataclass
class Question:
    """질문 데이터"""
    question_id: str
    text: str
    options: List[OptionCard]

    def to_dict(self):
        return {
            "question_id": self.question_id,
            "text": self.text,
            "options": [opt.to_dict() for opt in self.options]
        }


@dataclass
class UILanguageQuestionnaire:
    """Questionnaire UI Language"""
    type: UILanguageType
    total_questions: int
    current_question: int
    progress_percentage: Optional[int] = None
    question: Optional[Question] = None

    def to_dict(self):
        data = {
            "type": self.type.value,
            "total_questions": self.total_questions,
            "current_question": self.current_question,
        }
        if self.progress_percentage is not None:
            data["progress_percentage"] = self.progress_percentage
        if self.question:
            data["question"] = self.question.to_dict()
        return data


@dataclass
class ConditionPreview:
    """백테스트 조건 미리보기"""
    condition: str
    condition_info: List[str]

    def to_dict(self):
        return asdict(self)


@dataclass
class StrategyRecommendation:
    """전략 추천 카드"""
    rank: int
    strategy_id: str
    strategy_name: str
    summary: str
    match_score: float
    match_percentage: int
    match_reasons: List[str]
    tags: List[str]
    conditions_preview: List[ConditionPreview]
    icon: str
    badge: Optional[str] = None

    def to_dict(self):
        return {
            "rank": self.rank,
            "strategy_id": self.strategy_id,
            "strategy_name": self.strategy_name,
            "summary": self.summary,
            "match_score": self.match_score,
            "match_percentage": self.match_percentage,
            "match_reasons": self.match_reasons,
            "tags": self.tags,
            "conditions_preview": [c.to_dict() for c in self.conditions_preview],
            "icon": self.icon,
            "badge": self.badge
        }


@dataclass
class UserProfileSummary:
    """유저 프로필 요약"""
    investment_period: str
    investment_style: str
    risk_tolerance: str
    dividend_preference: str
    sector_preference: str

    def to_dict(self):
        return asdict(self)


@dataclass
class UILanguageRecommendation:
    """Strategy Recommendation UI Language"""
    type: UILanguageType
    recommendations: List[StrategyRecommendation]
    user_profile_summary: UserProfileSummary

    def to_dict(self):
        return {
            "type": self.type.value,
            "recommendations": [r.to_dict() for r in self.recommendations],
            "user_profile_summary": self.user_profile_summary.to_dict()
        }


@dataclass
class ConfigurationField:
    """백테스트 설정 필드"""
    field_id: str
    label: str
    type: str  # number, date, select, text
    unit: Optional[str] = None
    default_value: Optional[Any] = None
    min_value: Optional[Any] = None
    max_value: Optional[Any] = None
    step: Optional[Any] = None
    required: bool = True
    description: Optional[str] = None
    options: Optional[List[Dict[str, str]]] = None  # for select type

    def to_dict(self):
        data = {
            "field_id": self.field_id,
            "label": self.label,
            "type": self.type,
            "required": self.required,
        }
        if self.unit:
            data["unit"] = self.unit
        if self.default_value is not None:
            data["default_value"] = self.default_value
        if self.min_value is not None:
            data["min_value"] = self.min_value
        if self.max_value is not None:
            data["max_value"] = self.max_value
        if self.step is not None:
            data["step"] = self.step
        if self.description:
            data["description"] = self.description
        if self.options:
            data["options"] = self.options
        return data


@dataclass
class UILanguageBacktestConfiguration:
    """Backtest Configuration UI Language"""
    type: UILanguageType
    strategy: Dict[str, str]
    configuration_fields: List[ConfigurationField]

    def to_dict(self):
        return {
            "type": self.type.value,
            "strategy": self.strategy,
            "configuration_fields": [f.to_dict() for f in self.configuration_fields]
        }


# 5개 질문 세트
QUESTIONS_DATA = {
    "investment_period": {
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
    "investment_style": {
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
    "risk_tolerance": {
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
    "dividend_preference": {
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
    "sector_preference": {
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
}

# 전략 태그 매핑
STRATEGY_TAGS_MAPPING = {
    "cathy_wood": {
        "strategy_id": "cathy_wood",
        "strategy_name": "캐시 우드의 전략",
        "tags": ["long_term", "style_growth", "risk_high", "sector_innovation"],
        "summary": "AI·로봇·바이오 혁신 기술 및 고성장 기업 투자자 캐시우드의 전략",
        "conditions": [
            {"condition": "0 < PEG < 2", "condition_info": ["PEG = PER ÷ EPS성장률", "성장 대비 주가수준"]},
            {"condition": "매출 성장률 > 20%", "condition_info": ["매출액의 전년 동기 대비 성장률"]}
        ]
    },
    "peter_lynch": {
        "strategy_id": "peter_lynch",
        "strategy_name": "피터린치의 전략",
        "tags": ["long_term", "style_growth", "risk_mid", "prefer_both"],
        "summary": "PER·PEG를 활용해 실적 대비 저평가된 성장주를 콕 집어주는 린치식 전략",
        "conditions": [
            {"condition": "PER < 30", "condition_info": ["PER = 주가 ÷ 주당순이익(EPS)"]},
            {"condition": "0 < PEG < 1.8", "condition_info": ["PEG = PER ÷ EPS성장률", "성장 대비 주가수준"]}
        ]
    },
    "warren_buffett": {
        "strategy_id": "warren_buffett",
        "strategy_name": "워렌버핏의 전략",
        "tags": ["long_term", "style_value", "risk_low", "prefer_dividend", "sector_bluechip"],
        "summary": "우량 대형주에 투자하여 장기적 가치 상승을 노리는 버핏의 투자 철학",
        "conditions": [
            {"condition": "PER < 20", "condition_info": ["PER = 주가 ÷ 주당순이익(EPS)"]},
            {"condition": "ROE > 15%", "condition_info": ["ROE = (순이익 ÷ 자기자본) * 100"]}
        ]
    },
    "consistent_growth": {
        "strategy_id": "consistent_growth",
        "strategy_name": "꾸준 성장주",
        "tags": ["long_term", "style_growth", "risk_mid_low"],
        "summary": "앞으로 안정적인 성장을 이룰 종목",
        "conditions": [
            {"condition": "매출 CAGR(3Y) > 0", "condition_info": ["최근 3년 매출의 연평균 증가율"]},
            {"condition": "ROE > 10%", "condition_info": ["ROE = (순이익 ÷ 자기자본) * 100"]}
        ]
    }
}
