# Stock Lab Frontend 개발 가이드

**작성일**: 2025-01-12
**버전**: 1.0.0
**대상**: 모든 개발자 및 AI 어시스턴트

---

## 📌 필수 준수 사항

이 가이드는 **모든 코드 작성 시 반드시 따라야 하는 규칙**입니다.

---

## 🎯 핵심 원칙

### 1. 일관성 (Consistency)
- 기존 코드 패턴을 철저히 따를 것
- 새로운 패턴 도입 시 팀 논의 필수

### 2. 타입 안정성 (Type Safety)
- 모든 함수와 컴포넌트에 타입 명시
- `any` 타입 사용 금지

### 3. 컴포넌트 재사용성 (Reusability)
- 공통 로직은 반드시 추출
- 3번 이상 반복되는 코드는 컴포넌트/훅으로 분리

### 4. 성능 최적화 (Performance)
- React Compiler 자동 최적화 활용
- 불필요한 수동 메모이제이션 제거

---

## 📁 폴더 구조 규칙

### 구조 에시 (quant)
```
src/
├── app/                    # Next.js App Router 페이지
│   ├── (auth)/            # 라우트 그룹 (인증)
│   ├── quant/             # 퀀트 투자 페이지
│   └── layout.tsx         # 루트 레이아웃
├── components/            # React 컴포넌트
│   ├── common/            # 공통 컴포넌트 (재사용 가능)
│   ├── quant/             # 퀀트 도메인 컴포넌트
│   │   ├── ui/            # 기본 UI 컴포넌트
│   │   ├── sections/      # 섹션 컴포넌트
│   │   ├── layout/        # 레이아웃 컴포넌트
│   │   └── tabs/          # 탭 컴포넌트
│   └── ...
├── hooks/                 # Custom React Hooks
├── stores/                # Zustand 전역 상태
├── lib/                   # 유틸리티 함수
├── types/                 # TypeScript 타입 정의
└── api/                   # API 클라이언트
```

### 컴포넌트 계층 구조

**5가지 계층 (하위 → 상위)**:

1. **common/** - 프로젝트 전체에서 재사용 가능
   - Button, Input, Dropdown, Modal 등
   - 도메인 로직 없음

2. **ui/** - 도메인 특화 기본 UI
   - ConditionCard, FieldPanel, SectionHeader
   - 도메인 컨텍스트 포함하지만 비즈니스 로직 없음

3. **sections/** - 기능별 섹션
   - BuyConditionsSection, ConditionalSellSection
   - 비즈니스 로직 포함

4. **layout/** - 페이지 레이아웃
   - QuantStrategySummaryPanel, QuantStrategySidebar
   - 여러 섹션 조합

5. **tabs/** - 탭 페이지
   - BuyConditionTab, TargetSelectionTab
   - 페이지 수준 컴포넌트

### 폴더/파일 명명 규칙

| 타입 | 명명 규칙 | 예시 |
|-----|---------|------|
| 컴포넌트 | PascalCase | `Button.tsx`, `QuantStrategySummaryPanel.tsx` |
| 훅 | camelCase, use- 접두사 | `useFactorsQuery.ts`, `useBacktestConfigStore.ts` |
| 유틸리티 | kebab-case | `date-utils.ts`, `format-utils.ts` |
| 타입 파일 | kebab-case | `api.ts`, `backtest-config.ts` |
| 폴더 | kebab-case | `buy-conditions/`, `target-selection/` |

---

## 🧩 컴포넌트 작성 규칙

### 기본 구조

```typescript
"use client"; // 클라이언트 컴포넌트인 경우

// 1. External imports (라이브러리)
import { useState, useEffect } from "react";
import Image from "next/image";
import { useShallow } from "zustand/react/shallow";

// 2. Internal imports (프로젝트 내부)
import { Button, Input } from "@/components/common";
import { useBacktestConfigStore } from "@/stores";

// 3. Props 타입 정의
interface MyComponentProps {
  title: string;
  onSubmit: (data: FormData) => void;
  className?: string;
}

// 4. 컴포넌트 함수
export function MyComponent({
  title,
  onSubmit,
  className
}: MyComponentProps) {
  // 4-1. Hooks (상태, store, query)
  const [isOpen, setIsOpen] = useState(false);

  const { data } = useBacktestConfigStore(
    useShallow((state) => ({ data: state.data }))
  );

  // 4-2. Event handlers
  const handleClick = () => {
    setIsOpen(!isOpen);
  };

  // 4-3. Effects
  useEffect(() => {
    // ...
  }, []);

  // 4-4. JSX return
  return (
    <div className={className}>
      <h1>{title}</h1>
      {/* ... */}
    </div>
  );
}

// 5. 서브 컴포넌트 (필요한 경우)
function SubComponent() {
  // ...
}
```

### Props 패턴

#### 1. 기본 Props
```typescript
interface ButtonProps {
  text: string;
  onClick: () => void;
  disabled?: boolean;
}
```

#### 2. HTMLAttributes 확장
```typescript
interface InputProps extends React.InputHTMLAttributes<HTMLInputElement> {
  label?: string;
  error?: string;
}

// 사용
<Input
  label="이름"
  placeholder="입력하세요"
  onChange={handleChange}
/>
```

#### 3. Children Props
```typescript
interface CardProps {
  title: string;
  children: React.ReactNode;
}
```

#### 4. Omit 유틸리티
```typescript
// size prop 제외
interface CustomButtonProps extends Omit<ButtonProps, 'size'> {
  variant: 'primary' | 'secondary';
}
```

### 컴포넌트 분리 기준

**컴포넌트로 분리하는 경우**:
- 3번 이상 반복 사용
- 50줄 이상의 JSX
- 독립적인 상태 관리 필요
- 재사용 가능성이 있는 UI 패턴

**분리하지 않는 경우**:
- 한 곳에서만 사용
- 부모와 강하게 결합
- 단순 마크업 (10줄 이하)

---

## 🔄 상태 관리 패턴

### Zustand Store 작성

```typescript
// stores/backtestConfigStore.ts
import { create } from 'zustand';

interface BacktestConfigState {
  // 데이터
  initial_investment: number;
  buyConditionsUI: BuyCondition[];

  // 액션 (set 접두사)
  setInitialInvestment: (value: number) => void;
  addBuyConditionUI: () => void;
  updateBuyConditionUI: (id: string, data: Partial<BuyCondition>) => void;
}

export const useBacktestConfigStore = create<BacktestConfigState>((set) => ({
  // 초기 상태
  initial_investment: 5000,
  buyConditionsUI: [],

  // 액션 구현
  setInitialInvestment: (value) => set({ initial_investment: value }),

  addBuyConditionUI: () => set((state) => ({
    buyConditionsUI: [...state.buyConditionsUI, createNewCondition()]
  })),

  updateBuyConditionUI: (id, data) => set((state) => ({
    buyConditionsUI: state.buyConditionsUI.map((c) =>
      c.id === id ? { ...c, ...data } : c
    )
  })),
}));
```

### ⭐ React Compiler + Zustand 패턴 (필수)

**핵심 규칙**: `useShallow`로 데이터 선택, 함수는 직접 선택

```typescript
import { useShallow } from "zustand/react/shallow";

// ✅ 올바른 패턴
function MyComponent() {
  // 데이터는 useShallow로 묶어서 선택
  const {
    initial_investment,
    buyConditionsUI,
    buy_logic,
  } = useBacktestConfigStore(
    useShallow((state) => ({
      initial_investment: state.initial_investment,
      buyConditionsUI: state.buyConditionsUI,
      buy_logic: state.buy_logic,
    }))
  );

  // 함수들은 별도로 선택 (안정적인 참조)
  const setInitialInvestment = useBacktestConfigStore(state => state.setInitialInvestment);
  const addBuyConditionUI = useBacktestConfigStore(state => state.addBuyConditionUI);
  const setBuyLogic = useBacktestConfigStore(state => state.setBuyLogic);

  // ...
}
```

```typescript
// ❌ 잘못된 패턴 1: 함수를 객체에 포함
const {
  data,
  setData, // 함수를 객체에 포함 → infinite loop!
} = useBacktestConfigStore(
  useShallow((state) => ({
    data: state.data,
    setData: state.setData, // ❌
  }))
);

// ❌ 잘못된 패턴 2: useShallow 없이 객체 반환
const { data, count } = useBacktestConfigStore((state) => ({
  data: state.data,
  count: state.count,
})); // ❌ infinite loop!

// ❌ 잘못된 패턴 3: 개별 필드를 24개 라인으로 작성
const field1 = useBacktestConfigStore(state => state.field1);
const field2 = useBacktestConfigStore(state => state.field2);
// ... 22개 더 // ❌ 너무 장황함
```

### React Query 사용

#### useQuery - 조회 작업

**언제 사용?**: 서버 상태를 변경하지 않는 모든 조회 작업

```typescript
// hooks/useFactorsQuery.ts
import { useQuery } from "@tanstack/react-query";
import { getFactors } from "@/lib/api";

// 쿼리 키 체계화 (권장)
export const factorsQueryKey = {
  all: ["factors"] as const,
  lists: () => [...factorsQueryKey.all, "list"] as const,
  detail: (id: string) => [...factorsQueryKey.all, "detail", id] as const,
};

export function useFactorsQuery() {
  return useQuery({
    queryKey: factorsQueryKey.lists(),
    queryFn: () => getFactors(false),
    staleTime: 1000 * 60, // 1분
  });
}

// 컴포넌트에서 사용
function MyComponent() {
  const { data: factors = [], isLoading, error } = useFactorsQuery();

  if (isLoading) return <div>로딩중...</div>;
  if (error) return <div>에러 발생</div>;

  return <div>{factors.map(...)}</div>;
}
```

#### useMutation - 서버 상태 변경

**언제 사용?**: 데이터 생성(POST), 수정(PUT/PATCH), 삭제(DELETE) 작업

```typescript
// hooks/useBacktestQuery.ts
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { runBacktest, deleteBacktest } from "@/lib/api";

// 1. 생성(POST) - 백테스트 실행
export function useRunBacktestMutation() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: runBacktest,
    onSuccess: () => {
      // 성공 시 목록 캐시 자동 갱신
      queryClient.invalidateQueries({ queryKey: backtestQueryKey.lists() });
    },
  });
}

// 2. 삭제(DELETE) - 백테스트 삭제
export function useDeleteBacktestMutation() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: deleteBacktest,
    onSuccess: (_, backtestId) => {
      // 목록 갱신
      queryClient.invalidateQueries({ queryKey: backtestQueryKey.lists() });
      // 상세 캐시 제거
      queryClient.removeQueries({ queryKey: backtestQueryKey.detail(backtestId) });
    },
  });
}

// 컴포넌트에서 사용
function BacktestForm() {
  const mutation = useRunBacktestMutation();

  const handleSubmit = (data: BacktestConfig) => {
    mutation.mutate(data, {
      onSuccess: (result) => {
        console.log("백테스트 시작:", result.id);
      },
    });
  };

  return (
    <form onSubmit={handleSubmit}>
      {mutation.isLoading && <p>실행 중...</p>}
      {mutation.isError && <p>에러: {mutation.error.message}</p>}
      <button type="submit" disabled={mutation.isLoading}>
        백테스트 실행
      </button>
    </form>
  );
}
```

#### ⚠️ 중요: POST ≠ useMutation

**HTTP 메서드가 아닌 작업의 본질이 중요합니다!**

```typescript
// ❌ 잘못된 판단: POST이니까 useMutation 사용
// 실제로는 조회 작업이므로 useQuery 사용이 적절
export async function getStocksByIndustries(
  industryNames: string[]
): Promise<StockInfo[]> {
  // POST를 사용하는 이유: 산업명 배열이 URL에 담기 길어서
  const response = await axiosInstance.post("/industries/stocks-by-industries", {
    industries: industryNames,
  });
  return response.data;
}

// ✅ 올바른 선택: 조회 목적이므로 useQuery 사용
export function useStocksByIndustriesQuery(industryNames: string[]) {
  return useQuery({
    queryKey: ["stocks", "by-industries", industryNames],
    queryFn: () => getStocksByIndustries(industryNames),
    enabled: industryNames.length > 0,
  });
}
```

**판단 기준**:
- **서버 상태 변경** (생성/수정/삭제) → `useMutation`
- **조회 작업** (데이터만 가져옴) → `useQuery` (POST라도!)

#### 고급 패턴

**1. 무한 스크롤**
```typescript
export function useBacktestTradesInfiniteQuery(backtestId: string) {
  return useInfiniteQuery({
    queryKey: [...backtestQueryKey.trades(backtestId), { limit: 50 }],
    queryFn: ({ pageParam = 1 }) =>
      getBacktestTrades(backtestId, { page: pageParam, limit: 50 }),
    initialPageParam: 1,
    getNextPageParam: (lastPage) => {
      const { page, totalPages } = lastPage.pagination;
      return page < totalPages ? page + 1 : undefined;
    },
  });
}
```

**2. 폴링 (실시간 상태 추적)**
```typescript
export function useBacktestStatusQuery(backtestId: string) {
  return useQuery({
    queryKey: backtestQueryKey.status(backtestId),
    queryFn: () => getBacktestStatus(backtestId),
    refetchInterval: (query) => {
      const status = query.state.data?.status;
      // 완료되면 폴링 중단
      if (status === "completed" || status === "failed") return false;
      return 2000; // 2초마다 확인
    },
    refetchIntervalInBackground: true,
  });
}
```

---

## 🎨 스타일링 규칙

### Tailwind CSS 사용

```typescript
// ✅ 좋은 예
<button
  className="px-4 py-2 bg-brand-primary text-white rounded-md hover:bg-brand-hover"
>
  클릭
</button>

// ✅ 조건부 클래스 (tailwind-merge 사용)
import { cn } from "@/lib/utils";

<button
  className={cn(
    "px-4 py-2 rounded-md",
    variant === "primary" && "bg-brand-primary text-white",
    variant === "secondary" && "bg-bg-surface text-text-strong",
    disabled && "opacity-50 cursor-not-allowed"
  )}
>
```

### 디자인 토큰 (CSS Variables)

```typescript
// ✅ 토큰 사용
className="bg-brand-primary text-text-strong border-border-default"

// ❌ 직접 색상값 사용
className="bg-blue-600 text-gray-900 border-gray-300"
```

**주요 토큰**:
- **Colors**: `brand-primary`, `accent-primary`, `text-strong`, `bg-surface`
- **Spacing**: `4`, `8`, `12`, `16`, `24`, `32` (4px 단위)
- **Radius**: `rounded-md` (8px),

### 반응형 디자인

```typescript
// Breakpoints: sm (640px), md (768px), lg (1024px), xl (1280px)
<div className="w-full md:w-1/2 lg:w-1/3">
  <h1 className="text-lg md:text-xl lg:text-2xl">제목</h1>
</div>
```

---

## 📘 TypeScript 규칙

### Interface vs Type

```typescript
// ✅ Interface: 확장 가능한 객체 타입
interface User {
  id: number;
  name: string;
}

interface Admin extends User {
  role: string;
}

// ✅ Type: 유니온, 리터럴, 복잡한 타입
type Status = "pending" | "approved" | "rejected";
type ButtonVariant = "primary" | "secondary" | "danger";
type InputValue = string | number;
```

### 타입 위치

```typescript
// 1. 컴포넌트 로컬 타입 (해당 파일에서만 사용)
interface MyComponentProps {
  title: string;
}

// 2. 도메인별 타입 (types/backtest.ts)
export interface BuyCondition {
  id: string;
  factorName: string;
  operator: string;
  value: string;
}

// 3. API 타입 (types/api.ts)
export interface ApiResponse<T> {
  data: T;
  message: string;
}
```

### 타입 안정성

```typescript
// ✅ 좋은 예
function calculateTotal(items: Item[]): number {
  return items.reduce((sum, item) => sum + item.price, 0);
}

// ❌ 나쁜 예
function calculateTotal(items: any): any { // any 금지!
  return items.reduce((sum: any, item: any) => sum + item.price, 0);
}
```

---

## 🔧 Custom Hooks 작성

### 기본 구조

```typescript
// hooks/useDisclosure.ts
import { useState, useCallback } from "react";

interface UseDisclosureReturn {
  isOpen: boolean;
  open: () => void;
  close: () => void;
  toggle: () => void;
}

export function useDisclosure(initialState = false): UseDisclosureReturn {
  const [isOpen, setIsOpen] = useState(initialState);

  const open = useCallback(() => setIsOpen(true), []);
  const close = useCallback(() => setIsOpen(false), []);
  const toggle = useCallback(() => setIsOpen((prev) => !prev), []);

  return { isOpen, open, close, toggle };
}
```

**주의**: React Compiler 사용 시 `useCallback` 불필요하지만, 외부 라이브러리 호환을 위해 선택적 사용 가능

### Query Hook 패턴

```typescript
// hooks/useBacktestQuery.ts
import { useQuery } from "@tanstack/react-query";
import { runBacktest } from "@/api/backtest";
import type { BacktestConfig, BacktestResult } from "@/types/api";

export function useBacktestQuery(config: BacktestConfig) {
  return useQuery({
    queryKey: ["backtest", config],
    queryFn: () => runBacktest(config),
    enabled: !!config, // config 있을 때만 실행
    staleTime: 1000 * 60 * 5, // 5분
  });
}
```

---

## 📡 API 통신 패턴

### API 클라이언트 구조

```typescript
// api/backtest.ts
import { apiClient } from "@/lib/axios";
import type { Factor, SubFactor, BacktestResult } from "@/types/api";

export async function getFactors(isServer = false): Promise<Factor[]> {
  const client = isServer ? serverApiClient : apiClient;
  const response = await client.get<Factor[]>("/api/v1/factors/list");
  return response.data;
}

export async function runBacktest(
  config: BacktestConfig
): Promise<BacktestResult> {
  const response = await apiClient.post<BacktestResult>(
    "/api/v1/backtest/run",
    config
  );
  return response.data;
}
```

### Axios 인스턴스 설정

```typescript
// lib/axios.ts
import axios from "axios";

export const apiClient = axios.create({
  baseURL: process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000",
  timeout: 30000,
  headers: {
    "Content-Type": "application/json",
  },
});

// 서버 사이드용 (SSR/SSG)
export const serverApiClient = axios.create({
  baseURL: process.env.INTERNAL_API_URL || "http://backend:8000",
  timeout: 30000,
});
```

---

## ⚡ 성능 최적화 규칙

### React Compiler 활용

**✅ React Compiler가 자동으로 처리하는 것들**:
- `useMemo` - 값 메모이제이션
- `useCallback` - 함수 메모이제이션
- `React.memo` - 컴포넌트 메모이제이션

**❌ 더 이상 작성하지 말 것**:
```typescript
// ❌ React Compiler 사용 시 불필요
const memoizedValue = useMemo(() => calculateValue(data), [data]);
const memoizedCallback = useCallback(() => handleClick(), []);
const MemoizedComponent = React.memo(Component);
```

**✅ React Compiler가 자동 최적화**:
```typescript
// ✅ 단순하게 작성, 컴파일러가 자동 메모이제이션
const value = calculateValue(data);
const handleClick = () => { /* ... */ };
function Component() { /* ... */ }
```

### 코드 스플리팅

```typescript
// ✅ 동적 임포트
import dynamic from "next/dynamic";

const HeavyChart = dynamic(() => import("@/components/HeavyChart"), {
  loading: () => <div>차트 로딩중...</div>,
  ssr: false, // 클라이언트에서만 로드
});
```

---

## 🧪 테스트 작성 (TODO)

현재 테스트 설정은 없지만, 향후 도입 시 다음 패턴 적용:

```typescript
// __tests__/Button.test.tsx
import { render, screen } from "@testing-library/react";
import { Button } from "@/components/common/Button";

describe("Button", () => {
  it("텍스트를 렌더링한다", () => {
    render(<Button>클릭</Button>);
    expect(screen.getByText("클릭")).toBeInTheDocument();
  });
});
```

---

## 📝 코드 품질 관리

### Biome (린팅 + 포매팅)

biome.json
{
  "$schema": "https://biomejs.dev/schemas/2.2.0/schema.json",
  "vcs": {
    "enabled": true,
    "clientKind": "git",
    "useIgnoreFile": true
  },
  "formatter": {
    "enabled": true,
    "indentStyle": "space",
    "indentWidth": 2
  },
  "linter": {
    "enabled": true,
    "rules": {
      "recommended": true
    },
    "domains": {
      "next": "recommended",
      "react": "recommended"
    }
  },
  "assist": {
    "actions": {
      "source": {
        "organizeImports": "on"
      }
    }
  }
}

```bash
# 린팅 체크
pnpm run lint

# 자동 수정
pnpm run lint:fix

# 포매팅
pnpm run format
```

### TypeScript 체크

```bash
# 타입 체크
pnpm run typecheck
```

### Pre-commit Hook (권장)

```bash
# Husky + lint-staged 설정
# package.json
{
  "lint-staged": {
    "*.{ts,tsx}": ["biome check --write", "tsc --noEmit"]
  }
}
```

---

## 🚀 배포 전 체크리스트

### 필수 확인 사항

- [ ] `pnpm run typecheck` 통과
- [ ] `pnpm run lint` 통과
- [ ] `pnpm run build` 성공
- [ ] 로컬에서 프로덕션 빌드 테스트 (`pnpm start`)
- [ ] 브라우저 콘솔 에러 없음
- [ ] Lighthouse 점수 확인 (Performance, Accessibility)

### 성능 최적화 확인

- [ ] 불필요한 리렌더링 없음 (React DevTools Profiler)
- [ ] 큰 번들 사이즈 확인 (Next.js Bundle Analyzer)
- [ ] 이미지 최적화 (Next.js Image 컴포넌트 사용)

---

## 🐛 일반적인 실수와 해결책

### 1. Zustand Infinite Loop

**문제**:
```typescript
// ❌ 함수를 객체에 포함
const { data, setData } = useStore((state) => ({
  data: state.data,
  setData: state.setData, // infinite loop!
}));
```

**해결**:
```typescript
// ✅ useShallow + 함수 분리
import { useShallow } from "zustand/react/shallow";

const { data } = useStore(
  useShallow((state) => ({ data: state.data }))
);
const setData = useStore(state => state.setData);
```

### 2. 하이드레이션 에러

**문제**:
```typescript
// ❌ 서버와 클라이언트 렌더링 불일치
<div>{new Date().toLocaleString()}</div>
```

**해결**:
```typescript
// ✅ 클라이언트 전용으로 표시
const [isMounted, setIsMounted] = useState(false);

useEffect(() => {
  setIsMounted(true);
}, []);

return isMounted ? <div>{new Date().toLocaleString()}</div> : null;
```

### 3. 타입 에러 무시

**문제**:
```typescript
// ❌ any로 회피
const data: any = response.data;
```

**해결**:
```typescript
// ✅ 정확한 타입 정의
interface ApiResponse {
  data: User[];
  total: number;
}

const response = await api.get<ApiResponse>("/users");
const data: User[] = response.data.data;
```

---

## 📚 참고 자료

### 공식 문서
- [Next.js 16](https://nextjs.org/docs)
- [React 19](https://react.dev/)
- [React Compiler](https://react.dev/learn/react-compiler)
- [Zustand](https://docs.pmnd.rs/zustand/)
- [TanStack Query](https://tanstack.com/query/latest)
- [Tailwind CSS](https://tailwindcss.com/)
- [TypeScript](https://www.typescriptlang.org/)

---

## 📞 문의 및 개선 제안

이 가이드에 대한 질문이나 개선 제안이 있다면 팀 채널에 공유해주세요.

**마지막 업데이트**: 2025-01-12
**문서 버전**: 1.0.0
