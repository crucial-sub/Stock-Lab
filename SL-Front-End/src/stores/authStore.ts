import { create } from "zustand";

/**
 * 인증 상태 관리 스토어
 * - 세션 만료 모달 상태 관리
 * - 전역적으로 세션 만료 처리
 */
interface AuthStore {
  isSessionExpired: boolean;
  setSessionExpired: (expired: boolean) => void;
  authErrorMessage: string | null;
  setAuthErrorMessage: (message: string | null) => void;
}

export const useAuthStore = create<AuthStore>((set) => ({
  isSessionExpired: false,
  setSessionExpired: (expired: boolean) => set({ isSessionExpired: expired }),
  authErrorMessage: null,
  setAuthErrorMessage: (message: string | null) =>
    set({ authErrorMessage: message }),
}));
