/**
 * 스트리밍 채팅 메시지 컴포넌트
 *
 * useChatStream 훅과 StreamingMarkdownRenderer를 결합하여
 * 실시간 스트리밍 메시지를 렌더링하고 완료 시 chatStore에 저장합니다.
 *
 * 참조: AI_assistant_feature_spec.md 섹션 3.1, 3.3
 */

"use client";

import { useEffect } from "react";
import { useChatStream } from "@/hooks/useChatStream";
import { StreamingMarkdownRenderer } from "./StreamingMarkdownRenderer";
import { useChatStore } from "@/stores/chatStore";

interface StreamingChatMessageProps {
  /** 현재 세션 ID */
  sessionId: string;
  /** 전송할 메시지 */
  message: string;
  /** 스트리밍 시작 여부 */
  shouldStart: boolean;
}

/**
 * 스트리밍 채팅 메시지 컴포넌트
 *
 * - useChatStream으로 SSE 연결 및 스트리밍 처리
 * - StreamingMarkdownRenderer로 실시간 렌더링
 * - 스트리밍 완료 시 chatStore에 메시지 저장
 *
 * @example
 * ```tsx
 * function ChatInterface() {
 *   const { currentSessionId } = useChatStore();
 *   const [userMessage, setUserMessage] = useState("");
 *   const [shouldStream, setShouldStream] = useState(false);
 *
 *   const handleSend = () => {
 *     setShouldStream(true);
 *   };
 *
 *   return (
 *     <div>
 *       <input
 *         value={userMessage}
 *         onChange={(e) => setUserMessage(e.target.value)}
 *       />
 *       <button onClick={handleSend}>전송</button>
 *
 *       {shouldStream && (
 *         <StreamingChatMessage
 *           sessionId={currentSessionId!}
 *           message={userMessage}
 *           shouldStart={shouldStream}
 *         />
 *       )}
 *     </div>
 *   );
 * }
 * ```
 */
export function StreamingChatMessage({
  sessionId,
  message,
  shouldStart,
}: StreamingChatMessageProps) {
  const { content, isStreaming, connectionState, error, sendMessage, retry } =
    useChatStream(sessionId);

  const { addMessage } = useChatStore();

  // 메시지 전송 시작
  useEffect(() => {
    if (shouldStart && message) {
      sendMessage(message);
    }
  }, [shouldStart, message, sendMessage]);

  // 스트리밍 완료 시 chatStore에 저장
  useEffect(() => {
    if (connectionState === "complete" && content) {
      // AI 응답 메시지를 chatStore에 추가
      addMessage({
        id: `msg_${Date.now()}_${Math.random().toString(36).slice(2, 9)}`,
        role: "assistant",
        type: "markdown",
        content,
        createdAt: Date.now(),
      });
    }
  }, [connectionState, content, addMessage]);

  // 에러 발생 시 UI
  if (error) {
    return (
      <div className="flex justify-start mb-6">
        <div className="max-w-[75%] px-5 py-3.5 rounded-2xl shadow-sm bg-red-50 border border-red-200">
          <div className="text-[15px] text-red-900">
            <p className="font-semibold mb-2">⚠️ 오류가 발생했습니다</p>
            <p className="text-sm text-red-700">{error.message}</p>
            <button
              onClick={retry}
              className="mt-3 px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 transition-colors"
            >
              다시 시도
            </button>
          </div>
        </div>
      </div>
    );
  }

  // 연결 중 UI
  if (connectionState === "connecting" || connectionState === "reconnecting") {
    return (
      <div className="flex justify-start mb-6">
        <div className="max-w-[75%] px-5 py-3.5 rounded-2xl shadow-sm bg-white border border-gray-200">
          <div className="flex items-center gap-2 text-[15px] text-gray-600">
            <div className="w-2 h-2 bg-gray-400 rounded-full animate-pulse" />
            <span>
              {connectionState === "reconnecting"
                ? "재연결 시도 중..."
                : "연결 중..."}
            </span>
          </div>
        </div>
      </div>
    );
  }

  // 스트리밍 콘텐츠가 없으면 아무것도 렌더링하지 않음
  if (!content) {
    return null;
  }

  // 스트리밍 렌더링
  return (
    <StreamingMarkdownRenderer
      content={content}
      isStreaming={isStreaming}
      role="assistant"
    />
  );
}
