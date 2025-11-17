"use client";

import { useState } from "react";
import { SecondarySidebar } from "@/components/ai-assistant/SecondarySidebar";
import { StrategyCard } from "@/components/ai-assistant/StrategyCard";
import { AISearchInput } from "@/components/home/ui";
import { sendChatMessage, type ChatResponse } from "@/lib/api/chatbot";
import { ChatInterface } from "@/components/ai-assistant/ChatInterface";
import { ChatHistory } from "@/components/ai-assistant/ChatHistory";

interface Message {
  role: "user" | "assistant";
  content: string;
}

/**
 * AI 어시스턴트 페이지 클라이언트 컴포넌트
 *
 * @description 인터랙티브한 AI 어시스턴트 화면 UI를 담당합니다.
 * 이벤트 핸들러와 상태 관리가 필요한 부분만 클라이언트 컴포넌트로 분리.
 */

interface Strategy {
  id: string;
  title: string;
  description: string;
}

interface AIAssistantPageClientProps {
  /** 큰 카드 정보 */
  largeStrategy: {
    title: string;
    description: string;
  };
  /** 작은 카드 목록 */
  smallStrategies: Strategy[];
}

export function AIAssistantPageClient({
  largeStrategy,
  smallStrategies,
}: AIAssistantPageClientProps) {
  const [sessionId, setSessionId] = useState<string>("");
  const [chatResponse, setChatResponse] = useState<ChatResponse | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [messages, setMessages] = useState<Message[]>([]);
  const [questionHistory, setQuestionHistory] = useState<Array<{
    questionId: string;
    selectedOptionId: string;
    question: any;
  }>>([]);

  const handleLargeCardClick = async () => {
    // 전략 추천 플로우 시작
    console.log("Starting strategy recommendation flow");

    // 사용자 메시지 추가
    const userMessage = "전략 추천받고 싶어요";
    setMessages((prev) => [...prev, { role: "user", content: userMessage }]);

    setIsLoading(true);
    try {
      const response = await sendChatMessage({
        message: userMessage,
      });

      setSessionId(response.session_id);
      setChatResponse(response);

      // AI 응답 메시지 추가 (설문조사 시작이라는 응답)
      if (response.answer) {
        setMessages((prev) => [
          ...prev,
          { role: "assistant", content: response.answer },
        ]);
      }

      console.log("Response:", response);
      console.log("UI Language:", response.ui_language);
    } catch (error) {
      console.error("Failed to start recommendation:", error);
    } finally {
      setIsLoading(false);
    }
  };

  const handleStrategyClick = async (strategyId: string) => {
    // 전략 카드 클릭 시 해당 전략에 대해 질문
    const strategyTitles: { [key: string]: string } = {
      "1": "윌리엄 오닐의 전략",
      "2": "워렌 버핏의 전략",
      "3": "피터 린치의 전략",
      "4": "캐시 우드의 전략",
    };

    const strategyTitle = strategyTitles[strategyId];
    const userMessage = `${strategyTitle}에 대해 알려줘`;

    console.log(`Strategy ${strategyId} clicked:`, userMessage);

    // 사용자 메시지 추가
    setMessages((prev) => [...prev, { role: "user", content: userMessage }]);

    setIsLoading(true);
    try {
      const response = await sendChatMessage({
        message: userMessage,
        session_id: sessionId || undefined,
      });

      setSessionId(response.session_id);
      // 전략 카드 클릭 시에도 설문/추천 UI를 그대로 노출한다.
      setChatResponse(response);

      // AI 응답 메시지 추가
      setMessages((prev) => [
        ...prev,
        { role: "assistant", content: response.answer },
      ]);

      console.log("Response:", response);
    } catch (error) {
      console.error("Failed to get strategy info:", error);
    } finally {
      setIsLoading(false);
    }
  };

  const handleAISubmit = async (value: string) => {
    // AI 요청 처리
    console.log("AI request:", value);

    // 사용자 메시지 추가
    setMessages((prev) => [...prev, { role: "user", content: value }]);

    setIsLoading(true);
    try {
      const response = await sendChatMessage({
        message: value,
        session_id: sessionId || undefined,
      });

      setSessionId(response.session_id);
      setChatResponse(response);

      // AI 응답 메시지 추가
      setMessages((prev) => [
        ...prev,
        { role: "assistant", content: response.answer },
      ]);

      console.log("Response:", response);
      console.log("UI Language:", response.ui_language);
    } catch (error) {
      console.error("Failed to send message:", error);
    } finally {
      setIsLoading(false);
    }
  };

  const handleAnswerSelect = async (questionId: string, optionId: string, answerText: string) => {
    // 설문조사 답변 전송
    console.log("Answer selected:", questionId, optionId, answerText);

    // 현재 질문을 히스토리에 저장 (다음 질문으로 넘어가기 전에)
    if (chatResponse?.ui_language?.question) {
      setQuestionHistory((prev) => [...prev, {
        questionId: questionId,
        selectedOptionId: optionId,
        question: chatResponse.ui_language.question
      }]);
    }

    // 사용자 답변을 메시지에 추가
    setMessages((prev) => [...prev, { role: "user", content: answerText }]);

    setIsLoading(true);
    try {
      const response = await sendChatMessage({
        message: "",
        session_id: sessionId,
        answer: {
          question_id: questionId,
          option_id: optionId,
        },
      });

      setSessionId(response.session_id);
      setChatResponse(response);

      console.log("Response:", response);
      console.log("UI Language:", response.ui_language);
    } catch (error) {
      console.error("Failed to send answer:", error);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="flex h-full">
      {/* 2차 사이드바 */}
      <SecondarySidebar />

      {/* 메인 콘텐츠 */}
      <main className="flex-1 flex flex-col px-10 pt-[120px] pb-20 overflow-auto">
        {/* 설문조사 또는 전략 추천 UI */}
        {chatResponse?.ui_language ? (
          <ChatInterface
            chatResponse={chatResponse}
            isLoading={isLoading}
            onAnswerSelect={handleAnswerSelect}
            messages={messages}
            questionHistory={questionHistory}
          />
        ) : messages.length > 0 ? (
          /* 채팅 히스토리 표시 */
          <div className="flex-1 flex flex-col items-center">
            <h1 className="text-[32px] font-bold text-black text-center mb-[40px]">
              사용자님, 오늘도 수익을 내볼까요?
            </h1>

            <ChatHistory messages={messages} />

            <div className="sticky bottom-0 w-full max-w-[1000px] mt-8 bg-white pt-4">
              <AISearchInput
                placeholder="만들고 싶은 전략을 AI에게 요청하세요!"
                onSubmit={handleAISubmit}
              />
            </div>
          </div>
        ) : (
          /* 초기 화면 */
          <div className="flex flex-col items-center">
            {/* 타이틀 */}
            <h1 className="text-[32px] font-bold text-black text-center mb-[80px]">
              궁금한 내용을 AI에게 확인해보세요!
            </h1>

            {/* 큰 카드 */}
            <div className="w-full max-w-[1000px] mb-[112px]">
              <StrategyCard
                title={largeStrategy.title}
                description={largeStrategy.description}
                size="large"
                onClick={handleLargeCardClick}
              />
            </div>

            {/* 작은 카드 그리드 (2x2) */}
            <div className="grid grid-cols-2 gap-x-[40px] gap-y-[32px] mb-[114px]">
              {smallStrategies.map((strategy) => (
                <StrategyCard
                  key={strategy.id}
                  title={strategy.title}
                  description={strategy.description}
                  onClick={() => handleStrategyClick(strategy.id)}
                />
              ))}
            </div>

            {/* AI 입력창 */}
            <div className="w-full max-w-[1000px]">
              <AISearchInput
                placeholder="만들고 싶은 전략을 AI에게 요청하세요!"
                onSubmit={handleAISubmit}
              />
            </div>
          </div>
        )}
      </main>
    </div>
  );
}
