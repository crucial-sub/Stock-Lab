/**
 * 커뮤니티 관련 React Query 훅
 * - 게시글, 댓글, 좋아요, 랭킹 관련 쿼리 및 뮤테이션 제공
 */

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { communityApi } from "@/lib/api/community";
import type {
  PostListResponse,
  PostDetail,
  CommentListResponse,
  CommentItem,
  LikeResponse,
  TopRankingsResponse,
  RankingListResponse,
  PostCreate,
  PostUpdate,
  CommentCreate,
  CommentUpdate,
  CloneStrategyData,
} from "@/lib/api/community";

/**
 * 커뮤니티 쿼리 키
 */
export const communityQueryKey = {
  all: ["community"] as const,

  // 게시글
  posts: () => [...communityQueryKey.all, "posts"] as const,
  postList: (params?: {
    postType?: string;
    tags?: string;
    search?: string;
    page?: number;
    limit?: number;
  }) => [...communityQueryKey.posts(), params] as const,
  postDetail: (postId: string) =>
    [...communityQueryKey.posts(), "detail", postId] as const,

  // 댓글
  comments: (postId: string) =>
    [...communityQueryKey.postDetail(postId), "comments"] as const,

  // 랭킹
  rankings: () => [...communityQueryKey.all, "rankings"] as const,
  topRankings: () => [...communityQueryKey.rankings(), "top"] as const,
  rankingList: (params?: { page?: number; limit?: number }) =>
    [...communityQueryKey.rankings(), "list", params] as const,

  // 전략 복제
  cloneStrategy: (sessionId: string) =>
    [...communityQueryKey.all, "clone-strategy", sessionId] as const,
};

// ============================================================
// 게시글 관련 훅
// ============================================================

/**
 * 게시글 목록 조회 훅
 */
export function usePostsQuery(params?: {
  postType?: string;
  tags?: string;
  search?: string;
  page?: number;
  limit?: number;
}) {
  return useQuery<PostListResponse, Error>({
    queryKey: communityQueryKey.postList(params),
    queryFn: () => communityApi.getPosts(params),
  });
}

/**
 * 게시글 상세 조회 훅
 */
export function usePostDetailQuery(postId: string, enabled = true) {
  return useQuery<PostDetail, Error>({
    queryKey: communityQueryKey.postDetail(postId),
    queryFn: () => communityApi.getPost(postId),
    enabled: enabled && !!postId,
  });
}

/**
 * 게시글 작성 뮤테이션 훅
 */
export function useCreatePostMutation() {
  const queryClient = useQueryClient();

  return useMutation<PostDetail, Error, PostCreate>({
    mutationFn: communityApi.createPost,
    onSuccess: () => {
      // 게시글 목록 갱신
      queryClient.invalidateQueries({ queryKey: communityQueryKey.posts() });
    },
  });
}

/**
 * 게시글 수정 뮤테이션 훅
 */
export function useUpdatePostMutation() {
  const queryClient = useQueryClient();

  return useMutation<PostDetail, Error, { postId: string; data: PostUpdate }>({
    mutationFn: ({ postId, data }) => communityApi.updatePost(postId, data),
    onSuccess: (_, { postId }) => {
      // 게시글 상세 갱신
      queryClient.invalidateQueries({
        queryKey: communityQueryKey.postDetail(postId),
      });
      // 게시글 목록 갱신
      queryClient.invalidateQueries({ queryKey: communityQueryKey.posts() });
    },
  });
}

/**
 * 게시글 삭제 뮤테이션 훅
 */
export function useDeletePostMutation() {
  const queryClient = useQueryClient();

  return useMutation<void, Error, string>({
    mutationFn: communityApi.deletePost,
    onSuccess: (_, postId) => {
      // 게시글 목록 갱신
      queryClient.invalidateQueries({ queryKey: communityQueryKey.posts() });
      // 게시글 상세 캐시 제거
      queryClient.removeQueries({
        queryKey: communityQueryKey.postDetail(postId),
      });
    },
  });
}

// ============================================================
// 댓글 관련 훅
// ============================================================

/**
 * 댓글 목록 조회 훅
 */
export function useCommentsQuery(postId: string, enabled = true) {
  return useQuery<CommentListResponse, Error>({
    queryKey: communityQueryKey.comments(postId),
    queryFn: () => communityApi.getComments(postId),
    enabled: enabled && !!postId,
  });
}

/**
 * 댓글 작성 뮤테이션 훅
 */
export function useCreateCommentMutation() {
  const queryClient = useQueryClient();

  return useMutation<
    CommentItem,
    Error,
    { postId: string; data: CommentCreate }
  >({
    mutationFn: ({ postId, data }) => communityApi.createComment(postId, data),
    onSuccess: (_, { postId }) => {
      // 댓글 목록 갱신
      queryClient.invalidateQueries({
        queryKey: communityQueryKey.comments(postId),
      });
      // 게시글 상세 갱신 (댓글 수 업데이트)
      queryClient.invalidateQueries({
        queryKey: communityQueryKey.postDetail(postId),
      });
    },
  });
}

/**
 * 댓글 수정 뮤테이션 훅
 */
export function useUpdateCommentMutation() {
  const queryClient = useQueryClient();

  return useMutation<
    CommentItem,
    Error,
    { commentId: string; postId: string; data: CommentUpdate }
  >({
    mutationFn: ({ commentId, data }) =>
      communityApi.updateComment(commentId, data),
    onSuccess: (_, { postId }) => {
      // 댓글 목록 갱신
      queryClient.invalidateQueries({
        queryKey: communityQueryKey.comments(postId),
      });
    },
  });
}

/**
 * 댓글 삭제 뮤테이션 훅
 */
export function useDeleteCommentMutation() {
  const queryClient = useQueryClient();

  return useMutation<void, Error, { commentId: string; postId: string }>({
    mutationFn: ({ commentId }) => communityApi.deleteComment(commentId),
    onSuccess: (_, { postId }) => {
      // 댓글 목록 갱신
      queryClient.invalidateQueries({
        queryKey: communityQueryKey.comments(postId),
      });
      // 게시글 상세 갱신 (댓글 수 업데이트)
      queryClient.invalidateQueries({
        queryKey: communityQueryKey.postDetail(postId),
      });
    },
  });
}

// ============================================================
// 좋아요 관련 훅
// ============================================================

/**
 * 게시글 좋아요 토글 뮤테이션 훅
 */
export function useTogglePostLikeMutation() {
  const queryClient = useQueryClient();

  return useMutation<LikeResponse, Error, string>({
    mutationFn: communityApi.togglePostLike,
    onSuccess: (_, postId) => {
      // 게시글 상세 갱신 (좋아요 수 업데이트)
      queryClient.invalidateQueries({
        queryKey: communityQueryKey.postDetail(postId),
      });
      // 게시글 목록 갱신
      queryClient.invalidateQueries({ queryKey: communityQueryKey.posts() });
    },
  });
}

/**
 * 댓글 좋아요 토글 뮤테이션 훅
 */
export function useToggleCommentLikeMutation() {
  const queryClient = useQueryClient();

  return useMutation<LikeResponse, Error, { commentId: string; postId: string }>(
    {
      mutationFn: ({ commentId }) => communityApi.toggleCommentLike(commentId),
      onSuccess: (_, { postId }) => {
        // 댓글 목록 갱신 (좋아요 수 업데이트)
        queryClient.invalidateQueries({
          queryKey: communityQueryKey.comments(postId),
        });
      },
    }
  );
}

// ============================================================
// 랭킹 관련 훅
// ============================================================

/**
 * 상위 3개 랭킹 조회 훅
 */
export function useTopRankingsQuery() {
  return useQuery<TopRankingsResponse, Error>({
    queryKey: communityQueryKey.topRankings(),
    queryFn: communityApi.getTopRankings,
    staleTime: 1000 * 60 * 60, // 1시간 (Redis 캐시와 동일)
  });
}

/**
 * 전체 랭킹 목록 조회 훅
 */
export function useRankingsQuery(params?: { page?: number; limit?: number }) {
  return useQuery<RankingListResponse, Error>({
    queryKey: communityQueryKey.rankingList(params),
    queryFn: () => communityApi.getRankings(params),
  });
}

// ============================================================
// 전략 복제 관련 훅
// ============================================================

/**
 * 복제용 전략 데이터 조회 훅
 */
export function useCloneStrategyDataQuery(sessionId: string, enabled = true) {
  return useQuery<CloneStrategyData, Error>({
    queryKey: communityQueryKey.cloneStrategy(sessionId),
    queryFn: () => communityApi.getCloneStrategyData(sessionId),
    enabled: enabled && !!sessionId,
  });
}

/**
 * 전략 복제 실행 뮤테이션 훅
 */
export function useCloneStrategyMutation() {
  const queryClient = useQueryClient();

  return useMutation<{ message: string }, Error, string>({
    mutationFn: communityApi.cloneStrategy,
    onSuccess: () => {
      // 전략 목록 갱신 (복제된 전략 반영)
      queryClient.invalidateQueries({ queryKey: ["strategies"] });
    },
  });
}
