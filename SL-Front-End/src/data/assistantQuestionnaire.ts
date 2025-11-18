/**
 * AI 어시스턴트 투자 성향 설문 데이터
 *
 * 5개의 고정된 질문으로 구성되며, 각 선택지는 태그를 포함합니다.
 * 태그는 전략 추천 로직에서 사용됩니다.
 */

// ============================================================================
// 타입 정의
// ============================================================================

/**
 * 질문 선택지 인터페이스
 */
export interface QuestionOption {
  /** 선택지 고유 ID (예: "q1_short_term") */
  id: string;
  /** 이모지 아이콘 */
  icon: string;
  /** 선택지 레이블 */
  label: string;
  /** 선택지 설명 */
  description: string;
  /** 전략 매칭용 태그 배열 */
  tags: string[];
}

/**
 * 설문 질문 인터페이스
 */
export interface Question {
  /** 질문 고유 ID (예: "q1") */
  id: string;
  /** 질문 텍스트 */
  text: string;
  /** 질문 순서 (1부터 시작) */
  order: number;
  /** 선택지 배열 */
  options: QuestionOption[];
}

/**
 * 유저 답변 인터페이스
 */
export interface QuestionnaireAnswer {
  /** 질문 ID */
  questionId: string;
  /** 선택한 옵션 ID */
  optionId: string;
  /** 선택한 옵션의 태그 배열 */
  tags: string[];
}

// ============================================================================
// 설문 데이터
// ============================================================================

/**
 * 투자 성향 설문 질문 리스트
 */
export const QUESTIONNAIRE: Question[] = [
  {
    id: "q1",
    text: "보통 얼마 동안 보유할 생각으로 투자하시나요?",
    order: 1,
    options: [
      {
        id: "q1_short_term",
        icon: "⚡",
        label: "단기 매매 (며칠 ~ 몇 주)",
        description: "빠르게 사고팔면서 단기 수익을 노립니다.",
        tags: ["short_term"]
      },
      {
        id: "q1_mid_term",
        icon: "📊",
        label: "중기 투자 (몇 개월)",
        description: "몇 달 정도 흐름을 보면서 가져갑니다.",
        tags: ["mid_term"]
      },
      {
        id: "q1_long_term",
        icon: "🌱",
        label: "장기 투자 (1년 이상)",
        description: "좋은 기업을 골라 오래 들고 가고 싶어요.",
        tags: ["long_term"]
      }
    ]
  },
  {
    id: "q2",
    text: "어떤 투자 스타일이 마음에 드시나요?",
    order: 2,
    options: [
      {
        id: "q2_value",
        icon: "💎",
        label: "가치 투자",
        description: "저평가된 우량주를 찾아 장기 보유합니다.",
        tags: ["style_value"]
      },
      {
        id: "q2_growth",
        icon: "🚀",
        label: "성장 투자",
        description: "빠르게 성장하는 기업에 투자합니다.",
        tags: ["style_growth"]
      },
      {
        id: "q2_momentum",
        icon: "📈",
        label: "모멘텀 투자",
        description: "상승 추세인 종목을 따라 투자합니다.",
        tags: ["style_momentum"]
      },
      {
        id: "q2_dividend",
        icon: "💰",
        label: "배당 투자",
        description: "안정적인 배당 수익을 추구합니다.",
        tags: ["style_dividend"]
      }
    ]
  },
  {
    id: "q3",
    text: "주가 변동성(리스크)을 얼마나 감수하실 수 있나요?",
    order: 3,
    options: [
      {
        id: "q3_high",
        icon: "🎢",
        label: "크게 괜찮아요",
        description: "높은 수익을 위해 변동성을 감수할 수 있습니다.",
        tags: ["risk_high"]
      },
      {
        id: "q3_medium",
        icon: "⚖️",
        label: "어느 정도는 괜찮아요",
        description: "적당한 수준의 변동성은 감수 가능합니다.",
        tags: ["risk_medium"]
      },
      {
        id: "q3_low",
        icon: "🛡️",
        label: "최소한의 손실만 감수하고 싶어요",
        description: "안정적인 투자를 선호합니다.",
        tags: ["risk_low"]
      }
    ]
  },
  {
    id: "q4",
    text: "배당과 시세차익 중 무엇이 더 중요한가요?",
    order: 4,
    options: [
      {
        id: "q4_dividend",
        icon: "💵",
        label: "배당이 중요해요",
        description: "정기적인 배당 수익을 원합니다.",
        tags: ["prefer_dividend"]
      },
      {
        id: "q4_capital_gain",
        icon: "📊",
        label: "시세차익이 중요해요",
        description: "주가 상승을 통한 수익을 원합니다.",
        tags: ["prefer_capital_gain"]
      },
      {
        id: "q4_both",
        icon: "⚖️",
        label: "둘 다 중요해요",
        description: "배당과 시세차익 모두 고려합니다.",
        tags: ["prefer_both"]
      }
    ]
  },
  {
    id: "q5",
    text: "어떤 타입의 종목을 선호하시나요?",
    order: 5,
    options: [
      {
        id: "q5_innovation",
        icon: "🔬",
        label: "혁신 기술 기업",
        description: "AI, 바이오 등 혁신적인 기술 기업을 선호합니다.",
        tags: ["sector_innovation"]
      },
      {
        id: "q5_traditional",
        icon: "🏢",
        label: "전통 우량 기업",
        description: "안정적인 대형 우량 기업을 선호합니다.",
        tags: ["sector_traditional"]
      },
      {
        id: "q5_small_cap",
        icon: "💎",
        label: "중소형 성장주",
        description: "잠재력 있는 중소형 기업을 선호합니다.",
        tags: ["sector_small_cap"]
      },
      {
        id: "q5_any",
        icon: "🌐",
        label: "상관없어요",
        description: "종목 타입은 특별히 신경 쓰지 않습니다.",
        tags: ["sector_any"]
      }
    ]
  }
];

// ============================================================================
// 상수
// ============================================================================

/** 전체 설문 질문 수 */
export const TOTAL_QUESTIONS = QUESTIONNAIRE.length;

/** 설문 제목 */
export const QUESTIONNAIRE_TITLE = "투자 성향 설문";

/** 설문 시작 CTA 텍스트 */
export const QUESTIONNAIRE_CTA = "퀀트 투자나 주식 투자가 처음이신가요?";

/** 설문 시작 버튼 텍스트 */
export const QUESTIONNAIRE_START_BUTTON = "투자 성향 알아보기";

// ============================================================================
// 유틸리티 함수
// ============================================================================

/**
 * 질문 ID로 질문 데이터 조회
 */
export function getQuestionById(questionId: string): Question | undefined {
  return QUESTIONNAIRE.find(q => q.id === questionId);
}

/**
 * 질문 순서(order)로 질문 데이터 조회
 */
export function getQuestionByOrder(order: number): Question | undefined {
  return QUESTIONNAIRE.find(q => q.order === order);
}

/**
 * 답변 배열에서 모든 태그 추출
 */
export function extractTagsFromAnswers(answers: QuestionnaireAnswer[]): string[] {
  const allTags = answers.flatMap(answer => answer.tags);
  // 중복 제거
  return Array.from(new Set(allTags));
}

/**
 * 질문 ID와 옵션 ID로 QuestionnaireAnswer 생성
 */
export function createAnswer(
  questionId: string,
  optionId: string
): QuestionnaireAnswer | null {
  const question = getQuestionById(questionId);
  if (!question) return null;

  const option = question.options.find(opt => opt.id === optionId);
  if (!option) return null;

  return {
    questionId,
    optionId,
    tags: option.tags
  };
}

/**
 * 태그 → 명확한 한글 설명 매핑
 * 맥락 없이도 의미를 파악할 수 있도록 작성
 */
const TAG_LABEL_MAP: Record<string, string> = {
  // 투자 기간
  short_term: "단기 투자 선호",
  mid_term: "중기 투자 선호",
  long_term: "장기 투자 선호",

  // 투자 스타일
  style_value: "가치 투자 선호",
  style_growth: "성장 투자 선호",
  style_momentum: "모멘텀 투자 선호",
  style_dividend: "배당 투자 선호",

  // 위험 감수도
  risk_high: "높은 위험 감수 가능",
  risk_medium: "적당한 위험 감수",
  risk_low: "낮은 위험 선호",

  // 배당 vs 시세차익
  prefer_dividend: "배당 수익 중시",
  prefer_capital_gain: "시세차익 중시",
  prefer_both: "배당과 시세차익 모두 중시",

  // 종목 타입
  sector_innovation: "혁신 기술 기업 선호",
  sector_traditional: "전통 우량 기업 선호",
  sector_small_cap: "중소형 성장주 선호",
  sector_any: "종목 타입 무관",
};

/**
 * 영어 태그를 명확한 한글 설명으로 변환
 *
 * @param tag - 영어 태그 (예: "risk_low")
 * @returns 한글 설명 (예: "낮은 위험 선호") 또는 원본 태그
 */
export function getTagLabel(tag: string): string {
  return TAG_LABEL_MAP[tag] || tag;
}
