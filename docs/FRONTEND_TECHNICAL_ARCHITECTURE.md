# Stock Lab Frontend 기술 아키텍처

## 목차
1. [시스템 개요](#시스템-개요)
2. [기술 스택](#기술-스택)
3. [아키텍처 설계](#아키텍처-설계)
4. [프로젝트 구조](#프로젝트-구조)
5. [핵심 기능](#핵심-기능)
6. [상태 관리](#상태-관리)
7. [API 통신](#api-통신)
8. [성능 최적화](#성능-최적화)
9. [배포 및 운영](#배포-및-운영)

---

## 시스템 개요

### 프로젝트 목적
Stock Lab Frontend는 **퀀트 투자 백테스팅 플랫폼**의 사용자 인터페이스로, 개인 투자자가 데이터 기반의 투자 전략을 수립하고 검증할 수 있는 웹 애플리케이션입니다.

### 핵심 기능
1. **백테스트 UI**: 150+ 팩터 기반 전략 설정 및 시뮬레이션 결과 시각화
2. **백테스트 스트리밍**: WebSocket 기반 실시간 백테스트 스트리밍
3. **AI 어시스턴트**: SSE 기반 실시간 챗봇 인터페이스
4. **전략 랭킹**: 공개 전략 랭킹 및 복제 기능
5. **커뮤니티**: 전략 공유, 게시판, 댓글 시스템
6. **시장 데이터**: 실시간 시세 및 차트 시각화
7. **자동매매**: 키움증권 API 연동 자동매매 대시보드

### 시스템 요구사항
- **실시간 스트리밍**: WebSocket 및 SSE 기반 백테스트 진행률 및 AI 응답 스트리밍
- **대용량 데이터 처리**: 5년치 차트 데이터 무한 스크롤

---

## 기술 스택

### 프레임워크
```
Next.js 16.0+
- App Router (RSC 지원)
- Server Components (SSR 최적화)
- React 19.2 (Concurrent Features)
- React Compiler 활성화 (자동 메모이제이션)
```

### 상태 관리
```
Zustand 5.0+
- 경량 상태 관리 라이브러리
- 서버/클라이언트 상태 분리
- 하이드레이션 이슈 해결

TanStack Query 5.90+
- 서버 상태 관리 및 캐싱
- 무한 스크롤 (useInfiniteQuery)
- 실시간 폴링 (refetchInterval)
```

### UI/스타일링
```
Tailwind CSS 3.4+
- 유틸리티 퍼스트 CSS
- 반응형 디자인 (sm/md/lg/xl)
- 다크모드 지원 (ThemeContext)

Framer Motion 12+
- 애니메이션 라이브러리
- 페이지 전환 효과
- 컴포넌트 상태 애니메이션
```

### 차트 라이브러리
```
AMCharts 5
- 수익률 차트
- 포트폴리오 비중 차트
- 드래그 줌/패닝 지원

Lightweight Charts 5.0+
- 캔들스틱 차트
- 실시간 시세 차트
- 볼륨 차트
```

### 유틸리티
```
Axios 1.13+
- HTTP 클라이언트
- 요청/응답 인터셉터
- JWT 토큰 자동 주입

date-fns 4.1+
- 날짜 포맷팅
- 한국어 로케일

React Markdown 10.1+
- AI 응답 렌더링
- GFM 지원
- 코드 하이라이팅
```

### 개발 도구
```
TypeScript 5+
- 타입 안정성
- 인터페이스 기반 개발

Biome 2.2+
- ESLint + Prettier 대체
- 빠른 린팅/포맷팅
```

---

## 아키텍처 설계

### 1. 레이어드 아키텍처

```
┌─────────────────────────────────────────────────────────────┐
│                   Presentation Layer                        │
│  (App Router Pages, Server Components, Client Components)   │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│                   State Management Layer                    │
│  (Zustand Stores, TanStack Query Hooks)                     │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│                   Data Access Layer                         │
│  (API Functions, Axios Instances)                           │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│                   External Services                         │
│  (Backend API, Chatbot API, Kiwoom API)                     │
└─────────────────────────────────────────────────────────────┘
```

### 2. 컴포넌트 아키텍처

```
┌─────────────────────────────────────────────────────────────┐
│                     Root Layout                             │
│  ┌──────────────────────────────────────────────────────────┤
│  │  Providers (QueryClient, Theme, Auth)                    │
│  ├──────────────────────────────────────────────────────────┤
│  │  ┌─────────────┐  ┌──────────────────────────────────┐   │
│  │  │   SideNav   │  │           Main Content           │   │
│  │  │ (서버/클라이언트│  │  ┌──────────────────────────┐    │   │
│  │  │  하이브리드 )  │  │  │    Page Components       │    │   │
│  │  │             │  │  │  (Server Components)     │    │   │
│  │  │             │  │  ├──────────────────────────┤    │   │
│  │  │             │  │  │    Feature Components    │    │   │
│  │  │             │  │  │  (Client Components)     │    │   │
│  │  └─────────────┘  │  └──────────────────────────┘    │   │
│  └──────────────────────────────────────────────────────────┤
│  ┌──────────────────────────────────────────────────────┐   │
│  │  Global Components (Modal, FloatingChatWidget)       │   │
│  └──────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

### 3. 데이터 흐름

```
사용자 인터랙션
       ↓
[Client Component] → Zustand Store (UI 상태)
                   → TanStack Query (서버 상태)
       ↓
[API Layer] → Axios Instance → Backend API
       ↓
[Response] → Query Cache 업데이트 → UI 리렌더링
```

---

## 프로젝트 구조

```
SL-Front-End/
├── src/
│   ├── app/                    # Next.js App Router
│   │   ├── layout.tsx          # 루트 레이아웃 (SideNav, Providers)
│   │   ├── page.tsx            # 홈 페이지
│   │   ├── providers.tsx       # 전역 Provider (QueryClient, Auth)
│   │   │
│   │   ├── quant/              # 퀀트 백테스팅
│   │   │   ├── page.tsx        # 전략 목록 (포트폴리오)
│   │   │   ├── new/            # 새 전략 생성
│   │   │   ├── result/         # 백테스트 결과
│   │   │   └── auto-trading/   # 자동매매 대시보드
│   │   │
│   │   ├── ai-assistant/       # AI 챗봇
│   │   ├── market-price/       # 시세 조회
│   │   ├── news/               # 뉴스
│   │   ├── ranking/            # 전략 랭킹
│   │   ├── community/          # 커뮤니티
│   │   ├── mypage/             # 마이페이지
│   │   ├── login/              # 로그인
│   │   └── signup/             # 회원가입
│   │
│   ├── components/             # UI 컴포넌트 (40+ 컴포넌트)
│   │   ├── common/             # 공통 UI 컴포넌트
│   │   │   ├── Button.tsx      # 버튼
│   │   │   ├── Input.tsx       # 입력 필드
│   │   │   ├── Select.tsx      # 셀렉트 박스
│   │   │   ├── Dropdown.tsx    # 드롭다운
│   │   │   ├── ToggleSwitch.tsx # 토글 스위치
│   │   │   ├── Panel.tsx       # 패널 컨테이너
│   │   │   └── ...
│   │   │
│   │   ├── quant/              # 퀀트 관련 컴포넌트
│   │   │   ├── tabs/           # 탭 컴포넌트
│   │   │   ├── sections/       # 섹션 컴포넌트
│   │   │   ├── result/         # 결과 표시 컴포넌트
│   │   │   ├── ui/             # UI 서브 컴포넌트
│   │   │   ├── layout/         # 레이아웃 컴포넌트
│   │   │   ├── list/           # 목록 컴포넌트
│   │   │   ├── FactorSelectionModal.tsx
│   │   │   ├── PortfolioCard.tsx
│   │   │   └── ...
│   │   │
│   │   ├── ai-assistant/       # AI 챗봇 컴포넌트
│   │   │   ├── ChatInterface.tsx
│   │   │   ├── ChatMessage.tsx
│   │   │   ├── StreamingChatMessage.tsx
│   │   │   ├── QuestionnaireView.tsx
│   │   │   ├── RecommendationView.tsx
│   │   │   ├── renderers/      # 메시지 렌더러
│   │   │   └── ...
│   │   │
│   │   ├── home/               # 홈 화면 컴포넌트
│   │   ├── auth/               # 인증 컴포넌트
│   │   ├── modal/              # 모달 컴포넌트
│   │   ├── market-price/       # 시세 컴포넌트
│   │   ├── news/               # 뉴스 컴포넌트
│   │   ├── community/          # 커뮤니티 컴포넌트
│   │   ├── mypage/             # 마이페이지 컴포넌트
│   │   ├── SideNav.tsx         # 사이드 네비게이션
│   │   └── CandlestickChart.tsx # 캔들스틱 차트
│   │
│   ├── hooks/                  # 커스텀 훅 (20+ 훅)
│   │   ├── useBacktestQuery.ts # 백테스트 React Query
│   │   ├── useChatStream.ts    # SSE 채팅 스트리밍
│   │   ├── useFactorsQuery.ts  # 팩터 조회
│   │   ├── useStrategyList.ts  # 전략 목록
│   │   ├── useCommunityQuery.ts # 커뮤니티
│   │   ├── useMarketQuoteQuery.ts # 시세 조회
│   │   ├── useBuyCondition.ts  # 매수 조건 관리
│   │   ├── useSellCondition.ts # 매도 조건 관리
│   │   └── ...
│   │
│   ├── stores/                 # Zustand 상태 관리
│   │   ├── authStore.ts        # 인증 상태
│   │   ├── backtestConfigStore.ts # 백테스트 설정
│   │   ├── quantTabStore.ts    # 탭 상태
│   │   ├── chatStore.ts        # 채팅 상태
│   │   └── aiHelperStore.ts    # AI 헬퍼 상태
│   │
│   ├── lib/                    # 유틸리티 및 API
│   │   ├── axios.ts            # Axios 인스턴스
│   │   ├── query-client.ts     # React Query 클라이언트
│   │   ├── formatters.ts       # 포맷팅 유틸리티
│   │   ├── date-utils.ts       # 날짜 유틸리티
│   │   ├── markdown-utils.ts   # 마크다운 유틸리티
│   │   ├── api/                # API 함수 (18개 모듈)
│   │   │   ├── auth.ts         # 인증 API
│   │   │   ├── backtest.ts     # 백테스트 API
│   │   │   ├── strategy.ts     # 전략 API
│   │   │   ├── chatbot.ts      # 챗봇 API
│   │   │   ├── community.ts    # 커뮤니티 API
│   │   │   ├── market-quote.ts # 시세 API
│   │   │   ├── kiwoom.ts       # 키움 API
│   │   │   └── ...
│   │   └── auth/               # 인증 유틸리티
│   │
│   ├── types/                  # TypeScript 타입 정의 (16개 파일)
│   │   ├── api.ts              # API 요청/응답 타입
│   │   ├── factor.ts           # 팩터 타입
│   │   ├── strategy.ts         # 전략 타입
│   │   ├── message.ts          # 메시지 타입
│   │   ├── ui-language.ts      # AI UI 언어 타입
│   │   └── ...
│   │
│   ├── contexts/               # React Context
│   │   └── ThemeContext.tsx    # 테마 컨텍스트
│   │
│   ├── constants/              # 상수 정의
│   ├── styles/                 # 전역 스타일
│   └── utils/                  # 유틸리티 함수
│
├── public/                     # 정적 파일
├── next.config.ts              # Next.js 설정
├── tailwind.config.js          # Tailwind 설정
├── tsconfig.json               # TypeScript 설정
└── biome.json                  # Biome 린터 설정
```

---

## 핵심 기능

### 1. 백테스팅 시스템

#### 전략 설정 흐름
```
전략 생성 페이지 (/quant/new)
       ↓
┌─────────────────────────────────────────────────────────────┐
│  1. 기본 설정                                                 │
│     - 전략 이름, 기간, 초기 자본금                                │
│     - 수수료율, 슬리피지                                        │
├─────────────────────────────────────────────────────────────┤
│  2. 매수 조건 설정                                             │
│     - 팩터 선택 (FactorSelectionModal)                        │
│     - 조건식 구성 (A and B or C)                               │
│     - 우선순위 팩터, 종목당 비중                                  │
├─────────────────────────────────────────────────────────────┤
│  3. 매도 조건 설정                                             │
│     - 목표가/손절가 (토글)                                      │
│     - 보유 기간 (토글)                                         │
│     - 조건 매도 (토글)                                         │
├─────────────────────────────────────────────────────────────┤
│  4. 매매 대상 설정                                             │
│     - 전체 종목 / 테마 선택 / 개별 종목                            │
└─────────────────────────────────────────────────────────────┘
       ↓
백테스트 실행 (SSE 진행률 스트리밍)
       ↓
결과 페이지 (/quant/result/[id])
```

#### Zustand 상태 관리 (backtestConfigStore)
```typescript
interface BacktestConfigStore extends BacktestRunRequest {
  // UI 전용 상태
  buyConditionsUI: BuyConditionUI[];
  sellConditionsUI: SellConditionUI[];

  // 조건 관리 함수
  addBuyConditionUI: () => void;
  updateBuyConditionUI: (id: string, updates: Partial<BuyConditionUI>) => void;
  removeBuyConditionUI: (id: string) => void;

  // API 변환
  syncUIToAPI: () => void;
  getBacktestRequest: () => BacktestRunRequest;

  // 초기화
  reset: () => void;
}
```

#### React Query 훅 (useBacktestQuery)
```typescript
// 쿼리 키 팩토리
export const backtestQueryKey = {
  all: ["backtest"] as const,
  lists: () => [...backtestQueryKey.all, "list"] as const,
  detail: (id: string) => [...backtestQueryKey.details(), id] as const,
  trades: (id: string) => [...backtestQueryKey.detail(id), "trades"] as const,
  status: (id: string) => [...backtestQueryKey.detail(id), "status"] as const,
};

// 백테스트 실행
export function useRunBacktestMutation();

// 결과 조회
export function useBacktestResultQuery(backtestId: string);

// 상태 폴링 (2초 간격)
export function useBacktestStatusQuery(backtestId: string, enabled = true);

// 매매 내역 무한 스크롤
export function useBacktestTradesInfiniteQuery(backtestId: string);
```

### 2. AI 어시스턴트 시스템

#### SSE 기반 스트리밍 (useChatStream)
```typescript
interface UseChatStreamReturn {
  content: string;           // 누적된 응답 내용
  isStreaming: boolean;      // 스트리밍 진행 중 여부
  connectionState: SSEConnectionState; // 연결 상태
  error: Error | null;       // 에러 객체
  sendMessage: (message: string) => void;  // 메시지 전송
  abort: () => void;         // 스트리밍 중단
  retry: () => void;         // 재시도
}

// SSE 이벤트 타입
type SSEEventUnion =
  | { type: "stream_start"; messageId: string }
  | { type: "stream_chunk"; content: string }
  | { type: "stream_end" }
  | { type: "ui_language"; data: UILanguage }
  | { type: "error"; message: string };
```

#### UI Language 시스템
```typescript
// AI 응답에 따른 동적 UI 렌더링
type UILanguageType =
  | "questionnaire_start"    // 설문 시작
  | "questionnaire_progress" // 설문 진행
  | "strategy_recommendation" // 전략 추천
  | "backtest_configuration"; // 백테스트 설정

// ChatInterface 컴포넌트에서 타입별 렌더링
if (ui_language.type === "questionnaire_start") {
  return <QuestionnaireView ... />;
}
if (ui_language.type === "strategy_recommendation") {
  return <RecommendationView ... />;
}
```

### 3. 차트 시각화

#### 수익률 차트 (AMCharts 5)
```typescript
// 기능
- 누적 수익률 곡선
- 벤치마크 비교 (KOSPI/KOSDAQ)
- 드래그 줌/패닝
- 호버 툴팁

// 데이터 무한 스크롤
useBacktestYieldPointsInfiniteQuery(backtestId, limit = 100);
```

#### 캔들스틱 차트 (Lightweight Charts)
```typescript
// 기능
- OHLC 캔들
- 볼륨 차트
- 이동평균선 오버레이
- 크로스헤어
```

---

## 상태 관리

### 1. Zustand 스토어 구조

#### authStore - 인증 상태
```typescript
interface AuthStore {
  isSessionExpired: boolean;     // 세션 만료 여부
  setSessionExpired: (expired: boolean) => void;
  authErrorMessage: string | null; // 인증 에러 메시지
  setAuthErrorMessage: (message: string | null) => void;
}
```

#### backtestConfigStore - 백테스트 설정
```typescript
// 모든 백테스트 파라미터를 전역으로 관리
// UI 상태와 API 요청 형식을 분리하여 관리
// syncUIToAPI()로 변환 후 getBacktestRequest()로 API 요청 생성
```

#### chatStore - 채팅 상태
```typescript
interface ChatStore {
  sessionId: string | null;
  messages: Message[];
  isStreaming: boolean;
  addMessage: (message: Message) => void;
  clearMessages: () => void;
}
```

### 2. TanStack Query 활용

#### 쿼리 클라이언트 설정
```typescript
// lib/query-client.ts
function makeQueryClient() {
  return new QueryClient({
    defaultOptions: {
      queries: {
        staleTime: 60 * 1000,        // 1분
        gcTime: 5 * 60 * 1000,       // 5분
        retry: 1,
        refetchOnWindowFocus: false,
      },
    },
  });
}

// 싱글톤 패턴 (브라우저 환경)
let browserQueryClient: QueryClient | undefined = undefined;

export function getQueryClient() {
  if (isServer) {
    return makeQueryClient();
  }
  if (!browserQueryClient) {
    browserQueryClient = makeQueryClient();
  }
  return browserQueryClient;
}
```

#### 쿼리 키 팩토리 패턴
```typescript
export const backtestQueryKey = {
  all: ["backtest"] as const,
  lists: () => [...backtestQueryKey.all, "list"] as const,
  list: (params?: PaginationParams) => [...backtestQueryKey.lists(), params] as const,
  detail: (id: string) => [...backtestQueryKey.details(), id] as const,
};
```

---

## API 통신

### 1. Axios 인스턴스 설정

```typescript
// lib/axios.ts
export const axiosInstance = axios.create({
  baseURL: CLIENT_BASE_URL,       // 환경변수에서 가져옴
  timeout: 180000,                // 3분 (백테스트 용)
  headers: { "Content-Type": "application/json" },
  withCredentials: true,          // 쿠키 포함
});

// 요청 인터셉터 - JWT 토큰 자동 주입
axiosInstance.interceptors.request.use((config) => {
  const token = getAuthTokenFromCookie();
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// 응답 인터셉터 - 에러 핸들링
axiosInstance.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      // 세션 만료 모달 표시
      useAuthStore.getState().setSessionExpired(true);
    }
    return Promise.reject(error);
  }
);
```

### 2. API 모듈 구조

| 모듈 | 기능 | 엔드포인트 |
|------|------|-----------|
| auth.ts | 인증 | 로그인, 회원가입, 로그아웃 |
| backtest.ts | 백테스트 | 실행, 결과 조회, 상태 폴링 |
| strategy.ts | 전략 | 내 전략, 공개 전략, 랭킹 |
| chatbot.ts | AI 챗봇 | 메시지 전송, SSE 스트리밍 |
| community.ts | 커뮤니티 | 게시글, 댓글, 좋아요 |
| market-quote.ts | 시세 | 종목 시세, 차트 데이터 |
| kiwoom.ts | 키움 연동 | 계좌 연동, 주문 실행 |
| factors.ts | 팩터 | 팩터 목록, 카테고리 |
| themes.ts | 테마 | 테마 목록, 종목 |
| news.ts | 뉴스 | 뉴스 목록, 상세 |

---

## 성능 최적화

### 1. React Compiler 활성화
```typescript
// next.config.ts
const nextConfig: NextConfig = {
  reactCompiler: true,  // 자동 메모이제이션
};
```

### 2. 서버 컴포넌트 활용
```typescript
// SSR에서 데이터 프리페칭
// app/quant/result/[id]/page.tsx
export default async function ResultPage({ params }: { params: { id: string } }) {
  // 서버에서 데이터 로드
  const result = await getBacktestResult(params.id, true);
  return <ResultClient initialData={result} />;
}
```

### 3. 무한 스크롤
```typescript
// 대용량 데이터 처리
export function useBacktestTradesInfiniteQuery(backtestId: string, limit = 50) {
  return useInfiniteQuery({
    queryKey: [...backtestQueryKey.trades(backtestId), { limit }],
    queryFn: ({ pageParam = 1 }) => getBacktestTrades(backtestId, { page: pageParam, limit }),
    getNextPageParam: (lastPage) => {
      const { page, totalPages } = lastPage.pagination;
      return page < totalPages ? page + 1 : undefined;
    },
  });
}
```

### 4. 이미지 최적화
```typescript
// next/image 사용
<Image
  src="/logo.png"
  alt="Stock Lab"
  width={120}
  height={40}
  priority  // LCP 최적화
/>
```

### 5. 코드 스플리팅
```typescript
// 동적 임포트
const CandlestickChart = dynamic(
  () => import("@/components/CandlestickChart"),
  { loading: () => <ChartSkeleton /> }
);
```

---

## 배포 및 운영

### 1. 환경 변수

```bash
# .env.local
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000
NEXT_PUBLIC_CHATBOT_API_URL=http://localhost:8003
```

### 2. Docker 배포

#### Dockerfile
```dockerfile
FROM node:22-alpine AS builder

WORKDIR /app
COPY package*.json ./
RUN npm ci

COPY . .
RUN npm run build

FROM node:22-alpine AS runner
WORKDIR /app

COPY --from=builder /app/.next/standalone ./
COPY --from=builder /app/.next/static ./.next/static
COPY --from=builder /app/public ./public

EXPOSE 3000
CMD ["node", "server.js"]
```

#### next.config.ts
```typescript
const nextConfig: NextConfig = {
  output: "standalone",  // Docker 최적화
};
```

### 3. 개발 서버

```bash
# 의존성 설치
npm install

# 개발 서버 실행
npm run dev

# 타입 체크
npm run typecheck

# 린트
npm run lint

# 프로덕션 빌드
npm run build
npm run start
```

### 4. 반응형 브레이크포인트

| 브레이크포인트 | 화면 크기 | 레이아웃 |
|---------------|----------|---------|
| default | <640px | 모바일 (햄버거 메뉴) |
| sm | 640px+ | 태블릿 (축소 사이드바) |
| md | 768px+ | 태블릿 확장 |
| lg | 1024px+ | 데스크톱 (확장 사이드바) |
| xl | 1280px+ | 대형 데스크톱 |

---

## 부록

### A. 주요 의존성 버전

| 패키지 | 버전 | 용도 |
|--------|------|------|
| next | 16.0.1 | 프레임워크 |
| react | 19.2.0 | UI 라이브러리 |
| @tanstack/react-query | 5.90.5 | 서버 상태 관리 |
| zustand | 5.0.8 | 클라이언트 상태 관리 |
| axios | 1.13.1 | HTTP 클라이언트 |
| tailwindcss | 3.4.17 | CSS 프레임워크 |
| framer-motion | 12.23.24 | 애니메이션 |
| @amcharts/amcharts5 | 5.14.4 | 차트 |
| lightweight-charts | 5.0.9 | 캔들스틱 차트 |

### B. 참고 자료

- [Next.js 공식 문서](https://nextjs.org/docs)
- [TanStack Query 공식 문서](https://tanstack.com/query/latest)
- [Zustand 공식 문서](https://zustand-demo.pmnd.rs/)
- [Tailwind CSS 공식 문서](https://tailwindcss.com/docs)
- [AMCharts 5 문서](https://www.amcharts.com/docs/v5/)

---

**최종 수정일**: 2025-01-15
**작성자**: Frontend - 박정섭
