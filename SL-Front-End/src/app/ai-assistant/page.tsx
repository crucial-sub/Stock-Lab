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

const SAMPLE_QUESTION = {
  large: {
    question: "퀀트 투자나 주식 투자가 처음이신가요?",
    description:
      "본인의 성향을 파악해, AI가 추천하는 전략을 적용해보세요!\n간단한 질문에 대한 답변으로 AI가 분석하고 잘 맞는 전략을 추천해드립니다.",
  },
  small: [
    {
      id: "1",
      question: "퀀트 투자가 뭐야?",
    },
    {
      id: "2",
      question: "PBR, PER이 뭐야?",
    },
    {
      id: "3",
      question: "IT 테마의 동향을 확인해줘",
    },
    {
      id: "4",
      question: "퀀트 투자에서 중요한 가치가 뭐야?",
    },
  ],
};

export default async function AIAssistantPage({
  searchParams,
}: {
  searchParams: { [key: string]: string | string[] | undefined };
}) {
  const autoStart = searchParams?.autoStart === "questionnaire";
  // TODO: API에서 전략 데이터 가져오기
  // const strategies = await fetchStrategies();

  return (
    <AIAssistantPageClient
      largeSample={SAMPLE_QUESTION.large}
      smallSample={SAMPLE_QUESTION.small}
      autoStartQuestionnaire={autoStart}
    />
  );
}
