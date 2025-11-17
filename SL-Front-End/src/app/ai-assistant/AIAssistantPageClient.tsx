"use client";

import { useState, useEffect, useCallback } from "react";
import { SecondarySidebar } from "@/components/ai-assistant/SecondarySidebar";
import { StrategyCard } from "@/components/ai-assistant/StrategyCard";
import { AISearchInput } from "@/components/home/ui";
import { sendChatMessage, type ChatResponse } from "@/lib/api/chatbot";
import { ChatInterface } from "@/components/ai-assistant/ChatInterface";
import { ChatHistory } from "@/components/ai-assistant/ChatHistory";

interface Message {
  role: "user" | "assistant";
  content: string;
  backtestConditions?: any[];  // DSL 조건이 있을 경우
}

interface ChatSession {
  id: string;
  title: string;
  lastMessage: string;
  timestamp: number;
  messages: Message[];
  mode: "initial" | "chat" | "questionnaire";
  chatResponse?: ChatResponse | null;
  questionHistory?: Array<{
    questionId: string;
    selectedOptionId: string;
    question: any;
  }>;
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
  const [chatSessions, setChatSessions] = useState<ChatSession[]>([]);
  const [currentMode, setCurrentMode] = useState<"initial" | "chat" | "questionnaire">("initial");
  const [lastRequestTime, setLastRequestTime] = useState<number>(0);
  const MIN_REQUEST_INTERVAL = 2000; // 최소 2초 간격

  // 채팅 세션 저장 함수
  const saveChatSession = (sessionId: string, firstMessage: string) => {
    const newSession: ChatSession = {
      id: sessionId,
      title: firstMessage.length > 20 ? firstMessage.substring(0, 20) + "..." : firstMessage,
      lastMessage: firstMessage,
      timestamp: Date.now(),
      messages: messages,
      mode: currentMode,
      chatResponse: chatResponse,
      questionHistory: questionHistory,
    };

    setChatSessions((prev) => {
      // 이미 존재하는 세션이면 업데이트하지 않음
      if (prev.find(s => s.id === sessionId)) {
        return prev;
      }
      // 최신 세션을 앞에 추가
      return [newSession, ...prev];
    });
  };

  // 현재 세션 상태 업데이트 (메시지가 추가될 때마다)
  const updateCurrentSession = useCallback(() => {
    if (!sessionId) return;

    setChatSessions((prev) => {
      const existingIndex = prev.findIndex(s => s.id === sessionId);
      if (existingIndex === -1) return prev;

      const updated = [...prev];
      updated[existingIndex] = {
        ...updated[existingIndex],
        messages: messages,
        mode: currentMode,
        chatResponse: chatResponse,
        questionHistory: questionHistory,
        lastMessage: messages.length > 0 ? messages[messages.length - 1].content : "",
        timestamp: Date.now(),
      };
      return updated;
    });
  }, [sessionId, messages, currentMode, chatResponse, questionHistory]);

  // 채팅 세션 클릭 핸들러 - 이전 대화 불러오기
  const handleChatSessionClick = (chatId: string) => {
    console.log("Chat session clicked:", chatId);

    const session = chatSessions.find(s => s.id === chatId);
    if (!session) return;

    // 세션 상태 복원
    setSessionId(session.id);
    setMessages(session.messages || []);
    setCurrentMode(session.mode || "chat");
    setChatResponse(session.chatResponse || null);
    setQuestionHistory(session.questionHistory || []);
  };

  const handleLargeCardClick = async () => {
    // 전략 추천 플로우 시작
    console.log("Starting strategy recommendation flow");

    // 사용자 메시지 추가
    const userMessage = "전략 추천받고 싶어요";
    setMessages((prev) => [...prev, { role: "user", content: userMessage }]);
    setCurrentMode("questionnaire");

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

      // 채팅 세션 저장
      saveChatSession(response.session_id, userMessage);

      console.log("Response:", response);
      console.log("UI Language:", response.ui_language);
    } catch (error) {
      console.error("Failed to start recommendation:", error);
    } finally {
      setIsLoading(false);
    }
  };

  const handleStrategyClick = async (strategyId: string) => {
    // 전략 카드 클릭 시 해당 전략에 대해 질문 - 채팅 모드로 전환
    const strategyTitles: { [key: string]: string } = {
      "1": "윌리엄 오닐의 전략",
      "2": "워렌 버핏의 전략",
      "3": "피터 린치의 전략",
      "4": "캐시 우드의 전략",
    };

    const strategyTitle = strategyTitles[strategyId];
    const userMessage = `${strategyTitle}에 대해 알려줘`;

    console.log(`Strategy ${strategyId} clicked:`, userMessage);

    // 사용자 메시지 추가 및 채팅 모드로 전환
    setMessages((prev) => [...prev, { role: "user", content: userMessage }]);
    setCurrentMode("chat");

    setIsLoading(true);
    try {
      const response = await sendChatMessage({
        message: userMessage,
        session_id: sessionId || undefined,
      });

      setSessionId(response.session_id);

      // AI 응답 메시지 추가
      setMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          content: response.answer,
          backtestConditions: response.backtest_conditions
        },
      ]);

      // 채팅 세션 저장
      saveChatSession(response.session_id, userMessage);

      console.log("Response:", response);
    } catch (error) {
      console.error("Failed to get strategy info:", error);
    } finally {
      setIsLoading(false);
    }
  };

  const handleAISubmit = useCallback(async (value: string) => {
    // AI 요청 처리
    console.log("AI request:", value);

    // 이미 로딩 중이면 요청 무시 (연속 요청 방지)
    if (isLoading) {
      console.log("Already loading, ignoring request");
      return;
    }

    // 요청 간격 제한 (Rate Limiting)
    const now = Date.now();
    const timeSinceLastRequest = now - lastRequestTime;
    if (timeSinceLastRequest < MIN_REQUEST_INTERVAL) {
      const waitTime = Math.ceil((MIN_REQUEST_INTERVAL - timeSinceLastRequest) / 1000);
      setMessages((prev: Message[]) => [
        ...prev,
        {
          role: "assistant",
          content: `요청이 너무 빠릅니다. ${waitTime}초 후에 다시 시도해주세요.`,
        },
      ]);
      return;
    }

    setLastRequestTime(now);

    // 사용자 메시지 추가
    setMessages((prev) => [...prev, { role: "user", content: value }]);

    // 첫 입력이면 채팅 모드로 전환
    setCurrentMode((prev) => prev === "initial" ? "chat" : prev);

    setIsLoading(true);
    try {
      const response = await sendChatMessage({
        message: value,
        session_id: sessionId || undefined,
      });

      setSessionId(response.session_id);

      // ui_language가 있으면 questionnaire 모드로
      if (response.ui_language) {
        setChatResponse(response);
        setCurrentMode("questionnaire");
      }

      // AI 응답 메시지 추가
      setMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          content: response.answer,
          backtestConditions: response.backtest_conditions
        },
      ]);

      // 채팅 세션 저장
      if (!sessionId) {
        saveChatSession(response.session_id, value);
      }

      console.log("Response:", response);
      console.log("UI Language:", response.ui_language);
    } catch (error) {
      console.error("Failed to send message:", error);

      // 사용자 친화적인 에러 메시지 표시
      const errorMessage = error instanceof Error && error.message.includes("ThrottlingException")
        ? "요청이 많아 일시적으로 응답이 지연되고 있습니다.\n잠시 후(30초~1분) 다시 시도해주세요."
        : "메시지 전송에 실패했습니다. 잠시 후 다시 시도해주세요.";

      setMessages((prev: Message[]) => [
        ...prev,
        {
          role: "assistant",
          content: errorMessage,
        },
      ]);
    } finally {
      setIsLoading(false);
    }
  }, [sessionId, isLoading, lastRequestTime]);

  // localStorage에서 채팅 세션 불러오기
  useEffect(() => {
    const savedSessions = localStorage.getItem("ai-chat-sessions");
    if (savedSessions) {
      try {
        setChatSessions(JSON.parse(savedSessions));
      } catch (error) {
        console.error("Failed to load chat sessions:", error);
      }
    }
  }, []);

  // 홈 페이지에서 전달된 초기 메시지 확인
  useEffect(() => {
    const initialMessage = sessionStorage.getItem("ai-initial-message");
    if (initialMessage) {
      // 메시지를 읽은 후 삭제
      sessionStorage.removeItem("ai-initial-message");
      // 자동으로 메시지 전송
      handleAISubmit(initialMessage);
    }
  }, [handleAISubmit]);

  // chatSessions 변경 시 localStorage에 저장
  useEffect(() => {
    if (chatSessions.length > 0) {
      localStorage.setItem("ai-chat-sessions", JSON.stringify(chatSessions));
    }
  }, [chatSessions]);

  // 메시지 변경 시 현재 세션 업데이트
  useEffect(() => {
    if (messages.length > 0) {
      updateCurrentSession();
    }
  }, [messages, updateCurrentSession]);

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
      <SecondarySidebar
        chatHistory={chatSessions.map(session => ({
          id: session.id,
          title: session.title,
        }))}
        onChatClick={handleChatSessionClick}
      />

      {/* 메인 콘텐츠 */}
      <main className="flex-1 flex flex-col px-10 pt-[120px] pb-20 overflow-auto">
        {/* 설문조사 모드 */}
        {currentMode === "questionnaire" && chatResponse?.ui_language ? (
          <ChatInterface
            chatResponse={chatResponse}
            isLoading={isLoading}
            onAnswerSelect={handleAnswerSelect}
            messages={messages}
            questionHistory={questionHistory}
          />
        ) : currentMode === "chat" ? (
          /* 채팅 모드 */
          <div className="flex-1 flex flex-col w-full max-w-[1000px] mx-auto">
            {/* 스크롤 가능한 메시지 영역 */}
            <div className="flex-1 overflow-y-auto mb-4">
              <ChatHistory messages={messages} />
            </div>

            {/* 하단 고정 입력창 */}
            <div className="sticky bottom-0 w-full bg-white pt-4 border-t">
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
