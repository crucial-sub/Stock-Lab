import { create } from "zustand";

/**
 * 인증 상태 관리 스토어
 * - 세션 만료 모달 상태 관리
 * - 전역적으로 세션 만료 처리
 */
interface AuthStore {
  isSessionExpired: boolean;
  setSessionExpired: (expired: boolean) => void;
}

export const useAuthStore = create<AuthStore>((set) => ({
  isSessionExpired: false,
  setSessionExpired: (expired: boolean) => set({ isSessionExpired: expired }),
}));
