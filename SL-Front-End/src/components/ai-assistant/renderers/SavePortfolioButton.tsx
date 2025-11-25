/**
 * 백테스트 결과 포트폴리오 저장 버튼 컴포넌트
 *
 * 백테스트 결과를 사용자의 포트폴리오로 저장하는 버튼입니다.
 * - API 호출: POST /backtest/{backtestId}/save-portfolio
 * - 로딩 상태 표시
 * - 성공/에러 메시지 표시
 *
 * 참조: 2025-01-19-ai-assistant-backtest-execution-plan.md 섹션 8.4
 */

"use client";

import { savePortfolio } from "@/lib/api/backtest";
import { AxiosError } from "axios";
import { useState } from "react";

/**
 * SavePortfolioButton Props
 */
interface SavePortfolioButtonProps {
  /** 백테스트 ID */
  backtestId: string;
  /** 전략명 (포트폴리오 이름으로 사용) */
  strategyName?: string;
  /** 사용자명 */
  userName?: string;
}

/**
 * 전략명 축약 함수
 * "캐시 우드의 전략" -> "캐시우드"
 * "피터린치의 전략" -> "피터린치"
 */
function abbreviateStrategyName(name: string): string {
  return name
    .replace(/의\s*전략$/g, "") // "의 전략" 제거
    .replace(/\s+/g, ""); // 공백 제거
}

/**
 * 포트폴리오 이름 생성 함수
 * 형식: {userName}_{전략명 축약}_{MMDD}
 * 예: 박중섭_캐시우드_1125
 */
function generatePortfolioName(userName: string, strategyName: string): string {
  const abbreviatedName = abbreviateStrategyName(strategyName);
  const now = new Date();
  const month = String(now.getMonth() + 1).padStart(2, "0");
  const day = String(now.getDate()).padStart(2, "0");
  return `${userName}_${abbreviatedName}_${month}${day}`;
}

/**
 * 백테스트 결과를 포트폴리오로 저장하는 버튼 컴포넌트
 *
 * - 클릭 시 API 호출하여 포트폴리오 저장
 * - 로딩 중에는 버튼 비활성화 및 로딩 스피너 표시
 * - 성공/에러 메시지를 버튼 아래에 표시
 *
 * @example
 * ```tsx
 * function BacktestResult() {
 *   return <SavePortfolioButton backtestId="bt_123abc" />;
 * }
 * ```
 */
export function SavePortfolioButton({ backtestId, strategyName, userName }: SavePortfolioButtonProps) {
  const [loading, setLoading] = useState(false);
  const [success, setSuccess] = useState(false);
  const [error, setError] = useState<string | null>(null);

  /**
   * 포트폴리오 저장 핸들러
   */
  const handleSave = async () => {
    try {
      setLoading(true);
      setError(null);
      setSuccess(false);

      // 포트폴리오 이름 생성: {userName}_{전략명 축약}_{MMDD}
      // 예: "박중섭_캐시우드_1125"
      const portfolioName =
        userName && strategyName
          ? generatePortfolioName(userName, strategyName)
          : strategyName
            ? abbreviateStrategyName(strategyName)
            : undefined;

      // API 호출 (포트폴리오 이름 전달)
      const response = await savePortfolio(backtestId, portfolioName);

      // 성공 처리
      setSuccess(true);
      console.log("[SavePortfolioButton] 저장 완료:", response.message);

      // 3초 후 성공 메시지 제거
      setTimeout(() => {
        setSuccess(false);
      }, 3000);
    } catch (err) {
      // 에러 처리
      const axiosError = err as AxiosError<any>;
      const detail =
        axiosError.response?.data?.detail ||
        axiosError.response?.data?.message ||
        axiosError.message;
      const errorMessage =
        detail ||
        (err instanceof Error
          ? err.message
          : "포트폴리오 저장 중 오류가 발생했습니다.");
      setError(errorMessage);
      console.error("[SavePortfolioButton] 저장 실패:", err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex flex-col items-center gap-2">
      {/* 저장 버튼 */}
      <button
        onClick={handleSave}
        disabled={loading || success}
        className={[
          "px-6 py-3 rounded-lg font-medium text-white transition-all duration-200 mb-6",
          loading || success
            ? "bg-gray-400 cursor-not-allowed"
            : "bg-brand-purple hover:bg-brand-purple-dark active:scale-95",
        ].join(" ")}
        aria-label="백테스트 결과를 포트폴리오로 저장"
      >
        {loading ? (
          <span className="flex items-center gap-2">
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
            저장 중...
          </span>
        ) : success ? (
          <span className="flex items-center gap-2">
            <svg
              className="h-5 w-5"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M5 13l4 4L19 7"
              />
            </svg>
            저장 완료!
          </span>
        ) : (
          "포트폴리오로 저장"
        )}
      </button>

      {/* 성공 메시지 */}
      {success && (
        <p className="text-sm text-green-600 font-medium animate-fade-in">
          ✓ 포트폴리오에 저장되었습니다
        </p>
      )}

      {/* 에러 메시지 */}
      {error && (
        <p className="text-sm text-red-600 font-medium animate-fade-in">
          ✗ {error}
        </p>
      )}
    </div>
  );
}
