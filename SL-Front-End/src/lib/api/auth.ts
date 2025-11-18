import { clearAuthTokenCookie, setAuthTokenCookie } from "../auth/token";
import { axiosInstance } from "../axios";

export interface UserCreate {
  name: string;
  nickname: string;
  email: string;
  phone_number: string;
  password: string;
}

export interface UserResponse {
  user_id: string;
  name: string;
  nickname: string;
  email: string;
  phone_number: string;
  is_active: boolean;
  is_superuser: boolean;
  created_at: string;
  updated_at?: string;
  has_kiwoom_account?: boolean;
}

export interface Token {
  access_token: string;
  token_type: string;
}

export interface LoginRequest {
  email: string;
  password: string;
}

export const authApi = {
  /**
   * 회원가입
   */
  register: async (data: UserCreate): Promise<UserResponse> => {
    const response = await axiosInstance.post<UserResponse>(
      "/auth/register",
      data,
    );
    return response.data;
  },

  /**
   * 로그인
   */
  login: async (credentials: LoginRequest): Promise<Token> => {
    const response = await axiosInstance.post<Token>("/auth/login", null, {
      params: credentials, // 쿼리 파라미터로 전달
    });

    setAuthTokenCookie(response.data.access_token);
    return response.data;
  },

  /**
   * 로그아웃
   *
   * @description
   * 1. 백엔드에 로그아웃 요청 (Redis 있으면 토큰 블랙리스트 추가)
   * 2. 클라이언트 쿠키에서 토큰 삭제
   *
   * Redis가 없어도 작동하도록 설계됨 (Graceful degradation)
   */
  logout: async (): Promise<void> => {
    try {
      // 백엔드 로그아웃 엔드포인트 호출 (Redis 블랙리스트)
      await axiosInstance.post("/auth/logout");
    } catch (error) {
      // 백엔드 에러는 무시하고 계속 진행 (클라이언트 측 로그아웃은 항상 성공)
      console.warn("Backend logout failed, proceeding with client-side logout:", error);
    } finally {
      // 항상 클라이언트 쿠키 삭제
      clearAuthTokenCookie();
    }
  },

  /**
   * 현재 로그인한 유저 정보 조회
   */
  getCurrentUser: async (): Promise<UserResponse> => {
    const response = await axiosInstance.get<UserResponse>("/auth/me");
    return response.data;
  },

  /**
   * 현재 로그인한 유저 정보 조회 (서버 사이드)
   */
  getCurrentUserServer: async (token: string): Promise<UserResponse> => {
    const axios = (await import("axios")).default;
    const baseURL = process.env.NEXT_PUBLIC_API_URL || "http://sl_backend_dev:8000";
    const response = await axios.get<UserResponse>(
      `${baseURL}/api/v1/auth/me`,
      {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      },
    );
    return response.data;
  },

  /**
   * 닉네임 중복 확인
   */
  checkNickname: async (nickname: string): Promise<{ nickname: string; available: boolean }> => {
    const response = await axiosInstance.get(`/auth/check-nickname/${nickname}`);
    return response.data;
  },

  /**
   * 닉네임 변경
   */
  updateNickname: async (newNickname: string): Promise<UserResponse> => {
    const response = await axiosInstance.patch<UserResponse>(
      "/auth/update-nickname",
      null,
      { params: { new_nickname: newNickname } }
    );
    return response.data;
  },

  /**
   * 비밀번호 변경
   */
  updatePassword: async (data: { current_password: string; new_password: string }): Promise<{ message: string; email: string }> => {
    const response = await axiosInstance.patch("/auth/update-password", data);
    return response.data;
  },

  /**
   * 회원탈퇴
   */
  deleteAccount: async (data: { email: string; password: string; phone_number: string }): Promise<{ message: string; email: string }> => {
    const response = await axiosInstance.delete("/auth/delete-account", {
      data
    });
    return response.data;
  },
};
