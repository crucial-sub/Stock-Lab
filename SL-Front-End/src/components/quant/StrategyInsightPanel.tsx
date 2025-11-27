"use client";

import { isAxiosError } from "axios";
import { useCallback, useEffect, useMemo, useState } from "react";
import type {
  AutoTradingExecutionReportResponse,
  AutoTradingLog,
  AutoTradingRiskSnapshotResponse,
  RebalancePreviewResponse,
  TradeSignalItem,
} from "@/lib/api/auto-trading";
import { autoTradingApi } from "@/lib/api/auto-trading";

interface StrategySummary {
  id: string;
  strategyId: string;
  title: string;
  isActive: boolean;
}

interface StrategyInsightPanelProps {
  portfolios: StrategySummary[];
  selectedStrategyId: string | null;
  onSelect: (strategyId: string) => void;
}

type Nullable<T> = T | null;

const formatPercent = (value?: number | null, fractionDigits = 2) => {
  if (value === null || value === undefined || Number.isNaN(value)) {
    return "-";
  }
  const sign = value > 0 ? "+" : value < 0 ? "–" : "";
  const abs = Math.abs(value).toFixed(fractionDigits);
  return `${sign}${abs}%`;
};

const formatCurrency = (value?: number | null) => {
  if (value === null || value === undefined || Number.isNaN(value)) {
    return "-";
  }
  // 원화는 정수로 표시 (소수점 반올림)
  return `${Math.round(value).toLocaleString("ko-KR")}원`;
};

export function StrategyInsightPanel({
  portfolios,
  selectedStrategyId,
  onSelect,
}: StrategyInsightPanelProps) {
  const [preview, setPreview] =
    useState<Nullable<RebalancePreviewResponse>>(null);
  const [logs, setLogs] = useState<AutoTradingLog[]>([]);
  const [riskSnapshot, setRiskSnapshot] =
    useState<Nullable<AutoTradingRiskSnapshotResponse>>(null);
  const [executionReport, setExecutionReport] =
    useState<Nullable<AutoTradingExecutionReportResponse>>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const options = useMemo(
    () =>
      portfolios
        .filter((portfolio) => Boolean(portfolio.strategyId))
        .map((portfolio) => ({
          value: portfolio.strategyId,
          label: portfolio.title,
          isActive: portfolio.isActive,
        })),
    [portfolios],
  );

  const selectedPortfolio = portfolios.find(
    (portfolio) => portfolio.strategyId === selectedStrategyId,
  );

  const fetchData = useCallback(async () => {
    if (!selectedStrategyId || !selectedPortfolio?.isActive) {
      setPreview(null);
      setLogs([]);
      setRiskSnapshot(null);
      setExecutionReport(null);
      setError(
        selectedPortfolio?.isActive === false
          ? "가상 매매가 활성화된 전략만 실시간 리포트를 제공합니다."
          : null,
      );
      return;
    }

    setLoading(true);
    setError(null);

    const safeRequest = async <T,>(callback: () => Promise<T>) => {
      try {
        return await callback();
      } catch (err) {
        if (isAxiosError(err) && err.response?.status === 404) {
          return null;
        }
        throw err;
      }
    };

    try {
      const [previewRes, logsRes, riskRes, executionRes] = await Promise.all([
        safeRequest(() =>
          autoTradingApi.getRebalancePreview(selectedStrategyId),
        ),
        safeRequest(() =>
          autoTradingApi.getStrategyLogs(selectedStrategyId, {
            event_type: "ORDER_FILLED",
            limit: 5,
          }),
        ),
        safeRequest(() => autoTradingApi.getRiskSnapshot(selectedStrategyId)),
        safeRequest(() =>
          autoTradingApi.getExecutionReport(selectedStrategyId, 14),
        ),
      ]);

      setPreview(previewRes);
      setLogs(logsRes?.logs ?? []);
      setRiskSnapshot(riskRes);
      setExecutionReport(executionRes);
    } catch (err) {
      console.error("[StrategyInsightPanel] 데이터 로드 실패", err);
      setError("실시간 리포트를 불러오는 중 문제가 발생했습니다.");
    } finally {
      setLoading(false);
    }
  }, [selectedStrategyId, selectedPortfolio?.isActive]);

  useEffect(() => {
    if (selectedStrategyId) {
      fetchData();
    }
  }, [selectedStrategyId, fetchData]);

  const handleSelectChange = (value: string) => {
    onSelect(value);
  };

  const renderSignals = (signals: TradeSignalItem[]) => {
    if (!signals.length) {
      return (
        <p className="text-sm text-muted">
          아직 리밸런싱 시그널이 없습니다. 가상 매매를 실행하면 자동으로
          생성됩니다.
        </p>
      );
    }

    return (
      <ul className="space-y-3">
        {signals.slice(0, 5).map((signal) => (
          <li
            key={signal.stock_code}
            className="flex items-center justify-between rounded-xl border border-slate-100 px-4 py-3"
          >
            <div>
              <p className="text-sm font-semibold text-slate-900">
                {signal.stock_name ?? signal.stock_code}
              </p>
              <p className="text-xs text-slate-500">{signal.stock_code}</p>
            </div>
            <div className="text-right">
              <p className="text-sm font-semibold text-slate-900">
                {signal.quantity ? `${signal.quantity}주` : "-"}
              </p>
              <p className="text-xs text-slate-500">
                {signal.current_price
                  ? `${Math.round(signal.current_price).toLocaleString("ko-KR")}원`
                  : "-"}
              </p>
            </div>
          </li>
        ))}
      </ul>
    );
  };

  const renderLogs = (entries: AutoTradingLog[]) => {
    if (!entries.length) {
      return (
        <p className="text-sm text-muted">주문 체결 로그가 아직 없습니다.</p>
      );
    }

    return (
      <ul className="space-y-2">
        {entries.map((log) => (
          <li
            key={log.log_id}
            className="rounded-xl border border-slate-100 bg-slate-50 px-4 py-3"
          >
            <div className="flex items-center justify-between">
              <span className="text-xs font-semibold uppercase tracking-wide text-slate-500">
                {log.event_type.replace(/_/g, " ")}
              </span>
              <span className="text-xs text-slate-400">
                {new Date(log.created_at).toLocaleTimeString("ko-KR", {
                  hour: "2-digit",
                  minute: "2-digit",
                })}
              </span>
            </div>
            {log.message && (
              <p className="mt-1 text-sm text-slate-900">{log.message}</p>
            )}
          </li>
        ))}
      </ul>
    );
  };

  const renderAlerts = () => {
    if (!riskSnapshot?.alerts?.length) {
      return (
        <p className="text-sm text-muted">
          위험 경고가 없습니다. 안정적으로 운용 중입니다.
        </p>
      );
    }

    return (
      <ul className="space-y-2">
        {riskSnapshot.alerts.map((alert, index) => (
          <li
            key={`${alert.type}-${index}`}
            className={`rounded-xl px-4 py-3 text-sm ${
              alert.severity === "critical"
                ? "bg-red-50 text-red-700"
                : "bg-amber-50 text-amber-700"
            }`}
          >
            {alert.message}
          </li>
        ))}
      </ul>
    );
  };

  return (
    <section className="mt-16">
      <div className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
        <div>
          <h3 className="text-2xl font-bold text-slate-900">
            실시간 전략 리포트
          </h3>
          <p className="text-sm text-slate-500">
            시그널부터 체결, 리스크까지 한눈에 확인하세요.
          </p>
        </div>
        {options.length > 0 && (
          <div className="flex w-full flex-col gap-2 md:w-auto md:flex-row md:items-center">
            <select
              value={selectedStrategyId ?? ""}
              onChange={(event) => handleSelectChange(event.target.value)}
              className="rounded-xl border border-slate-200 bg-white px-4 py-2 text-sm text-slate-900 shadow-sm outline-none focus:border-brand-soft focus:ring-2 focus:ring-brand-soft/30"
            >
              {options.map((option) => (
                <option key={option.value} value={option.value}>
                  {option.label}
                  {!option.isActive ? " · 백테스트" : ""}
                </option>
              ))}
            </select>
            <button
              type="button"
              onClick={fetchData}
              className="rounded-xl border border-slate-200 px-4 py-2 text-sm font-semibold text-slate-700 transition hover:border-slate-300 hover:text-slate-900"
              disabled={loading || !selectedStrategyId}
            >
              새로고침
            </button>
          </div>
        )}
      </div>

      {!options.length ? (
        <div className="mt-6 rounded-2xl bg-slate-50 px-6 py-10 text-center text-sm text-slate-500">
          아직 가상매매로 전환된 전략이 없습니다. 전략을 활성화하면 실시간
          리포트를 확인할 수 있습니다.
        </div>
      ) : !selectedPortfolio?.isActive ? (
        <div className="mt-6 rounded-2xl bg-slate-50 px-6 py-10 text-center text-sm text-slate-500">
          선택한 전략은 아직 가상매매가 시작되지 않았습니다. 키움증권 연동을
          활성화하면 실시간 리포트를 볼 수 있습니다.
        </div>
      ) : (
        <div className="mt-6 grid grid-cols-1 gap-6 lg:grid-cols-12">
          <div className="col-span-12 rounded-3xl border border-slate-100 bg-white/80 p-6 shadow-[0_20px_60px_rgba(15,23,42,0.08)] backdrop-blur">
            {loading ? (
              <p className="text-sm text-slate-400">데이터 불러오는 중...</p>
            ) : error ? (
              <p className="text-sm text-red-500">{error}</p>
            ) : (
              <div className="grid gap-6 lg:grid-cols-12">
                <div className="col-span-12 lg:col-span-5">
                  <div className="mb-4 flex items-center justify-between">
                    <div>
                      <p className="text-xs uppercase tracking-wide text-slate-400">
                        Rebalance Preview
                      </p>
                      <h4 className="text-lg font-semibold text-slate-900">
                        예상 매수 후보
                      </h4>
                    </div>
                    <p className="text-xs text-slate-400">
                      {preview?.generated_at
                        ? new Date(preview.generated_at).toLocaleString(
                            "ko-KR",
                            {
                              month: "short",
                              day: "numeric",
                              hour: "2-digit",
                              minute: "2-digit",
                            },
                          )
                        : "—"}
                    </p>
                  </div>
                  {renderSignals(preview?.candidates ?? [])}
                </div>
                <div className="col-span-12 lg:col-span-7">
                  <div className="mb-4 flex items-center justify-between">
                    <div>
                      <p className="text-xs uppercase tracking-wide text-slate-400">
                        Order Timeline
                      </p>
                      <h4 className="text-lg font-semibold text-slate-900">
                        체결 모니터
                      </h4>
                    </div>
                  </div>
                  {renderLogs(logs)}
                </div>
              </div>
            )}
          </div>

          <div className="col-span-12 lg:col-span-6 rounded-3xl border border-slate-100 bg-white/80 p-6 shadow-[0_20px_60px_rgba(15,23,42,0.08)]">
            <div className="mb-4">
              <p className="text-xs uppercase tracking-wide text-slate-400">
                Risk Monitor
              </p>
              <h4 className="text-lg font-semibold text-slate-900">
                위험 현황
              </h4>
            </div>
            {riskSnapshot ? (
              <div className="space-y-5">
                <div className="grid grid-cols-2 gap-4 text-sm">
                  <div className="rounded-2xl bg-slate-50 p-4">
                    <p className="text-xs uppercase tracking-wide text-slate-400">
                      투자 중 자산
                    </p>
                    <p className="text-lg font-semibold text-slate-900">
                      {formatCurrency(riskSnapshot.invested_value)}
                    </p>
                  </div>
                  <div className="rounded-2xl bg-slate-50 p-4">
                    <p className="text-xs uppercase tracking-wide text-slate-400">
                      현금
                    </p>
                    <p className="text-lg font-semibold text-slate-900">
                      {formatCurrency(riskSnapshot.cash_balance)}
                    </p>
                  </div>
                  <div className="rounded-2xl bg-slate-50 p-4">
                    <p className="text-xs uppercase tracking-wide text-slate-400">
                      총 자산
                    </p>
                    <p className="text-lg font-semibold text-slate-900">
                      {formatCurrency(riskSnapshot.total_value)}
                    </p>
                  </div>
                  <div className="rounded-2xl bg-slate-50 p-4">
                    <p className="text-xs uppercase tracking-wide text-slate-400">
                      투자 비중
                    </p>
                    <p className="text-lg font-semibold text-slate-900">
                      {formatPercent((riskSnapshot.exposure_ratio ?? 0) * 100)}
                    </p>
                  </div>
                </div>
                {renderAlerts()}
              </div>
            ) : (
              <p className="text-sm text-slate-400">
                위험 데이터를 불러오는 중이거나 아직 생성되지 않았습니다.
              </p>
            )}
          </div>

          <div className="col-span-12 lg:col-span-6 rounded-3xl border border-slate-100 bg-white/80 p-6 shadow-[0_20px_60px_rgba(15,23,42,0.08)]">
            <div className="mb-4">
              <p className="text-xs uppercase tracking-wide text-slate-400">
                Execution vs Backtest
              </p>
              <h4 className="text-lg font-semibold text-slate-900">
                실거래 리포트
              </h4>
            </div>
            {executionReport ? (
              <div className="space-y-4">
                <div className="grid grid-cols-2 gap-4 text-sm">
                  <div className="rounded-2xl bg-slate-50 p-4">
                    <p className="text-xs uppercase tracking-wide text-slate-400">
                      누적 실거래 수익률
                    </p>
                    <p className="text-lg font-semibold text-slate-900">
                      {formatPercent(
                        executionReport.summary.cumulative_live_return,
                      )}
                    </p>
                  </div>
                  <div className="rounded-2xl bg-slate-50 p-4">
                    <p className="text-xs uppercase tracking-wide text-slate-400">
                      누적 백테스트 수익률
                    </p>
                    <p className="text-lg font-semibold text-slate-900">
                      {formatPercent(
                        executionReport.summary.cumulative_backtest_return,
                      )}
                    </p>
                  </div>
                  <div className="rounded-2xl bg-slate-50 p-4">
                    <p className="text-xs uppercase tracking-wide text-slate-400">
                      평균 추적 오차
                    </p>
                    <p className="text-lg font-semibold text-slate-900">
                      {formatPercent(
                        executionReport.summary.average_tracking_error,
                      )}
                    </p>
                  </div>
                  <div className="rounded-2xl bg-slate-50 p-4">
                    <p className="text-xs uppercase tracking-wide text-slate-400">
                      실현-기대 차이
                    </p>
                    <p className="text-lg font-semibold text-slate-900">
                      {formatCurrency(
                        executionReport.summary.realized_vs_expected ?? 0,
                      )}
                    </p>
                  </div>
                </div>
                <p className="text-xs text-slate-400">
                  최근 {executionReport.summary.days}거래일 기준
                </p>
              </div>
            ) : (
              <p className="text-sm text-slate-400">
                실거래 리포트가 아직 생성되지 않았습니다.
              </p>
            )}
          </div>
        </div>
      )}
    </section>
  );
}
