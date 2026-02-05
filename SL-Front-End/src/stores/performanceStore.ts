import { create } from "zustand";

/**
 * 성능 메트릭 타입
 */
export interface PerformanceMetrics {
  fps: number;
  memory: {
    usedJSHeapSize: number;
    totalJSHeapSize: number;
    jsHeapSizeLimit: number;
  } | null;
  networkLatency: number;
  queryStats: {
    active: number;
    cached: number;
    stale: number;
  };
}

/**
 * 성능 모니터링 스토어
 * - 개발 모드에서만 활성화
 * - FPS, 메모리, 네트워크 latency, React Query 상태를 추적
 */
interface PerformanceStore {
  isEnabled: boolean;
  metrics: PerformanceMetrics;
  toggleEnabled: () => void;
  updateMetrics: (partial: Partial<PerformanceMetrics>) => void;
  resetMetrics: () => void;
}

const initialMetrics: PerformanceMetrics = {
  fps: 0,
  memory: null,
  networkLatency: 0,
  queryStats: {
    active: 0,
    cached: 0,
    stale: 0,
  },
};

export const usePerformanceStore = create<PerformanceStore>((set) => ({
  isEnabled: false,
  metrics: initialMetrics,

  toggleEnabled: () => set((state) => ({ isEnabled: !state.isEnabled })),

  updateMetrics: (partial) =>
    set((state) => ({
      metrics: { ...state.metrics, ...partial },
    })),

  resetMetrics: () => set({ metrics: initialMetrics }),
}));
