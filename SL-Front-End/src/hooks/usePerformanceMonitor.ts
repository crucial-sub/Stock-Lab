import { usePerformanceStore } from "@/stores/performanceStore";
import { useQueryClient } from "@tanstack/react-query";
import { useCallback, useEffect, useRef } from "react";

/**
 * 성능 모니터링 훅
 * - FPS 측정: requestAnimationFrame loop
 * - Memory 측정: performance.memory (Chrome only)
 * - Network latency: PerformanceObserver ('resource' entries)
 * - Query stats: queryClient.getQueryCache().getAll()
 */
export function usePerformanceMonitor() {
  const queryClient = useQueryClient();
  const { isEnabled, updateMetrics } = usePerformanceStore();

  // FPS 측정을 위한 ref
  const frameCountRef = useRef(0);
  const lastTimeRef = useRef(performance.now());
  const rafIdRef = useRef<number | null>(null);

  // Network latency 샘플 저장
  const latencySamplesRef = useRef<number[]>([]);

  // FPS 측정 함수
  const measureFPS = useCallback(
    (currentTime: number) => {
      frameCountRef.current++;

      if (currentTime - lastTimeRef.current >= 1000) {
        const fps = Math.round(
          (frameCountRef.current * 1000) / (currentTime - lastTimeRef.current)
        );
        updateMetrics({ fps });
        frameCountRef.current = 0;
        lastTimeRef.current = currentTime;
      }

      rafIdRef.current = requestAnimationFrame(measureFPS);
    },
    [updateMetrics]
  );

  // Memory 측정 함수
  const measureMemory = useCallback(() => {
    // Chrome only API
    const perfWithMemory = performance as Performance & {
      memory?: {
        usedJSHeapSize: number;
        totalJSHeapSize: number;
        jsHeapSizeLimit: number;
      };
    };

    if (perfWithMemory.memory) {
      updateMetrics({
        memory: {
          usedJSHeapSize: perfWithMemory.memory.usedJSHeapSize,
          totalJSHeapSize: perfWithMemory.memory.totalJSHeapSize,
          jsHeapSizeLimit: perfWithMemory.memory.jsHeapSizeLimit,
        },
      });
    }
  }, [updateMetrics]);

  // React Query 상태 측정 함수
  const measureQueryStats = useCallback(() => {
    const queries = queryClient.getQueryCache().getAll();
    const active = queries.filter(
      (q) => q.state.fetchStatus === "fetching"
    ).length;
    const stale = queries.filter((q) => q.isStale()).length;
    const cached = queries.length;

    updateMetrics({
      queryStats: { active, cached, stale },
    });
  }, [queryClient, updateMetrics]);

  // FPS 모니터링 시작/중지
  useEffect(() => {
    if (!isEnabled) {
      if (rafIdRef.current) {
        cancelAnimationFrame(rafIdRef.current);
        rafIdRef.current = null;
      }
      return;
    }

    rafIdRef.current = requestAnimationFrame(measureFPS);

    return () => {
      if (rafIdRef.current) {
        cancelAnimationFrame(rafIdRef.current);
        rafIdRef.current = null;
      }
    };
  }, [isEnabled, measureFPS]);

  // Memory 및 Query Stats 주기적 측정
  useEffect(() => {
    if (!isEnabled) return;

    const intervalId = setInterval(() => {
      measureMemory();
      measureQueryStats();
    }, 1000);

    return () => clearInterval(intervalId);
  }, [isEnabled, measureMemory, measureQueryStats]);

  // Network latency 측정 (PerformanceObserver)
  useEffect(() => {
    if (!isEnabled) return;

    // PerformanceObserver가 지원되지 않는 환경 체크
    if (typeof PerformanceObserver === "undefined") return;

    const observer = new PerformanceObserver((list) => {
      const entries = list.getEntries() as PerformanceResourceTiming[];

      const apiEntries = entries.filter(
        (entry) =>
          entry.initiatorType === "fetch" || entry.initiatorType === "xmlhttprequest"
      );

      if (apiEntries.length > 0) {
        // 새 샘플 추가
        apiEntries.forEach((entry) => {
          latencySamplesRef.current.push(entry.duration);
        });

        // 최근 10개 샘플만 유지
        if (latencySamplesRef.current.length > 10) {
          latencySamplesRef.current = latencySamplesRef.current.slice(-10);
        }

        // 평균 계산
        const avgLatency =
          latencySamplesRef.current.reduce((sum, val) => sum + val, 0) /
          latencySamplesRef.current.length;

        updateMetrics({ networkLatency: Math.round(avgLatency) });
      }
    });

    try {
      observer.observe({ entryTypes: ["resource"] });
    } catch {
      // PerformanceObserver 지원하지 않는 환경
    }

    return () => {
      observer.disconnect();
      latencySamplesRef.current = [];
    };
  }, [isEnabled, updateMetrics]);

  return { isEnabled };
}
