# 프론트엔드 인증 구현 가이드

Stock-Lab 백엔드 API와 연동하기 위한 프론트엔드 인증 구현 가이드입니다.

## 목차
1. [Quick Start](#quick-start)
2. [API 엔드포인트 요약](#api-엔드포인트-요약)
3. [TypeScript 타입 정의](#typescript-타입-정의)
4. [토큰 관리](#토큰-관리)
5. [API 클라이언트 설정](#api-클라이언트-설정)
6. [React/Next.js 구현 예시](#reactnextjs-구현-예시)
7. [에러 처리](#에러-처리)
8. [보안 고려사항](#보안-고려사항)
9. [실전 팁](#실전-팁)

---

## Quick Start

### 1. 환경 변수 설정

```env
# .env.local (Next.js)
NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1
```

### 2. 필요한 패키지 설치

```bash
npm install axios
# 또는
yarn add axios
```

---

## API 엔드포인트 요약

| 메서드 | 엔드포인트 | 설명 | 인증 필요 |
|--------|-----------|------|----------|
| POST | `/auth/register` | 회원가입 | ❌ |
| POST | `/auth/login` | 로그인 | ❌ |
| GET | `/auth/me` | 현재 유저 정보 조회 | ✅ |
| GET | `/auth/users/{user_id}` | 특정 유저 정보 조회 | ✅ |

### 베이스 URL
```
http://localhost:8000/api/v1
```

---

## TypeScript 타입 정의

```typescript
// types/auth.ts

// 유저 정보
export interface User {
  id: string; // UUID
  name: string;
  email: string;
  phone_number: string;
  is_active: boolean;
  is_superuser: boolean;
  created_at: string;
}

// 회원가입 요청
export interface RegisterRequest {
  name: string;
  email: string;
  phone_number: string; // 숫자만, 10-20자
  password: string; // 최소 8자
}

// 로그인 요청
export interface LoginRequest {
  email: string;
  password: string;
}

// 토큰 응답
export interface TokenResponse {
  access_token: string;
  token_type: "bearer";
}

// API 에러 응답
export interface ApiError {
  detail: string;
}

// 유효성 검증 에러
export interface ValidationError {
  detail: Array<{
    loc: string[];
    msg: string;
    type: string;
  }>;
}
```

---

## 토큰 관리

### 토큰 저장 방식 비교

| 방식 | 보안성 | 지속성 | 사용 케이스 |
|------|--------|--------|------------|
| `localStorage` | 중간 | 브라우저 종료 후에도 유지 | 일반적인 웹앱 |
| `sessionStorage` | 중간 | 탭 닫으면 삭제 | 보안이 중요한 경우 |
| `httpOnly Cookie` | 높음 | 서버에서 설정 필요 | 프로덕션 권장 |
| `메모리 (상태)` | 높음 | 새로고침 시 삭제 | 매우 민감한 데이터 |

### 토큰 유틸리티 함수

```typescript
// utils/auth.ts

const TOKEN_KEY = 'access_token';

export const tokenStorage = {
  // 토큰 저장
  set: (token: string): void => {
    localStorage.setItem(TOKEN_KEY, token);
  },

  // 토큰 가져오기
  get: (): string | null => {
    return localStorage.getItem(TOKEN_KEY);
  },

  // 토큰 삭제
  remove: (): void => {
    localStorage.removeItem(TOKEN_KEY);
  },

  // 토큰 존재 여부
  exists: (): boolean => {
    return !!localStorage.getItem(TOKEN_KEY);
  }
};

// Authorization 헤더 생성
export const getAuthHeader = (): string | null => {
  const token = tokenStorage.get();
  return token ? `Bearer ${token}` : null;
};
```

---

## API 클라이언트 설정

### Axios 인스턴스 생성

```typescript
// lib/api.ts
import axios, { AxiosError, AxiosInstance, InternalAxiosRequestConfig } from 'axios';
import { tokenStorage } from '@/utils/auth';

// Axios 인스턴스 생성
export const api: AxiosInstance = axios.create({
  baseURL: process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1',
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// 요청 인터셉터: 모든 요청에 토큰 자동 추가
api.interceptors.request.use(
  (config: InternalAxiosRequestConfig) => {
    const token = tokenStorage.get();
    if (token && config.headers) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error: AxiosError) => {
    return Promise.reject(error);
  }
);

// 응답 인터셉터: 401 에러 시 자동 로그아웃
api.interceptors.response.use(
  (response) => response,
  (error: AxiosError) => {
    if (error.response?.status === 401) {
      // 토큰 만료 또는 유효하지 않음
      tokenStorage.remove();
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);
```

### 인증 API 함수

```typescript
// services/auth.service.ts
import { api } from '@/lib/api';
import {
  User,
  RegisterRequest,
  LoginRequest,
  TokenResponse
} from '@/types/auth';
import { tokenStorage } from '@/utils/auth';

export const authService = {
  // 회원가입
  register: async (data: RegisterRequest): Promise<User> => {
    const response = await api.post<User>('/auth/register', data);
    return response.data;
  },

  // 로그인
  login: async (data: LoginRequest): Promise<TokenResponse> => {
    const response = await api.post<TokenResponse>('/auth/login', null, {
      params: data, // 쿼리 파라미터로 전달
    });

    // 토큰 저장
    tokenStorage.set(response.data.access_token);

    return response.data;
  },

  // 로그아웃
  logout: (): void => {
    tokenStorage.remove();
  },

  // 현재 유저 정보 조회
  getCurrentUser: async (): Promise<User> => {
    const response = await api.get<User>('/auth/me');
    return response.data;
  },

  // 특정 유저 정보 조회
  getUserById: async (userId: string): Promise<User> => {
    const response = await api.get<User>(`/auth/users/${userId}`);
    return response.data;
  },

  // 로그인 상태 확인
  isAuthenticated: (): boolean => {
    return tokenStorage.exists();
  },
};
```

---

## React/Next.js 구현 예시

### 1. Auth Context (상태 관리)

```typescript
// context/AuthContext.tsx
'use client';

import React, { createContext, useContext, useState, useEffect } from 'react';
import { User } from '@/types/auth';
import { authService } from '@/services/auth.service';

interface AuthContextType {
  user: User | null;
  loading: boolean;
  login: (email: string, password: string) => Promise<void>;
  logout: () => void;
  register: (data: RegisterRequest) => Promise<void>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);

  // 페이지 로드 시 유저 정보 가져오기
  useEffect(() => {
    const loadUser = async () => {
      if (authService.isAuthenticated()) {
        try {
          const userData = await authService.getCurrentUser();
          setUser(userData);
        } catch (error) {
          console.error('Failed to load user:', error);
          authService.logout();
        }
      }
      setLoading(false);
    };

    loadUser();
  }, []);

  const login = async (email: string, password: string) => {
    await authService.login({ email, password });
    const userData = await authService.getCurrentUser();
    setUser(userData);
  };

  const logout = () => {
    authService.logout();
    setUser(null);
  };

  const register = async (data: RegisterRequest) => {
    await authService.register(data);
    // 회원가입 후 자동 로그인
    await login(data.email, data.password);
  };

  return (
    <AuthContext.Provider value={{ user, loading, login, logout, register }}>
      {children}
    </AuthContext.Provider>
  );
}

// Custom Hook
export function useAuth() {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within AuthProvider');
  }
  return context;
}
```

### 2. 회원가입 페이지

```typescript
// app/register/page.tsx
'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { useAuth } from '@/context/AuthContext';

export default function RegisterPage() {
  const router = useRouter();
  const { register } = useAuth();
  const [formData, setFormData] = useState({
    name: '',
    email: '',
    phone_number: '',
    password: '',
  });
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      await register(formData);
      router.push('/dashboard');
    } catch (err: any) {
      setError(err.response?.data?.detail || '회원가입에 실패했습니다');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-md mx-auto mt-8">
      <h1 className="text-2xl font-bold mb-4">회원가입</h1>

      {error && (
        <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded mb-4">
          {error}
        </div>
      )}

      <form onSubmit={handleSubmit} className="space-y-4">
        <div>
          <label className="block text-sm font-medium mb-1">이름</label>
          <input
            type="text"
            value={formData.name}
            onChange={(e) => setFormData({ ...formData, name: e.target.value })}
            className="w-full px-3 py-2 border rounded"
            required
          />
        </div>

        <div>
          <label className="block text-sm font-medium mb-1">이메일</label>
          <input
            type="email"
            value={formData.email}
            onChange={(e) => setFormData({ ...formData, email: e.target.value })}
            className="w-full px-3 py-2 border rounded"
            required
          />
        </div>

        <div>
          <label className="block text-sm font-medium mb-1">전화번호 (숫자만)</label>
          <input
            type="tel"
            pattern="[0-9]{10,20}"
            value={formData.phone_number}
            onChange={(e) => setFormData({ ...formData, phone_number: e.target.value })}
            placeholder="01012345678"
            className="w-full px-3 py-2 border rounded"
            required
          />
        </div>

        <div>
          <label className="block text-sm font-medium mb-1">비밀번호 (최소 8자)</label>
          <input
            type="password"
            minLength={8}
            value={formData.password}
            onChange={(e) => setFormData({ ...formData, password: e.target.value })}
            className="w-full px-3 py-2 border rounded"
            required
          />
        </div>

        <button
          type="submit"
          disabled={loading}
          className="w-full bg-blue-600 text-white py-2 rounded hover:bg-blue-700 disabled:opacity-50"
        >
          {loading ? '처리 중...' : '회원가입'}
        </button>
      </form>
    </div>
  );
}
```

### 3. 로그인 페이지

```typescript
// app/login/page.tsx
'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { useAuth } from '@/context/AuthContext';
import Link from 'next/link';

export default function LoginPage() {
  const router = useRouter();
  const { login } = useAuth();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      await login(email, password);
      router.push('/dashboard');
    } catch (err: any) {
      const errorMessage = err.response?.data?.detail || '로그인에 실패했습니다';
      setError(errorMessage);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-md mx-auto mt-8">
      <h1 className="text-2xl font-bold mb-4">로그인</h1>

      {error && (
        <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded mb-4">
          {error}
        </div>
      )}

      <form onSubmit={handleSubmit} className="space-y-4">
        <div>
          <label className="block text-sm font-medium mb-1">이메일</label>
          <input
            type="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            className="w-full px-3 py-2 border rounded"
            required
          />
        </div>

        <div>
          <label className="block text-sm font-medium mb-1">비밀번호</label>
          <input
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            className="w-full px-3 py-2 border rounded"
            required
          />
        </div>

        <button
          type="submit"
          disabled={loading}
          className="w-full bg-blue-600 text-white py-2 rounded hover:bg-blue-700 disabled:opacity-50"
        >
          {loading ? '로그인 중...' : '로그인'}
        </button>
      </form>

      <p className="mt-4 text-center text-sm">
        계정이 없으신가요?{' '}
        <Link href="/register" className="text-blue-600 hover:underline">
          회원가입
        </Link>
      </p>
    </div>
  );
}
```

### 4. Protected Route (인증 필요한 페이지)

```typescript
// components/ProtectedRoute.tsx
'use client';

import { useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { useAuth } from '@/context/AuthContext';

export default function ProtectedRoute({ children }: { children: React.ReactNode }) {
  const { user, loading } = useAuth();
  const router = useRouter();

  useEffect(() => {
    if (!loading && !user) {
      router.push('/login');
    }
  }, [user, loading, router]);

  if (loading) {
    return <div>로딩 중...</div>;
  }

  if (!user) {
    return null;
  }

  return <>{children}</>;
}

// 사용 예시
// app/dashboard/page.tsx
import ProtectedRoute from '@/components/ProtectedRoute';

export default function DashboardPage() {
  return (
    <ProtectedRoute>
      <div>
        <h1>대시보드</h1>
        {/* 대시보드 컨텐츠 */}
      </div>
    </ProtectedRoute>
  );
}
```

### 5. 유저 프로필 컴포넌트

```typescript
// components/UserProfile.tsx
'use client';

import { useAuth } from '@/context/AuthContext';

export default function UserProfile() {
  const { user, logout } = useAuth();

  if (!user) return null;

  return (
    <div className="p-4 border rounded">
      <h2 className="text-xl font-bold mb-2">내 프로필</h2>
      <div className="space-y-2">
        <p><strong>이름:</strong> {user.name}</p>
        <p><strong>이메일:</strong> {user.email}</p>
        <p><strong>전화번호:</strong> {user.phone_number}</p>
        <p><strong>가입일:</strong> {new Date(user.created_at).toLocaleDateString()}</p>
        <p>
          <strong>상태:</strong>{' '}
          <span className={user.is_active ? 'text-green-600' : 'text-red-600'}>
            {user.is_active ? '활성' : '비활성'}
          </span>
        </p>
      </div>

      <button
        onClick={logout}
        className="mt-4 px-4 py-2 bg-red-600 text-white rounded hover:bg-red-700"
      >
        로그아웃
      </button>
    </div>
  );
}
```

---

## 에러 처리

### 에러 타입별 처리

```typescript
// utils/error-handler.ts
import { AxiosError } from 'axios';
import { ApiError, ValidationError } from '@/types/auth';

export function handleAuthError(error: unknown): string {
  if (error instanceof AxiosError) {
    const status = error.response?.status;
    const data = error.response?.data;

    switch (status) {
      case 400:
        // 이메일/전화번호 중복
        return data?.detail || '입력한 정보를 확인해주세요';

      case 401:
        // 인증 실패
        return '이메일 또는 비밀번호가 올바르지 않습니다';

      case 403:
        // 비활성화된 계정
        return '비활성화된 계정입니다';

      case 404:
        // 유저를 찾을 수 없음
        return '사용자를 찾을 수 없습니다';

      case 422:
        // 유효성 검증 실패
        const validationError = data as ValidationError;
        if (validationError.detail && validationError.detail.length > 0) {
          return validationError.detail[0].msg;
        }
        return '입력 정보가 유효하지 않습니다';

      case 500:
        return '서버 오류가 발생했습니다';

      default:
        return '알 수 없는 오류가 발생했습니다';
    }
  }

  return '네트워크 오류가 발생했습니다';
}
```

### 사용 예시

```typescript
try {
  await authService.login({ email, password });
} catch (error) {
  const errorMessage = handleAuthError(error);
  setError(errorMessage);
}
```

---

## 보안 고려사항

### 1. XSS (Cross-Site Scripting) 방지
```typescript
// 사용자 입력 데이터를 항상 검증
const sanitizeInput = (input: string): string => {
  return input.trim().replace(/[<>]/g, '');
};
```

### 2. CSRF (Cross-Site Request Forgery) 방지
```typescript
// API 호출 시 Origin 헤더 확인
api.defaults.headers.common['X-Requested-With'] = 'XMLHttpRequest';
```

### 3. 토큰 만료 처리
```typescript
// JWT 토큰 디코딩하여 만료 시간 확인
import { jwtDecode } from 'jwt-decode';

export function isTokenExpired(token: string): boolean {
  try {
    const decoded: any = jwtDecode(token);
    const currentTime = Date.now() / 1000;
    return decoded.exp < currentTime;
  } catch {
    return true;
  }
}

// 사용
const token = tokenStorage.get();
if (token && isTokenExpired(token)) {
  tokenStorage.remove();
  // 로그인 페이지로 리다이렉트
}
```

### 4. HTTPS 사용 (프로덕션)
```typescript
// 프로덕션 환경에서는 반드시 HTTPS 사용
if (process.env.NODE_ENV === 'production' && !window.location.protocol.includes('https')) {
  console.warn('HTTPS를 사용해주세요');
}
```

### 5. 민감한 정보 노출 방지
```typescript
// 에러 로그에 비밀번호 등 민감한 정보 포함하지 않기
const sanitizeErrorLog = (error: any) => {
  const { password, ...safeData } = error.config?.data || {};
  return safeData;
};
```

---

## 실전 팁

### 1. 폼 유효성 검증

```typescript
// utils/validation.ts

export const validation = {
  email: (email: string): boolean => {
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return emailRegex.test(email);
  },

  password: (password: string): { valid: boolean; message?: string } => {
    if (password.length < 8) {
      return { valid: false, message: '비밀번호는 최소 8자 이상이어야 합니다' };
    }
    // 추가 검증 (영문, 숫자, 특수문자 포함 등)
    return { valid: true };
  },

  phoneNumber: (phone: string): boolean => {
    const phoneRegex = /^[0-9]{10,20}$/;
    return phoneRegex.test(phone);
  },

  name: (name: string): boolean => {
    return name.trim().length >= 1 && name.trim().length <= 100;
  },
};
```

### 2. 로딩 상태 관리

```typescript
// hooks/useAsync.ts
import { useState, useCallback } from 'react';

export function useAsync<T>() {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [data, setData] = useState<T | null>(null);

  const execute = useCallback(async (asyncFunction: () => Promise<T>) => {
    setLoading(true);
    setError(null);
    try {
      const result = await asyncFunction();
      setData(result);
      return result;
    } catch (err: any) {
      const errorMessage = handleAuthError(err);
      setError(errorMessage);
      throw err;
    } finally {
      setLoading(false);
    }
  }, []);

  return { loading, error, data, execute };
}

// 사용 예시
const { loading, error, execute } = useAsync<User>();

const handleLogin = async () => {
  await execute(() => authService.login({ email, password }));
};
```

### 3. React Hook Form + Zod 사용 (추천)

```bash
npm install react-hook-form zod @hookform/resolvers
```

```typescript
// schemas/auth.schema.ts
import { z } from 'zod';

export const registerSchema = z.object({
  name: z.string().min(1, '이름을 입력해주세요').max(100),
  email: z.string().email('올바른 이메일 형식이 아닙니다'),
  phone_number: z.string().regex(/^[0-9]{10,20}$/, '전화번호는 10-20자의 숫자만 입력 가능합니다'),
  password: z.string().min(8, '비밀번호는 최소 8자 이상이어야 합니다'),
});

export type RegisterFormData = z.infer<typeof registerSchema>;

// 사용 예시
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';

const { register, handleSubmit, formState: { errors } } = useForm<RegisterFormData>({
  resolver: zodResolver(registerSchema),
});
```

### 4. 자동 로그인 (Remember Me)

```typescript
// utils/auth.ts
const REMEMBER_ME_KEY = 'remember_me';

export const rememberMe = {
  set: (email: string): void => {
    localStorage.setItem(REMEMBER_ME_KEY, email);
  },

  get: (): string | null => {
    return localStorage.getItem(REMEMBER_ME_KEY);
  },

  remove: (): void => {
    localStorage.removeItem(REMEMBER_ME_KEY);
  },
};
```

### 5. 디버깅 도구

```typescript
// utils/debug.ts
export const debugAuth = () => {
  if (process.env.NODE_ENV === 'development') {
    console.log('Token:', tokenStorage.get());
    console.log('Is Authenticated:', authService.isAuthenticated());
  }
};
```

---

## 자주 발생하는 문제 해결

### 1. CORS 에러
백엔드에서 CORS 설정이 올바른지 확인하세요.

### 2. 401 Unauthorized 반복
- 토큰이 올바르게 저장되었는지 확인
- Authorization 헤더 형식: `Bearer <token>`
- 토큰 만료 여부 확인

### 3. 422 Unprocessable Entity
- 입력 데이터 형식 확인 (특히 전화번호는 숫자만)
- 필수 필드 누락 여부 확인

### 4. 네트워크 에러
- API 서버가 실행 중인지 확인
- 베이스 URL이 올바른지 확인

---

## 추가 참고 자료

- [FastAPI 공식 문서](https://fastapi.tiangolo.com/)
- [Axios 문서](https://axios-http.com/)
- [React Hook Form](https://react-hook-form.com/)
- [Zod 문서](https://zod.dev/)
- [Next.js 인증 가이드](https://nextjs.org/docs/authentication)

---

## 체크리스트

회원가입/로그인 구현 시 확인할 사항:

- [ ] TypeScript 타입 정의 완료
- [ ] API 클라이언트 설정 (axios + 인터셉터)
- [ ] 토큰 저장/관리 로직 구현
- [ ] Auth Context/Provider 구현
- [ ] 회원가입 페이지 구현
- [ ] 로그인 페이지 구현
- [ ] Protected Route 구현
- [ ] 에러 처리 구현
- [ ] 폼 유효성 검증 추가
- [ ] 로딩 상태 UI 추가
- [ ] 로그아웃 기능 구현
- [ ] 보안 고려사항 적용 (XSS, CSRF 방지 등)
- [ ] 프로덕션 환경 설정 (HTTPS, 환경변수 등)

---

## 문의 및 이슈

문제가 발생하면 백엔드 팀에게 문의하거나 다음 정보를 함께 제공해주세요:
- 에러 메시지
- HTTP 상태 코드
- 요청 데이터
- 브라우저 콘솔 로그
