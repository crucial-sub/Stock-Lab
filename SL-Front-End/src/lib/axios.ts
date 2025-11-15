/**
 * Axios 인스턴스 설정
 * - API 요청을 위한 기본 설정을 구성합니다
 * - baseURL, timeout, headers 등을 설정합니다
 * - 요청/응답 인터셉터를 통해 공통 로직을 처리합니다
 */

import axios from "axios";
import { getAuthTokenFromCookie } from "./auth/token";

/**
 * Axios 기본 인스턴스
 * - 서버/클라이언트 환경 모두에서 사용 가능합니다
 * - baseURL은 환경변수에서 가져옵니다
 */
export const axiosInstance = axios.create({
  baseURL: process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000/api/v1",
  timeout: 30000, // 30초
  headers: {
    "Content-Type": "application/json",
  },
  // 쿠키를 포함한 요청을 위해 credentials 설정
  withCredentials: true,
});

/**
 * 요청 인터셉터
 * - 요청 전에 공통 로직을 처리합니다
 * - 예: 인증 토큰 추가, 로깅 등
 */
axiosInstance.interceptors.request.use(
  (config) => {
    // 요청 전 처리 (예: 토큰 추가)
    const token = getAuthTokenFromCookie();
    if (token) {
      config.headers = config.headers ?? {};
      config.headers.Authorization = `Bearer ${token}`;
    }

    return config;
  },
  (error) => {
    return Promise.reject(error);
  },
);

/**
 * 응답 인터셉터
 * - 응답 후 공통 로직을 처리합니다
 * - 에러 핸들링, 로깅 등을 수행합니다
 */
axiosInstance.interceptors.response.use(
  (response) => {
    // 성공 응답 처리
    return response;
  },
  (error) => {
    // 에러 응답 처리
    if (error.response) {
      // 서버가 응답을 반환한 경우
      const { status, data, config } = error.response;
      const requestUrl = config?.url || '';

      // /auth/me 요청의 401/403 에러는 로그 출력 안 함 (정상적인 비로그인 상태)
      const isAuthMeRequest = requestUrl.includes('/auth/me');
      const isAuthError = status === 401 || status === 403;

      if (isAuthMeRequest && isAuthError) {
        // 로그인하지 않은 상태에서의 정상적인 에러이므로 무시
        return Promise.reject(error);
      }

      // 401 에러: 인증 실패
      if (status === 401) {
        // 로그인 페이지로 리다이렉트 등의 처리
        console.error("인증 실패:", data);
      }

      // 403 에러: 권한 없음
      if (status === 403) {
        console.error("권한 없음:", data);
      }

      // 500 에러: 서버 오류
      if (status >= 500) {
        console.error("서버 오류:", data);
      }
    } else if (error.request) {
      // 요청은 보냈지만 응답을 받지 못한 경우
      console.error("네트워크 오류:", error.request);
    } else {
      // 요청 설정 중에 오류가 발생한 경우
      console.error("요청 오류:", error.message);
    }

    return Promise.reject(error);
  },
);

/**
 * 서버 사이드에서만 사용하는 Axios 인스턴스
 * - SSR 환경에서 사용합니다
 * - 서버 내부 URL을 사용할 수 있습니다
 */
export const axiosServerInstance = axios.create({
  baseURL: process.env.API_BASE_URL ?? process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000/api/v1",
  timeout: 30000,
  headers: {
    "Content-Type": "application/json",
  },
});

// 서버 인스턴스에도 동일한 인터셉터 적용
axiosServerInstance.interceptors.request.use(
  (config) => {
    return config;
  },
  (error) => {
    return Promise.reject(error);
  },
);

axiosServerInstance.interceptors.response.use(
  (response) => {
    return response;
  },
  (error) => {
    if (error.response) {
      const { status, data } = error.response;

      if (status === 401) {
        console.error("인증 실패:", data);
      }

      if (status === 403) {
        console.error("권한 없음:", data);
      }

      if (status >= 500) {
        console.error("서버 오류:", data);
      }
    } else if (error.request) {
      console.error("네트워크 오류:", error.request);
    } else {
      console.error("요청 오류:", error.message);
    }

    return Promise.reject(error);
  },
);
