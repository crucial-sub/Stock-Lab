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
  isPublic?: boolean;
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

export interface PublicStrategyListItem {
  strategyId: string;
  strategyName: string;
  description: string | null;
  isAnonymous: boolean;
  hideStrategyDetails: boolean;
  ownerName: string | null;
  totalReturn: number | null;
  annualizedReturn: number | null;
  createdAt: string;
  updatedAt: string;
}

export interface PublicStrategiesResponse {
  strategies: PublicStrategyListItem[];
  total: number;
  page: number;
  limit: number;
  hasNext: boolean;
}

export interface StrategyUpdatePayload {
  strategyName?: string;
  description?: string;
}

export interface StrategyUpdateResponse {
  message: string;
  strategyName?: string;
}

export interface StrategySharingSettingsPayload {
  isPublic?: boolean;
  isAnonymous?: boolean;
  hideStrategyDetails?: boolean;
}

export interface StrategySharingSettingsResponse {
  message: string;
  strategy_id: string;
  settings: {
    is_public: boolean;
    is_anonymous: boolean;
    hide_strategy_details: boolean;
  };
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

  /**
   * 공개 전략 목록 조회 (최신순)
   */
  getPublicStrategies: async (params?: {
    page?: number;
    limit?: number;
  }): Promise<PublicStrategiesResponse> => {
    const response = await axiosInstance.get<PublicStrategiesResponse>(
      "/strategies/public",
      { params },
    );
    return response.data;
  },

  /**
   * 투자전략 정보 수정 (이름/설명)
   */
  updateStrategy: async (
    strategyId: string,
    payload: StrategyUpdatePayload,
  ): Promise<StrategyUpdateResponse> => {
    const requestBody: Record<string, string | undefined> = {};

    if (payload.strategyName !== undefined) {
      requestBody.strategy_name = payload.strategyName;
    }
    if (payload.description !== undefined) {
      requestBody.description = payload.description;
    }

    const response = await axiosInstance.patch<StrategyUpdateResponse>(
      `/strategies/${strategyId}`,
      requestBody,
    );
    return response.data;
  },

  /**
   * 투자전략 공개/익명 설정 수정
   */
  updateSharingSettings: async (
    strategyId: string,
    payload: StrategySharingSettingsPayload,
  ): Promise<StrategySharingSettingsResponse> => {
    const requestBody: Record<string, boolean | undefined> = {};

    if (payload.isPublic !== undefined) {
      requestBody.is_public = payload.isPublic;
    }
    if (payload.isAnonymous !== undefined) {
      requestBody.is_anonymous = payload.isAnonymous;
    }
    if (payload.hideStrategyDetails !== undefined) {
      requestBody.hide_strategy_details = payload.hideStrategyDetails;
    }

    const response = await axiosInstance.patch<StrategySharingSettingsResponse>(
      `/strategies/${strategyId}/settings`,
      requestBody,
    );
    return response.data;
  },
};
