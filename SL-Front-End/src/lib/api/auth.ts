import { clearAuthTokenCookie, setAuthTokenCookie } from "../auth/token";
import { axiosInstance } from "../axios";

export interface UserCreate {
  name: string;
  email: string;
  phone_number: string;
  password: string;
}

export interface UserResponse {
  user_id: string;
  name: string;
  email: string;
  phone_number: string;
  is_active: boolean;
  is_superuser: boolean;
  created_at: string;
  updated_at: string;
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
   */
  logout: async (): Promise<void> => {
    clearAuthTokenCookie();
  },

  /**
   * 현재 로그인한 유저 정보 조회
   */
  getCurrentUser: async (): Promise<UserResponse> => {
    const response = await axiosInstance.get<UserResponse>("/auth/me");
    return response.data;
  },
};
