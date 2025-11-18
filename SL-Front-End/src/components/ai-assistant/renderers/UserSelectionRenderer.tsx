/**
 * 유저 선택 메시지 렌더러
 *
 * 유저가 설문 질문에서 선택한 답변을 표시
 */

"use client";

import type { UserSelectionMessage } from "@/types/message";

interface UserSelectionRendererProps {
  message: UserSelectionMessage;
}

/**
 * 유저 선택 메시지를 렌더링하는 컴포넌트
 */
export function UserSelectionRenderer({ message }: UserSelectionRendererProps) {
  return (
    <div className="flex justify-end mb-6">
      <div className="max-w-[75%] px-5 py-3.5 rounded-2xl shadow-sm bg-blue-600 text-white">
        <div className="text-[15px] leading-relaxed">
          {message.displayText}
        </div>
      </div>
    </div>
  );
}
