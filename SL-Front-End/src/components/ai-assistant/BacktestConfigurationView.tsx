"use client";

import { useMemo, useState } from "react";
import { useRouter } from "next/navigation";
import { runBacktest } from "@/lib/api/backtest";
import type { BacktestConfigurationUILanguage } from "@/lib/api/chatbot";
import type { BacktestRunRequest } from "@/types/api";

interface BacktestConfigurationViewProps {
  uiLanguage: BacktestConfigurationUILanguage;
}

function normalizeInvestment(raw: number): number {
  if (!Number.isFinite(raw)) return 10000; // 기본 1억(만원 단위) 대비 여유치
  // 원 단위로 오는 경우 10,000으로 나눠 만원 단위로 변환
  return raw > 100000 ? Math.round(raw / 10000) : raw;
}

export function BacktestConfigurationView({ uiLanguage }: BacktestConfigurationViewProps) {
  const router = useRouter();
  const [isRunning, setIsRunning] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const preparedConfig = useMemo<BacktestRunRequest | null>(() => {
    if (!uiLanguage.backtest_config) return null;

    const fieldMap = new Map(uiLanguage.configuration_fields.map((f) => [f.field_id, f]));

    const initialCapitalField = fieldMap.get("initial_capital");
    const startField = fieldMap.get("start_date");
    const endField = fieldMap.get("end_date");

    const initialInvestment = normalizeInvestment(Number(initialCapitalField?.default_value ?? 10000000));
    const startDate = (startField?.default_value as string | undefined)?.replace(/-/g, "") ?? "20210101";
    const endDate = (endField?.default_value as string | undefined)?.replace(/-/g, "") ?? "20241231";

    return {
      ...uiLanguage.backtest_config,
      strategy_name: uiLanguage.strategy.strategy_name,
      initial_investment: initialInvestment,
      start_date: startDate,
      end_date: endDate,
    };
  }, [uiLanguage]);

  const handleRun = async () => {
    if (!preparedConfig) {
      setError("백테스트 템플릿이 없습니다. 전략 정보를 다시 불러와 주세요.");
      return;
    }

    setIsRunning(true);
    setError(null);
    try {
      const result = await runBacktest(preparedConfig);
      router.push(`/quant/result/${result.backtestId}`);
    } catch (err) {
      console.error(err);
      const message =
        err instanceof Error ? err.message : "백테스트 실행 중 오류가 발생했습니다.";
      setError(message);
    } finally {
      setIsRunning(false);
    }
  };

  return (
    <div className="w-full max-w-[720px] mx-auto rounded-2xl border border-gray-200 bg-white p-6 shadow-md">
      <div className="flex items-start justify-between gap-3">
        <div>
          <p className="text-sm text-gray-500">전략</p>
          <h2 className="text-2xl font-semibold text-gray-900">{uiLanguage.strategy.strategy_name}</h2>
          <p className="mt-1 text-sm text-gray-600">
            버튼을 누르면 기본 설정(매수/매도 조건, 테마, 포트폴리오 비중)이 한 번에 적용됩니다.
          </p>
        </div>
        <button
          type="button"
          onClick={handleRun}
          disabled={isRunning || !preparedConfig}
          className={`rounded-lg px-4 py-2 text-white font-semibold transition-colors ${
            isRunning || !preparedConfig
              ? "bg-gray-400 cursor-not-allowed"
              : "bg-indigo-600 hover:bg-indigo-700"
          }`}
        >
          {isRunning ? "실행 중..." : "실행하기"}
        </button>
      </div>

      {preparedConfig && (
        <div className="mt-4 grid gap-3 md:grid-cols-2">
          <div className="rounded-lg bg-indigo-50 p-3">
            <p className="text-xs font-semibold text-indigo-700">매수 조건</p>
            <ul className="mt-2 space-y-1 text-sm text-gray-800">
              {preparedConfig.buy_conditions.map((cond) => (
                <li key={cond.name} className="flex gap-2">
                  <span className="text-indigo-600 font-semibold">{cond.name}</span>
                  <span>{cond.exp_left_side} {cond.inequality} {cond.exp_right_side}</span>
                </li>
              ))}
            </ul>
          </div>
          {preparedConfig.condition_sell?.sell_conditions && (
            <div className="rounded-lg bg-rose-50 p-3">
              <p className="text-xs font-semibold text-rose-700">매도 조건</p>
              <ul className="mt-2 space-y-1 text-sm text-gray-800">
                {preparedConfig.condition_sell.sell_conditions.map((cond) => (
                  <li key={cond.name} className="flex gap-2">
                    <span className="text-rose-600 font-semibold">{cond.name}</span>
                    <span>{cond.exp_left_side} {cond.inequality} {cond.exp_right_side}</span>
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>
      )}

      {error && (
        <div className="mt-4 rounded-lg bg-red-50 px-4 py-3 text-sm text-red-700">
          {error}
        </div>
      )}
    </div>
  );
}
