import { axiosInstance, axiosServerInstance } from "../axios";

export interface StrategyStatisticsSummary {
  totalReturn?: number | null;
  annualizedReturn?: number | null;
  maxDrawdown?: number | null;
  sharpeRatio?: number | null;
  winRate?: number | null;
}

export interface StrategyListItem {
  sessionId: string;
  strategyId: string;
  strategyName: string;
  isActive: boolean;
  status: string; // PENDING/RUNNING/COMPLETED/FAILED
  totalReturn?: number | null;
  createdAt: string;
  updatedAt: string;
}

// 기존 호환성 유지를 위한 타입 (useStrategyList에서 사용)
export interface StrategyDetailItem extends StrategyListItem {
  progress?: number;
  statistics?: StrategyStatisticsSummary | null;
}

export interface MyStrategiesResponse {
  strategies: StrategyDetailItem[];
  total: number;
}

export const strategyApi = {
  /**
   * 내 백테스트 결과 목록 조회 (클라이언트 사이드)
   */
  getMyStrategies: async (): Promise<MyStrategiesResponse> => {
    const response =
      await axiosInstance.get<MyStrategiesResponse>("/strategies/my");
    return response.data;
  },

  /**
   * 내 백테스트 결과 목록 조회 (서버 사이드)
   * @param token - 인증 토큰
   */
  getMyStrategiesServer: async (
    token: string,
  ): Promise<MyStrategiesResponse> => {
    const response = await axiosServerInstance.get<MyStrategiesResponse>(
      "/strategies/my",
      {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      },
    );
    return response.data;
  },

  /**
   * 백테스트 세션 삭제
   */
  deleteBacktestSessions: async (sessionIds: string[]): Promise<void> => {
    await axiosInstance.delete("/strategies/sessions", {
      data: { session_ids: sessionIds },
    });
  },
};
