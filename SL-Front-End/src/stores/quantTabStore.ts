import { create } from "zustand";

/**
 * 퀀트 전략 생성 페이지의 탭 상태 관리
 * - 매수 조건 / 매도 조건 / 매매 대상 탭 전환
 * - 사이드바와 메인 컨텐츠 간 상태 공유
 */

type TabType = "buy" | "sell" | "target";

interface QuantTabStore {
  activeTab: TabType;
  setActiveTab: (tab: TabType) => void;
}

export const useQuantTabStore = create<QuantTabStore>((set) => ({
  activeTab: "buy",
  setActiveTab: (tab) => set({ activeTab: tab }),
}));
