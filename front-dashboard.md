# 투자전략 Dashboard 프론트엔드 구현 가이드

## 개요

두 개의 새로운 페이지를 구현합니다:
1. **내 투자전략 페이지** (`/my-strategies`): 본인이 만든 투자전략을 모아서 보는 페이지
2. **공개 투자전략 랭킹 페이지** (`/strategy-ranking`): 높은 수익률을 기록한 공개 투자전략 랭킹

## 1. TypeScript 타입 정의

### 파일: `SL-Front-End/src/types/api.ts`

기존 파일 끝에 다음 타입들을 추가하세요:

```typescript
// ========== Strategy (투자전략) 관련 타입 ==========

/** 투자전략 공개 설정 */
export interface StrategySharingSettings {
  isPublic: boolean; // 공개 여부 (랭킹 집계)
  isAnonymous: boolean; // 익명 여부
  hideStrategyDetails: boolean; // 전략 내용 숨김 여부
}

/** 투자전략 통계 요약 */
export interface StrategyStatisticsSummary {
  totalReturn?: number; // 총 수익률 (%)
  annualizedReturn?: number; // 연환산 수익률 (%)
  maxDrawdown?: number; // 최대 낙폭 (%)
  sharpeRatio?: number; // 샤프 비율
  winRate?: number; // 승률 (%)
}

/** 내 투자전략 항목 */
export interface MyStrategyItem {
  strategyId: string;
  strategyName: string;
  strategyType?: string;
  description?: string;
  isPublic: boolean;
  isAnonymous: boolean;
  hideStrategyDetails: boolean;
  initialCapital?: number;
  backtestStartDate?: string;
  backtestEndDate?: string;
  statistics?: StrategyStatisticsSummary;
  createdAt: string;
  updatedAt: string;
}

/** 내 투자전략 목록 응답 */
export interface MyStrategiesResponse {
  strategies: MyStrategyItem[];
  total: number;
}

/** 공개 투자전략 랭킹 항목 */
export interface StrategyRankingItem {
  strategyId: string;
  strategyName: string;
  ownerName?: string; // 익명이면 null
  isAnonymous: boolean;
  strategyType?: string; // 숨김이면 null
  description?: string; // 숨김이면 null
  hideStrategyDetails: boolean;
  backtestStartDate?: string;
  backtestEndDate?: string;
  totalReturn: number;
  annualizedReturn: number;
  maxDrawdown?: number;
  sharpeRatio?: number;
  volatility?: number;
  winRate?: number;
  totalTrades?: number;
  createdAt: string;
}

/** 공개 투자전략 랭킹 응답 */
export interface StrategyRankingResponse {
  rankings: StrategyRankingItem[];
  total: number;
  page: number;
  limit: number;
  sortBy: "total_return" | "annualized_return";
}
```

### BacktestRunRequest에 공개 설정 필드 추가

기존 `BacktestRunRequest` 인터페이스에 다음 필드들을 추가하세요:

```typescript
export interface BacktestRunRequest {
  // ... 기존 필드들 ...

  // 공개 설정 (선택 사항)
  is_public?: boolean;
  is_anonymous?: boolean;
  hide_strategy_details?: boolean;
}
```

---

## 2. API 클라이언트 함수

### 파일: `SL-Front-End/src/lib/api/strategy.ts` (새로 생성)

```typescript
import axios from "axios";
import type {
  MyStrategiesResponse,
  StrategyRankingResponse,
  StrategySharingSettings,
} from "@/types/api";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000/api/v1";

/**
 * 내 투자전략 목록 조회
 */
export async function getMyStrategies(): Promise<MyStrategiesResponse> {
  const response = await axios.get(`${API_BASE_URL}/strategies/my`, {
    headers: {
      Authorization: `Bearer ${localStorage.getItem("access_token")}`,
    },
  });
  return response.data;
}

/**
 * 공개 투자전략 랭킹 조회
 * @param sortBy 정렬 기준 ("total_return" | "annualized_return")
 * @param page 페이지 번호 (기본: 1)
 * @param limit 페이지당 항목 수 (기본: 20)
 */
export async function getPublicStrategiesRanking(
  sortBy: "total_return" | "annualized_return" = "annualized_return",
  page: number = 1,
  limit: number = 20
): Promise<StrategyRankingResponse> {
  const response = await axios.get(`${API_BASE_URL}/strategies/public/ranking`, {
    params: { sort_by: sortBy, page, limit },
  });
  return response.data;
}

/**
 * 투자전략 공개 설정 변경
 * @param strategyId 전략 ID
 * @param settings 변경할 설정
 */
export async function updateStrategySharingSettings(
  strategyId: string,
  settings: Partial<StrategySharingSettings>
): Promise<{ message: string; strategy_id: string; settings: StrategySharingSettings }> {
  const response = await axios.patch(
    `${API_BASE_URL}/strategies/${strategyId}/settings`,
    settings,
    {
      headers: {
        Authorization: `Bearer ${localStorage.getItem("access_token")}`,
      },
    }
  );
  return response.data;
}
```

---

## 3. 내 투자전략 페이지

### 파일: `SL-Front-End/src/app/my-strategies/page.tsx` (새로 생성)

```tsx
"use client";

import { useEffect, useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { getMyStrategies, updateStrategySharingSettings } from "@/lib/api/strategy";
import type { MyStrategyItem } from "@/types/api";

export default function MyStrategiesPage() {
  const queryClient = useQueryClient();

  // 내 투자전략 목록 조회
  const { data, isLoading, error } = useQuery({
    queryKey: ["my-strategies"],
    queryFn: getMyStrategies,
  });

  // 공개 설정 변경 mutation
  const updateSettingsMutation = useMutation({
    mutationFn: ({ strategyId, settings }: {
      strategyId: string;
      settings: Partial<{ isPublic: boolean; isAnonymous: boolean; hideStrategyDetails: boolean }>
    }) => updateStrategySharingSettings(strategyId, settings),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["my-strategies"] });
    },
  });

  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
          <p className="mt-4 text-gray-600">로딩 중...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-center text-red-600">
          <p className="text-xl font-semibold">오류가 발생했습니다</p>
          <p className="mt-2">{error.message}</p>
        </div>
      </div>
    );
  }

  const strategies = data?.strategies || [];

  return (
    <div className="container mx-auto px-4 py-8">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900">내 투자전략</h1>
        <p className="mt-2 text-gray-600">
          총 {data?.total || 0}개의 투자전략
        </p>
      </div>

      {strategies.length === 0 ? (
        <div className="text-center py-12">
          <p className="text-gray-500 text-lg">생성된 투자전략이 없습니다.</p>
          <a
            href="/quant"
            className="mt-4 inline-block px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
          >
            백테스트 시작하기
          </a>
        </div>
      ) : (
        <div className="space-y-4">
          {strategies.map((strategy) => (
            <StrategyDetailCard
              key={strategy.strategyId}
              strategy={strategy}
              onUpdateSettings={(settings) =>
                updateSettingsMutation.mutate({
                  strategyId: strategy.strategyId,
                  settings,
                })
              }
            />
          ))}
        </div>
      )}
    </div>
  );
}

// 개별 투자전략 카드 컴포넌트 (상세 리스트 형태)
function StrategyDetailCard({
  strategy,
  onUpdateSettings,
}: {
  strategy: MyStrategyItem;
  onUpdateSettings: (settings: any) => void;
}) {
  const [isExpanded, setIsExpanded] = useState(false);

  return (
    <div className="border rounded-lg bg-white shadow-sm hover:shadow-md transition-shadow">
      {/* 헤더 */}
      <div
        className="p-6 cursor-pointer"
        onClick={() => setIsExpanded(!isExpanded)}
      >
        <div className="flex items-center justify-between">
          <div className="flex-1">
            <div className="flex items-center gap-3">
              <h3 className="text-xl font-semibold text-gray-900">
                {strategy.strategyName}
              </h3>
              {strategy.isPublic && (
                <span className="px-2 py-1 text-xs font-medium bg-green-100 text-green-800 rounded">
                  공개
                </span>
              )}
              {strategy.isAnonymous && (
                <span className="px-2 py-1 text-xs font-medium bg-gray-100 text-gray-600 rounded">
                  익명
                </span>
              )}
            </div>
            <p className="mt-1 text-sm text-gray-500">
              {strategy.strategyType} • 생성일: {new Date(strategy.createdAt).toLocaleDateString()}
            </p>
          </div>

          {/* 주요 통계 */}
          {strategy.statistics && (
            <div className="flex gap-6 text-center">
              <div>
                <p className="text-xs text-gray-500">총 수익률</p>
                <p className={`text-lg font-bold ${
                  strategy.statistics.totalReturn && strategy.statistics.totalReturn > 0
                    ? "text-red-600"
                    : "text-blue-600"
                }`}>
                  {strategy.statistics.totalReturn?.toFixed(2)}%
                </p>
              </div>
              <div>
                <p className="text-xs text-gray-500">연환산 수익률</p>
                <p className={`text-lg font-bold ${
                  strategy.statistics.annualizedReturn && strategy.statistics.annualizedReturn > 0
                    ? "text-red-600"
                    : "text-blue-600"
                }`}>
                  {strategy.statistics.annualizedReturn?.toFixed(2)}%
                </p>
              </div>
              <div>
                <p className="text-xs text-gray-500">MDD</p>
                <p className="text-lg font-bold text-gray-900">
                  {strategy.statistics.maxDrawdown?.toFixed(2)}%
                </p>
              </div>
              <div>
                <p className="text-xs text-gray-500">샤프 비율</p>
                <p className="text-lg font-bold text-gray-900">
                  {strategy.statistics.sharpeRatio?.toFixed(2)}
                </p>
              </div>
            </div>
          )}

          <button
            className="ml-4 text-gray-400 hover:text-gray-600"
            onClick={(e) => {
              e.stopPropagation();
              setIsExpanded(!isExpanded);
            }}
          >
            <svg
              className={`w-6 h-6 transform transition-transform ${
                isExpanded ? "rotate-180" : ""
              }`}
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M19 9l-7 7-7-7"
              />
            </svg>
          </button>
        </div>
      </div>

      {/* 펼쳐진 영역 */}
      {isExpanded && (
        <div className="px-6 pb-6 border-t">
          <div className="mt-4 grid grid-cols-2 gap-6">
            {/* 왼쪽: 전략 정보 */}
            <div>
              <h4 className="font-semibold text-gray-900 mb-3">전략 정보</h4>
              <dl className="space-y-2 text-sm">
                <div className="flex justify-between">
                  <dt className="text-gray-600">초기 자본금:</dt>
                  <dd className="font-medium">
                    {strategy.initialCapital?.toLocaleString()}원
                  </dd>
                </div>
                <div className="flex justify-between">
                  <dt className="text-gray-600">백테스트 기간:</dt>
                  <dd className="font-medium">
                    {strategy.backtestStartDate} ~ {strategy.backtestEndDate}
                  </dd>
                </div>
                {strategy.description && (
                  <div className="mt-3">
                    <dt className="text-gray-600 mb-1">설명:</dt>
                    <dd className="text-gray-900">{strategy.description}</dd>
                  </div>
                )}
              </dl>
            </div>

            {/* 오른쪽: 공개 설정 */}
            <div>
              <h4 className="font-semibold text-gray-900 mb-3">공개 설정</h4>
              <div className="space-y-3">
                <label className="flex items-center gap-2 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={strategy.isPublic}
                    onChange={(e) =>
                      onUpdateSettings({ isPublic: e.target.checked })
                    }
                    className="w-4 h-4 text-blue-600 rounded focus:ring-blue-500"
                  />
                  <span className="text-sm">
                    공개 (랭킹에 집계됨)
                  </span>
                </label>

                <label className="flex items-center gap-2 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={strategy.isAnonymous}
                    onChange={(e) =>
                      onUpdateSettings({ isAnonymous: e.target.checked })
                    }
                    className="w-4 h-4 text-blue-600 rounded focus:ring-blue-500"
                  />
                  <span className="text-sm">
                    익명 (이름 숨김)
                  </span>
                </label>

                <label className="flex items-center gap-2 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={strategy.hideStrategyDetails}
                    onChange={(e) =>
                      onUpdateSettings({
                        hideStrategyDetails: e.target.checked,
                      })
                    }
                    className="w-4 h-4 text-blue-600 rounded focus:ring-blue-500"
                  />
                  <span className="text-sm">
                    전략 내용 숨김
                  </span>
                </label>
              </div>

              <div className="mt-4 text-xs text-gray-500">
                <p>• 공개 설정 시 랭킹 페이지에 표시됩니다</p>
                <p>• 익명 설정 시 이름이 표시되지 않습니다</p>
                <p>• 전략 숨김 시 매수/매도 조건이 비공개됩니다</p>
              </div>
            </div>
          </div>

          {/* 모든 통계 표시 */}
          {strategy.statistics && (
            <div className="mt-6 pt-6 border-t">
              <h4 className="font-semibold text-gray-900 mb-3">상세 통계</h4>
              <div className="grid grid-cols-5 gap-4 text-sm">
                <div className="text-center p-3 bg-gray-50 rounded">
                  <p className="text-gray-600 mb-1">총 수익률</p>
                  <p className="font-bold text-lg">
                    {strategy.statistics.totalReturn?.toFixed(2)}%
                  </p>
                </div>
                <div className="text-center p-3 bg-gray-50 rounded">
                  <p className="text-gray-600 mb-1">연환산 수익률</p>
                  <p className="font-bold text-lg">
                    {strategy.statistics.annualizedReturn?.toFixed(2)}%
                  </p>
                </div>
                <div className="text-center p-3 bg-gray-50 rounded">
                  <p className="text-gray-600 mb-1">최대 낙폭</p>
                  <p className="font-bold text-lg">
                    {strategy.statistics.maxDrawdown?.toFixed(2)}%
                  </p>
                </div>
                <div className="text-center p-3 bg-gray-50 rounded">
                  <p className="text-gray-600 mb-1">샤프 비율</p>
                  <p className="font-bold text-lg">
                    {strategy.statistics.sharpeRatio?.toFixed(2)}
                  </p>
                </div>
                <div className="text-center p-3 bg-gray-50 rounded">
                  <p className="text-gray-600 mb-1">승률</p>
                  <p className="font-bold text-lg">
                    {strategy.statistics.winRate?.toFixed(1)}%
                  </p>
                </div>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
```

---

## 4. 공개 투자전략 랭킹 페이지

### 파일: `SL-Front-End/src/app/strategy-ranking/page.tsx` (새로 생성)

```tsx
"use client";

import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { getPublicStrategiesRanking } from "@/lib/api/strategy";
import type { StrategyRankingItem } from "@/types/api";

export default function StrategyRankingPage() {
  const [sortBy, setSortBy] = useState<"total_return" | "annualized_return">("annualized_return");
  const [page, setPage] = useState(1);
  const limit = 20;

  // 랭킹 데이터 조회
  const { data, isLoading, error } = useQuery({
    queryKey: ["strategy-ranking", sortBy, page],
    queryFn: () => getPublicStrategiesRanking(sortBy, page, limit),
  });

  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
          <p className="mt-4 text-gray-600">랭킹 로딩 중...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-center text-red-600">
          <p className="text-xl font-semibold">오류가 발생했습니다</p>
          <p className="mt-2">{error.message}</p>
        </div>
      </div>
    );
  }

  const rankings = data?.rankings || [];
  const totalPages = Math.ceil((data?.total || 0) / limit);

  return (
    <div className="container mx-auto px-4 py-8">
      {/* 헤더 */}
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900">투자전략 랭킹</h1>
        <p className="mt-2 text-gray-600">
          높은 수익률을 기록한 공개 투자전략 Top {data?.total || 0}
        </p>
      </div>

      {/* 정렬 필터 */}
      <div className="mb-6 flex items-center gap-4">
        <label className="text-sm font-medium text-gray-700">정렬 기준:</label>
        <div className="flex gap-2">
          <button
            onClick={() => {
              setSortBy("total_return");
              setPage(1);
            }}
            className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
              sortBy === "total_return"
                ? "bg-blue-600 text-white"
                : "bg-gray-100 text-gray-700 hover:bg-gray-200"
            }`}
          >
            총 수익률
          </button>
          <button
            onClick={() => {
              setSortBy("annualized_return");
              setPage(1);
            }}
            className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
              sortBy === "annualized_return"
                ? "bg-blue-600 text-white"
                : "bg-gray-100 text-gray-700 hover:bg-gray-200"
            }`}
          >
            연환산 수익률
          </button>
        </div>
      </div>

      {/* 랭킹 리스트 */}
      {rankings.length === 0 ? (
        <div className="text-center py-12 bg-gray-50 rounded-lg">
          <p className="text-gray-500 text-lg">공개된 투자전략이 없습니다.</p>
        </div>
      ) : (
        <div className="space-y-3">
          {rankings.map((ranking, index) => (
            <RankingCard
              key={ranking.strategyId}
              ranking={ranking}
              rank={(page - 1) * limit + index + 1}
              sortBy={sortBy}
            />
          ))}
        </div>
      )}

      {/* 페이지네이션 */}
      {totalPages > 1 && (
        <div className="mt-8 flex items-center justify-center gap-2">
          <button
            onClick={() => setPage((p) => Math.max(1, p - 1))}
            disabled={page === 1}
            className="px-4 py-2 rounded-lg bg-gray-100 text-gray-700 hover:bg-gray-200 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            이전
          </button>

          <div className="flex gap-1">
            {Array.from({ length: Math.min(5, totalPages) }, (_, i) => {
              let pageNum = i + 1;
              if (totalPages > 5) {
                if (page <= 3) {
                  pageNum = i + 1;
                } else if (page >= totalPages - 2) {
                  pageNum = totalPages - 4 + i;
                } else {
                  pageNum = page - 2 + i;
                }
              }
              return (
                <button
                  key={pageNum}
                  onClick={() => setPage(pageNum)}
                  className={`w-10 h-10 rounded-lg ${
                    page === pageNum
                      ? "bg-blue-600 text-white"
                      : "bg-gray-100 text-gray-700 hover:bg-gray-200"
                  }`}
                >
                  {pageNum}
                </button>
              );
            })}
          </div>

          <button
            onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
            disabled={page === totalPages}
            className="px-4 py-2 rounded-lg bg-gray-100 text-gray-700 hover:bg-gray-200 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            다음
          </button>
        </div>
      )}
    </div>
  );
}

// 개별 랭킹 카드
function RankingCard({
  ranking,
  rank,
  sortBy,
}: {
  ranking: StrategyRankingItem;
  rank: number;
  sortBy: "total_return" | "annualized_return";
}) {
  const [showDetails, setShowDetails] = useState(false);

  // 메인 수익률 (정렬 기준에 따라)
  const mainReturn = sortBy === "total_return" ? ranking.totalReturn : ranking.annualizedReturn;
  const mainReturnLabel = sortBy === "total_return" ? "총 수익률" : "연환산 수익률";

  return (
    <div className="border rounded-lg bg-white shadow-sm hover:shadow-md transition-shadow">
      <div className="p-6">
        <div className="flex items-center gap-6">
          {/* 순위 */}
          <div className="flex-shrink-0 w-16 text-center">
            <div
              className={`text-3xl font-bold ${
                rank === 1
                  ? "text-yellow-500"
                  : rank === 2
                  ? "text-gray-400"
                  : rank === 3
                  ? "text-orange-600"
                  : "text-gray-600"
              }`}
            >
              {rank}
            </div>
            {rank <= 3 && <div className="text-xs text-gray-500 mt-1">위</div>}
          </div>

          {/* 전략 정보 */}
          <div className="flex-1">
            <div className="flex items-center gap-2 mb-1">
              <h3 className="text-lg font-semibold text-gray-900">
                {ranking.strategyName}
              </h3>
              {ranking.isAnonymous && (
                <span className="px-2 py-0.5 text-xs bg-gray-100 text-gray-600 rounded">
                  익명
                </span>
              )}
              {ranking.hideStrategyDetails && (
                <span className="px-2 py-0.5 text-xs bg-yellow-100 text-yellow-800 rounded">
                  전략 비공개
                </span>
              )}
            </div>

            <div className="flex items-center gap-4 text-sm text-gray-600">
              <span>{ranking.ownerName || "익명"}</span>
              {!ranking.hideStrategyDetails && ranking.strategyType && (
                <span>• {ranking.strategyType}</span>
              )}
              <span>
                • {ranking.backtestStartDate} ~ {ranking.backtestEndDate}
              </span>
            </div>
          </div>

          {/* 주요 수익률 */}
          <div className="flex-shrink-0 text-right">
            <p className="text-xs text-gray-500 mb-1">{mainReturnLabel}</p>
            <p
              className={`text-3xl font-bold ${
                mainReturn > 0 ? "text-red-600" : "text-blue-600"
              }`}
            >
              {mainReturn.toFixed(2)}%
            </p>
          </div>

          {/* 통계 그리드 */}
          <div className="flex gap-6 text-center">
            <div>
              <p className="text-xs text-gray-500">샤프 비율</p>
              <p className="text-lg font-semibold text-gray-900">
                {ranking.sharpeRatio?.toFixed(2) || "-"}
              </p>
            </div>
            <div>
              <p className="text-xs text-gray-500">MDD</p>
              <p className="text-lg font-semibold text-gray-900">
                {ranking.maxDrawdown?.toFixed(2) || "-"}%
              </p>
            </div>
            <div>
              <p className="text-xs text-gray-500">승률</p>
              <p className="text-lg font-semibold text-gray-900">
                {ranking.winRate?.toFixed(1) || "-"}%
              </p>
            </div>
          </div>

          {/* 상세보기 버튼 */}
          <button
            onClick={() => setShowDetails(!showDetails)}
            className="flex-shrink-0 text-gray-400 hover:text-gray-600"
          >
            <svg
              className={`w-6 h-6 transform transition-transform ${
                showDetails ? "rotate-180" : ""
              }`}
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M19 9l-7 7-7-7"
              />
            </svg>
          </button>
        </div>

        {/* 상세 정보 (펼쳐진 경우) */}
        {showDetails && (
          <div className="mt-6 pt-6 border-t">
            <div className="grid grid-cols-6 gap-4 text-sm">
              <div className="text-center p-3 bg-gray-50 rounded">
                <p className="text-gray-600 mb-1">총 수익률</p>
                <p className="font-bold">{ranking.totalReturn.toFixed(2)}%</p>
              </div>
              <div className="text-center p-3 bg-gray-50 rounded">
                <p className="text-gray-600 mb-1">연환산 수익률</p>
                <p className="font-bold">{ranking.annualizedReturn.toFixed(2)}%</p>
              </div>
              <div className="text-center p-3 bg-gray-50 rounded">
                <p className="text-gray-600 mb-1">변동성</p>
                <p className="font-bold">{ranking.volatility?.toFixed(2) || "-"}%</p>
              </div>
              <div className="text-center p-3 bg-gray-50 rounded">
                <p className="text-gray-600 mb-1">샤프 비율</p>
                <p className="font-bold">{ranking.sharpeRatio?.toFixed(2) || "-"}</p>
              </div>
              <div className="text-center p-3 bg-gray-50 rounded">
                <p className="text-gray-600 mb-1">최대 낙폭</p>
                <p className="font-bold">{ranking.maxDrawdown?.toFixed(2) || "-"}%</p>
              </div>
              <div className="text-center p-3 bg-gray-50 rounded">
                <p className="text-gray-600 mb-1">거래 횟수</p>
                <p className="font-bold">{ranking.totalTrades || "-"}</p>
              </div>
            </div>

            {!ranking.hideStrategyDetails && ranking.description && (
              <div className="mt-4 p-4 bg-gray-50 rounded">
                <p className="text-sm text-gray-700">{ranking.description}</p>
              </div>
            )}

            {ranking.hideStrategyDetails && (
              <div className="mt-4 p-4 bg-yellow-50 rounded text-center">
                <p className="text-sm text-yellow-800">
                  ⚠️ 이 전략의 상세 내용은 작성자가 비공개로 설정했습니다
                </p>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
```

---

## 5. 백테스트 실행 페이지에 공개 설정 탭 추가

### 파일: `SL-Front-End/src/app/quant/page.tsx` (수정)

기존 백테스트 실행 페이지에 공개 설정 섹션을 추가합니다.

#### 1) 상태 추가

```typescript
// 공개 설정 상태 추가
const [isPublic, setIsPublic] = useState(false);
const [isAnonymous, setIsAnonymous] = useState(false);
const [hideStrategyDetails, setHideStrategyDetails] = useState(false);
```

#### 2) 백테스트 실행 시 공개 설정 포함

```typescript
const backtestRequest: BacktestRunRequest = {
  // ... 기존 필드들 ...
  is_public: isPublic,
  is_anonymous: isAnonymous,
  hide_strategy_details: hideStrategyDetails,
};
```

#### 3) UI에 공개 설정 탭 추가

기존 백테스트 설정 폼 하단에 다음 섹션을 추가하세요:

```tsx
{/* 공개 설정 섹션 */}
<div className="mt-8 border-t pt-6">
  <h3 className="text-lg font-semibold text-gray-900 mb-4">
    공개 설정
  </h3>
  <p className="text-sm text-gray-600 mb-4">
    백테스트 완료 후, 이 전략을 공개 랭킹에 포함할지 설정합니다.
  </p>

  <div className="space-y-4">
    {/* 공개 여부 */}
    <label className="flex items-start gap-3 cursor-pointer">
      <input
        type="checkbox"
        checked={isPublic}
        onChange={(e) => setIsPublic(e.target.checked)}
        className="mt-1 w-4 h-4 text-blue-600 rounded focus:ring-blue-500"
      />
      <div>
        <span className="font-medium text-gray-900">
          공개 (랭킹 집계)
        </span>
        <p className="text-sm text-gray-500 mt-1">
          이 전략의 수익률을 공개 랭킹 페이지에 표시합니다.
        </p>
      </div>
    </label>

    {/* 익명 여부 */}
    <label
      className={`flex items-start gap-3 cursor-pointer ${
        !isPublic ? "opacity-50 cursor-not-allowed" : ""
      }`}
    >
      <input
        type="checkbox"
        checked={isAnonymous}
        onChange={(e) => setIsAnonymous(e.target.checked)}
        disabled={!isPublic}
        className="mt-1 w-4 h-4 text-blue-600 rounded focus:ring-blue-500"
      />
      <div>
        <span className="font-medium text-gray-900">익명</span>
        <p className="text-sm text-gray-500 mt-1">
          랭킹에서 사용자 이름을 숨깁니다.
        </p>
      </div>
    </label>

    {/* 전략 내용 숨김 */}
    <label
      className={`flex items-start gap-3 cursor-pointer ${
        !isPublic ? "opacity-50 cursor-not-allowed" : ""
      }`}
    >
      <input
        type="checkbox"
        checked={hideStrategyDetails}
        onChange={(e) => setHideStrategyDetails(e.target.checked)}
        disabled={!isPublic}
        className="mt-1 w-4 h-4 text-blue-600 rounded focus:ring-blue-500"
      />
      <div>
        <span className="font-medium text-gray-900">
          전략 내용 숨김
        </span>
        <p className="text-sm text-gray-500 mt-1">
          매수/매도 조건, 팩터, 대상 종목 등 전략의 상세 내용을 숨깁니다.
          수익률 통계만 공개됩니다.
        </p>
      </div>
    </label>
  </div>

  <div className="mt-4 p-3 bg-blue-50 rounded-lg">
    <p className="text-sm text-blue-800">
      💡 공개 설정은 나중에 "내 투자전략" 페이지에서 변경할 수 있습니다.
    </p>
  </div>
</div>
```

---

## 6. 네비게이션 링크 추가

### 파일: `SL-Front-End/src/components/layout/Header.tsx` (또는 네비게이션 컴포넌트)

헤더 또는 사이드바 네비게이션에 다음 링크를 추가하세요:

```tsx
<nav>
  {/* 기존 링크들... */}

  <a
    href="/my-strategies"
    className="nav-link"
  >
    내 투자전략
  </a>

  <a
    href="/strategy-ranking"
    className="nav-link"
  >
    전략 랭킹
  </a>
</nav>
```

---

## 7. 환경 변수 확인

`.env.local` 파일에 API 엔드포인트가 설정되어 있는지 확인하세요:

```env
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000/api/v1
```

---

## 8. 라우팅 설정 (Next.js App Router)

Next.js 13+ App Router를 사용하는 경우, 다음 폴더 구조를 따르세요:

```
SL-Front-End/src/app/
├── my-strategies/
│   └── page.tsx          # 내 투자전략 페이지
├── strategy-ranking/
│   └── page.tsx          # 공개 랭킹 페이지
└── quant/
    └── page.tsx          # 백테스트 페이지 (기존, 수정)
```

---

## 9. 백엔드 마이그레이션 실행

프론트엔드 개발 전에 백엔드 데이터베이스 마이그레이션을 실행해야 합니다:

```bash
cd SL-Back-end

# PostgreSQL에 접속하여 마이그레이션 실행
psql -U postgres -d quant_investment_db -f migrations/add_portfolio_sharing_fields.sql

# 또는 Docker 환경에서
docker exec -i postgres psql -U postgres -d quant_investment_db < migrations/add_portfolio_sharing_fields.sql
```

---

## 10. 테스트 체크리스트

구현 후 다음 사항들을 테스트하세요:

### 내 투자전략 페이지
- [ ] 로그인 후 본인의 전략 목록이 표시되는가?
- [ ] 전략이 없을 때 안내 메시지가 표시되는가?
- [ ] 상세 정보 펼치기/접기가 동작하는가?
- [ ] 공개 설정 변경이 즉시 반영되는가?
- [ ] 통계 데이터가 정확하게 표시되는가?

### 공개 랭킹 페이지
- [ ] 정렬 기준 변경(총 수익률/연환산 수익률)이 동작하는가?
- [ ] 페이지네이션이 정상 작동하는가?
- [ ] 익명 설정이 제대로 반영되는가? (이름 숨김)
- [ ] 전략 내용 숨김이 제대로 동작하는가?
- [ ] 로그인 없이도 접근 가능한가?

### 백테스트 실행 페이지
- [ ] 공개 설정 체크박스가 표시되는가?
- [ ] 공개 설정이 백테스트 요청에 포함되는가?
- [ ] 비공개 상태에서 익명/숨김 옵션이 비활성화되는가?

---

## 11. API 엔드포인트 정리

### 백엔드 API (FastAPI)

| 메서드 | 경로 | 설명 | 인증 |
|--------|------|------|------|
| GET | `/api/v1/strategies/my` | 내 투자전략 목록 조회 | 필요 |
| GET | `/api/v1/strategies/public/ranking` | 공개 랭킹 조회 | 불필요 |
| PATCH | `/api/v1/strategies/{strategy_id}/settings` | 공개 설정 변경 | 필요 |
| POST | `/api/v1/backtest/run` | 백테스트 실행 (공개 설정 포함) | 불필요 |

---

## 12. 추가 고려사항

### 성능 최적화
- 랭킹 페이지는 무한 스크롤 또는 가상 스크롤로 개선 가능
- 캐싱을 통해 API 호출 최소화

### UX 개선
- 로딩 스켈레톤 UI 추가
- 에러 바운더리 설정
- 토스트 알림으로 설정 변경 피드백

### 접근성
- 키보드 내비게이션 지원
- 스크린 리더 호환성 확인
- ARIA 라벨 추가

---

## 문의사항

구현 중 문제가 발생하면 다음을 확인하세요:

1. **CORS 오류**: 백엔드 `main.py`의 CORS 설정 확인
2. **인증 오류**: localStorage의 `access_token` 확인
3. **타입 오류**: TypeScript 타입 정의가 백엔드 응답과 일치하는지 확인

---

**작성일**: 2025-01-06
**버전**: 2.0 (Strategy 용어로 통일)
