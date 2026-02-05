"use client";

import { usePerformanceStore } from "@/stores/performanceStore";
import { usePerformanceMonitor } from "@/hooks/usePerformanceMonitor";

/**
 * 성능 대시보드 컴포넌트
 * - 개발 모드에서만 렌더링
 * - FPS (color-coded: green >=55, yellow >=30, red <30)
 * - Memory bar (used/limit)
 * - API Latency (ms)
 * - React Query stats (Active/Cached/Stale)
 */
export function PerformanceDashboard() {
  // 개발 모드에서만 렌더링
  if (process.env.NODE_ENV !== "development") {
    return null;
  }

  return <PerformanceDashboardContent />;
}

function PerformanceDashboardContent() {
  const { isEnabled, metrics, toggleEnabled } = usePerformanceStore();

  // 성능 모니터링 훅 활성화
  usePerformanceMonitor();

  // FPS 색상 결정
  const getFpsColor = (fps: number) => {
    if (fps >= 55) return "text-green-500";
    if (fps >= 30) return "text-yellow-500";
    return "text-red-500";
  };

  // 메모리 사용률 계산
  const getMemoryUsage = () => {
    if (!metrics.memory) return null;
    const { usedJSHeapSize, jsHeapSizeLimit } = metrics.memory;
    const percentage = (usedJSHeapSize / jsHeapSizeLimit) * 100;
    return {
      used: (usedJSHeapSize / 1024 / 1024).toFixed(1),
      limit: (jsHeapSizeLimit / 1024 / 1024).toFixed(0),
      percentage,
    };
  };

  const memoryUsage = getMemoryUsage();

  // 메모리 바 색상
  const getMemoryBarColor = (percentage: number) => {
    if (percentage >= 80) return "bg-red-500";
    if (percentage >= 60) return "bg-yellow-500";
    return "bg-green-500";
  };

  return (
    <>
      {/* Toggle Button */}
      <button
        type="button"
        onClick={toggleEnabled}
        className="fixed bottom-4 right-4 z-50 w-10 h-10 rounded-full bg-gray-800 text-white flex items-center justify-center shadow-lg hover:bg-gray-700 transition-colors"
        title="성능 대시보드 토글"
      >
        <span className="text-sm">📊</span>
      </button>

      {/* Dashboard Panel */}
      {isEnabled && (
        <div className="fixed bottom-16 right-4 z-50 w-64 bg-gray-900 text-white rounded-lg shadow-xl p-4 font-mono text-xs">
          <div className="flex items-center justify-between mb-3">
            <h3 className="font-semibold text-sm">Performance</h3>
            <span className="text-gray-400 text-[10px]">DEV</span>
          </div>

          {/* FPS */}
          <div className="mb-3">
            <div className="flex items-center justify-between mb-1">
              <span className="text-gray-400">FPS</span>
              <span className={`font-bold ${getFpsColor(metrics.fps)}`}>
                {metrics.fps}
              </span>
            </div>
            <div className="h-1.5 bg-gray-700 rounded-full overflow-hidden">
              <div
                className={`h-full transition-all duration-300 ${getFpsColor(metrics.fps).replace("text-", "bg-")}`}
                style={{ width: `${Math.min(100, (metrics.fps / 60) * 100)}%` }}
              />
            </div>
          </div>

          {/* Memory */}
          {memoryUsage && (
            <div className="mb-3">
              <div className="flex items-center justify-between mb-1">
                <span className="text-gray-400">Memory</span>
                <span className="text-gray-300">
                  {memoryUsage.used}MB / {memoryUsage.limit}MB
                </span>
              </div>
              <div className="h-1.5 bg-gray-700 rounded-full overflow-hidden">
                <div
                  className={`h-full transition-all duration-300 ${getMemoryBarColor(memoryUsage.percentage)}`}
                  style={{ width: `${memoryUsage.percentage}%` }}
                />
              </div>
            </div>
          )}

          {/* API Latency */}
          <div className="mb-3">
            <div className="flex items-center justify-between">
              <span className="text-gray-400">API Latency</span>
              <span
                className={
                  metrics.networkLatency > 500
                    ? "text-red-400"
                    : metrics.networkLatency > 200
                      ? "text-yellow-400"
                      : "text-green-400"
                }
              >
                {metrics.networkLatency}ms
              </span>
            </div>
          </div>

          {/* React Query Stats */}
          <div>
            <div className="text-gray-400 mb-1.5">React Query</div>
            <div className="grid grid-cols-3 gap-2 text-center">
              <div className="bg-gray-800 rounded px-2 py-1.5">
                <div className="text-blue-400 font-bold">
                  {metrics.queryStats.active}
                </div>
                <div className="text-gray-500 text-[10px]">Active</div>
              </div>
              <div className="bg-gray-800 rounded px-2 py-1.5">
                <div className="text-green-400 font-bold">
                  {metrics.queryStats.cached}
                </div>
                <div className="text-gray-500 text-[10px]">Cached</div>
              </div>
              <div className="bg-gray-800 rounded px-2 py-1.5">
                <div className="text-yellow-400 font-bold">
                  {metrics.queryStats.stale}
                </div>
                <div className="text-gray-500 text-[10px]">Stale</div>
              </div>
            </div>
          </div>
        </div>
      )}
    </>
  );
}
