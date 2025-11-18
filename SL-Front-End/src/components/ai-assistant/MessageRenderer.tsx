/**
 * 메시지 렌더러 컴포넌트
 *
 * 채팅 히스토리의 각 메시지 타입에 따라 적절한 렌더러를 선택하여 렌더링
 * React Compiler가 활성화되어 있으므로 useMemo, useCallback 불필요
 */

"use client";

import type { Message } from "@/types/message";

// 개별 렌더러 컴포넌트 임포트 (스켈레톤)
import { TextRenderer } from "./renderers/TextRenderer";
import { MarkdownRenderer } from "./renderers/MarkdownRenderer";
import { QuestionRenderer } from "./renderers/QuestionRenderer";
import { UserSelectionRenderer } from "./renderers/UserSelectionRenderer";
import { StrategyRecommendationRenderer } from "./renderers/StrategyRecommendationRenderer";
import { BacktestResultRenderer } from "./renderers/BacktestResultRenderer";

// 메시지 타입별 렌더러 맵
const MESSAGE_RENDERERS = {
  text: TextRenderer,
  markdown: MarkdownRenderer,
  question: QuestionRenderer,
  user_selection: UserSelectionRenderer,
  strategy_recommendation: StrategyRecommendationRenderer,
  backtest_result: BacktestResultRenderer,
} as const;

interface MessageRendererProps {
  message: Message;
}

/**
 * 메시지 타입에 따라 적절한 렌더러를 선택하여 렌더링하는 컴포넌트
 */
export function MessageRenderer({ message }: MessageRendererProps) {
  const Renderer = MESSAGE_RENDERERS[message.type];

  if (!Renderer) {
    console.error(`Unknown message type: ${message.type}`);
    return null;
  }

  // 타입별로 적절한 props 전달
  return <Renderer message={message as any} />;
}
