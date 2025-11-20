/**
 * 메시지 렌더러 컴포넌트
 *
 * 채팅 히스토리의 각 메시지 타입에 따라 적절한 렌더러를 선택하여 렌더링
 * React Compiler가 활성화되어 있으므로 useMemo, useCallback 불필요
 */

"use client";

import type { Message } from "@/types/message";

// 개별 렌더러 컴포넌트 임포트
import { TextRenderer } from "./renderers/TextRenderer";
import { MarkdownRenderer } from "./renderers/MarkdownRenderer";
import { QuestionRenderer } from "./renderers/QuestionRenderer";
import { UserSelectionRenderer } from "./renderers/UserSelectionRenderer";
import { StrategyRecommendationRenderer } from "./renderers/StrategyRecommendationRenderer";
import { BacktestConfigRenderer } from "./renderers/BacktestConfigRenderer";
import { BacktestExecutionRenderer } from "./renderers/BacktestExecutionRenderer";
import { BacktestResultRenderer } from "./renderers/BacktestResultRenderer";

interface MessageRendererProps {
  message: Message;
  /** 백테스트 시작 콜백 (BacktestConfigRenderer에서 사용) */
  onBacktestStart?: (
    strategyName: string,
    config: {
      investmentAmount: number;
      startDate: string;
      endDate: string;
    }
  ) => void;
}

/**
 * 메시지 타입에 따라 적절한 렌더러를 선택하여 렌더링하는 컴포넌트
 * switch-case로 타입 가드를 적용하여 타입 안전성 보장
 */
export function MessageRenderer({ message, onBacktestStart }: MessageRendererProps) {
  // switch-case로 타입 가드 적용
  switch (message.type) {
    case "text":
      return <TextRenderer message={message} />;

    case "markdown":
      return <MarkdownRenderer message={message} />;

    case "question":
      return <QuestionRenderer message={message} />;

    case "user_selection":
      return <UserSelectionRenderer message={message} />;

    case "strategy_recommendation":
      return <StrategyRecommendationRenderer message={message} />;

    case "backtest_config":
      return <BacktestConfigRenderer message={message} onBacktestStart={onBacktestStart} />;

    case "backtest_execution":
      return (
        <BacktestExecutionRenderer
          backtestId={message.backtestId}
          strategyId={message.strategyId}
          strategyName={message.strategyName}
          userName={message.userName || "사용자"}
          config={{
            initialCapital: message.config.investmentAmount * 10000, // 만원 → 원 변환
            startDate: message.config.startDate,
            endDate: message.config.endDate,
          }}
        />
      );

    case "backtest_result":
      return <BacktestResultRenderer message={message} />;

    default:
      // 타입스크립트의 exhaustive check로 모든 케이스를 처리했는지 검증
      const _exhaustiveCheck: never = message;
      console.error(`Unknown message type:`, _exhaustiveCheck);
      return null;
  }
}
