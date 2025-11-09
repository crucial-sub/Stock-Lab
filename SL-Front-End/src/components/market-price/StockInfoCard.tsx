"use client";

import { useState } from "react";

interface StockInfoCardProps {
  name: string;
  code: string;
}

const periodTabs = [
  "30일",
  "90일",
  "120일",
  "180일",
  "1년",
  "2년",
  "3년",
];

const changeStats = [
  { label: "일주일 전", value: "-2,000원 (-2.77%)" },
  { label: "30일 전", value: "38,500원 (+12.75%)" },
  { label: "180일 전", value: "-113,000원 (-30.01%)" },
];

const scoreBreakdowns = [
  { title: "모멘텀", score: 18, caption: "전일 대비 +8점" },
  { title: "펀더멘탈", score: 61, caption: "4주전 대비 +51점" },
];

const overviewStats = [
  { label: "시가총액", value: "589조 39억원" },
  { label: "PSR", value: "1.91배" },
  { label: "PBR", value: "1.48배" },
];

const supplyScores = [
  { title: "외국인 수급 점수", score: 91, caption: "외국인 관심도" },
  { title: "기관 수급점수", score: 2, caption: "기관 관심도" },
];

export function StockInfoCard({ name, code }: StockInfoCardProps) {
  const [activePeriod, setActivePeriod] = useState(periodTabs[0]);

  return (
    <article className="flex flex-col gap-[1.25rem] bg-white p-[2rem] text-text-strong">
      <header className="text-start">
        <p className="text-[0.8rem] text-text-muted font-normal">코스피 | {code}</p>
        <h2 className="text-[1.5rem] font-semibold">{name}</h2>
        <div className="mt-[-0.5rem] text-[1.5rem] font-semibold">265,500원</div>
        <p className="text-brand-primary font-semibold">+2,000원 (0.76%)</p>
        <p className="pt-[0.25rem] text-[0.8rem] text-text-muted font-normal">2025년 12월 31일 기준</p>
      </header>
      <div className="flex flex-wrap justify-center gap-3">
        {periodTabs.map((tab) => {
          const isActive = tab === activePeriod;
          return (
            <button
              key={tab}
              type="button"
              className={`rounded-[8px] px-[0.75rem] py-[0.25rem] text-[1rem] font-normal transition ${
                isActive ? "bg-brand-primary text-white font-semibold" : "text-text-body font-normal"
              }`}
              onClick={() => setActivePeriod(tab)}
            >
              {tab}
            </button>
          );
        })}
      </div>
      <GraphPlaceholder />
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
        감소했어요 🥲
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
          const valueColor = isPositive ? "text-brand-primary" : "text-[#007DFC]";

          return (
            <div key={stat.label} className={`flex flex-col gap-1 ${alignment}`}>
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
        <div className="py-[1rem] flex flex-col gap-6">
          <div className="flex items-center justify-center">
            <DiagnosisCircle score={39} delta={-14} />
          </div>
          <div className="grid gap-6 md:grid-cols-2">
            {scoreBreakdowns.map((item) => (
              <Card key={item.title} title={item.title} value={`${item.score}점`} caption={item.caption} />
            ))}
          </div>
        </div>
      </section>

      <Divider />
      <section className="rounded-[8px]">
        <SectionHeader title="개요" />
        <p className="pt-[0.25rem] text-[0.8rem] font-normal text-text-muted">
          하드웨어 및 장비, 전기 / 전자제품
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
                <p className="text-[0.8rem] font-normal text-text-muted">{stat.label}</p>
                <p className="text-[1.2rem] font-semibold text-text-strong">{stat.value}</p>
              </div>
            );
          })}
        </div>
      </section>

      <Divider />
      <section className="pt-[1rem]">
        <SectionHeader title="수급점수" />
        <p className="pt-[0.25rem] text-[0.8rem] font-normal text-text-muted">
          수급 동향을 점수화했어요
        </p>
        <div className="pt-[1rem] grid gap-4 md:grid-cols-2">
          {supplyScores.map((stat) => (
            <Card key={stat.title} title={stat.title} value={`${stat.score}점`} caption={stat.caption} />
          ))}
        </div>
      </section>
    </article>
  );
}

function Divider() {
  return (
    <div className="h-[1rem] w-full"
      style={{
        backgroundColor: "var(--color-bg-app)",
        marginLeft: "-2rem",
        marginRight: "-2rem",
        width: "calc(100% + 4rem)",
      }}
    />
  );
}

function GraphPlaceholder() {
  return (
    <svg viewBox="0 0 400 100" className="h-32 w-full" role="img" aria-label="주가 추세 그래프">
      <rect width="100%" height="100%" fill="#FFFFFF" />
      <path
        d="M0 60 Q20 50, 40 55 T80 50 T120 52 T160 58 T200 40 T240 35 T280 50 T320 70 T360 80 T400 90"
        fill="none"
        stroke="#FF6464"
        strokeWidth="4"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
      <line x1="0" y1="95" x2="400" y2="95" stroke="#FF6464" strokeDasharray="4 4" strokeWidth="1" />
    </svg>
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

function Card({ title, value, caption }: CardProps) {
  return (
    <div className="rounded-[8px] border border-border py-[1rem] pl-[1rem] text-start">
      <p className="text-[0.9rem] font-normal text-text-muted">{title}</p>
      <p className="pt-[0.5rem] text-[1.5rem] font-semibold text-text-strong">{value}</p>
      {caption && <p className="pt-[0.25rem] text-[0.9rem] font-normal text-text-muted">{caption}</p>}
    </div>
  );
}

interface DiagnosisCircleProps {
  score: number;
  delta: number;
}

function DiagnosisCircle({ score, delta }: DiagnosisCircleProps) {
  const circumference = 2 * Math.PI * 60;
  const progress = (score / 100) * circumference;

  return (
    <div className="relative h-[12rem] w-[12rem]">
      <svg viewBox="0 0 160 160" className="h-full w-full">
        <circle cx="80" cy="80" r="60" fill="none" stroke="#C8C8C8" strokeWidth="10" />
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
        <p className="text-[1.8rem] font-semibold text-text-strong">{score}점</p>
        <p className="text-[0.8rem] font-normal text-text-muted">전일 대비 {delta}점</p>
      </div>
    </div>
  );
}
