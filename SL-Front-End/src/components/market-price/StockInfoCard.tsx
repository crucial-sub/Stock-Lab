"use client";

import { useEffect, useState } from "react";
import { type CompanyInfoResponse, companyApi } from "@/lib/api/company";
import { StockPriceChart } from "./StockPriceChart";

interface StockInfoCardProps {
  name: string;
  code: string;
}

const periodTabs = ["30일", "90일", "120일", "180일", "1년", "2년", "3년"];

/**
 * 기간 텍스트를 일 단위 숫자로 변환
 */
function periodToDays(period: string): number {
  if (period.includes("년")) {
    const years = parseInt(period, 10);
    return years * 365;
  }
  return parseInt(period, 10);
}

export function StockInfoCard({ name, code }: StockInfoCardProps) {
  const [activePeriod, setActivePeriod] = useState(periodTabs[0]);
  const [companyData, setCompanyData] = useState<CompanyInfoResponse | null>(
    null,
  );
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchCompanyInfo = async () => {
      try {
        setLoading(true);
        const data = await companyApi.getCompanyInfo(code);
        setCompanyData(data);
      } catch (error) {
        console.error("종목 정보 조회 실패:", error);
      } finally {
        setLoading(false);
      }
    };

    fetchCompanyInfo();
  }, [code]);

  if (loading || !companyData) {
    return <StockInfoSkeleton />;
  }

  const { basicInfo, investmentIndicators } = companyData;

  // 가격 변동 통계 계산
  const changeStats = [
    {
      label: "일주일 전",
      value: basicInfo.changevs1w
        ? `${basicInfo.changevs1w > 0 ? "+" : ""}${basicInfo.changevs1w.toLocaleString()}원 (${basicInfo.changeRate1w?.toFixed(2) || 0}%)`
        : "-",
    },
    {
      label: "30일 전",
      value: basicInfo.changevs1m
        ? `${basicInfo.changevs1m > 0 ? "+" : ""}${basicInfo.changevs1m.toLocaleString()}원 (${basicInfo.changeRate1m?.toFixed(2) || 0}%)`
        : "-",
    },
    {
      label: "60일 전",
      value: basicInfo.changevs2m
        ? `${basicInfo.changevs2m > 0 ? "+" : ""}${basicInfo.changevs2m.toLocaleString()}원 (${basicInfo.changeRate2m?.toFixed(2) || 0}%)`
        : "-",
    },
  ];

  // 시가총액 포맷팅 (1조 미만이면 억 단위만 표시)
  const formatMarketCap = (marketCap: number): string => {
    const trillion = Math.floor(marketCap / 1000000000000);
    const billion = Math.floor((marketCap % 1000000000000) / 100000000);

    if (trillion > 0) {
      return `${trillion}조 ${billion}억원`;
    }
    return `${billion}억원`;
  };

  // PSR 계산 (API에서 안 오면 계산)
  const calculatePSR = (): number | null => {
    if (investmentIndicators.psr) {
      return investmentIndicators.psr;
    }
    // Fallback: 시가총액 / 최근 분기 매출액으로 계산
    if (basicInfo.marketCap && companyData.quarterlyPerformance?.[0]?.revenue) {
      const revenue = companyData.quarterlyPerformance[0].revenue;
      if (revenue && revenue !== 0) {
        return basicInfo.marketCap / revenue;
      }
    }
    return null;
  };

  // PBR 계산 (API에서 안 오면 계산)
  const calculatePBR = (): number | null => {
    if (investmentIndicators.pbr) {
      return investmentIndicators.pbr;
    }
    // Fallback: 시가총액 / 자본총계로 계산
    if (basicInfo.marketCap && companyData.balanceSheets?.[0]?.totalEquity) {
      const totalEquity = companyData.balanceSheets[0].totalEquity;
      if (totalEquity && totalEquity !== 0) {
        return basicInfo.marketCap / totalEquity;
      }
    }
    return null;
  };

  // 개요 통계
  const overviewStats = [
    {
      label: "시가총액",
      value: basicInfo.marketCap ? formatMarketCap(basicInfo.marketCap) : "-",
    },
    {
      label: "PSR",
      value: (() => {
        const psr = calculatePSR();
        return psr ? `${psr.toFixed(2)}배` : "-";
      })(),
    },
    {
      label: "PBR",
      value: (() => {
        const pbr = calculatePBR();
        return pbr ? `${pbr.toFixed(2)}배` : "-";
      })(),
    },
  ];

  return (
    <article className="flex flex-col min-w-[50rem] gap-[1.25rem] bg-white p-[2rem] text-text-strong">
      <header className="text-start">
        <p className="text-[0.8rem] text-text-muted font-normal">
          {basicInfo.marketType || "코스피"} | {code}
        </p>
        <h2 className="text-[1.5rem] font-semibold">{name}</h2>
        <div className="mt-[-0.5rem] text-[1.5rem] font-semibold">
          {basicInfo.currentPrice
            ? `${basicInfo.currentPrice.toLocaleString()}원`
            : "-"}
        </div>
        <p
          className={`font-semibold ${
            (basicInfo.changevs1d || 0) > 0
              ? "text-brand-primary"
              : (basicInfo.changevs1d || 0) < 0
                ? "text-accent-primary"
                : "text-text-muted"
          }`}
        >
          {basicInfo.changevs1d
            ? `${basicInfo.changevs1d > 0 ? "+" : ""}${basicInfo.changevs1d.toLocaleString()}원 (${basicInfo.fluctuationRate?.toFixed(2) || 0}%)`
            : "0원 (0%)"}
        </p>
        <p className="pt-[0.25rem] text-[0.8rem] text-text-muted font-normal">
          {basicInfo.tradeDate
            ? new Date(basicInfo.tradeDate).toLocaleDateString("ko-KR", {
                year: "numeric",
                month: "long",
                day: "numeric",
              })
            : "-"}{" "}
          기준
        </p>
      </header>
      <div className="flex flex-wrap justify-center gap-3">
        {periodTabs.map((tab) => {
          const isActive = tab === activePeriod;
          return (
            <button
              key={tab}
              type="button"
              className={`rounded-[8px] px-[0.75rem] py-[0.25rem] text-[1rem] font-normal transition ${
                isActive
                  ? "bg-brand-primary text-white font-semibold"
                  : "text-text-body font-normal"
              }`}
              onClick={() => setActivePeriod(tab)}
            >
              {tab}
            </button>
          );
        })}
      </div>
      <StockPriceChart
        data={companyData.priceHistory}
        period={periodToDays(activePeriod)}
        isRising={(basicInfo.changevs1d || 0) >= 0}
      />
      <Divider />
      <p className="text-[1rem] text-start font-semibold">
        주가가 일주일 전에 비해{" "}
        <span
          className={
            changeStats[0].value.includes("+")
              ? "text-brand-primary"
              : "text-accent-primary"
          }
        >
          {changeStats[0].value.match(/[-+]?[0-9,.]+%/gu)?.[0] ?? "-"}
        </span>{" "}
        {changeStats[0].value.includes("+") ? "증가했어요 🚀" : "감소했어요 🥲"}
      </p>
      <div className="grid md:grid-cols-3 pt-[0.5rem]">
        {changeStats.map((stat, index) => {
          const alignment =
            index === 0
              ? "items-start text-left"
              : index === 1
                ? "items-center text-center"
                : "items-end text-right";
          const isPositive = stat.value.includes("+");
          const valueColor = isPositive
            ? "text-brand-primary"
            : "text-[#007DFC]";

          return (
            <div
              key={stat.label}
              className={`flex flex-col gap-1 ${alignment}`}
            >
              <span className="text-sm text-[#A0A0A0]">{stat.label}</span>
              <span className={`text-base font-semibold ${valueColor}`}>
                {stat.value}
              </span>
            </div>
          );
        })}
      </div>

      <Divider />
      <section className="rounded-[8px] bg-white">
        <SectionHeader title="종목 진단 점수" helper="?" />
        <div className="py-[1rem] flex items-center justify-center">
          <p className="text-text-muted">종목 진단 점수는 준비 중입니다.</p>
        </div>
      </section>

      <Divider />
      <section className="rounded-[8px]">
        <SectionHeader title="개요" />
        <p className="pt-[0.25rem] text-[0.8rem] font-normal text-text-muted">
          {basicInfo.industry || "산업 정보 없음"}
        </p>
        <div className="pt-[1rem] grid md:grid-cols-3">
          {overviewStats.map((stat, index) => {
            const alignment =
              index === 0
                ? "items-start text-left"
                : index === 1
                  ? "items-center text-center"
                  : "items-end text-right";
            return (
              <div
                key={stat.label}
                className={`flex flex-col gap-1 ${alignment}`}
              >
                <p className="text-[0.8rem] font-normal text-text-muted">
                  {stat.label}
                </p>
                <p className="text-[1.2rem] font-semibold text-text-strong">
                  {stat.value}
                </p>
              </div>
            );
          })}
        </div>
      </section>

      <Divider />
      <section className="pt-[1rem]">
        <SectionHeader title="수급점수" />
        <p className="pt-[0.25rem] text-[0.8rem] font-normal text-text-muted">
          수급점수는 준비 중입니다.
        </p>
      </section>
    </article>
  );
}

function Divider() {
  return (
    <div
      className="h-[1rem] w-full"
      style={{
        backgroundColor: "var(--color-bg-app)",
        marginLeft: "-2rem",
        marginRight: "-2rem",
        width: "calc(100% + 4rem)",
      }}
    />
  );
}

interface SectionHeaderProps {
  title: string;
  helper?: string;
}

function SectionHeader({ title, helper }: SectionHeaderProps) {
  return (
    <div className="flex items-center gap-2">
      <h3 className="text-xl font-semibold text-[#000000]">{title}</h3>
      {helper && <span className="text-sm text-[#A0A0A0]">{helper}</span>}
    </div>
  );
}

interface CardProps {
  title: string;
  value: string;
  caption?: string;
}

function _Card({ title, value, caption }: CardProps) {
  return (
    <div className="rounded-[8px] border border-border py-[1rem] pl-[1rem] text-start">
      <p className="text-[0.9rem] font-normal text-text-muted">{title}</p>
      <p className="pt-[0.5rem] text-[1.5rem] font-semibold text-text-strong">
        {value}
      </p>
      {caption && (
        <p className="pt-[0.25rem] text-[0.9rem] font-normal text-text-muted">
          {caption}
        </p>
      )}
    </div>
  );
}

interface DiagnosisCircleProps {
  score: number;
  delta: number;
}

function _DiagnosisCircle({ score, delta }: DiagnosisCircleProps) {
  const circumference = 2 * Math.PI * 60;
  const progress = (score / 100) * circumference;

  return (
    <div className="relative h-[12rem] w-[12rem]">
      <svg viewBox="0 0 160 160" className="h-full w-full">
        <circle
          cx="80"
          cy="80"
          r="60"
          fill="none"
          stroke="#C8C8C8"
          strokeWidth="10"
        />
        <circle
          cx="80"
          cy="80"
          r="60"
          fill="none"
          stroke="#FF6464"
          strokeWidth="10"
          strokeDasharray={`${progress} ${circumference - progress}`}
          strokeLinecap="round"
          transform="rotate(-90 80 80)"
        />
      </svg>
      <div className="absolute inset-0 flex flex-col items-center justify-center text-center">
        <p className="text-[0.8rem] font-normal text-text-muted">종합점수</p>
        <p className="text-[1.8rem] font-semibold text-text-strong">
          {score}점
        </p>
        <p className="text-[0.8rem] font-normal text-text-muted">
          전일 대비 {delta}점
        </p>
      </div>
    </div>
  );
}

/**
 * 스켈레톤 UI - 데이터 로딩 중에도 실제 콘텐츠와 비슷한 크기의 뼈대를 표시
 */
function StockInfoSkeleton() {
  return (
    <article className="flex flex-col gap-[1.25rem] bg-white p-[2rem] text-text-strong w-[800px]">
      {/* 헤더 스켈레톤 */}
      <header className="text-start">
        <div className="h-4 w-32 bg-gray-200 rounded animate-pulse mb-2" />
        <div className="h-8 w-48 bg-gray-300 rounded animate-pulse mb-2" />
        <div className="h-8 w-40 bg-gray-300 rounded animate-pulse mb-1" />
        <div className="h-6 w-36 bg-gray-200 rounded animate-pulse mb-1" />
        <div className="h-4 w-32 bg-gray-200 rounded animate-pulse" />
      </header>

      {/* 기간 탭 스켈레톤 */}
      <div className="flex flex-wrap justify-center gap-3">
        {Array.from({ length: 7 }).map((_, i) => (
          <div
            key={i}
            className="h-8 w-16 bg-gray-200 rounded-[8px] animate-pulse"
          />
        ))}
      </div>

      {/* 그래프 스켈레톤 */}
      <div className="h-32 w-full bg-gray-100 rounded animate-pulse" />

      <Divider />

      {/* 주가 변동 텍스트 스켈레톤 */}
      <div className="h-6 w-full bg-gray-200 rounded animate-pulse" />

      {/* 가격 변동 통계 스켈레톤 */}
      <div className="grid md:grid-cols-3 pt-[0.5rem] gap-4">
        {Array.from({ length: 3 }).map((_, i) => (
          <div key={i} className="flex flex-col gap-1">
            <div className="h-4 w-20 bg-gray-200 rounded animate-pulse" />
            <div className="h-6 w-32 bg-gray-300 rounded animate-pulse" />
          </div>
        ))}
      </div>

      <Divider />

      {/* 종목 진단 점수 스켈레톤 */}
      <section className="rounded-[8px] bg-white">
        <div className="h-7 w-40 bg-gray-300 rounded animate-pulse mb-4" />
        <div className="py-[1rem] flex items-center justify-center">
          <div className="h-6 w-48 bg-gray-200 rounded animate-pulse" />
        </div>
      </section>

      <Divider />

      {/* 개요 스켈레톤 */}
      <section className="rounded-[8px]">
        <div className="h-7 w-24 bg-gray-300 rounded animate-pulse mb-2" />
        <div className="h-4 w-full bg-gray-200 rounded animate-pulse mb-4" />
        <div className="grid md:grid-cols-3 gap-4">
          {Array.from({ length: 3 }).map((_, i) => (
            <div key={i} className="flex flex-col gap-1">
              <div className="h-4 w-16 bg-gray-200 rounded animate-pulse" />
              <div className="h-6 w-24 bg-gray-300 rounded animate-pulse" />
            </div>
          ))}
        </div>
      </section>

      <Divider />

      {/* 수급점수 스켈레톤 */}
      <section className="pt-[1rem]">
        <div className="h-7 w-32 bg-gray-300 rounded animate-pulse mb-2" />
        <div className="h-4 w-full bg-gray-200 rounded animate-pulse" />
      </section>
    </article>
  );
}
