/**
 * 백테스트 설정 입력 폼 렌더러
 *
 * 투자 금액, 시작일, 종료일을 입력받고 유효성 검증을 수행
 * 모든 필드가 유효할 때만 백테스트 시작 버튼 활성화
 */

"use client";

import { authApi } from "@/lib/api/auth";
import { getStrategyDetail } from "@/lib/api/investment-strategy";
import type { BacktestConfig, BacktestConfigMessage } from "@/types/message";
import { useEffect, useMemo, useState } from "react";

interface PeriodPreset {
  id: string;
  label: string;
  months: number;
}

const PERIOD_PRESETS: PeriodPreset[] = [
  { id: "3m", label: "3개월", months: 3 },
  { id: "6m", label: "6개월", months: 6 },
  { id: "1y", label: "1년", months: 12 },
  { id: "2y", label: "2년", months: 24 },
  { id: "3y", label: "3년", months: 36 },
];

const MIN_START_DATE = new Date("2020-01-01");

const formatDate = (date: Date) => date.toISOString().split("T")[0];

const subtractMonths = (date: Date, months: number) => {
  const result = new Date(date);
  result.setMonth(result.getMonth() - months);
  return result;
};

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
  // 기본값: 투자 금액 5,000만원, 종료일 어제, 시작일 1년 전
  const maxSelectableEndDate = useMemo(() => {
    const date = new Date();
    date.setDate(date.getDate() - 1);
    return formatDate(date);
  }, []);

  const defaultPreset = PERIOD_PRESETS.find((preset) => preset.id === "1y")!;
  const defaultStartDate = formatDate(
    subtractMonths(new Date(maxSelectableEndDate), defaultPreset.months),
  );

  const [config, setConfig] = useState<BacktestConfig>({
    investmentAmount: 5000,
    startDate: defaultStartDate,
    endDate: maxSelectableEndDate,
  });
  const [selectedPreset, setSelectedPreset] = useState<string | null>(
    defaultPreset.id,
  );

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
    const selectedDate = new Date(date);

    if (selectedDate < MIN_START_DATE) {
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
    const latestAllowed = new Date(maxSelectableEndDate);

    if (end <= start) {
      return "투자 종료일은 시작일보다 이후여야 합니다.";
    }
    if (end > latestAllowed) {
      return "투자 종료일은 어제 날짜 이전이어야 합니다.";
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
    setSelectedPreset(null);

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
    setSelectedPreset(null);

    // 실시간 유효성 검증
    const error = validateEndDate(value, config.startDate);
    setErrors((prev) => ({ ...prev, endDate: error }));
  }

  /**
   * 기간 프리셋 선택 시 자동으로 날짜 설정
   */
  function handlePresetSelect(preset: PeriodPreset) {
    const endDate = maxSelectableEndDate;
    let computedStart = subtractMonths(new Date(endDate), preset.months);
    if (computedStart < MIN_START_DATE) {
      computedStart = new Date(MIN_START_DATE);
    }
    const startDate = formatDate(computedStart);

    setConfig((prev) => ({
      ...prev,
      startDate,
      endDate,
    }));
    setSelectedPreset(preset.id);
    setErrors((prev) => ({
      ...prev,
      startDate: validateStartDate(startDate),
      endDate: validateEndDate(endDate, startDate),
    }));
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
      <div className="w-full rounded-[12px] border-[0.5px] border-[#18223433] bg-[#1822340D] p-5 shadow-elev-card-soft">
        {/* 헤더 */}
        <span className="text-[1.25rem] font-semibold text-black">
          백테스트 설정
        </span>
        <p className="mt-2 text-[1rem] text-muted font-normal">
          선택하신 <span className="font-semibold">{message.strategyName}</span> 전략으로
          과거 데이터를 기반으로 테스트해보겠습니다.
        </p>

        {/* 설정 폼 */}
        <div className="mt-5">
          <div className="grid grid-cols-1 gap-10 md:grid-cols-2">
            {/* 투자 금액 */}
            <div>
              <label
                htmlFor="investmentAmount"
                className="block text-[0.875rem] font-semibold text-muted"
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
                className={`mt-1 block w-full rounded-[12px] border-[0.5px] bg-white/40 ${errors.investmentAmount
                  ? "border-price-up"
                  : "border-gray-300"
                  } px-4 py-2 focus:border-brand-purple focus:outline-none`}
                placeholder="예: 5000"
              />
              {errors.investmentAmount && (
                <p className="mt-1 text-[0.75rem] text-price-up">
                  {errors.investmentAmount}
                </p>
              )}
              {!errors.investmentAmount && (
                <p className="mt-1 text-[0.75rem] text-muted">
                  {config.investmentAmount.toLocaleString()}만원 (
                  {(config.investmentAmount * 10000).toLocaleString()}원)
                </p>
              )}
            </div>

            {/* 기간 프리셋 */}
            <div>
              <p className="text-[0.875rem] font-semibold text-muted">빠른 기간 선택</p>
              <div className="mt-1 flex flex-wrap gap-2">
                {PERIOD_PRESETS.map((preset) => {
                  const isActive = selectedPreset === preset.id;
                  return (
                    <button
                      key={preset.id}
                      type="button"
                      onClick={() => handlePresetSelect(preset)}
                      className={`rounded-full px-4 py-2 text-[0.875rem] font-normal text-muted transition ${
                        isActive
                          ? "bg-brand-purple text-white font-semibold"
                          : "bg-white/40 border-[0.5px] border-[#18223433] text-muted font-normal hover:bg-white/80"
                      }`}
                    >
                      {preset.label}
                    </button>
                  );
                })}
              </div>
              {selectedPreset && (
                <p className="mt-1 text-[0.75rem] text-muted">
                  {PERIOD_PRESETS.find((preset) => preset.id === selectedPreset)?.label} 기준으로 자동 설정되었습니다.
                </p>
              )}
            </div>
          </div>
        </div>

        {/* 백테스트 시작 버튼 */}
        <div className="mt-10">
          <button
            onClick={handleStartBacktest}
            disabled={!isFormValid || isSubmitting}
            className={`w-full py-3 rounded-[12px] text-[1.125rem] font-semibold transition-colors ${isFormValid && !isSubmitting
              ? "bg-brand-purple text-white hover:opacity-80"
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
          <p className="mt-3 text-[0.75rem] text-muted text-center">
            ✓ 모든 입력값이 유효합니다. 백테스트를 시작할 수 있습니다.
          </p>
        )}

        {/* API 에러 메시지 */}
        {apiError && (
          <div className="mt-3 rounded-[12px] bg-red-50 border border-red-200 px-4 py-3">
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
