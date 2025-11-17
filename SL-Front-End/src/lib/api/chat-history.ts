import { axiosInstance } from "../axios";

// 타입 정의
export interface ChatMessage {
  message_id?: string;
  role: "user" | "assistant";
  content: string;
  intent?: string;
  backtest_conditions?: any;
  ui_language?: any;
  message_order: number;
  created_at?: string;
}

export interface ChatSession {
  session_id: string;
  user_id: string;
  title: string;
  mode: string;
  created_at: string;
  updated_at: string;
  messages?: ChatMessage[];
}

export interface ChatSessionListItem {
  session_id: string;
  title: string;
  mode: string;
  created_at: string;
  updated_at: string;
  message_count: number;
  last_message_preview?: string;
}

export interface SaveChatRequest {
  session_id?: string;
  title: string;
  mode: string;
  messages: Omit<ChatMessage, "message_id" | "created_at">[];
}

export const chatHistoryApi = {
  /**
   * 채팅 세션 목록 조회
   */
  getSessions: async (
    limit: number = 50,
    offset: number = 0
  ): Promise<ChatSessionListItem[]> => {
    const response = await axiosInstance.get<ChatSessionListItem[]>(
      "/chat/sessions",
      {
        params: { limit, offset },
      }
    );
    return response.data;
  },

  /**
   * 특정 채팅 세션 조회 (메시지 포함)
   */
  getSession: async (sessionId: string): Promise<ChatSession> => {
    const response = await axiosInstance.get<ChatSession>(
      `/chat/sessions/${sessionId}`
    );
    return response.data;
  },

  /**
   * 채팅 세션 삭제
   */
  deleteSession: async (sessionId: string): Promise<void> => {
    await axiosInstance.delete(`/chat/sessions/${sessionId}`);
  },

  /**
   * 채팅 저장 (새 세션 또는 기존 세션 업데이트)
   */
  saveChat: async (request: SaveChatRequest): Promise<ChatSession> => {
    const response = await axiosInstance.post<ChatSession>(
      "/chat/save",
      request
    );
    return response.data;
  },
};
