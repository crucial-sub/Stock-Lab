/**
 * 백테스트 결과 메시지 렌더러
 *
 * 백테스트 통계, 차트, 요약을 렌더링
 */

"use client";

import type { BacktestResultMessage } from "@/types/message";

interface BacktestResultRendererProps {
  message: BacktestResultMessage;
}

/**
 * 백테스트 결과를 렌더링하는 컴포넌트
 */
export function BacktestResultRenderer({ message }: BacktestResultRendererProps) {
  const { statistics, summary } = message.results;

  return (
    <div className="flex justify-start mb-6">
      <div className="max-w-[95%] w-full rounded-2xl border border-gray-200 bg-white shadow-sm overflow-hidden">
        {/* 제목 */}
        <div className="px-5 py-4 border-b border-gray-200">
          <h3 className="text-lg font-bold text-gray-900">
            백테스트 결과 📊
          </h3>
        </div>

        {/* 통계 카드 */}
        <div className="px-5 py-4">
          <div className="grid grid-cols-2 gap-4">
            <div className="bg-gray-50 rounded-lg p-4">
              <p className="text-xs text-gray-600">누적 수익률</p>
              <p className="text-2xl font-bold text-gray-900 mt-1">
                {statistics.total_return.toFixed(2)}%
              </p>
            </div>

            <div className="bg-gray-50 rounded-lg p-4">
              <p className="text-xs text-gray-600">연평균 수익률 (CAGR)</p>
              <p className="text-2xl font-bold text-gray-900 mt-1">
                {statistics.cagr.toFixed(2)}%
              </p>
            </div>

            <div className="bg-gray-50 rounded-lg p-4">
              <p className="text-xs text-gray-600">최대 낙폭 (MDD)</p>
              <p className="text-2xl font-bold text-red-600 mt-1">
                {statistics.mdd.toFixed(2)}%
              </p>
            </div>

            <div className="bg-gray-50 rounded-lg p-4">
              <p className="text-xs text-gray-600">총 손익</p>
              <p
                className={[
                  "text-2xl font-bold mt-1",
                  statistics.profit >= 0 ? "text-blue-600" : "text-red-600",
                ].join(" ")}
              >
                {statistics.profit >= 0 ? "+" : ""}
                {(statistics.profit / 10000).toFixed(0)}만원
              </p>
            </div>
          </div>

          {/* 요약 */}
          <div className="mt-6">
            <h4 className="text-sm font-semibold text-gray-900 mb-2">
              분석 요약
            </h4>
            <ul className="space-y-2">
              {summary.map((item, index) => (
                <li key={index} className="text-sm text-gray-700 flex items-start gap-2">
                  <span className="text-purple-600 mt-1">•</span>
                  <span>{item}</span>
                </li>
              ))}
            </ul>
          </div>

          {/* TODO: 차트 렌더링 (추후 구현) */}
          <div className="mt-6 bg-gray-100 rounded-lg p-8 text-center text-gray-500">
            차트 렌더링 (추후 구현)
          </div>
        </div>
      </div>
    </div>
  );
}
