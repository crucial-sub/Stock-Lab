"use client";

import { useState } from "react";

/**
 * 백테스트 결과 페이지 - 새 디자인
 *
 * Figma 디자인에 따른 4-탭 레이아웃:
 * - 거래내역 (매매 종목 정보)
 * - 수익률 (누적 수익률 차트)
 * - 매매결과 (통계 정보)
 * - 설정 조건 (매수/매도/매매대상 설정 요약)
 */

interface QuantResultPageClientProps {
  backtestId: string;
}

export function QuantResultPageClientNew({
  backtestId,
}: QuantResultPageClientProps) {
  const [activeTab, setActiveTab] = useState<
    "history" | "returns" | "statistics" | "settings"
  >("history");

  // 모의 데이터
  const mockStats = {
    dailyReturn: "0.06%",
    annualReturn: "15.19%",
    cagr: "15.23%",
    mdd: "3.09%",
    initialCapital: "50,000,000원",
    totalProfit: "7,532,099원",
    finalAssets: "57,32,099원",
  };

  const mockTrades = [
    {
      stock: "화인베스틸",
      days: 2375,
      buyPrice: 3401,
      profitRate: "-4.63",
      buyDate: "2025.10.23",
      sellDate: "2025.10.24",
      returnRate: "9.09",
      profitAmount: "7,703,265",
    },
    // ... 더 많은 거래 데이터
  ];

  return (
    <div className="min-h-screen bg-bg-app py-6 px-6">
      <div className="max-w-[1400px] mx-auto">
        {/* 페이지 제목 */}
        <h1 className="text-[2rem] font-bold text-text-strong mb-6">
          매매 결과
        </h1>

        {/* 통계 섹션 (상단 고정) */}
        <div className="bg-bg-surface rounded-lg shadow-card p-6 mb-6">
          {/* 통계 헤더 */}
          <div className="flex justify-between items-start mb-8">
            {/* 왼쪽: 통계 지표 */}
            <div>
              <h2 className="text-lg font-bold text-text-strong mb-4">통계</h2>
              <div className="grid grid-cols-4 gap-8">
                {/* 일 평균 수익률 */}
                <div>
                  <div className="text-accent-primary text-2xl font-bold mb-1">
                    {mockStats.dailyReturn}
                  </div>
                  <div className="text-sm text-text-body">일 평균 수익률 ⓘ</div>
                </div>

                {/* 누적 수익률 */}
                <div>
                  <div className="text-accent-primary text-2xl font-bold mb-1">
                    {mockStats.annualReturn}
                  </div>
                  <div className="text-sm text-text-body">누적 수익률 ⓘ</div>
                </div>

                {/* CAGR */}
                <div>
                  <div className="text-accent-primary text-2xl font-bold mb-1">
                    {mockStats.cagr}
                  </div>
                  <div className="text-sm text-text-body">CAGR ⓘ</div>
                </div>

                {/* MDD */}
                <div>
                  <div className="text-text-strong text-2xl font-bold mb-1">
                    {mockStats.mdd}
                  </div>
                  <div className="text-sm text-text-body">MDD ⓘ</div>
                </div>
              </div>

              {/* 하단 수치 */}
              <div className="grid grid-cols-3 gap-8 mt-6">
                {/* 투자 원금 */}
                <div>
                  <div className="text-text-strong text-xl font-bold mb-1">
                    {mockStats.initialCapital}
                  </div>
                  <div className="text-sm text-text-body">투자 원금</div>
                </div>

                {/* 총 손익 */}
                <div>
                  <div className="text-accent-primary text-xl font-bold mb-1">
                    {mockStats.totalProfit}
                  </div>
                  <div className="text-sm text-text-body">총 손익 ⓘ</div>
                </div>

                {/* 현재 총 자산 */}
                <div>
                  <div className="text-text-strong text-xl font-bold mb-1">
                    {mockStats.finalAssets}
                  </div>
                  <div className="text-sm text-text-body">현재 총 자산</div>
                </div>
              </div>
            </div>

            {/* 오른쪽: 수익률 차트 (간단한 바 차트) */}
            <div className="w-[500px]">
              <h3 className="text-sm font-semibold text-text-strong mb-3">
                수익률 (%)
              </h3>
              <div className="flex items-end gap-2 h-32">
                {[
                  { label: "최근 거래일", value: -0.37, color: "bg-blue-500" },
                  { label: "최근 월주일", value: -2.13, color: "bg-blue-600" },
                  { label: "최근 1개월", value: -1.85, color: "bg-blue-700" },
                  { label: "최근 3개월", value: -2.38, color: "bg-red-400" },
                  { label: "최근 6개월", value: 8.02, color: "bg-red-500" },
                  { label: "최근 1년", value: 16.15, color: "bg-red-600" },
                ].map((item, i) => (
                  <div key={i} className="flex-1 flex flex-col items-center">
                    <div className="w-full h-24 flex items-end justify-center">
                      <div
                        className={`w-full ${item.color} rounded-t`}
                        style={{
                          height: `${Math.abs(item.value) * 3}px`,
                          minHeight: "4px",
                        }}
                      />
                    </div>
                    <div className="text-xs text-text-body mt-2 text-center">
                      {item.label}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>

        {/* 탭 네비게이션 */}
        <div className="flex gap-3 mb-6">
          <button
            onClick={() => setActiveTab("history")}
            className={`px-6 py-2.5 rounded-sm font-medium transition-colors ${activeTab === "history"
                ? "bg-accent-primary text-white"
                : "bg-bg-surface text-text-body hover:bg-bg-muted"
              }`}
          >
            거래내역
          </button>
          <button
            onClick={() => setActiveTab("returns")}
            className={`px-6 py-2.5 rounded-sm font-medium transition-colors ${activeTab === "returns"
                ? "bg-accent-primary text-white"
                : "bg-bg-surface text-text-body hover:bg-bg-muted"
              }`}
          >
            수익률
          </button>
          <button
            onClick={() => setActiveTab("statistics")}
            className={`px-6 py-2.5 rounded-sm font-medium transition-colors ${activeTab === "statistics"
                ? "bg-accent-primary text-white"
                : "bg-bg-surface text-text-body hover:bg-bg-muted"
              }`}
          >
            매매결과
          </button>
          <button
            onClick={() => setActiveTab("settings")}
            className={`px-6 py-2.5 rounded-sm font-medium transition-colors ${activeTab === "settings"
                ? "bg-accent-primary text-white"
                : "bg-bg-surface text-text-body hover:bg-bg-muted"
              }`}
          >
            설정 조건
          </button>
        </div>

        {/* 탭 컨텐츠 */}
        {activeTab === "history" && (
          <div className="bg-bg-surface rounded-lg shadow-card overflow-hidden">
            {/* 테이블 헤더 */}
            <div className="grid grid-cols-[1fr_100px_100px_100px_120px_120px_100px_120px] gap-4 px-6 py-4 bg-bg-muted border-b border-border-subtle">
              <div className="text-sm font-medium text-text-muted">
                매매 종목명
              </div>
              <div className="text-sm font-medium text-text-muted text-right">
                거래 단가 (원)
              </div>
              <div className="text-sm font-medium text-text-muted text-right">
                수량 (주)
              </div>
              <div className="text-sm font-medium text-text-muted text-right">
                수익률 (%)
              </div>
              <div className="text-sm font-medium text-text-muted text-right">
                매수 일자
              </div>
              <div className="text-sm font-medium text-text-muted text-right">
                매도 일자
              </div>
              <div className="text-sm font-medium text-text-muted text-right">
                보유 비중 (%)
              </div>
              <div className="text-sm font-medium text-text-muted text-right">
                평가 금액 (원)
              </div>
            </div>

            {/* 테이블 바디 */}
            <div>
              {mockTrades.map((trade, idx) => (
                <div
                  key={idx}
                  className="grid grid-cols-[1fr_100px_100px_100px_120px_120px_100px_120px] gap-4 px-6 py-4 border-b border-border-subtle hover:bg-bg-muted transition-colors"
                >
                  <div className="text-text-body">{trade.stock}</div>
                  <div className="text-text-body text-right">{trade.days}</div>
                  <div className="text-text-body text-right">
                    {trade.buyPrice}
                  </div>
                  <div
                    className={`text-right font-semibold ${parseFloat(trade.profitRate) < 0
                        ? "text-accent-primary"
                        : "text-brand-primary"
                      }`}
                  >
                    {trade.profitRate}
                  </div>
                  <div className="text-text-body text-right">
                    {trade.buyDate}
                  </div>
                  <div className="text-text-body text-right">
                    {trade.sellDate}
                  </div>
                  <div className="text-text-body text-right">
                    {trade.returnRate}
                  </div>
                  <div className="text-text-body text-right">
                    {trade.profitAmount}
                  </div>
                </div>
              ))}
            </div>

            {/* 페이지네이션 */}
            <div className="flex items-center justify-center gap-4 py-6">
              <button
                type="button"
                className="w-8 h-8 flex items-center justify-center text-text-muted hover:text-text-body"
              >
                &lt;
              </button>
              <button
                type="button"
                className="w-8 h-8 flex items-center justify-center bg-accent-primary text-white rounded font-medium"
              >
                1
              </button>
              <button
                type="button"
                className="w-8 h-8 flex items-center justify-center text-text-muted hover:text-text-body"
              >
                &gt;
              </button>
            </div>
          </div>
        )}

        {activeTab === "returns" && (
          <div className="bg-bg-surface rounded-lg shadow-card p-6">
            {/* 차트 탭 */}
            <div className="flex gap-3 mb-6">
              {["누적 수익률", "연도별 수익률", "월별 수익률", "종목별 수익률", "총 자산"].map(
                (tab) => (
                  <button
                    key={tab}
                    className="px-4 py-2 text-sm font-medium text-text-body hover:text-text-strong border border-border-default rounded-sm hover:bg-bg-muted transition-colors"
                  >
                    {tab}
                  </button>
                )
              )}
            </div>

            {/* 차트 영역 */}
            <div className="space-y-4">
              <h3 className="text-lg font-bold text-text-strong mb-4">
                누적 수익률
              </h3>
              <div className="flex justify-between items-center mb-2">
                <div className="flex items-center gap-4 text-sm">
                  <span className="flex items-center gap-2">
                    <span className="w-3 h-3 bg-accent-primary rounded-full" />
                    수익률
                  </span>
                  <span className="flex items-center gap-2">
                    <span className="w-3 h-3 bg-orange-500 rounded-full" />
                    KOSPI
                  </span>
                  <span className="flex items-center gap-2">
                    <span className="w-3 h-3 bg-blue-500 rounded-full" />
                    KOSDAQ
                  </span>
                  <span className="flex items-center gap-2">
                    <span className="w-3 h-3 bg-purple-500 rounded-full" />
                    원래전략
                  </span>
                </div>
                <div className="flex gap-2">
                  <button className="px-3 py-1 text-sm border border-border-default rounded-sm hover:bg-bg-muted">
                    일별
                  </button>
                  <button className="px-3 py-1 text-sm border border-border-default rounded-sm hover:bg-bg-muted">
                    로그
                  </button>
                </div>
              </div>

              {/* 플레이스홀더 차트 */}
              <div className="w-full h-96 bg-bg-app rounded-lg border border-border-default flex items-center justify-center">
                <p className="text-text-muted">
                  차트 컴포넌트 (Recharts 또는 Chart.js 사용)
                </p>
              </div>
            </div>
          </div>
        )}

        {activeTab === "statistics" && (
          <div className="bg-bg-surface rounded-lg shadow-card p-6">
            <h3 className="text-lg font-bold text-text-strong mb-6">
              매매 결과 통계
            </h3>

            <div className="grid grid-cols-3 gap-6">
              {/* 왼쪽 섹션 */}
              <div className="space-y-6">
                <div>
                  <div className="text-2xl font-bold text-text-strong mb-1">
                    242일
                  </div>
                  <div className="text-sm text-text-body">총 거래일</div>
                </div>

                <div>
                  <div className="text-2xl font-bold text-text-strong mb-1">
                    2.87%
                  </div>
                  <div className="text-sm text-text-body">
                    수익률에 평균 수익률
                  </div>
                </div>

                <div>
                  <div className="text-2xl font-bold text-text-strong mb-1">
                    0.45
                  </div>
                  <div className="text-sm text-text-body">일 표준편차</div>
                </div>

                <div>
                  <div className="text-2xl font-bold text-text-strong mb-1">
                    1.82
                  </div>
                  <div className="text-sm text-text-body">Sharpe Ratio</div>
                </div>

                <div>
                  <div className="text-2xl font-bold text-text-strong mb-1">
                    73%
                  </div>
                  <div className="text-sm text-text-body">고점 대비 절반 비율</div>
                </div>
              </div>

              {/* 중간 섹션 */}
              <div className="space-y-6">
                <div>
                  <div className="text-2xl font-bold text-text-strong mb-1">
                    5.05일
                  </div>
                  <div className="text-sm text-text-body">평균 보유일</div>
                </div>

                <div>
                  <div className="text-2xl font-bold text-accent-primary mb-1">
                    -2.08%
                  </div>
                  <div className="text-sm text-text-body">
                    손실률에 평균 수익률
                  </div>
                </div>

                <div>
                  <div className="text-2xl font-bold text-text-strong mb-1">
                    1.97
                  </div>
                  <div className="text-sm text-text-body">월 표준편차</div>
                </div>

                <div>
                  <div className="text-2xl font-bold text-text-strong mb-1">
                    1.35%
                  </div>
                  <div className="text-sm text-text-body">월 평균 수익률</div>
                </div>

                <div>
                  <div className="text-2xl font-bold text-text-strong mb-1">
                    0.55
                  </div>
                  <div className="text-sm text-text-body">KOSPI 상관성</div>
                </div>
              </div>

              {/* 오른쪽 섹션 */}
              <div className="space-y-6">
                <div>
                  <div className="text-2xl font-bold text-text-strong mb-1">
                    809회
                  </div>
                  <div className="text-sm text-text-body">총 매매 횟수</div>
                </div>

                <div>
                  <div className="text-2xl font-bold text-text-strong mb-1">
                    1.38
                  </div>
                  <div className="text-sm text-text-body">평균 손익비</div>
                </div>

                <div>
                  <div className="text-2xl font-bold text-text-strong mb-1">
                    1.34
                  </div>
                  <div className="text-sm text-text-body">CPC Index</div>
                </div>

                <div>
                  <div className="text-2xl font-bold text-text-strong mb-1">
                    57% / 0% / 43%
                  </div>
                  <div className="text-sm text-text-body">
                    익절 승률(상승/보합/하락)
                  </div>
                </div>

                <div>
                  <div className="text-2xl font-bold text-text-strong mb-1">
                    0.56
                  </div>
                  <div className="text-sm text-text-body">KOSDAQ 상관성</div>
                </div>
              </div>
            </div>

            {/* 차트 섹션 */}
            <div className="grid grid-cols-3 gap-6 mt-12">
              {/* 매매 성공률 */}
              <div>
                <h4 className="text-base font-semibold text-text-strong mb-4">
                  매매 성공률
                </h4>
                <div className="h-48 bg-bg-app rounded-lg border border-border-default flex items-center justify-center">
                  <p className="text-text-muted">막대 차트</p>
                </div>
              </div>

              {/* 유니버스별 매수 비중 */}
              <div>
                <h4 className="text-base font-semibold text-text-strong mb-4">
                  유니버스별 매수 비중
                </h4>
                <div className="h-48 bg-bg-app rounded-lg border border-border-default flex items-center justify-center">
                  <p className="text-text-muted">막대 차트</p>
                </div>
              </div>

              {/* 매도 조건별 비중 */}
              <div>
                <h4 className="text-base font-semibold text-text-strong mb-4">
                  매도 조건별 비중
                </h4>
                <div className="h-48 bg-bg-app rounded-lg border border-border-default flex items-center justify-center">
                  <p className="text-text-muted">막대 차트</p>
                </div>
              </div>
            </div>
          </div>
        )}

        {activeTab === "settings" && (
          <div className="grid grid-cols-3 gap-6">
            {/* 매수 조건 */}
            <div className="bg-bg-surface rounded-lg shadow-card p-6 border-l-4 border-accent-primary">
              <h3 className="text-lg font-bold text-accent-primary mb-4">
                매수 조건
              </h3>

              <div className="space-y-4">
                <div>
                  <h4 className="text-sm font-semibold text-text-strong mb-2">
                    일반 조건
                  </h4>
                  <div className="space-y-1 text-sm text-text-body">
                    <p>백테스트 데이터 기준: 일봉</p>
                    <p>투자 금액: 5,000만원</p>
                    <p>수수료율: 0.1%</p>
                  </div>
                </div>

                <div>
                  <h4 className="text-sm font-semibold text-text-strong mb-2">
                    매수 조건식
                  </h4>
                  <div className="space-y-1 text-sm text-text-body">
                    <p>A, B</p>
                  </div>
                </div>

                <div>
                  <h4 className="text-sm font-semibold text-text-strong mb-2">
                    투자 시작일
                  </h4>
                  <div className="text-sm text-text-body">2025.12.30</div>
                </div>

                <div>
                  <h4 className="text-sm font-semibold text-text-strong mb-2">
                    매수 비중 설정
                  </h4>
                  <div className="space-y-1 text-sm text-text-body">
                    <p>종목당 매수 비중: 10%</p>
                  </div>
                </div>

                <div>
                  <h4 className="text-sm font-semibold text-text-strong mb-2">
                    매수 방법 선택
                  </h4>
                  <div className="space-y-1 text-sm text-text-body">
                    <p>종목당 매수 금액 (원형식): 0원일</p>
                  </div>
                </div>
              </div>
            </div>

            {/* 매도 조건 */}
            <div className="bg-bg-surface rounded-lg shadow-card p-6 border-l-4 border-blue-500">
              <h3 className="text-lg font-bold text-blue-500 mb-4">
                매도 조건
              </h3>

              <div className="space-y-4">
                <div>
                  <h4 className="text-sm font-semibold text-accent-primary mb-2">
                    목표가 / 손절가 (활성화)
                  </h4>
                  <div className="space-y-1 text-sm text-text-body">
                    <p>목표가 (활성화)</p>
                    <p>매수가 대비 10% 상승</p>
                  </div>
                </div>

                <div>
                  <h4 className="text-sm font-semibold text-accent-primary mb-2">
                    보유 기간 (활성화)
                  </h4>
                  <div className="space-y-1 text-sm text-text-body">
                    <p>최소 종목 보유일: 10일</p>
                    <p>최대 종목 보유일: 10일</p>
                    <p>매도 가격 기준: 전일 종가 기준, 10%</p>
                  </div>
                </div>

                <div>
                  <h4 className="text-sm font-semibold text-accent-primary mb-2">
                    조건 매도 (활성화)
                  </h4>
                  <div className="space-y-1 text-sm text-text-body">
                    <p>매도 조건식 설정: A, B</p>
                    <p>논리 조건식: A and B</p>
                    <p>매도 가격 기준: 전일 종가 기준, 10%</p>
                  </div>
                </div>
              </div>
            </div>

            {/* 매매 대상 */}
            <div className="bg-bg-surface rounded-lg shadow-card p-6 border-l-4 border-green-500">
              <h3 className="text-lg font-bold text-green-500 mb-4">
                매매 대상
              </h3>

              <div className="space-y-4">
                <div>
                  <h4 className="text-sm font-semibold text-text-strong mb-2">
                    매매 대상 종목
                  </h4>
                  <div className="space-y-1 text-sm text-text-body">
                    <p>선택한 매매 대상 종목: 2539 종목</p>
                    <p>전체 종목: 3580 종목</p>
                  </div>
                </div>

                <div>
                  <h4 className="text-sm font-semibold text-text-strong mb-2">
                    선택한 유니버스
                  </h4>
                  <ul className="space-y-1 text-sm text-text-body list-disc list-inside">
                    <li>코스피 대형</li>
                    <li>코스피 중대형</li>
                    <li>코스피 중형</li>
                    <li>코스피 중소형</li>
                    <li>코스피 소형</li>
                    <li>코스피 초소형</li>
                  </ul>
                </div>

                <div>
                  <h4 className="text-sm font-semibold text-text-strong mb-2">
                    선택한 테마
                  </h4>
                  <div className="space-y-1 text-sm text-text-body">
                    <p>선택한 테마 수: 29개</p>
                    <p>전체 테마 수: 29개</p>
                  </div>
                </div>

                <div>
                  <h4 className="text-sm font-semibold text-text-strong mb-2">
                    선택한 세부 종목
                  </h4>
                  <ul className="space-y-1 text-sm text-text-body list-disc list-inside">
                    <li>삼성전자</li>
                    <li>삼성바이오로직스</li>
                    <li>삼성SDI</li>
                    <li>삼성물산</li>
                  </ul>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
