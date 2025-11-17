"use client";

interface PerformanceChartSectionProps {
  title?: string;
}

export function PerformanceChartSection({
}: PerformanceChartSectionProps) {
  return (
    <section className="flex w-full flex-col gap-4">
      <div className="rounded-[12px] border border-[#18223433] bg-white p-6 shadow-elev-card">
        <div className="h-64 w-full">
          <svg
            viewBox="0 0 400 160"
            preserveAspectRatio="none"
            className="h-full w-full text-brand"
          >
            <polyline
              fill="none"
              stroke="currentColor"
              strokeWidth="3"
              points="0,120 40,100 80,110 120,80 160,70 200,90 240,60 280,70 320,40 360,80 400,50"
            />
            <line
              x1="0"
              y1="150"
              x2="400"
              y2="150"
              stroke="#F5A3B7"
              strokeWidth="2"
              strokeDasharray="6 6"
            />
          </svg>
        </div>
      </div>
    </section>
  );
}
