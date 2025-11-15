import { axiosInstance } from "../axios";

export interface StrategyStatisticsSummary {
  totalReturn?: number | null;
  annualizedReturn?: number | null;
  maxDrawdown?: number | null;
  sharpeRatio?: number | null;
  winRate?: number | null;
}

export interface StrategyDetailItem {
  sessionId: string;
  strategyId: string;
  strategyName: string;
  strategyType?: string | null;
  description?: string | null;
  isPublic: boolean;
  isAnonymous: boolean;
  hideStrategyDetails: boolean;
  initialCapital?: number | null;
  backtestStartDate?: string | null;
  backtestEndDate?: string | null;
  status: string; // PENDING/RUNNING/COMPLETED/FAILED
  progress: number;
  errorMessage?: string | null;
  statistics?: StrategyStatisticsSummary | null;
  createdAt: string;
  updatedAt: string;
}

export interface MyStrategiesResponse {
  strategies: StrategyDetailItem[];
  total: number;
}

export const strategyApi = {
  /**
   * 내 백테스트 결과 목록 조회
   */
  getMyStrategies: async (): Promise<MyStrategiesResponse> => {
    const response = await axiosInstance.get<MyStrategiesResponse>("/strategies/my");
    return response.data;
  },

  /**
   * 백테스트 세션 삭제
   */
  deleteBacktestSessions: async (sessionIds: string[]): Promise<void> => {
    await axiosInstance.delete("/strategies/sessions", {
      data: { session_ids: sessionIds }
    });
  },
};
