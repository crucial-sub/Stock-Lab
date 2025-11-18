/**
 * AI 어시스턴트 채팅 상태 관리 스토어 (Zustand)
 *
 * 채팅 세션 및 메시지 상태를 관리하며,
 * 로컬 스토리지 영속성을 제공합니다.
 */

import { create } from "zustand";
import { persist } from "zustand/middleware";
import type { ChatSession } from "@/types/session";
import type { Message } from "@/types/message";

// 스토어 상태 인터페이스
interface ChatStore {
  // 상태
  sessions: ChatSession[];         // 모든 세션 목록
  currentSessionId: string | null; // 현재 활성 세션 ID
  messages: Message[];             // 현재 세션의 메시지 히스토리

  // 액션
  createSession: () => ChatSession;                        // 새 세션 생성
  selectSession: (id: string) => void;                     // 세션 선택 및 메시지 로드
  addMessage: (message: Message) => void;                  // 현재 세션에 메시지 추가
  updateMessage: (id: string, updates: Partial<Message>) => void; // 메시지 수정
  deleteSession: (id: string) => void;                     // 세션 삭제
  updateSessionStatus: (status: ChatSession["status"]) => void; // 세션 상태 업데이트
}

// Zustand 스토어 생성
export const useChatStore = create<ChatStore>()(
  persist(
    (set, get) => ({
      // 초기 상태
      sessions: [],
      currentSessionId: null,
      messages: [],

      // 새 세션 생성
      createSession: () => {
        const newSession: ChatSession = {
          id: `session_${Date.now()}_${Math.random().toString(36).slice(2, 9)}`,
          title: "새로운 대화",
          messages: [],
          createdAt: Date.now(),
          updatedAt: Date.now(),
          status: "idle",
          metadata: {
            questionnaireAnswers: [],
          },
        };

        set((state) => ({
          sessions: [newSession, ...state.sessions],
          currentSessionId: newSession.id,
          messages: [],
        }));

        return newSession;
      },

      // 세션 선택 및 메시지 로드
      selectSession: (id: string) => {
        const { sessions } = get();
        const session = sessions.find((s) => s.id === id);

        if (session) {
          set({
            currentSessionId: id,
            messages: session.messages,
          });
        }
      },

      // 현재 세션에 메시지 추가 (불변성 유지)
      addMessage: (message: Message) => {
        const { currentSessionId, sessions, messages } = get();

        if (!currentSessionId) {
          console.error("현재 세션이 없습니다. 먼저 세션을 생성하세요.");
          return;
        }

        // 메시지 배열에 추가 (불변성 유지)
        const updatedMessages = [...messages, message];

        // 세션 업데이트
        const updatedSessions = sessions.map((session) =>
          session.id === currentSessionId
            ? {
                ...session,
                messages: updatedMessages,
                updatedAt: Date.now(),
                // 첫 번째 메시지인 경우 제목 설정
                title:
                  session.messages.length === 0 && message.role === "user"
                    ? message.type === "text" || message.type === "markdown"
                      ? message.content.slice(0, 30) + (message.content.length > 30 ? "..." : "")
                      : "새로운 대화"
                    : session.title,
              }
            : session
        );

        set({
          messages: updatedMessages,
          sessions: updatedSessions,
        });
      },

      // 메시지 수정 (메타데이터 업데이트용)
      updateMessage: (id: string, updates: Partial<Message>) => {
        const { currentSessionId, sessions, messages } = get();

        if (!currentSessionId) {
          console.error("현재 세션이 없습니다.");
          return;
        }

        // 메시지 업데이트 (불변성 유지)
        const updatedMessages = messages.map((msg) =>
          msg.id === id ? { ...msg, ...updates } : msg
        );

        // 세션 업데이트
        const updatedSessions = sessions.map((session) =>
          session.id === currentSessionId
            ? {
                ...session,
                messages: updatedMessages,
                updatedAt: Date.now(),
              }
            : session
        );

        set({
          messages: updatedMessages,
          sessions: updatedSessions,
        });
      },

      // 세션 삭제
      deleteSession: (id: string) => {
        const { currentSessionId, sessions } = get();

        // 삭제할 세션이 현재 세션인 경우 초기화
        if (currentSessionId === id) {
          set({
            currentSessionId: null,
            messages: [],
          });
        }

        // 세션 목록에서 제거 (불변성 유지)
        const updatedSessions = sessions.filter((session) => session.id !== id);

        set({
          sessions: updatedSessions,
        });
      },

      // 세션 상태 업데이트
      updateSessionStatus: (status: ChatSession["status"]) => {
        const { currentSessionId, sessions } = get();

        if (!currentSessionId) {
          console.error("현재 세션이 없습니다.");
          return;
        }

        const updatedSessions = sessions.map((session) =>
          session.id === currentSessionId
            ? {
                ...session,
                status,
                updatedAt: Date.now(),
              }
            : session
        );

        set({
          sessions: updatedSessions,
        });
      },
    }),
    {
      name: "chat-storage", // localStorage 키 이름
      partialize: (state) => ({
        // sessions 목록만 localStorage에 저장
        // currentSessionId와 messages는 sessionStorage에 저장됨
        sessions: state.sessions,
      }),
    }
  )
);

// 현재 세션 상태를 sessionStorage에 저장/복원하는 헬퍼 함수
export const saveCurrentSession = () => {
  const { currentSessionId, messages } = useChatStore.getState();

  if (currentSessionId) {
    sessionStorage.setItem(
      "current-session",
      JSON.stringify({ currentSessionId, messages })
    );
  }
};

export const restoreCurrentSession = () => {
  const stored = sessionStorage.getItem("current-session");

  if (stored) {
    try {
      const { currentSessionId, messages } = JSON.parse(stored);
      useChatStore.setState({ currentSessionId, messages });
    } catch (error) {
      console.error("세션 복원 실패:", error);
    }
  }
};
