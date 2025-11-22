"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { useSearchParams } from "next/navigation";
import { ChatHistory } from "@/components/ai-assistant/ChatHistory";
import { SecondarySidebar } from "@/components/ai-assistant/SecondarySidebar";
import { StrategyCard } from "@/components/ai-assistant/StrategyCard";
import { StreamingMarkdownRenderer } from "@/components/ai-assistant/StreamingMarkdownRenderer";
import { QuestionnaireFlow } from "@/components/ai-assistant/QuestionnaireFlow";
import { StrategyRecommendationRenderer } from "@/components/ai-assistant/StrategyRecommendationRenderer";
import { AISearchInput } from "@/components/home/ui";
import { useChatStream } from "@/hooks/useChatStream";
import { chatHistoryApi } from "@/lib/api/chat-history";
import { sendChatMessage, type ChatResponse } from "@/lib/api/chatbot";
import { runBacktest, type BacktestRunRequest } from "@/lib/api/backtest";
import { getStrategyDetail } from "@/lib/api/investment-strategy";
import { getAuthTokenFromCookie } from "@/lib/auth/token";
import type { QuestionnaireAnswer, Question } from "@/data/assistantQuestionnaire";
import { createAnswer } from "@/data/assistantQuestionnaire";
import type { StrategyDetail } from "@/types/investment-strategy";
import type {
  BacktestConfigMessage,
  BacktestExecutionMessage,
  MarkdownMessage,
  Message,
  TextMessage,
} from "@/types/message";
import { getTopRecommendations, type StrategyMatch } from "@/utils/strategyMatcher";

// crypto.randomUUID polyfill (HTTP 환경 지원)
function generateUUID(): string {
  if (typeof crypto !== 'undefined' && typeof crypto.randomUUID === 'function') {
    return crypto.randomUUID();
  }
  // Fallback: 간단한 UUID v4 생성
  return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, (c) => {
    const r = Math.random() * 16 | 0;
    const v = c === 'x' ? r : (r & 0x3 | 0x8);
    return v.toString(16);
  });
}

// 메시지 생성 헬퍼 함수
function createTextMessage(role: "user" | "assistant", content: string): TextMessage {
  return {
    id: `msg_${Date.now()}_${Math.random().toString(36).slice(2, 9)}`,
    type: "text",
    role,
    content,
    createdAt: Date.now(),
  };
}

function createMarkdownMessage(role: "assistant", content: string): MarkdownMessage {
  return {
    id: `msg_${Date.now()}_${Math.random().toString(36).slice(2, 9)}`,
    type: "markdown",
    role,
    content,
    createdAt: Date.now(),
  };
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
    question: string;
  }>;
  // 새로운 설문 시스템용
  questionnaireAnswers?: QuestionnaireAnswer[];
  strategyRecommendations?: StrategyMatch[];
  selectedStrategy?: { id: string; name: string };
  currentQuestionStep?: number;
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
  autoStartQuestionnaire?: boolean;
}

export function AIAssistantPageClient({
  largeSample,
  smallSample,
  autoStartQuestionnaire = false,
}: AIAssistantPageClientProps) {
  const searchParams = useSearchParams();
  const [sessionId, setSessionId] = useState<string>("");
  const [chatResponse, setChatResponse] = useState<ChatResponse | null>(null);
  const [_isLoading, setIsLoading] = useState(false);
  const [messages, setMessages] = useState<Message[]>([]);
  const [questionHistory, setQuestionHistory] = useState<Array<{
    questionId: string;
    selectedOptionId: string;
    question: string;
  }>>([]);
  const [chatSessions, setChatSessions] = useState<ChatSession[]>([]);
  const hasAutoStartedRef = useRef(false);
  const shouldAutoStart =
    autoStartQuestionnaire || searchParams.get("autoStart") === "questionnaire";
  const [currentMode, setCurrentMode] = useState<"initial" | "chat" | "questionnaire">("initial");
  const [lastRequestTime, setLastRequestTime] = useState<number>(0);
  const MIN_REQUEST_INTERVAL = 2000; // 최소 2초 간격

  // 새로운 설문 시스템 상태
  const [questionnaireAnswers, setQuestionnaireAnswers] = useState<QuestionnaireAnswer[]>([]);
  const [strategyRecommendations, setStrategyRecommendations] = useState<StrategyMatch[]>([]);
  const [selectedStrategy, setSelectedStrategy] = useState<StrategyDetail | null>(null);

  // SSE 스트리밍 상태
  const [, setStreamingMessage] = useState<string>("");

  // 스크롤 컨테이너 ref (직접 제어용)
  const scrollContainerRef = useRef<HTMLDivElement>(null);

  // useChatStream 훅 (세션 ID가 있을 때만 활성화)
  const {
    content: streamContent,
    isStreaming,
    connectionState,
    error: streamError,
    sendMessage: sendStreamMessage,
  } = useChatStream(sessionId || "temp_session");

  // 세션 중복 제거 유틸리티 함수
  const dedupeSessions = useCallback((sessions: ChatSession[]) => {
    const seen = new Set<string>();
    return sessions.filter((session) => {
      if (seen.has(session.id)) return false;
      seen.add(session.id);
      return true;
    });
  }, []);

  // 채팅 세션 저장 함수 (로컬 상태)
  // 중복 체크 로직 인라인으로 최적화
  const saveChatSession = (sessionId: string, firstMessage: string) => {
    const newSession: ChatSession = {
      id: sessionId,
      title:
        firstMessage.length > 20
          ? `${firstMessage.substring(0, 20)}...`
          : firstMessage,
      lastMessage: firstMessage,
      timestamp: Date.now(),
      messages: messages,
      mode: currentMode,
      chatResponse: chatResponse,
      questionHistory: questionHistory,
    };

    setChatSessions((prev) => {
      // 중복 체크: 이미 존재하는 세션이면 추가하지 않음
      const exists = prev.some((s) => s.id === sessionId);
      return exists ? prev : [newSession, ...prev];
    });
  };

  // DB에 채팅 저장 (로그인된 사용자만)
  const saveChatToDB = async (sessionId: string, title: string, msgs: Message[]) => {
    const token = getAuthTokenFromCookie();
    if (!token) {
      return; // 로그인 안된 경우 저장 안함
    }

    try {
      // user와 assistant 메시지만 필터링 (system 제외)
      // message_order 추가 (배열 인덱스 기반)
      const validMessages = msgs
        .filter(msg => msg.role === "user" || msg.role === "assistant")
        .map((msg, index) => ({
          role: msg.role as "user" | "assistant",
          content: "content" in msg ? msg.content : "",
          message_order: index,
        }));

      if (validMessages.length === 0) {
        return; // 저장할 메시지 없으면 스킵
      }

      // sessionId를 그대로 전송 (백엔드 upsert 로직으로 업데이트 또는 생성)
      const requestData = {
        session_id: sessionId,
        title,
        mode: currentMode,
        messages: validMessages,
      };

      await chatHistoryApi.saveChat(requestData);
    } catch (error) {
      console.error("Failed to save chat to DB:", error);
    }
  };

  // 현재 세션 상태 업데이트 (메시지가 추가될 때마다)
  const updateCurrentSession = useCallback(() => {
    if (!sessionId || messages.length === 0) return;

    // 마지막 메시지의 content 추출 (타입 안전하게)
    const lastMessage = messages[messages.length - 1];
    const lastMessageText = lastMessage && "content" in lastMessage
      ? lastMessage.content.substring(0, 50)
      : "";

    // 첫 메시지로 제목 생성
    const firstMessage = messages[0];
    const title = firstMessage && "content" in firstMessage
      ? firstMessage.content.substring(0, 20)
      : "새 채팅";

    setChatSessions((prev) => {
      const existingIndex = prev.findIndex(s => s.id === sessionId);

      // 새 세션 생성 또는 기존 세션 업데이트
      const sessionData: ChatSession = {
        id: sessionId,
        title,
        lastMessage: lastMessageText,
        timestamp: Date.now(),
        messages: messages,
        mode: currentMode,
        chatResponse: chatResponse,
        questionHistory: questionHistory,
        questionnaireAnswers: questionnaireAnswers,
        strategyRecommendations: strategyRecommendations,
      };

      if (existingIndex === -1) {
        // 새 세션 추가
        return dedupeSessions([sessionData, ...prev]);
      } else {
        // 기존 세션 업데이트
        const updated = [...prev];
        updated[existingIndex] = sessionData;
        return updated;
      }
    });

    // DB에도 저장 (로그인된 사용자만) - 비동기로 별도 실행
    saveChatToDB(sessionId, title, messages);
  }, [sessionId, messages, currentMode, chatResponse, questionHistory, questionnaireAnswers, strategyRecommendations, dedupeSessions]);

  // 채팅 세션 클릭 핸들러 - 이전 대화 불러오기
  const handleChatSessionClick = async (chatId: string) => {
    const session = chatSessions.find(s => s.id === chatId);
    if (!session) return;

    const token = getAuthTokenFromCookie();

    // 로그인된 경우 DB에서 전체 메시지 불러오기
    if (token && session.messages.length === 0) {
      try {
        const fullSession = await chatHistoryApi.getSession(chatId);
        const dbMessages: Message[] = fullSession.messages?.map(msg => {
          // DB 메시지를 적절한 Message 타입으로 변환
          if (msg.role === "user") {
            return createTextMessage("user", msg.content);
          } else {
            // assistant 메시지는 마크다운으로 처리
            return createMarkdownMessage("assistant", msg.content);
          }
        }) || [];

        setSessionId(fullSession.session_id);
        setMessages(dbMessages);
        setCurrentMode(fullSession.mode as "initial" | "chat" | "questionnaire");
        setChatResponse(null);
        setQuestionHistory([]);
        // 로컬 세션에서 설문 데이터 복원 (DB에는 저장 안 됨)
        setQuestionnaireAnswers(session.questionnaireAnswers || []);
        setStrategyRecommendations(session.strategyRecommendations || []);
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
    setQuestionnaireAnswers(session.questionnaireAnswers || []);
    setStrategyRecommendations(session.strategyRecommendations || []);
  };

  const handleLargeCardClick = useCallback(() => {
    // 전략 추천 플로우 시작 (새로운 설문 시스템)
    // 세션 ID 생성
    const newSessionId = generateUUID();
    setSessionId(newSessionId);

    // 사용자 메시지 추가
    const userMessage = "투자 성향 설문을 시작하고 싶어요";
    setMessages((prev) => [...prev, createTextMessage("user", userMessage)]);

    // 설문 모드로 전환
    setCurrentMode("questionnaire");
    setQuestionnaireAnswers([]);

    // AI 환영 메시지 추가
    const welcomeMessage = "투자 성향을 파악하여 맞춤 전략을 추천해드리겠습니다. 5개의 질문에 답변해주세요.";
    setMessages((prev) => [
      ...prev,
      createMarkdownMessage("assistant", welcomeMessage),
    ]);

    // 채팅 세션 저장
    saveChatSession(newSessionId, userMessage);
  }, [saveChatSession]);

  useEffect(() => {
    if (shouldAutoStart && !hasAutoStartedRef.current) {
      hasAutoStartedRef.current = true;
      handleLargeCardClick();
    }
  }, [shouldAutoStart, handleLargeCardClick]);

  const handleSampleClick = async (strategyId: string) => {
    // small sample 카드 클릭 시 해당 전략에 대해 질문 - 채팅 모드로 전환

    const userMessage = smallSample.find((sample) => (sample.id === strategyId))?.question || "";

    // 세션 ID 생성 (없는 경우) - UUID 형식으로 생성
    if (!sessionId) {
      const newSessionId = generateUUID();
      setSessionId(newSessionId);
      saveChatSession(newSessionId, userMessage);
    }

    // 사용자 메시지 추가 및 채팅 모드로 전환
    setMessages((prev) => [...prev, createTextMessage("user", userMessage)]);
    setCurrentMode("chat");

    // SSE 스트리밍 시작
    setStreamingMessage(userMessage);
    sendStreamMessage(userMessage);
  };

  const handleAISubmit = useCallback(async (value: string) => {
    // 이미 스트리밍 중이면 요청 무시
    if (isStreaming) {
      return;
    }

    // 요청 간격 제한 (Rate Limiting)
    const now = Date.now();
    const timeSinceLastRequest = now - lastRequestTime;
    if (timeSinceLastRequest < MIN_REQUEST_INTERVAL) {
      const waitTime = Math.ceil((MIN_REQUEST_INTERVAL - timeSinceLastRequest) / 1000);
      setMessages((prev) => [
        ...prev,
        createTextMessage("assistant", `요청이 너무 빠릅니다. ${waitTime}초 후에 다시 시도해주세요.`),
      ]);
      return;
    }

    setLastRequestTime(now);

    // 이번 요청 이후의 모드 결정 (initial이면 chat으로 전환)
    const nextMode = currentMode === "initial" ? "chat" : currentMode;
    setCurrentMode(nextMode);

    // 세션 ID 생성 (없는 경우) - UUID 형식으로 생성
    if (!sessionId) {
      const newSessionId = generateUUID();
      setSessionId(newSessionId);
      saveChatSession(newSessionId, value);
    }

    // 사용자 메시지 추가
    setMessages((prev) => [...prev, createTextMessage("user", value)]);

    // SSE 스트리밍 시작
    setStreamingMessage(value);
    sendStreamMessage(value);
  }, [sessionId, isStreaming, lastRequestTime, currentMode, sendStreamMessage]);

  /**
   * 백테스트 시작 콜백
   * BacktestConfigRenderer에서 백테스트가 시작될 때 호출되어 BacktestExecutionMessage를 메시지 히스토리에 추가
   */
  const handleBacktestStart = useCallback(async (
    strategyName: string,
    config: {
      investmentAmount: number;
      startDate: string;
      endDate: string;
    }
  ) => {
    if (!selectedStrategy) {
      return;
    }

    try {
      // 날짜 형식 변환: YYYY-MM-DD → YYYYMMDD
      const formatDate = (dateStr: string) => dateStr.replace(/-/g, "");

      // BacktestRunRequest 생성
      const backtestRequest: BacktestRunRequest = {
        // 전략 설정에서 가져오기
        ...(selectedStrategy.backtest_config as BacktestRunRequest),
        // 사용자 입력값으로 덮어쓰기
        strategy_name: strategyName,
        start_date: formatDate(config.startDate),
        end_date: formatDate(config.endDate),
        initial_investment: config.investmentAmount,
      };

      // POST /backtest/run 호출
      const response = await runBacktest(backtestRequest);

      // BacktestExecutionMessage 생성
      const executionMessage: BacktestExecutionMessage = {
        id: `msg_${Date.now()}_${Math.random().toString(36).slice(2, 9)}`,
        type: "backtest_execution",
        role: "assistant",
        backtestId: response.backtestId,  // 실제 백테스트 ID
        strategyId: selectedStrategy.id,
        strategyName,
        config: {
          investmentAmount: config.investmentAmount,
          startDate: config.startDate,
          endDate: config.endDate,
        },
        createdAt: Date.now(),
      };

      // 메시지 히스토리에 추가
      setMessages((prev) => {
        const updatedMessages = [...prev, executionMessage];

        // DB에 채팅 히스토리 저장 (비동기)
        if (sessionId) {
          saveChatToDB(
            sessionId,
            `${strategyName} 백테스트 실행`,
            updatedMessages
          );
        }

        return updatedMessages;
      });

      // 스크롤을 부드럽게 아래로 이동
      setTimeout(() => {
        if (scrollContainerRef.current) {
          scrollContainerRef.current.scrollTo({
            top: scrollContainerRef.current.scrollHeight,
            behavior: "smooth",
          });
        }
      }, 100);
    } catch (error) {
      console.error("Failed to start backtest:", error);
    }
  }, [selectedStrategy, sessionId]);

  // DB 또는 localStorage에서 채팅 세션 불러오기
  useEffect(() => {
    const loadChatSessions = async () => {
      const token = getAuthTokenFromCookie();

      // 로그인된 경우 DB에서 불러오기
      if (token) {
        try {
          const dbSessions = await chatHistoryApi.getSessions(50, 0);

          // localStorage에서 questionnaire 데이터 가져오기 (DB에는 저장 안 됨)
          const localSessions = getLocalSessions();
          const localSessionsMap = new Map(localSessions.map(s => [s.id, s]));

          const formattedSessions: ChatSession[] = dbSessions.map(session => {
            const localSession = localSessionsMap.get(session.session_id);

            return {
              id: session.session_id,
              title: session.title,
              lastMessage: session.last_message_preview || "",
              timestamp: new Date(session.created_at).getTime(),
              messages: [], // 세션 클릭 시 따로 불러옴
              mode: session.mode as "initial" | "chat" | "questionnaire",
              // localStorage의 questionnaire 데이터 병합
              questionnaireAnswers: localSession?.questionnaireAnswers || [],
              strategyRecommendations: localSession?.strategyRecommendations || [],
            };
          });

          setChatSessions(dedupeSessions(formattedSessions));
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

    const getLocalSessions = (): ChatSession[] => {
      const savedSessions = localStorage.getItem("ai-chat-sessions");
      if (savedSessions) {
        try {
          return JSON.parse(savedSessions);
        } catch (error) {
          console.error("Failed to parse localStorage sessions:", error);
          return [];
        }
      }
      return [];
    };

    const loadFromLocalStorage = () => {
      const sessions = getLocalSessions();
      if (sessions.length > 0) {
        setChatSessions(dedupeSessions(sessions));
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

  // SSE 스트리밍 완료 시 메시지 추가
  useEffect(() => {
    if (connectionState === "complete" && streamContent) {
      setMessages((prev) => [
        ...prev,
        createMarkdownMessage("assistant", streamContent),
      ]);
      setStreamingMessage(""); // 스트리밍 메시지 초기화
    }
  }, [connectionState, streamContent]);

  // SSE 스트리밍 에러 처리
  useEffect(() => {
    if (streamError) {
      console.error("Streaming error:", streamError);
      setMessages((prev) => [
        ...prev,
        createTextMessage("assistant", streamError.message || "메시지 전송에 실패했습니다. 잠시 후 다시 시도해주세요."),
      ]);
      setStreamingMessage(""); // 스트리밍 메시지 초기화
    }
  }, [streamError]);

  // 자동 스크롤 (메시지 변경 또는 스트리밍 콘텐츠 변경 시)
  useEffect(() => {
    if (scrollContainerRef.current) {
      const container = scrollContainerRef.current;
      // scrollTop을 최대값으로 설정하여 항상 최하단으로 스크롤
      container.scrollTop = container.scrollHeight;
    }
  }, [messages, streamContent]);

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

  // 전체 채팅 삭제 핸들러
  const handleDeleteAllChats = async () => {
    const token = getAuthTokenFromCookie();

    // 로그인된 경우 DB에서도 전체 삭제
    if (token) {
      try {
        // 모든 세션을 순차적으로 삭제
        await Promise.all(
          chatSessions.map(session => chatHistoryApi.deleteSession(session.id))
        );
      } catch (error) {
        console.error("Failed to delete all chats from DB:", error);
      }
    }

    // 로컬 상태 전체 삭제
    setChatSessions([]);

    // 현재 세션도 초기화
    setSessionId("");
    setMessages([]);
    setCurrentMode("initial");
    setChatResponse(null);
    setQuestionHistory([]);
  };

  const _handleAnswerSelect = async (questionId: string, optionId: string, answerText: string) => {
    // 현재 질문을 히스토리에 저장 (다음 질문으로 넘어가기 전에)
    if (chatResponse?.ui_language?.type?.startsWith("questionnaire") && "question" in chatResponse.ui_language) {
      const question = chatResponse.ui_language.question;
      if (question && question.question_id === questionId) {
        setQuestionHistory((prev) => [...prev, {
          questionId: questionId,
          selectedOptionId: optionId,
          question: question.text
        }]);
      }
    }

    // 사용자 답변을 메시지에 추가
    setMessages((prev) => [...prev, createTextMessage("user", answerText)]);

    setIsLoading(true);
    try {
      const response = await sendChatMessage({
        message: "",
        session_id: sessionId,
        answer: {
          question_id: questionId,
          option_id: optionId,
        },
        client_type: "assistant",
      });

      setSessionId(response.session_id);
      setChatResponse(response);
    } catch (error) {
      console.error("Failed to send answer:", error);
    } finally {
      setIsLoading(false);
    }
  };

  // 새로운 설문 시스템용 핸들러
  const handleQuestionnaireAnswerSelect = (
    questionId: string,
    optionId: string,
    _answerText: string,
  ) => {
    // 답변을 상태에 저장
    const answer = createAnswer(questionId, optionId);
    if (answer) {
      setQuestionnaireAnswers((prev) => {
        // 기존 답변 제거 (수정 케이스)
        const filtered = prev.filter(a => a.questionId !== questionId);
        return [...filtered, answer];
      });
    }

    // 메시지는 추가하지 않음 (선택지에 UI로만 표시)
  };

  const handleQuestionnaireComplete = async (tags: string[]) => {
    // 전략 매칭 알고리즘 실행
    const recommendations = getTopRecommendations(tags, 3);

    // 전략 추천 결과 저장 (메시지 추가 없음)
    setStrategyRecommendations(recommendations);
  };

  // 설문조사 다시 시작 핸들러
  const handleQuestionnaireRestart = () => {
    // 설문 관련 상태만 초기화 (메시지는 유지)
    setQuestionnaireAnswers([]);
    setStrategyRecommendations([]);

    // 사용자에게 재시작 안내 메시지 추가
    const restartMessage = "설문조사를 처음부터 다시 시작합니다.";
    setMessages((prev) => [
      ...prev,
      createMarkdownMessage("assistant", restartMessage),
    ]);
  };

  // 전략 선택 핸들러
  const handleStrategySelect = async (strategyId: string, strategyName: string) => {
    try {
      // 전략 상세 정보 조회 (backtest_config 포함)
      const strategyDetail = await getStrategyDetail(strategyId);

      // 선택된 전략 저장
      setSelectedStrategy(strategyDetail);

      // BacktestConfigMessage를 messages 배열에 추가
      const configMessage: BacktestConfigMessage = {
        id: `msg_${Date.now()}_${Math.random().toString(36).slice(2, 9)}`,
        type: "backtest_config",
        role: "assistant",
        strategyId,
        strategyName,
        createdAt: Date.now(),
      };

    setMessages((prev) => {
      const updatedMessages = [...prev, configMessage];

      // DB에 채팅 히스토리 저장 (비동기)
      if (sessionId) {
        saveChatToDB(
          sessionId,
          `${strategyName} 백테스트 설정`,
          updatedMessages
        );
      }

      return updatedMessages;
    });

    // 스크롤을 부드럽게 아래로 이동
    setTimeout(() => {
      if (scrollContainerRef.current) {
        scrollContainerRef.current.scrollTo({
          top: scrollContainerRef.current.scrollHeight,
          behavior: "smooth",
        });
      }
    }, 100);
    } catch (error) {
      console.error("Failed to select strategy:", error);
    }
  };

  // 새 채팅 시작: 상태 초기화
  const handleNewChat = () => {
    setSessionId("");
    setMessages([]);
    setCurrentMode("initial");
    setChatResponse(null);
    setQuestionHistory([]);
    setQuestionnaireAnswers([]);
    setStrategyRecommendations([]);
  };

  return (
    <div className="flex h-screen">
      {/* 2차 사이드바 */}
      <SecondarySidebar
        chatHistory={chatSessions.map(session => ({
          id: session.id,
          title: session.title,
        }))}
        onChatClick={handleChatSessionClick}
        onChatDelete={handleChatDelete}
        onDeleteAll={handleDeleteAllChats}
        onNewChat={handleNewChat}
      />

      {/* 메인 콘텐츠 - 넘침 방지, 높이 고정 */}
      <main className="flex-1 flex flex-col px-10 pt-[120px] pb-20 overflow-hidden">
        {/* 설문조사 모드 (새로운 설문 시스템) */}
        {currentMode === "questionnaire" ? (
          <div className="flex-1 flex flex-col w-full max-w-[1000px] mx-auto min-h-0">
            {/* 채팅 히스토리 표시 (스크롤 가능) */}
            <div
              ref={scrollContainerRef}
              className="flex-1 overflow-y-auto mb-4 px-4 [&::-webkit-scrollbar]:hidden [-ms-overflow-style:none] [scrollbar-width:none]"
            >
              {/* 초기 메시지만 표시 (text, markdown) */}
              <div className="w-full max-w-[1000px] mx-auto mb-6">
                <ChatHistory
                  messages={messages.filter(m => m.type === 'text' || m.type === 'markdown')}
                  isWaitingForAI={false}
                  onBacktestStart={handleBacktestStart}
                />
              </div>

              {/* QuestionnaireFlow 컴포넌트 (항상 표시) */}
              <QuestionnaireFlow
                answers={questionnaireAnswers}
                onAnswerSelect={handleQuestionnaireAnswerSelect}
                onComplete={handleQuestionnaireComplete}
                isRecommendationShown={strategyRecommendations.length > 0}
                onRestart={handleQuestionnaireRestart}
              />

              {/* 전략 추천 결과 (QuestionnaireFlow 아래에 추가) */}
              {strategyRecommendations.length > 0 && (
                <StrategyRecommendationRenderer
                  recommendations={strategyRecommendations}
                  onSelectStrategy={handleStrategySelect}
                />
              )}

              {/* 백테스트 메시지만 표시 (backtest_config, backtest_execution) */}
              {/* 전략 추천 아래에 배치되어 올바른 순서 보장 */}
              <div className="w-full max-w-[1000px] mx-auto">
                <ChatHistory
                  messages={messages.filter(m => m.type === 'backtest_config' || m.type === 'backtest_execution')}
                  isWaitingForAI={false}
                  onBacktestStart={handleBacktestStart}
                />
              </div>
            </div>
          </div>
        ) : currentMode === "chat" ? (
          /* 채팅 모드 */
          <div className="flex-1 flex flex-col w-full max-w-[1000px] mx-auto min-h-0">
            {/* 스크롤 가능한 메시지 영역 - 스크롤바 숨김 */}
            <div
              ref={scrollContainerRef}
              className="flex-1 overflow-y-auto mb-4 px-4 [&::-webkit-scrollbar]:hidden [-ms-overflow-style:none] [scrollbar-width:none]"
            >
              <div className="w-full max-w-[1000px] mx-auto">
                <ChatHistory
                  messages={messages}
                  isWaitingForAI={
                    connectionState === "connecting" ||
                    connectionState === "connected" ||
                    (isStreaming && !streamContent)
                  }
                  onBacktestStart={handleBacktestStart}
                />

                {/* SSE 스트리밍 중인 메시지 */}
                {isStreaming && streamContent && (
                  <StreamingMarkdownRenderer
                    content={streamContent}
                    isStreaming={isStreaming}
                    compactMaxBullets={3}
                  />
                )}
              </div>
            </div>

            {/* 하단 고정 입력창 */}
            <div className="sticky bottom-0 w-full pt-4">
              <AISearchInput
                placeholder="만들고 싶은 전략을 AI에게 요청하세요!"
                onSubmit={handleAISubmit}
                disabled={isStreaming}
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
