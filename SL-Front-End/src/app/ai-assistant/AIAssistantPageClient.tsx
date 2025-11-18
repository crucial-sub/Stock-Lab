"use client";

import { ChatHistory } from "@/components/ai-assistant/ChatHistory";
import { ChatInterface } from "@/components/ai-assistant/ChatInterface";
import { SecondarySidebar } from "@/components/ai-assistant/SecondarySidebar";
import { StrategyCard } from "@/components/ai-assistant/StrategyCard";
import { AISearchInput } from "@/components/home/ui";
import { chatHistoryApi } from "@/lib/api/chat-history";
import { sendChatMessage, type ChatResponse } from "@/lib/api/chatbot";
import { getAuthTokenFromCookie } from "@/lib/auth/token";
import { useCallback, useEffect, useState } from "react";

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

interface AIAssistantPageClientProps {
  /** 큰 카드 정보 */
  largeSample: {
    question: string;
    description: string;
  };
  /** 작은 카드 목록 */
  smallSample: {
    id: string;
    question: string;
  }[];
}

export function AIAssistantPageClient({
  largeSample,
  smallSample,
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
  const dedupeSessions = useCallback((list: ChatSession[]) => {
    const map = new Map<string, ChatSession>();
    list.forEach((s) => map.set(s.id, s));
    return Array.from(map.values());
  }, []);

  // 채팅 세션 저장 함수 (로컬 상태)
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
      const next = prev.find((s) => s.id === sessionId)
        ? prev
        : [newSession, ...prev];
      return dedupeSessions(next);
    });
  };

  // DB에 채팅 저장 (로그인된 사용자만)
  const saveChatToDB = async (sessionId: string, title: string, msgs: Message[]) => {
    const token = getAuthTokenFromCookie();
    if (!token) return; // 로그인 안된 경우 저장 안함

    try {
      await chatHistoryApi.saveChat({
        session_id: sessionId,
        title,
        mode: currentMode,
        messages: msgs.map((msg, idx) => ({
          role: msg.role,
          content: msg.content,
          message_order: idx,
          backtest_conditions: msg.backtestConditions,
        })),
      });
      console.log("Chat saved to DB:", sessionId);
    } catch (error) {
      console.error("Failed to save chat to DB:", error);
    }
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

    // DB에도 저장 (로그인된 사용자만) - 비동기로 별도 실행
    if (messages.length > 0) {
      const title = messages[0]?.content.substring(0, 20) || "새 채팅";
      saveChatToDB(sessionId, title, messages);
    }
  }, [sessionId, messages, currentMode, chatResponse, questionHistory]);

  // 채팅 세션 클릭 핸들러 - 이전 대화 불러오기
  const handleChatSessionClick = async (chatId: string) => {
    console.log("Chat session clicked:", chatId);

    const session = chatSessions.find(s => s.id === chatId);
    if (!session) return;

    const token = getAuthTokenFromCookie();

    // 로그인된 경우 DB에서 전체 메시지 불러오기
    if (token && session.messages.length === 0) {
      try {
        const fullSession = await chatHistoryApi.getSession(chatId);
        const dbMessages: Message[] = fullSession.messages?.map(msg => ({
          role: msg.role,
          content: msg.content,
          backtestConditions: msg.backtest_conditions,
        })) || [];

        setSessionId(fullSession.session_id);
        setMessages(dbMessages);
        setCurrentMode(fullSession.mode as "initial" | "chat" | "questionnaire");
        setChatResponse(null);
        setQuestionHistory([]);
        console.log("Loaded messages from DB:", dbMessages.length);
      } catch (error) {
        console.error("Failed to load session from DB:", error);
        // 실패 시 로컬 세션 사용
        loadLocalSession(session);
      }
    } else {
      // 로그인 안됐거나 이미 메시지가 있으면 로컬 세션 사용
      loadLocalSession(session);
    }
  };

  const loadLocalSession = (session: ChatSession) => {
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

  const handleSampleClick = async (strategyId: string) => {
    // small sample 카드 클릭 시 해당 전략에 대해 질문 - 채팅 모드로 전환

    const userMessage = smallSample.find((sample) => (sample.id === strategyId))?.question || "";

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

    // 이번 요청 이후의 모드 결정 (initial이면 chat으로 전환)
    const nextMode = currentMode === "initial" ? "chat" : currentMode;
    setCurrentMode(nextMode);

    // 사용자 메시지 추가
    setMessages((prev) => [...prev, { role: "user", content: value }]);

    setIsLoading(true);
    try {
      const response = await sendChatMessage({
        message: value,
        session_id: sessionId || undefined,
      });

      setSessionId(response.session_id);

      // ui_language가 있더라도 사용자가 채팅을 원하면 chat 모드를 유지
      // (추천 카드 등에서 진입 시에는 nextMode를 미리 questionnaire로 설정해 사용)
      if (response.ui_language && nextMode !== "chat") {
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
  }, [sessionId, isLoading, lastRequestTime, currentMode]);

  // DB 또는 localStorage에서 채팅 세션 불러오기
  useEffect(() => {
    const loadChatSessions = async () => {
      const token = getAuthTokenFromCookie();

      // 로그인된 경우 DB에서 불러오기
      if (token) {
        try {
          const dbSessions = await chatHistoryApi.getSessions(50, 0);
          const formattedSessions: ChatSession[] = dbSessions.map(session => ({
            id: session.session_id,
            title: session.title,
            lastMessage: session.last_message_preview || "",
            timestamp: new Date(session.created_at).getTime(),
            messages: [], // 세션 클릭 시 따로 불러옴
            mode: session.mode as "initial" | "chat" | "questionnaire",
          }));
          setChatSessions(dedupeSessions(formattedSessions));
          console.log("Loaded chat sessions from DB:", formattedSessions.length);
        } catch (error) {
          console.error("Failed to load chat sessions from DB:", error);
          // DB 실패 시 localStorage에서 불러오기
          loadFromLocalStorage();
        }
      } else {
        // 로그인 안된 경우 localStorage에서 불러오기
        loadFromLocalStorage();
      }
    };

    const loadFromLocalStorage = () => {
      const savedSessions = localStorage.getItem("ai-chat-sessions");
      if (savedSessions) {
        try {
          setChatSessions(dedupeSessions(JSON.parse(savedSessions)));
          console.log("Loaded chat sessions from localStorage");
        } catch (error) {
          console.error("Failed to load chat sessions from localStorage:", error);
        }
      }
    };

    loadChatSessions();
  }, [dedupeSessions]);

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

  // 메시지 변경 시 현재 세션 업데이트 (과도한 실행 방지용 디바운스)
  useEffect(() => {
    if (messages.length === 0) return;
    const debounce = setTimeout(() => {
      updateCurrentSession();
    }, 300);
    return () => clearTimeout(debounce);
  }, [messages, updateCurrentSession]);

  // 채팅 삭제 핸들러
  const handleChatDelete = async (chatId: string) => {
    const token = getAuthTokenFromCookie();

    // 로그인된 경우 DB에서도 삭제
    if (token) {
      try {
        await chatHistoryApi.deleteSession(chatId);
        console.log("Chat deleted from DB:", chatId);
      } catch (error) {
        console.error("Failed to delete chat from DB:", error);
      }
    }

    // 로컬 상태에서 삭제
    setChatSessions((prev) => prev.filter(s => s.id !== chatId));

    // 삭제한 세션이 현재 세션이면 초기화
    if (sessionId === chatId) {
      setSessionId("");
      setMessages([]);
      setCurrentMode("initial");
      setChatResponse(null);
      setQuestionHistory([]);
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

  // 새 채팅 시작: 상태 초기화
  const handleNewChat = () => {
    setSessionId("");
    setMessages([]);
    setCurrentMode("initial");
    setChatResponse(null);
    setQuestionHistory([]);
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
        onChatDelete={handleChatDelete}
        onNewChat={handleNewChat}
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
                question={largeSample.question}
                description={largeSample.description}
                size="large"
                onClick={handleLargeCardClick}
              />
            </div>

            {/* 작은 카드 그리드 (2x2) */}
            <div className="grid grid-cols-2 gap-x-[40px] gap-y-[32px] mb-[114px]">
              {smallSample.map((strategy) => (
                <StrategyCard
                  key={strategy.id}
                  question={strategy.question}
                  onClick={() => handleSampleClick(strategy.id)}
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
