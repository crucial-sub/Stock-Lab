import { axiosInstance } from "../axios";

// ============================================================
// 타입 정의
// ============================================================

export interface PostSummary {
  postId: string;
  title: string;
  contentPreview: string;
  authorNickname: string | null;
  authorId: string | null;
  isAnonymous: boolean;
  tags: string[] | null;
  postType: string;
  viewCount: number;
  likeCount: number;
  commentCount: number;
  createdAt: string;
  updatedAt: string;
}

export interface StrategySnapshot {
  strategyName: string;
  strategyType: string | null;
  description: string | null;
  buyConditions: Record<string, unknown>[];
  sellConditions: Record<string, unknown>;
  tradeTargets: Record<string, unknown>;
}

export interface SessionSnapshot {
  initialCapital: number;
  startDate: string;
  endDate: string;
  totalReturn: number;
  annualizedReturn: number | null;
  maxDrawdown: number | null;
  sharpeRatio: number | null;
  winRate: number | null;
}

export interface PostDetail {
  postId: string;
  title: string;
  content: string;
  authorNickname: string | null;
  authorId: string | null;
  isAnonymous: boolean;
  tags: string[] | null;
  postType: string;
  strategySnapshot: StrategySnapshot | null;
  sessionSnapshot: SessionSnapshot | null;
  viewCount: number;
  likeCount: number;
  commentCount: number;
  isLiked: boolean;
  createdAt: string;
  updatedAt: string;
}

export interface PostListResponse {
  posts: PostSummary[];
  total: number;
  page: number;
  limit: number;
  hasNext: boolean;
}

export interface PostCreate {
  title: string;
  content: string;
  tags?: string[];
  postType?: string;
  strategyId?: string;
  sessionId?: string;
  isAnonymous?: boolean;
}

export interface PostUpdate {
  title?: string;
  content?: string;
  tags?: string[];
}

export interface CommentItem {
  commentId: string;
  postId: string;
  content: string;
  authorNickname: string | null;
  authorId: string | null;
  isAnonymous: boolean;
  parentCommentId: string | null;
  likeCount: number;
  isLiked: boolean;
  createdAt: string;
  updatedAt: string;
  replies: CommentItem[];
}

export interface CommentListResponse {
  comments: CommentItem[];
  total: number;
}

export interface CommentCreate {
  content: string;
  parentCommentId?: string;
  isAnonymous?: boolean;
}

export interface CommentUpdate {
  content: string;
}

export interface LikeResponse {
  isLiked: boolean;
  likeCount: number;
}

export interface RankingItem {
  rank: number;
  strategyId: string;
  sessionId: string;
  strategyName: string;
  authorNickname: string | null;
  totalReturn: number;
  annualizedReturn: number | null;
  maxDrawdown: number | null;
  sharpeRatio: number | null;
}

export interface TopRankingsResponse {
  rankings: RankingItem[];
  updatedAt: string;
}

export interface RankingListResponse {
  rankings: RankingItem[];
  total: number;
  page: number;
  limit: number;
}

export interface CloneStrategyData {
  strategyName: string;
  isDayOrMonth: string;
  initialInvestment: number;
  startDate: string;
  endDate: string;
  commissionRate: number;
  slippage: number;
  buyConditions: Record<string, unknown>[];
  buyLogic: string;
  priorityFactor: string | null;
  priorityOrder: string;
  perStockRatio: number;
  maxHoldings: number;
  maxBuyValue: number | null;
  maxDailyStock: number | null;
  buyPriceBasis: string;
  buyPriceOffset: number;
  targetAndLoss: Record<string, unknown> | null;
  holdDays: Record<string, unknown> | null;
  conditionSell: Record<string, unknown> | null;
  tradeTargets: Record<string, unknown>;
}

// ============================================================
// 게시글 API
// ============================================================

export const communityApi = {
  /**
   * 게시글 목록 조회
   */
  getPosts: async (params?: {
    postType?: string;
    tags?: string | string[];
    search?: string;
    userId?: string;
    page?: number;
    limit?: number;
  }): Promise<PostListResponse> => {
    const { postType, userId, tags, search, page, limit } = params || {};

    // API가 기대하는 형태로 매핑
    const tagsParam =
      tags === undefined || tags === null || tags === ""
        ? undefined
        : Array.isArray(tags)
          ? tags.join(",")
          : tags;

    const response = await axiosInstance.get<PostListResponse>(
      "/community/posts",
      {
        params: {
          post_type: postType,
          user_id: userId, // camelCase를 snake_case로 변환
          tags: tagsParam,
          search,
          page,
          limit,
        },
      },
    );
    return response.data;
  },

  /**
   * 게시글 상세 조회
   */
  getPost: async (postId: string): Promise<PostDetail> => {
    const response = await axiosInstance.get<PostDetail>(
      `/community/posts/${postId}`
    );
    return response.data;
  },

  /**
   * 게시글 작성
   */
  createPost: async (data: PostCreate): Promise<PostDetail> => {
    const response = await axiosInstance.post<PostDetail>(
      "/community/posts",
      data
    );
    return response.data;
  },

  /**
   * 게시글 수정
   */
  updatePost: async (
    postId: string,
    data: PostUpdate
  ): Promise<PostDetail> => {
    const response = await axiosInstance.put<PostDetail>(
      `/community/posts/${postId}`,
      data
    );
    return response.data;
  },

  /**
   * 게시글 삭제
   */
  deletePost: async (postId: string): Promise<void> => {
    await axiosInstance.delete(`/community/posts/${postId}`);
  },

  // ============================================================
  // 댓글 API
  // ============================================================

  /**
   * 댓글 목록 조회 (트리 구조)
   */
  getComments: async (postId: string): Promise<CommentListResponse> => {
    const response = await axiosInstance.get<CommentListResponse>(
      `/community/posts/${postId}/comments`
    );
    return response.data;
  },

  /**
   * 댓글 작성
   */
  createComment: async (
    postId: string,
    data: CommentCreate
  ): Promise<CommentItem> => {
    const response = await axiosInstance.post<CommentItem>(
      `/community/posts/${postId}/comments`,
      data
    );
    return response.data;
  },

  /**
   * 댓글 수정
   */
  updateComment: async (
    commentId: string,
    data: CommentUpdate
  ): Promise<CommentItem> => {
    const response = await axiosInstance.put<CommentItem>(
      `/community/comments/${commentId}`,
      data
    );
    return response.data;
  },

  /**
   * 댓글 삭제
   */
  deleteComment: async (commentId: string): Promise<void> => {
    await axiosInstance.delete(`/community/comments/${commentId}`);
  },

  // ============================================================
  // 좋아요 API
  // ============================================================

  /**
   * 게시글 좋아요 토글
   */
  togglePostLike: async (postId: string): Promise<LikeResponse> => {
    const response = await axiosInstance.post<LikeResponse>(
      `/community/posts/${postId}/like`
    );
    return response.data;
  },

  /**
   * 댓글 좋아요 토글
   */
  toggleCommentLike: async (commentId: string): Promise<LikeResponse> => {
    const response = await axiosInstance.post<LikeResponse>(
      `/community/comments/${commentId}/like`
    );
    return response.data;
  },

  // ============================================================
  // 랭킹 API
  // ============================================================

  /**
   * 상위 3개 랭킹 조회
   */
  getTopRankings: async (): Promise<TopRankingsResponse> => {
    const response = await axiosInstance.get<TopRankingsResponse>(
      "/community/rankings/top"
    );
    return response.data;
  },

  /**
   * 전체 랭킹 목록 조회
   */
  getRankings: async (params?: {
    page?: number;
    limit?: number;
  }): Promise<RankingListResponse> => {
    const response = await axiosInstance.get<RankingListResponse>(
      "/community/rankings",
      { params }
    );
    return response.data;
  },

  // ============================================================
  // 전략 복제 API
  // ============================================================

  /**
   * 복제용 전략 데이터 조회
   */
  getCloneStrategyData: async (
    sessionId: string
  ): Promise<CloneStrategyData> => {
    const response = await axiosInstance.get<CloneStrategyData>(
      `/community/clone-strategy/${sessionId}`
    );
    return response.data;
  },

  /**
   * 전략 복제 실행
   */
  cloneStrategy: async (sessionId: string): Promise<{ message: string }> => {
    const response = await axiosInstance.post<{ message: string }>(
      `/community/clone-strategy/${sessionId}`
    );
    return response.data;
  },
};
