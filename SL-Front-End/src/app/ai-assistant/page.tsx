import { AIAssistantPageClient } from "./AIAssistantPageClient";

/**
 * AI 어시스턴트 페이지 (서버 컴포넌트)
 *
 * @description AI 어시스턴트 메인 화면의 진입점입니다.
 * 서버에서 전략 데이터를 준비하고, 적절한 화면을 렌더링합니다.
 *
 * @future
 * - 전략 데이터를 API에서 가져오기: const strategies = await fetchStrategies();
 * - 사용자별 추천 전략 제공
 */

const STRATEGIES = {
  large: {
    title: "퀀트 투자나 주식 투자가 처음이신가요?",
    description:
      "본인의 성향을 파악해, AI가 추천하는 전략을 적용해보세요!\n간단한 질문에 대한 답변으로 AI가 분석하고 잘 맞는 전략을 추천해드립니다.",
  },
  small: [
    {
      id: "1",
      title: "윌리엄 오닐의 전략",
      description:
        "회사가 돈을 꾸준히 잘 벌고 성장하는지 보고 좋은 기업을 찾는 기준\n이익 증가 / 수익성 / 주가 흐름이 좋은 튼튼한 기업을 골라내는 방법",
    },
    {
      id: "2",
      title: "워렌 버핏의 전략",
      description:
        "재무 튼튼하고 성장하는 우량주를 싸게 고르는 방식\n돈 잘 벌고 빚 적은 기업을 저평가됐을 때 찾는 기준",
    },
    {
      id: "3",
      title: "피터 린치의 전략",
      description:
        "가치 대비 싸면서 재무가 튼튼한 성장·우량 회사를 골라내는 기준\n성장성, 안정성, 배당까지 고르게 좋은 기업을 찾는 방법",
    },
    {
      id: "4",
      title: "캐시 우드의 전략",
      description:
        "성장 빠르고 기술 좋은 기업 중에서 싸게 평가된 기업을 골라내는 기준\n매출이 빨리 늘고 재무가 튼튼한 기업만 추려 고성장 우량주를 찾는 방식",
    },
  ],
};

export default async function AIAssistantPage() {
  // TODO: API에서 전략 데이터 가져오기
  // const strategies = await fetchStrategies();

  return (
    <AIAssistantPageClient
      largeStrategy={STRATEGIES.large}
      smallStrategies={STRATEGIES.small}
    />
  );
}
