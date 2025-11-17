# 전략 복제 기능 구현 가이드

**작성일**: 2025-01-17
**이슈**: PROJ-84
**대상**: 프론트엔드 개발자
**선행 작업**: 백엔드 API 구현 완료 (`GET /api/v1/strategies/sessions/{session_id}/clone-data`)

---

## 📌 기능 개요

**목적**: 사용자가 자신의 전략 목록(내 백테스트 목록)에서 특정 전략을 복제하여 새로운 백테스트를 실행할 수 있도록 함

**현재 상태**:
- ✅ 전략 목록 표시만 가능 (조회 전용)
- ❌ 전략 내용 복제/수정 기능 없음

**구현 목표**:
- ✅ 커뮤니티의 포트폴리오 공유와 동일한 복제 UX
- ✅ 전략의 매수/매도 조건, 기간, 종목 등을 그대로 복제
- ✅ 복제 후 백테스트 설정 화면에서 수정 가능
- ✅ 새로운 백테스트로 실행

---

## 🏗️ 아키텍처 설계

### 1. 데이터 흐름

```
전략 목록 화면 (quant/main)
  ↓
사용자가 "복제" 버튼 클릭
  ↓
API 호출: GET /strategies/sessions/{session_id}/clone-data
  ↓
CloneStrategyData 응답 수신
  ↓
Zustand Store에 데이터 설정 (useBacktestConfigStore)
  ↓
백테스트 설정 화면으로 이동 (quant/new)
  ↓
사용자가 설정 수정/확인 후 실행
```

### 2. 참고 구현 (커뮤니티)

**파일**: `SL-Front-End/src/lib/api/community.ts:340-347`

```typescript
/**
 * 복제용 전략 데이터 조회
 */
getCloneStrategyData: async (
  sessionId: string
): Promise<CloneStrategyData> => {
  const response = await axiosInstance.get<CloneStrategyData>(
    `/community/clone-strategy/${sessionId}`
  );
  return response.data;
},
```

---

## 🔧 구현 단계

### Step 1: API 함수 추가

**파일**: `src/lib/api/strategy.ts`

**위치**: `strategyApi` 객체 내부 (line 69 이후)

```typescript
export const strategyApi = {
  // ... 기존 함수들 ...

  /**
   * 백테스트 세션 복제 데이터 조회
   * @param sessionId - 복제할 백테스트 세션 ID
   * @returns 복제용 전략 설정 데이터
   */
  getSessionCloneData: async (
    sessionId: string
  ): Promise<CloneStrategyData> => {
    const response = await axiosInstance.get<CloneStrategyData>(
      `/strategies/sessions/${sessionId}/clone-data`
    );
    return response.data;
  },
};
```

**타입 임포트 추가**:

```typescript
// 파일 상단에 추가
import type { CloneStrategyData } from "./community";
```

---

### Step 2: React Query Hook 작성

**파일**: `src/hooks/useStrategyQuery.ts` (신규 파일)

```typescript
"use client";

import { useQuery, useMutation } from "@tanstack/react-query";
import { strategyApi } from "@/lib/api/strategy";
import type { CloneStrategyData } from "@/lib/api/community";

/**
 * 전략 복제 데이터 조회 (수동 실행용)
 * enabled: false로 설정하여 refetch()로만 실행
 */
export function useStrategyCloneQuery(sessionId: string | null) {
  return useQuery({
    queryKey: ["strategy", "clone", sessionId],
    queryFn: () => {
      if (!sessionId) throw new Error("Session ID is required");
      return strategyApi.getSessionCloneData(sessionId);
    },
    enabled: false, // 자동 실행 방지
    staleTime: 0, // 항상 최신 데이터
  });
}

/**
 * 대안: useMutation 패턴 (추천)
 * 복제는 일회성 작업이므로 mutation이 더 적합
 */
export function useCloneStrategyMutation() {
  return useMutation({
    mutationFn: (sessionId: string) =>
      strategyApi.getSessionCloneData(sessionId),
  });
}
```

**어느 패턴을 선택할까?**

| 패턴 | 장점 | 단점 | 추천도 |
|-----|------|------|--------|
| `useQuery` + `refetch()` | 캐싱 가능 | 코드가 약간 복잡 | ⭐⭐⭐ |
| `useMutation` | 간결함, 일회성 작업에 적합 | 캐싱 안됨 | ⭐⭐⭐⭐⭐ |

**추천**: `useMutation` 사용 (복제는 일회성 작업이므로)

---

### Step 3: 전략 목록 아이템에 복제 버튼 추가

**파일**: `src/components/quant/list/StrategyListItem.tsx`

**현재 구조**:
- 체크박스
- 전략 이름 (결과 페이지 링크)
- 일평균 수익률
- 누적 수익률
- MDD
- 생성일

**추가할 내용**: 복제 버튼 (Actions 열)

```typescript
"use client";

import Image from "next/image";
import Link from "next/link";
import { useRouter } from "next/navigation";
import type { Strategy } from "@/types/strategy";
import { useCloneStrategyMutation } from "@/hooks/useStrategyQuery";
import { useBacktestConfigStore } from "@/stores/backtestConfigStore";

interface StrategyListItemProps {
  strategy: Strategy;
  isSelected: boolean;
  onToggle: (id: string) => void;
}

export function StrategyListItem({
  strategy,
  isSelected,
  onToggle,
}: StrategyListItemProps) {
  const router = useRouter();
  const cloneMutation = useCloneStrategyMutation();

  // Zustand store에서 설정 적용 함수 가져오기
  const applyCloneData = useBacktestConfigStore(
    (state) => state.applyCloneData
  );

  const handleClone = async () => {
    try {
      // 1. 복제 데이터 조회
      const cloneData = await cloneMutation.mutateAsync(strategy.sessionId);

      // 2. Zustand store에 데이터 적용
      applyCloneData(cloneData);

      // 3. 백테스트 설정 화면으로 이동
      router.push("/quant/new");
    } catch (error) {
      console.error("전략 복제 실패:", error);
      // TODO: 에러 토스트 표시
      alert("전략 복제에 실패했습니다.");
    }
  };

  return (
    <tr className={`${isSelected ? "rounded-md shadow-card" : ""}`}>
      {/* 체크박스 */}
      <td className="p-[10px] text-left">
        <Image
          src={`/icons/${isSelected ? "check-box-blue" : "check-box-blank"}.svg`}
          alt="체크"
          width={20}
          height={20}
          onClick={() => onToggle(strategy.id)}
          className="cursor-pointer"
        />
      </td>

      {/* 전략 이름 */}
      <td className="p-[10px]">
        <Link
          href={`/quant/result/${strategy.id}`}
          className={`text-[18px] text-left font-semibold ${isSelected ? "text-accent-primary" : ""}`}
        >
          {strategy.name}
        </Link>
      </td>

      {/* 일평균 수익률 */}
      <td
        className={`p-[10px] text-[18px] text-left font-semibold ${
          strategy.dailyAverageReturn > 0
            ? "text-brand-primary"
            : "text-accent-primary"
        }`}
      >
        {strategy.dailyAverageReturn > 0 ? "+" : ""}
        {strategy.dailyAverageReturn.toFixed(2)}%
      </td>

      {/* 누적 수익률 */}
      <td
        className={`p-[10px] text-[18px] text-left font-semibold ${
          strategy.cumulativeReturn > 0
            ? "text-brand-primary"
            : "text-accent-primary"
        }`}
      >
        {strategy.cumulativeReturn > 0 ? "+" : ""}
        {strategy.cumulativeReturn.toFixed(2)}%
      </td>

      {/* MDD */}
      <td
        className={`p-[10px] text-[18px] text-left font-semibold ${
          strategy.maxDrawdown < 0 ? "text-accent-primary" : "text-gray-500"
        }`}
      >
        {strategy.maxDrawdown.toFixed(2)}%
      </td>

      {/* 생성일 */}
      <td className="p-[10px] text-[18px] text-left font-semibold">
        {strategy.createdAt}
      </td>

      {/* 복제 버튼 (신규 추가) */}
      <td className="p-[10px] text-center">
        <button
          onClick={handleClone}
          disabled={cloneMutation.isPending}
          className="px-4 py-2 bg-brand-primary text-white rounded-md hover:bg-brand-hover disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {cloneMutation.isPending ? "복제 중..." : "복제"}
        </button>
      </td>
    </tr>
  );
}
```

**테이블 헤더도 수정 필요** (`StrategyList.tsx` 등):

```typescript
<thead>
  <tr>
    <th>선택</th>
    <th>전략 이름</th>
    <th>일평균 수익률</th>
    <th>누적 수익률</th>
    <th>MDD</th>
    <th>생성일</th>
    <th>작업</th> {/* 신규 추가 */}
  </tr>
</thead>
```

---

### Step 4: Zustand Store 함수 추가

**파일**: `src/stores/backtestConfigStore.ts`

**추가할 함수**: `applyCloneData` (복제 데이터를 store에 적용)

```typescript
import { create } from "zustand";
import type { CloneStrategyData } from "@/lib/api/community";

interface BacktestConfigState {
  // ... 기존 상태들 ...

  // 기존 액션들
  setInitialInvestment: (value: number) => void;
  // ... 기타 액션들 ...

  /**
   * 복제 데이터를 store에 적용
   * @param cloneData - API에서 받은 복제 데이터
   */
  applyCloneData: (cloneData: CloneStrategyData) => void;

  /**
   * Store 초기화 (선택 사항)
   */
  resetConfig: () => void;
}

export const useBacktestConfigStore = create<BacktestConfigState>((set) => ({
  // ... 기존 초기 상태 ...

  // ... 기존 액션들 ...

  applyCloneData: (cloneData) =>
    set({
      strategy_name: cloneData.strategyName,
      is_day_or_month: cloneData.isDayOrMonth,
      initial_investment: cloneData.initialInvestment,
      start_date: cloneData.startDate,
      end_date: cloneData.endDate,
      commission_rate: cloneData.commissionRate,
      slippage: cloneData.slippage,

      // 매수 조건
      buyConditionsUI: cloneData.buyConditions.map((condition, index) => ({
        id: `clone-${Date.now()}-${index}`,
        ...condition,
      })),
      buy_logic: cloneData.buyLogic,
      priority_factor: cloneData.priorityFactor,
      priority_order: cloneData.priorityOrder,

      // 매수 비중
      per_stock_ratio: cloneData.perStockRatio,
      max_holdings: cloneData.maxHoldings,
      max_buy_value: cloneData.maxBuyValue,
      max_daily_stock: cloneData.maxDailyStock,
      buy_price_basis: cloneData.buyPriceBasis,
      buy_price_offset: cloneData.buyPriceOffset,

      // 매도 조건
      target_and_loss: cloneData.targetAndLoss,
      hold_days: cloneData.holdDays,
      condition_sell: cloneData.conditionSell,

      // 매매 대상
      trade_targets: cloneData.tradeTargets,
    }),

  resetConfig: () =>
    set({
      // 초기 상태로 복원
      // ... 초기값들 ...
    }),
}));
```

**주의사항**:
- `buyConditionsUI`의 각 조건에 고유한 `id`를 생성해야 함
- `Date.now()`를 사용하여 중복 방지
- 기존 store 구조에 맞게 필드명 조정 필요

---

### Step 5: 타입 정의 확인

**파일**: `src/lib/api/community.ts`

**이미 정의된 타입** (line 144-166):

```typescript
export interface CloneStrategyData {
  strategyName: string;
  isDayOrMonth: string;
  initialInvestment: number;
  startDate: string;
  endDate: string;
  commissionRate: number;
  slippage: number;
  buyConditions: Record<string, unknown>[];
  buyLogic: string;
  priorityFactor: string | null;
  priorityOrder: string;
  perStockRatio: number;
  maxHoldings: number;
  maxBuyValue: number | null;
  maxDailyStock: number | null;
  buyPriceBasis: string;
  buyPriceOffset: number;
  targetAndLoss: Record<string, unknown> | null;
  holdDays: Record<string, unknown> | null;
  conditionSell: Record<string, unknown> | null;
  tradeTargets: Record<string, unknown>;
}
```

**추가 작업 필요 없음** - 이미 정의되어 있음

---

### Step 6: Strategy 타입에 sessionId 추가 (필요시)

**파일**: `src/types/strategy.ts` (또는 관련 타입 파일)

**확인 사항**: `Strategy` 타입에 `sessionId` 필드가 있는지 확인

```typescript
export interface Strategy {
  id: string;
  sessionId: string; // ← 이 필드가 있어야 함
  name: string;
  dailyAverageReturn: number;
  cumulativeReturn: number;
  maxDrawdown: number;
  createdAt: string;
  // ... 기타 필드들
}
```

**없다면 추가 필요**:
- 백엔드 응답에서 `sessionId`를 받아오고 있는지 확인
- `StrategyListItem` API 응답에 포함되어 있는지 확인 (`src/lib/api/strategy.ts:11-20`)

---

## 🎨 UI/UX 고려사항

### 1. 버튼 스타일

**옵션 1: 텍스트 버튼** (현재 제안)
```typescript
<button className="px-4 py-2 bg-brand-primary text-white rounded-md hover:bg-brand-hover">
  복제
</button>
```

**옵션 2: 아이콘 버튼**
```typescript
<button className="p-2 hover:bg-bg-hover rounded-md">
  <Image src="/icons/copy.svg" alt="복제" width={20} height={20} />
</button>
```

**옵션 3: 드롭다운 메뉴** (여러 액션이 있을 경우)
```typescript
<DropdownMenu>
  <DropdownMenuItem onClick={handleClone}>복제</DropdownMenuItem>
  <DropdownMenuItem onClick={handleDelete}>삭제</DropdownMenuItem>
  <DropdownMenuItem onClick={handleShare}>공유</DropdownMenuItem>
</DropdownMenu>
```

### 2. 로딩 상태 표시

```typescript
{cloneMutation.isPending && (
  <div className="flex items-center gap-2">
    <Spinner size="sm" />
    <span>복제 중...</span>
  </div>
)}
```

### 3. 에러 처리

**Toast 알림 사용 (권장)**:

```typescript
import { toast } from "sonner"; // 또는 프로젝트에서 사용 중인 toast 라이브러리

const handleClone = async () => {
  try {
    const cloneData = await cloneMutation.mutateAsync(strategy.sessionId);
    applyCloneData(cloneData);

    toast.success("전략이 복제되었습니다");
    router.push("/quant/new");
  } catch (error) {
    toast.error("전략 복제에 실패했습니다");
    console.error(error);
  }
};
```

### 4. 확인 다이얼로그 (선택 사항)

사용자가 실수로 복제 버튼을 누를 수 있으므로:

```typescript
const handleClone = async () => {
  const confirmed = confirm(
    `"${strategy.name}" 전략을 복제하시겠습니까?\n기존 설정이 모두 대체됩니다.`
  );

  if (!confirmed) return;

  // ... 복제 로직
};
```

---

## 🧪 테스트 시나리오

### 1. 정상 케이스

1. **복제 버튼 클릭**
   - [ ] 버튼이 "복제 중..." 상태로 변경
   - [ ] API 호출 성공

2. **Store 적용 확인**
   - [ ] 모든 설정값이 올바르게 적용됨
   - [ ] 매수 조건이 정확히 복제됨
   - [ ] 매도 조건이 정확히 복제됨

3. **화면 이동**
   - [ ] `/quant/new` 페이지로 이동
   - [ ] 복제된 데이터가 폼에 표시됨

4. **수정 및 실행**
   - [ ] 사용자가 설정 수정 가능
   - [ ] 백테스트 실행 가능

### 2. 에러 케이스

1. **네트워크 에러**
   - [ ] 에러 메시지 표시
   - [ ] 버튼 상태 복구

2. **권한 없음 (403)**
   - [ ] 적절한 에러 메시지
   - [ ] 로그인 페이지로 리다이렉트

3. **세션 없음 (404)**
   - [ ] "전략을 찾을 수 없습니다" 메시지

---

## 🔍 참고: 백엔드 API 명세

### Endpoint

```
GET /api/v1/strategies/sessions/{session_id}/clone-data
```

### 인증

**필수**: Bearer Token (본인이 소유한 세션만 조회 가능)

### Path Parameters

| 이름 | 타입 | 설명 |
|-----|------|------|
| `session_id` | string | 복제할 백테스트 세션 ID (UUID) |

### Response (200 OK)

```json
{
  "strategyName": "내 전략 (복제)",
  "isDayOrMonth": "daily",
  "initialInvestment": 5000,
  "startDate": "20230101",
  "endDate": "20231231",
  "commissionRate": 0.015,
  "slippage": 0.1,
  "buyConditions": [
    {
      "factorName": "PER",
      "operator": "<",
      "value": "10"
    }
  ],
  "buyLogic": "AND",
  "priorityFactor": "PBR",
  "priorityOrder": "desc",
  "perStockRatio": 5.0,
  "maxHoldings": 20,
  "maxBuyValue": null,
  "maxDailyStock": null,
  "buyPriceBasis": "CLOSE",
  "buyPriceOffset": 0.0,
  "targetAndLoss": {
    "enabled": true,
    "targetPercent": 10,
    "lossPercent": -5
  },
  "holdDays": null,
  "conditionSell": null,
  "tradeTargets": {
    "use_all_stocks": true,
    "selected_themes": [],
    "selected_stocks": []
  }
}
```

### Error Responses

| 코드 | 설명 |
|-----|------|
| 401 | 인증 필요 (로그인 안됨) |
| 403 | 권한 없음 (다른 사용자의 세션) |
| 404 | 세션을 찾을 수 없음 |
| 500 | 서버 에러 |

---

## 📂 파일 수정 체크리스트

### 필수 수정

- [ ] `src/lib/api/strategy.ts` - API 함수 추가
- [ ] `src/hooks/useStrategyQuery.ts` - React Query Hook 작성 (신규 파일)
- [ ] `src/components/quant/list/StrategyListItem.tsx` - 복제 버튼 추가
- [ ] `src/components/quant/list/StrategyList.tsx` - 테이블 헤더 수정
- [ ] `src/stores/backtestConfigStore.ts` - `applyCloneData` 함수 추가

### 선택 사항

- [ ] `src/types/strategy.ts` - `sessionId` 필드 확인/추가
- [ ] Toast 알림 라이브러리 설정 (없는 경우)
- [ ] 복제 아이콘 추가 (`public/icons/copy.svg`)

---

## 🎯 완료 기준

### 기능 요구사항

- [x] 백엔드 API 구현 완료
- [ ] 전략 목록에 복제 버튼 표시
- [ ] 복제 버튼 클릭 시 데이터 조회
- [ ] Zustand Store에 데이터 적용
- [ ] 백테스트 설정 화면으로 이동
- [ ] 복제된 데이터가 폼에 올바르게 표시

### 비기능 요구사항

- [ ] 타입 에러 없음 (`pnpm typecheck` 통과)
- [ ] 린트 에러 없음 (`pnpm lint` 통과)
- [ ] 로딩 상태 표시
- [ ] 에러 처리 및 사용자 피드백
- [ ] 반응형 디자인 (모바일 지원)

---

## 🚨 주의사항

### 1. Zustand Infinite Loop 방지

**잘못된 패턴**:
```typescript
const { data, setData } = useBacktestConfigStore((state) => ({
  data: state.data,
  setData: state.setData, // ❌ infinite loop!
}));
```

**올바른 패턴**:
```typescript
import { useShallow } from "zustand/react/shallow";

const { data } = useBacktestConfigStore(
  useShallow((state) => ({ data: state.data }))
);
const setData = useBacktestConfigStore((state) => state.setData);
```

### 2. Router 사용

**App Router에서는** `next/navigation` 사용:
```typescript
import { useRouter } from "next/navigation"; // ✅
// import { useRouter } from "next/router"; // ❌ Pages Router용
```

### 3. 클라이언트 컴포넌트 명시

useRouter, Zustand, React Query 사용 시:
```typescript
"use client"; // ✅ 파일 최상단에 추가
```

---

## 📞 문의 및 이슈

구현 중 문제가 발생하면:
1. 이 가이드를 먼저 확인
2. `FRONTEND_DEVELOPMENT_GUIDE.md` 참조
3. 커뮤니티의 복제 기능 구현 참고 (`src/lib/api/community.ts:340-347`)
4. 팀 채널에 질문

**관련 이슈**: PROJ-84
**백엔드 구현**: `SL-Back-end/app/api/routes/strategy.py:353-430`
**마지막 업데이트**: 2025-01-17
