/**
 * 백테스트 설정 입력 폼 렌더러
 *
 * 투자 금액, 시작일, 종료일을 입력받고 유효성 검증을 수행
 * 모든 필드가 유효할 때만 백테스트 시작 버튼 활성화
 */

"use client";

import { useState, useEffect } from "react";
import type { BacktestConfigMessage, BacktestConfig } from "@/types/message";
import { getStrategyDetail } from "@/lib/api/investment-strategy";
import { authApi } from "@/lib/api/auth";

interface BacktestConfigRendererProps {
  message: BacktestConfigMessage;
  /**
   * 백테스트 시작 시 호출되는 콜백
   * @param strategyName - 전략명
   * @param config - 백테스트 설정
   */
  onBacktestStart?: (
    strategyName: string,
    config: {
      investmentAmount: number;
      startDate: string;
      endDate: string;
    }
  ) => void;
}

interface ValidationError {
  investmentAmount?: string;
  startDate?: string;
  endDate?: string;
}

/**
 * 백테스트 설정 메시지를 렌더링하는 컴포넌트
 */
export function BacktestConfigRenderer({
  message,
  onBacktestStart,
}: BacktestConfigRendererProps) {
  // 기본값: 투자 금액 5,000만원, 시작일 1년 1일 전, 종료일 1일 전
  const today = new Date().toISOString().split("T")[0];
  const yesterday = new Date(Date.now() - 24 * 60 * 60 * 1000).toISOString().split("T")[0];
  const oneYearAndOneDayAgo = new Date(
    Date.now() - (365 + 1) * 24 * 60 * 60 * 1000
  ).toISOString().split("T")[0];

  const [config, setConfig] = useState<BacktestConfig>({
    investmentAmount: 5000,
    startDate: oneYearAndOneDayAgo,
    endDate: yesterday,
  });

  const [errors, setErrors] = useState<ValidationError>({});
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [apiError, setApiError] = useState<string | null>(null);
  const [userId, setUserId] = useState<string | null>(null);

  /**
   * 현재 사용자 정보 로드
   */
  useEffect(() => {
    async function loadCurrentUser() {
      try {
        const user = await authApi.getCurrentUser();
        setUserId(user.user_id);
      } catch (error) {
        console.error("Failed to load user:", error);
        setApiError("사용자 정보를 불러올 수 없습니다.");
      }
    }
    loadCurrentUser();
  }, []);

  /**
   * 투자 금액 유효성 검증
   * - 최소 100만원 이상, 최대 10억원 이하
   */
  function validateInvestmentAmount(amount: number): string | undefined {
    if (amount < 100) {
      return "투자 금액은 100만원 이상이어야 합니다.";
    }
    if (amount > 100000) {
      return "투자 금액은 10억원 이하여야 합니다.";
    }
    return undefined;
  }

  /**
   * 투자 시작일 유효성 검증
   * - 2020-01-01 이후
   */
  function validateStartDate(date: string): string | undefined {
    const minDate = new Date("2020-01-01");
    const selectedDate = new Date(date);

    if (selectedDate < minDate) {
      return "투자 시작일은 2020-01-01 이후여야 합니다.";
    }
    return undefined;
  }

  /**
   * 투자 종료일 유효성 검증
   * - 시작일보다 이후
   * - 오늘 날짜 이전
   */
  function validateEndDate(endDate: string, startDate: string): string | undefined {
    const end = new Date(endDate);
    const start = new Date(startDate);
    const now = new Date();

    if (end <= start) {
      return "투자 종료일은 시작일보다 이후여야 합니다.";
    }
    if (end > now) {
      return "투자 종료일은 오늘 날짜 이전이어야 합니다.";
    }
    return undefined;
  }

  /**
   * 전체 폼 유효성 검증
   */
  function validateForm(): boolean {
    const newErrors: ValidationError = {};

    const amountError = validateInvestmentAmount(config.investmentAmount);
    if (amountError) newErrors.investmentAmount = amountError;

    const startError = validateStartDate(config.startDate);
    if (startError) newErrors.startDate = startError;

    const endError = validateEndDate(config.endDate, config.startDate);
    if (endError) newErrors.endDate = endError;

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  }

  /**
   * 투자 금액 변경 핸들러
   */
  function handleAmountChange(value: string) {
    const numValue = Number.parseInt(value, 10);
    if (Number.isNaN(numValue)) return;

    setConfig((prev) => ({ ...prev, investmentAmount: numValue }));

    // 실시간 유효성 검증
    const error = validateInvestmentAmount(numValue);
    setErrors((prev) => ({ ...prev, investmentAmount: error }));
  }

  /**
   * 시작일 변경 핸들러
   */
  function handleStartDateChange(value: string) {
    setConfig((prev) => ({ ...prev, startDate: value }));

    // 실시간 유효성 검증
    const startError = validateStartDate(value);
    const endError = validateEndDate(config.endDate, value);
    setErrors((prev) => ({
      ...prev,
      startDate: startError,
      endDate: endError,
    }));
  }

  /**
   * 종료일 변경 핸들러
   */
  function handleEndDateChange(value: string) {
    setConfig((prev) => ({ ...prev, endDate: value }));

    // 실시간 유효성 검증
    const error = validateEndDate(value, config.startDate);
    setErrors((prev) => ({ ...prev, endDate: error }));
  }

  /**
   * 백테스트 시작 핸들러
   *
   * POST /backtest/run API 호출은 handleBacktestStart에서 수행
   * 여기서는 전략명과 설정만 부모 컴포넌트에 전달
   */
  async function handleStartBacktest() {
    if (!validateForm()) return;

    if (!userId) {
      setApiError("사용자 정보를 불러오는 중입니다. 잠시 후 다시 시도해주세요.");
      return;
    }

    setIsSubmitting(true);
    setApiError(null); // 이전 에러 초기화

    try {
      // 1. 전략 상세 정보 조회 (전략명을 위해 필요)
      const strategyDetail = await getStrategyDetail(message.strategyId);

      // 부모 컴포넌트에 백테스트 시작 알림
      // handleBacktestStart가 POST API 호출 후 백엔드에서 backtestId를 받아옴
      if (onBacktestStart) {
        onBacktestStart(strategyDetail.name, config);
      } else {
        // 콜백이 없는 경우 경고 표시
        console.warn(
          "onBacktestStart callback not provided. " +
          "Parent component should handle backtest execution message."
        );
      }
    } catch (error) {
      console.error("Backtest preparation error:", error);
      const errorMessage =
        error instanceof Error
          ? error.message
          : "백테스트 준비 중 오류가 발생했습니다.";
      setApiError(errorMessage);
    } finally {
      setIsSubmitting(false);
    }
  }

  const isFormValid =
    !errors.investmentAmount && !errors.startDate && !errors.endDate;

  return (
    <div className="flex justify-start mb-6">
      <div className="max-w-[95%] w-full rounded-2xl border border-gray-200 bg-white px-5 py-4 shadow-sm">
        {/* 헤더 */}
        <h3 className="text-base font-bold text-gray-900">
          백테스트 설정
        </h3>
        <p className="mt-1 text-sm text-gray-600">
          선택하신 <span className="font-semibold">{message.strategyName}</span> 전략으로
          과거 데이터를 기반으로 테스트해보겠습니다.
        </p>

        {/* 설정 폼 */}
        <div className="mt-4 space-y-4">
          {/* 투자 금액 */}
          <div>
            <label
              htmlFor="investmentAmount"
              className="block text-sm font-medium text-gray-700"
            >
              투자 금액 (만원)
            </label>
            <input
              type="number"
              id="investmentAmount"
              value={config.investmentAmount}
              onChange={(e) => handleAmountChange(e.target.value)}
              min={100}
              max={100000}
              className={`mt-1 block w-full rounded-lg border ${
                errors.investmentAmount
                  ? "border-red-500"
                  : "border-gray-300"
              } px-3 py-2 shadow-sm focus:border-purple-500 focus:outline-none focus:ring-1 focus:ring-purple-500`}
              placeholder="예: 5000"
            />
            {errors.investmentAmount && (
              <p className="mt-1 text-xs text-red-600">
                {errors.investmentAmount}
              </p>
            )}
            {!errors.investmentAmount && (
              <p className="mt-1 text-xs text-gray-500">
                {config.investmentAmount.toLocaleString()}만원 (
                {(config.investmentAmount * 10000).toLocaleString()}원)
              </p>
            )}
          </div>

          {/* 투자 시작일 */}
          <div>
            <label
              htmlFor="startDate"
              className="block text-sm font-medium text-gray-700"
            >
              투자 시작일
            </label>
            <input
              type="date"
              id="startDate"
              value={config.startDate}
              onChange={(e) => handleStartDateChange(e.target.value)}
              min="2020-01-01"
              max={today}
              className={`mt-1 block w-full rounded-lg border ${
                errors.startDate ? "border-red-500" : "border-gray-300"
              } px-3 py-2 shadow-sm focus:border-purple-500 focus:outline-none focus:ring-1 focus:ring-purple-500`}
            />
            {errors.startDate && (
              <p className="mt-1 text-xs text-red-600">{errors.startDate}</p>
            )}
          </div>

          {/* 투자 종료일 */}
          <div>
            <label
              htmlFor="endDate"
              className="block text-sm font-medium text-gray-700"
            >
              투자 종료일
            </label>
            <input
              type="date"
              id="endDate"
              value={config.endDate}
              onChange={(e) => handleEndDateChange(e.target.value)}
              min={config.startDate}
              max={today}
              className={`mt-1 block w-full rounded-lg border ${
                errors.endDate ? "border-red-500" : "border-gray-300"
              } px-3 py-2 shadow-sm focus:border-purple-500 focus:outline-none focus:ring-1 focus:ring-1 focus:ring-purple-500`}
            />
            {errors.endDate && (
              <p className="mt-1 text-xs text-red-600">{errors.endDate}</p>
            )}
          </div>
        </div>

        {/* 백테스트 시작 버튼 */}
        <div className="mt-6">
          <button
            onClick={handleStartBacktest}
            disabled={!isFormValid || isSubmitting}
            className={`w-full py-3 rounded-lg font-medium transition-colors ${
              isFormValid && !isSubmitting
                ? "bg-purple-600 text-white hover:bg-purple-700"
                : "bg-gray-300 text-gray-500 cursor-not-allowed"
            }`}
          >
            {isSubmitting ? (
              <span className="flex items-center justify-center gap-2">
                <svg
                  className="animate-spin h-5 w-5 text-white"
                  xmlns="http://www.w3.org/2000/svg"
                  fill="none"
                  viewBox="0 0 24 24"
                >
                  <circle
                    className="opacity-25"
                    cx="12"
                    cy="12"
                    r="10"
                    stroke="currentColor"
                    strokeWidth="4"
                  />
                  <path
                    className="opacity-75"
                    fill="currentColor"
                    d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
                  />
                </svg>
                백테스트 시작 중...
              </span>
            ) : (
              "백테스트 시작하기"
            )}
          </button>
        </div>

        {/* 안내 문구 */}
        {isFormValid && !isSubmitting && !apiError && (
          <p className="mt-3 text-xs text-gray-500 text-center">
            ✓ 모든 입력값이 유효합니다. 백테스트를 시작할 수 있습니다.
          </p>
        )}

        {/* API 에러 메시지 */}
        {apiError && (
          <div className="mt-3 rounded-lg bg-red-50 border border-red-200 px-4 py-3">
            <div className="flex items-start gap-2">
              <span className="text-red-600 text-lg">⚠️</span>
              <div className="flex-1">
                <p className="text-sm font-medium text-red-900">
                  오류가 발생했습니다
                </p>
                <p className="mt-1 text-xs text-red-700">{apiError}</p>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
