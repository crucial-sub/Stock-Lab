# Next.js + FastAPI 연동 가이드

## 목차
1. [Next.js 기본 구조 이해](#1-nextjs-기본-구조-이해)
2. [현재 프로젝트 구조 분석](#2-현재-프로젝트-구조-분석)
3. [API 연동 방법](#3-api-연동-방법)
4. [수정해야 할 파일 목록](#4-수정해야-할-파일-목록)
5. [구현 단계별 가이드](#5-구현-단계별-가이드)

---

## 1. Next.js 기본 구조 이해

### 1.1 Next.js란?
- React 기반의 풀스택 웹 프레임워크
- 서버사이드 렌더링(SSR) 및 정적 사이트 생성(SSG) 지원
- 파일 기반 라우팅 시스템

### 1.2 핵심 개념

#### 📁 App Router (Next.js 13+)
```
src/app/
├── page.tsx              → 홈페이지 (/)
├── market-price/
│   └── page.tsx          → 시세 페이지 (/market-price)
└── layout.tsx            → 전체 레이아웃
```

#### 🎨 컴포넌트
- **클라이언트 컴포넌트**: `"use client"` 선언, 상태 관리 및 브라우저 API 사용 가능
- **서버 컴포넌트**: 기본값, 서버에서 렌더링, async/await로 데이터 페칭 가능

---

## 2. 현재 프로젝트 구조 분석

### 2.1 전체 디렉토리 구조
```
SL-Front-End/
├── src/
│   ├── app/                    # 페이지 라우팅
│   │   ├── page.tsx           # 홈페이지
│   │   ├── market-price/
│   │   │   └── page.tsx       # 시세 페이지
│   │   └── layout.tsx
│   │
│   ├── components/            # 재사용 컴포넌트
│   │   ├── common/            # 공통 컴포넌트 (Button, Input 등)
│   │   ├── home/
│   │   │   ├── TodayMarketSection.tsx      # ⭐ 홈 시세 섹션
│   │   │   └── MarketTickerCard.tsx        # ⭐ 시세 카드
│   │   └── market-price/
│   │       └── StockInfoCard.tsx           # ⭐ 종목 상세 카드
│   │
│   ├── lib/                   # 유틸리티 및 설정
│   │   ├── api/               # API 함수들
│   │   │   ├── index.ts       # API export
│   │   │   └── backtest.ts    # 백테스트 API 예제
│   │   └── axios.ts           # ⭐ Axios 설정
│   │
│   ├── types/                 # TypeScript 타입 정의
│   │   ├── stock.ts           # 주식 관련 타입
│   │   └── api.ts             # API 응답 타입
│   │
│   ├── hooks/                 # Custom Hooks
│   └── stores/                # 상태 관리 (Zustand 등)
│
├── public/                    # 정적 파일 (이미지, 아이콘 등)
├── package.json
└── next.config.ts
```

### 2.2 주요 컴포넌트 역할

#### 홈페이지 (`src/app/page.tsx`)
- `TodayMarketSection` 컴포넌트를 렌더링
- **현재**: 하드코딩된 mock 데이터 사용
- **목표**: FastAPI에서 실시간 데이터 가져오기

#### 시세 페이지 (`src/app/market-price/page.tsx`)
- 전체 종목 리스트를 표시
- 탭별 정렬 기능 (최근 본 주식, 체결량 순, 등락률 순 등)
- **현재**: mock 데이터 사용
- **목표**: FastAPI market_quote API 연동

---

## 3. API 연동 방법

### 3.1 Axios 설정 이해 (`src/lib/axios.ts`)

```typescript
// 클라이언트용 인스턴스
export const axiosInstance = axios.create({
  baseURL: process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000/api/v1",
  timeout: 30000,
  withCredentials: true,
});

// 서버용 인스턴스 (SSR에서 사용)
export const axiosServerInstance = axios.create({
  baseURL: process.env.API_BASE_URL ?? "http://localhost:8000/api/v1",
  // ...
});
```

**환경변수 설정** (`.env.local` 파일 생성 필요)
```bash
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000/api/v1
```

### 3.2 API 함수 작성 패턴 (`src/lib/api/backtest.ts` 참고)

```typescript
import { axiosInstance } from "../axios";

// 1. 응답 타입 정의
interface MarketQuoteResponse {
  items: MarketQuoteItem[];
  total: number;
  page: number;
  page_size: number;
  has_next: boolean;
}

// 2. API 함수 작성
export async function getMarketQuotes(
  sortBy: string = "market_cap",
  sortOrder: string = "desc",
  page: number = 1,
  pageSize: number = 50,
  userId?: string
): Promise<MarketQuoteResponse> {
  const response = await axiosInstance.get<MarketQuoteResponse>(
    "/market/quotes",
    {
      params: {
        sort_by: sortBy,
        sort_order: sortOrder,
        page,
        page_size: pageSize,
        user_id: userId,
      },
    }
  );
  return response.data;
}
```

### 3.3 컴포넌트에서 API 호출하기

#### 패턴 1: 클라이언트 컴포넌트 (useEffect 사용)
```typescript
"use client";

import { useState, useEffect } from "react";
import { getMarketQuotes } from "@/lib/api";

export default function MarketPage() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function fetchData() {
      try {
        const result = await getMarketQuotes();
        setData(result);
      } catch (error) {
        console.error("API 호출 실패:", error);
      } finally {
        setLoading(false);
      }
    }

    fetchData();
  }, []);

  if (loading) return <div>로딩 중...</div>;

  return <div>{/* 데이터 렌더링 */}</div>;
}
```

#### 패턴 2: 서버 컴포넌트 (async/await 직접 사용)
```typescript
// "use client" 선언 없음
import { getMarketQuotes } from "@/lib/api";

export default async function MarketPage() {
  // 서버에서 직접 데이터 페칭
  const data = await getMarketQuotes();

  return <div>{/* 데이터 렌더링 */}</div>;
}
```

---

## 4. 수정해야 할 파일 목록

### 4.1 새로 생성할 파일

#### ✅ `src/lib/api/market.ts` - 시세 API 함수
```typescript
/**
 * 시세 관련 API 함수
 */
import { axiosInstance } from "../axios";

// 전체 종목 시세 조회
export async function getMarketQuotes(params) { ... }

// 관심종목 추가
export async function addFavoriteStock(userId, stockCode) { ... }

// 관심종목 삭제
export async function removeFavoriteStock(userId, stockCode) { ... }

// 최근 본 주식 조회
export async function getRecentStocks(userId) { ... }
```

#### ✅ `src/lib/api/company.ts` - 종목정보 API 함수
```typescript
/**
 * 종목정보 관련 API 함수
 */
import { axiosInstance } from "../axios";

// 종목 상세 정보 조회
export async function getCompanyInfo(stockCode, userId?) { ... }

// 종목 검색
export async function searchCompanies(query, limit?) { ... }
```

#### ✅ `src/types/market.ts` - 시세 타입 정의
```typescript
export interface MarketQuoteItem {
  stock_code: string;
  stock_name: string;
  current_price: number;
  vs_previous: number;
  change_rate: number;
  volume: number;
  trading_value: number;
  market_cap: number;
  trade_date: string;
  is_favorite: boolean;
}

export interface MarketQuoteResponse {
  items: MarketQuoteItem[];
  total: number;
  page: number;
  page_size: number;
  has_next: boolean;
}
```

#### ✅ `src/types/company.ts` - 종목정보 타입 정의
```typescript
export interface CompanyBasicInfo {
  companyName: string;
  stockCode: string;
  stockName: string;
  currentPrice: number;
  vsPrevious: number;
  previousClose: number;
  fluctuationRate: number;
  changeVs1d: number;
  changeVs1w: number;
  changeVs1m: number;
  changeVs2m: number;
  changeRate1d: number;
  changeRate1w: number;
  changeRate1m: number;
  changeRate2m: number;
  marketCap: number;
  isFavorite: boolean;
  // ... 기타 필드
}

export interface CompanyInfoResponse {
  basicInfo: CompanyBasicInfo;
  investmentIndicators: {...};
  profitabilityIndicators: {...};
  financialRatios: {...};
  quarterlyPerformance: [...];
  incomeStatements: [...];
  balanceSheets: [...];
  priceHistory: [...];
}
```

### 4.2 수정할 파일

#### 🔧 `src/lib/api/index.ts`
```typescript
// 새로운 API export 추가
export * from "./market";
export * from "./company";
```

#### 🔧 `src/app/page.tsx` - 홈페이지
```typescript
// Before: 하드코딩된 데이터
const marketTickers: MarketTickerCardProps[] = [...]

// After: API에서 데이터 가져오기
"use client";
import { useEffect, useState } from "react";
import { getMarketQuotes } from "@/lib/api";

// 데이터 변환 함수 추가
function transformToTickerProps(apiData): MarketTickerCardProps[] {
  return apiData.items.slice(0, 10).map(item => ({
    id: item.stock_code,
    name: item.stock_name,
    code: item.stock_code,
    price: `${item.current_price.toLocaleString()}원`,
    change: `${item.change_rate > 0 ? '+' : ''}${item.change_rate}%`,
    trend: item.change_rate >= 0 ? "up" : "down",
    logoSrc: "/icons/default-logo.svg",
    graph: item.change_rate >= 0 ? "icons/up-graph.svg" : "icons/down-graph.svg"
  }));
}
```

#### 🔧 `src/app/market-price/page.tsx` - 시세 페이지
```typescript
// Before: mockMarketRows 사용
const mockMarketRows = [...]

// After: API 연동
const [rows, setRows] = useState([]);
const [page, setPage] = useState(1);
const [totalPages, setTotalPages] = useState(1);

useEffect(() => {
  async function fetchMarketData() {
    const sortByMap = {
      "최근 본 주식": "recent",  // 별도 API 필요
      "체결량 순": "volume",
      "등락률 순": "change_rate",
      "거래 대금 순": "trading_value",
      "시가총액 순": "market_cap",
    };

    const result = await getMarketQuotes(
      sortByMap[selectedTab],
      "desc",
      page,
      50,
      userId  // 로그인 사용자 ID
    );

    // 데이터 변환
    const transformedData = result.items.map((item, index) => ({
      rank: (page - 1) * 50 + index + 1,
      name: item.stock_name,
      code: item.stock_code,
      price: `${item.current_price.toLocaleString()}원`,
      change: `${item.change_rate > 0 ? '+' : ''}${item.change_rate}%`,
      trend: item.change_rate >= 0 ? "up" : "down",
      volume: `${item.volume.toLocaleString()}주`,
      tradingValue: `${Math.floor(item.trading_value / 100000000)}억원`,
      marketCap: `${Math.floor(item.market_cap / 100000000)}억원`,
      isFavorite: item.is_favorite,
    }));

    setRows(transformedData);
    setTotalPages(Math.ceil(result.total / result.page_size));
  }

  fetchMarketData();
}, [selectedTab, page]);
```

#### 🔧 `src/components/home/TodayMarketSection.tsx`
- 현재는 수정 불필요 (props로 데이터 받음)
- 필요시 로딩 상태나 에러 처리 추가

#### 🔧 `src/components/market-price/StockInfoCard.tsx`
```typescript
// Before: 하드코딩된 데이터
const changeStats = [...]
const scoreBreakdowns = [...]

// After: props로 받아서 표시
interface StockInfoCardProps {
  stockCode: string;
}

export function StockInfoCard({ stockCode }: StockInfoCardProps) {
  const [data, setData] = useState<CompanyInfoResponse | null>(null);

  useEffect(() => {
    async function fetchCompanyInfo() {
      const result = await getCompanyInfo(stockCode);
      setData(result);
    }
    fetchCompanyInfo();
  }, [stockCode]);

  if (!data) return <div>로딩 중...</div>;

  // data.basicInfo 활용해서 렌더링
}
```

---

## 5. 구현 단계별 가이드

### Step 1: 환경 설정
```bash
# .env.local 파일 생성 (프론트엔드 루트)
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000/api/v1
```

### Step 2: 타입 정의
1. `src/types/market.ts` 생성
2. `src/types/company.ts` 생성
3. FastAPI 응답 스키마와 1:1 매칭되도록 작성

### Step 3: API 함수 작성
1. `src/lib/api/market.ts` 생성
   - `getMarketQuotes()` 함수 작성
   - `addFavoriteStock()` 함수 작성
   - `removeFavoriteStock()` 함수 작성
   - `getRecentStocks()` 함수 작성

2. `src/lib/api/company.ts` 생성
   - `getCompanyInfo()` 함수 작성
   - `searchCompanies()` 함수 작성

3. `src/lib/api/index.ts` 업데이트
   ```typescript
   export * from "./market";
   export * from "./company";
   ```

### Step 4: 홈페이지 연동
1. `src/app/page.tsx` 수정
   - `"use client"` 추가
   - `useState`, `useEffect` import
   - API 호출 로직 추가
   - 데이터 변환 함수 작성
   - 로딩/에러 상태 처리

### Step 5: 시세 페이지 연동
1. `src/app/market-price/page.tsx` 수정
   - API 호출 로직으로 교체
   - 탭별 정렬 파라미터 연동
   - 페이지네이션 구현
   - 관심종목 추가/삭제 기능 구현

### Step 6: 종목 상세 연동
1. `src/components/market-price/StockInfoCard.tsx` 수정
   - API로 데이터 페칭
   - 차트 데이터 연동 (priceHistory)
   - 재무 지표 표시

### Step 7: 테스트
1. FastAPI 서버 실행: `cd SL-Back-end && venv/Scripts/uvicorn app.main:app --reload`
2. Next.js 서버 실행: `cd SL-Front-End && npm run dev`
3. http://localhost:3000 접속하여 확인

---

## 6. 백엔드 API 엔드포인트 정리

### 시세 API
```
GET /api/v1/market/quotes
Query Parameters:
  - sort_by: volume | change_rate | trading_value | market_cap | name
  - sort_order: asc | desc
  - page: 페이지 번호 (1부터 시작)
  - page_size: 페이지 크기 (1-100)
  - user_id: 사용자 ID (선택, UUID)

Response:
{
  "items": [...],
  "total": 2000,
  "page": 1,
  "page_size": 50,
  "has_next": true
}
```

### 종목정보 API
```
GET /api/v1/company/{stock_code}/info
Query Parameters:
  - user_id: 사용자 ID (선택, 관심종목 판단 및 최근 본 주식 기록)

Response:
{
  "basicInfo": {...},
  "investmentIndicators": {...},
  "profitabilityIndicators": {...},
  "financialRatios": {...},
  "quarterlyPerformance": [...],
  "incomeStatements": [...],
  "balanceSheets": [...],
  "priceHistory": [...]
}
```

### 종목 검색 API
```
GET /api/v1/company/search
Query Parameters:
  - query: 검색어 (종목명 또는 종목코드)
  - limit: 최대 결과 수 (기본 10)

Response:
[
  {
    "companyName": "삼성전자",
    "stockCode": "005930",
    "stockName": "삼성전자",
    "marketType": "KOSPI"
  },
  ...
]
```

### 관심종목 API
```
POST /api/v1/users/{user_id}/favorites
Body: { "stock_code": "005930" }

DELETE /api/v1/users/{user_id}/favorites/{stock_code}

GET /api/v1/users/{user_id}/favorites
Query Parameters:
  - page, page_size
```

### 최근 본 주식 API
```
GET /api/v1/users/{user_id}/recent-stocks
Query Parameters:
  - limit: 최대 개수 (기본 10)
```

---

## 7. 유용한 팁

### 데이터 변환 (camelCase ↔ snake_case)
FastAPI는 snake_case, Next.js는 camelCase를 주로 사용합니다.
백엔드에서 `serialization_alias`로 이미 camelCase로 변환해주고 있으니, 그대로 사용하면 됩니다.

### 에러 처리
```typescript
try {
  const data = await getMarketQuotes();
  setData(data);
} catch (error) {
  if (axios.isAxiosError(error)) {
    console.error("API 에러:", error.response?.data);
    // 사용자에게 에러 메시지 표시
  }
}
```

### 로딩 상태
```typescript
const [loading, setLoading] = useState(true);
const [error, setError] = useState<string | null>(null);

useEffect(() => {
  async function fetch() {
    try {
      setLoading(true);
      const data = await getMarketQuotes();
      setData(data);
    } catch (err) {
      setError("데이터를 불러오는데 실패했습니다.");
    } finally {
      setLoading(false);
    }
  }
  fetch();
}, []);

if (loading) return <div>로딩 중...</div>;
if (error) return <div>{error}</div>;
```

### React Query 사용 (선택사항)
더 나은 데이터 페칭을 원한다면:
```typescript
import { useQuery } from "@tanstack/react-query";

function MarketPage() {
  const { data, isLoading, error } = useQuery({
    queryKey: ["market-quotes", selectedTab, page],
    queryFn: () => getMarketQuotes(selectedTab, "desc", page),
  });

  // ...
}
```

---

## 8. 디버깅 가이드

### API 호출이 안 될 때
1. 백엔드 서버 실행 확인: http://localhost:8000/docs
2. 프론트 환경변수 확인: `.env.local` 파일 존재 및 내용 확인
3. 브라우저 개발자 도구 Network 탭에서 요청 확인
4. CORS 에러 확인 (백엔드에서 CORS 설정 필요)

### 타입 에러가 날 때
1. 백엔드 응답 구조와 타입 정의 일치 확인
2. `console.log()`로 실제 응답 데이터 확인
3. optional 필드는 `?` 사용

### 렌더링이 안 될 때
1. `console.log()`로 데이터 확인
2. 배열/객체 구조 확인
3. null/undefined 체크 확인

---

## 요약

1. **타입 정의** (`src/types/`) → FastAPI 응답과 매칭
2. **API 함수** (`src/lib/api/`) → axios로 HTTP 요청
3. **컴포넌트** → useEffect + useState로 데이터 페칭
4. **데이터 변환** → API 응답을 UI 컴포넌트가 원하는 형태로 변환
5. **에러 처리** → try-catch + 로딩/에러 상태 관리

이제 시작할 준비가 되었습니다! 🚀
