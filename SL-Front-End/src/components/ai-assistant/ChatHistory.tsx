"use client";

import { ChatMessage } from "./ChatMessage";

interface Message {
  role: "user" | "assistant";
  content: string;
}

interface ChatHistoryProps {
  messages: Message[];
}

/**
 * 채팅 히스토리 컴포넌트
 */
export function ChatHistory({ messages }: ChatHistoryProps) {
  return (
    <div className="w-full max-w-[1000px] mx-auto">
      <div className="space-y-1">
        {messages.map((message, index) => (
          <ChatMessage
            key={index}
            role={message.role}
            content={message.content}
          />
        ))}
      </div>
    </div>
  );
}
