# Stock Lab Frontend UI 컴포넌트 명세서

## 목차
1. [개요](#개요)
2. [페이지 구조](#페이지-구조)
3. [공통 컴포넌트](#공통-컴포넌트)
4. [퀀트 백테스팅 컴포넌트](#퀀트-백테스팅-컴포넌트)
5. [AI 어시스턴트 컴포넌트](#ai-어시스턴트-컴포넌트)
6. [차트 컴포넌트](#차트-컴포넌트)
7. [커뮤니티 컴포넌트](#커뮤니티-컴포넌트)
8. [디자인 시스템](#디자인-시스템)

---

## 개요

### 컴포넌트 설계 원칙
1. **단일 책임**: 각 컴포넌트는 하나의 역할만 수행
2. **재사용성**: 공통 컴포넌트는 `components/common/`에 분리
3. **컴포지션**: 작은 컴포넌트를 조합하여 복잡한 UI 구성
4. **서버/클라이언트 분리**: RSC와 클라이언트 컴포넌트 명확히 구분

### 컴포넌트 분류
| 분류 | 위치 | 특징 |
|------|------|------|
| 공통 UI | `components/common/` | 재사용 가능한 기본 UI 요소 |
| 기능별 | `components/{feature}/` | 특정 기능에 종속된 컴포넌트 |
| 레이아웃 | `app/layout.tsx` | 전역 레이아웃 |
| 페이지 | `app/{route}/page.tsx` | 라우트별 페이지 컴포넌트 |

---

## 페이지 구조

### 라우트 맵

```
/                       # 홈 (랜딩 페이지)
├── /login              # 로그인
├── /signup             # 회원가입
│
├── /quant              # 퀀트 백테스팅
│   ├── /quant          # 전략 목록 (포트폴리오)
│   ├── /quant/new      # 새 전략 생성
│   ├── /quant/result/[id] # 백테스트 결과
│   └── /quant/auto-trading # 자동매매 대시보드
│
├── /ai-assistant       # AI 챗봇
│
├── /market-price       # 시세 조회
│   └── /market-price/[stockCode] # 종목 상세
│
├── /news               # 뉴스
│   └── /news/[id]      # 뉴스 상세
│
├── /ranking            # 전략 랭킹
│
├── /community          # 커뮤니티
│   ├── /community      # 게시글 목록
│   ├── /community/[id] # 게시글 상세
│   └── /community/write # 글쓰기
│
└── /mypage             # 마이페이지
    ├── /mypage         # 프로필
    └── /mypage/settings # 설정
```

### 루트 레이아웃 (layout.tsx)

```typescript
/**
 * 루트 레이아웃 (반응형)
 *
 * 구조:
 * ┌─────────────────────────────────────────┐
 * │ <html>                                  │
 * │   <body className="flex h-screen">     │
 * │     <Providers>                         │
 * │       <SideNav />                       │
 * │       <main className="flex-1">        │
 * │         {children}                      │
 * │       </main>                           │
 * │       <SessionExpiredModal />           │
 * │       <FloatingChatWidget />            │
 * │     </Providers>                        │
 * │   </body>                               │
 * │ </html>                                 │
 * └─────────────────────────────────────────┘
 */
export default async function RootLayout({ children }) {
  const cookieStore = await cookies();
  const hasToken = !!cookieStore.get("access_token")?.value;

  return (
    <html lang="ko">
      <body className="flex h-screen overflow-hidden antialiased">
        <Providers>
          <SideNav serverHasToken={hasToken} />
          <main className="flex-1 h-full overflow-auto bg-background pt-16 sm:pt-0">
            {children}
          </main>
        </Providers>
      </body>
    </html>
  );
}
```

---

## 공통 컴포넌트

### 1. Button

```typescript
/**
 * 기본 버튼 컴포넌트
 *
 * @param variant - "primary" | "secondary" | "outline" | "ghost" | "danger"
 * @param size - "sm" | "md" | "lg"
 * @param disabled - 비활성화 여부
 * @param loading - 로딩 상태
 */
interface ButtonProps {
  variant?: "primary" | "secondary" | "outline" | "ghost" | "danger";
  size?: "sm" | "md" | "lg";
  disabled?: boolean;
  loading?: boolean;
  children: React.ReactNode;
  onClick?: () => void;
}

// 사용 예시
<Button variant="primary" size="md" loading={isSubmitting}>
  백테스트 실행
</Button>
```

### 2. Input

```typescript
/**
 * 입력 필드 컴포넌트
 *
 * @param type - "text" | "email" | "password" | "number"
 * @param label - 라벨 텍스트
 * @param error - 에러 메시지
 * @param suffix - 접미사 (예: "만원", "%")
 */
interface InputProps {
  type?: "text" | "email" | "password" | "number";
  label?: string;
  placeholder?: string;
  value: string;
  onChange: (value: string) => void;
  error?: string;
  suffix?: string;
}

// 사용 예시
<Input
  label="초기 투자금"
  type="number"
  value={capital}
  onChange={setCapital}
  suffix="만원"
/>
```

### 3. Select

```typescript
/**
 * 셀렉트 박스 컴포넌트
 *
 * @param options - 선택 옵션 배열
 * @param value - 선택된 값
 * @param onChange - 변경 핸들러
 */
interface SelectProps {
  options: { value: string; label: string }[];
  value: string;
  onChange: (value: string) => void;
  placeholder?: string;
}

// 사용 예시
<Select
  options={[
    { value: "daily", label: "일봉" },
    { value: "weekly", label: "주봉" },
  ]}
  value={period}
  onChange={setPeriod}
/>
```

### 4. Dropdown

```typescript
/**
 * 드롭다운 메뉴 컴포넌트
 *
 * 검색 기능 및 다중 선택 지원
 */
interface DropdownProps {
  items: DropdownItem[];
  value: string | string[];
  onChange: (value: string | string[]) => void;
  searchable?: boolean;
  multiple?: boolean;
  placeholder?: string;
}

// 사용 예시
<Dropdown
  items={themes}
  value={selectedThemes}
  onChange={setSelectedThemes}
  searchable
  multiple
  placeholder="테마를 선택하세요"
/>
```

### 5. ToggleSwitch

```typescript
/**
 * 토글 스위치 컴포넌트
 *
 * 매도 조건 토글 등에 사용
 */
interface ToggleSwitchProps {
  checked: boolean;
  onChange: (checked: boolean) => void;
  label?: string;
  disabled?: boolean;
}

// 사용 예시
<ToggleSwitch
  checked={useTargetPrice}
  onChange={setUseTargetPrice}
  label="목표가/손절가 사용"
/>
```

### 6. Panel

```typescript
/**
 * 패널 컨테이너 컴포넌트
 *
 * 섹션 구분 및 그룹핑에 사용
 */
interface PanelProps {
  title?: string;
  description?: string;
  children: React.ReactNode;
  collapsible?: boolean;
}

// 사용 예시
<Panel title="매수 조건 설정" description="종목 선정 기준을 설정합니다">
  {/* 매수 조건 폼 */}
</Panel>
```

### 7. Modal (SessionExpiredModal)

```typescript
/**
 * 세션 만료 모달
 *
 * 전역에서 인증 오류 시 자동 표시
 */
interface SessionExpiredModalProps {
  isOpen: boolean;
  message?: string | null;
  onClose: () => void;
}

// 사용 (providers.tsx에서 전역 관리)
<SessionExpiredModal
  isOpen={isSessionExpired || !!authErrorMessage}
  message={authErrorMessage}
  onClose={() => {
    setSessionExpired(false);
    setAuthErrorMessage(null);
  }}
/>
```

---

## 퀀트 백테스팅 컴포넌트

### 1. PortfolioDashboard

```typescript
/**
 * 포트폴리오 대시보드 (전략 목록 페이지)
 *
 * 위치: /quant
 *
 * 구조:
 * ┌─────────────────────────────────────────┐
 * │ 헤더 (전략 생성 버튼)                    │
 * ├─────────────────────────────────────────┤
 * │ CreatePortfolioCard (새 전략 카드)       │
 * ├─────────────────────────────────────────┤
 * │ PortfolioCard × N (전략 목록)            │
 * └─────────────────────────────────────────┘
 */
export function PortfolioDashboard() {
  const { data: strategies, isLoading } = useStrategyListQuery();

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
      <CreatePortfolioCard />
      {strategies?.map((strategy) => (
        <PortfolioCard key={strategy.id} strategy={strategy} />
      ))}
    </div>
  );
}
```

### 2. PortfolioCard

```typescript
/**
 * 전략 카드 컴포넌트
 *
 * 표시 정보:
 * - 전략 이름
 * - 총 수익률
 * - 연환산 수익률
 * - 최대 낙폭
 * - 상태 (완료/진행중/실패)
 */
interface PortfolioCardProps {
  strategy: {
    id: string;
    name: string;
    totalReturn: number;
    annualizedReturn: number;
    maxDrawdown: number;
    status: "completed" | "running" | "failed";
    createdAt: string;
  };
}

export function PortfolioCard({ strategy }: PortfolioCardProps) {
  return (
    <Link href={`/quant/result/${strategy.id}`}>
      <div className="p-6 bg-white rounded-xl shadow-sm hover:shadow-md transition">
        <h3 className="font-bold text-lg">{strategy.name}</h3>
        <div className="mt-4 grid grid-cols-2 gap-4">
          <Stat label="총 수익률" value={`${strategy.totalReturn}%`} />
          <Stat label="연환산" value={`${strategy.annualizedReturn}%`} />
          <Stat label="MDD" value={`${strategy.maxDrawdown}%`} />
        </div>
      </div>
    </Link>
  );
}
```

### 3. FactorSelectionModal

```typescript
/**
 * 팩터 선택 모달
 *
 * 기능:
 * - 팩터 카테고리별 필터링 (가치/성장/퀄리티/모멘텀/규모)
 * - 팩터 검색
 * - 서브팩터(함수) 선택
 * - 인자 선택 (예: 이동평균 일수)
 */
interface FactorSelectionModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSelect: (factor: Factor, subFactor?: SubFactor, argument?: string) => void;
  selectedFactorId?: number;
}

export function FactorSelectionModal({ isOpen, onClose, onSelect }) {
  const { data: factors } = useFactorsQuery();
  const { data: subFactors } = useSubFactorsQuery();

  return (
    <Modal isOpen={isOpen} onClose={onClose} title="팩터 선택">
      <div className="flex">
        {/* 카테고리 탭 */}
        <CategoryTabs categories={FACTOR_CATEGORIES} />

        {/* 팩터 목록 */}
        <div className="flex-1">
          <SearchInput placeholder="팩터 검색..." />
          <div className="grid grid-cols-2 gap-2">
            {factors?.map((factor) => (
              <FactorItem
                key={factor.id}
                factor={factor}
                onSelect={onSelect}
              />
            ))}
          </div>
        </div>

        {/* 서브팩터 패널 (선택 시 표시) */}
        {selectedFactor && (
          <SubFactorPanel
            subFactors={subFactors}
            onSelect={(sf, arg) => onSelect(selectedFactor, sf, arg)}
          />
        )}
      </div>
    </Modal>
  );
}
```

### 4. 백테스트 설정 탭 컴포넌트

```typescript
/**
 * 탭 구조 (/quant/new)
 *
 * ┌─────────────────────────────────────────────────────────┐
 * │ [기본설정] [매수조건] [매도조건] [매매대상]               │
 * ├─────────────────────────────────────────────────────────┤
 * │                                                         │
 * │  탭 내용                                                 │
 * │                                                         │
 * └─────────────────────────────────────────────────────────┘
 */

// 기본 설정 탭
export function BasicSettingsTab() {
  const { setStrategyName, setStartDate, setEndDate } = useBacktestConfigStore();

  return (
    <div className="space-y-6">
      <Input label="전략 이름" onChange={setStrategyName} />
      <DateRangePicker
        startDate={startDate}
        endDate={endDate}
        onStartChange={setStartDate}
        onEndChange={setEndDate}
      />
      <Input label="초기 투자금" suffix="만원" type="number" />
      <Input label="수수료율" suffix="%" type="number" />
    </div>
  );
}

// 매수 조건 탭
export function BuyConditionTab() {
  const { buyConditionsUI, addBuyConditionUI, updateBuyConditionUI } = useBacktestConfigStore();

  return (
    <div className="space-y-4">
      {buyConditionsUI.map((condition) => (
        <ConditionRow
          key={condition.id}
          condition={condition}
          onUpdate={(updates) => updateBuyConditionUI(condition.id, updates)}
          onOpenFactorModal={() => openModal(condition.id)}
        />
      ))}
      <Button variant="outline" onClick={addBuyConditionUI}>
        + 조건 추가
      </Button>
    </div>
  );
}

// 매도 조건 탭
export function SellConditionTab() {
  const { target_and_loss, hold_days, setTargetAndLoss, setHoldDays } = useBacktestConfigStore();

  return (
    <div className="space-y-6">
      {/* 목표가/손절가 섹션 */}
      <Panel title="목표가/손절가">
        <ToggleSwitch checked={!!target_and_loss} onChange={toggleTargetLoss} />
        {target_and_loss && (
          <div className="grid grid-cols-2 gap-4">
            <Input label="목표가" suffix="%" value={target_and_loss.target_gain} />
            <Input label="손절가" suffix="%" value={target_and_loss.stop_loss} />
          </div>
        )}
      </Panel>

      {/* 보유 기간 섹션 */}
      <Panel title="보유 기간">
        <ToggleSwitch checked={!!hold_days} onChange={toggleHoldDays} />
        {hold_days && (
          <div className="grid grid-cols-2 gap-4">
            <Input label="최소 보유일" suffix="일" />
            <Input label="최대 보유일" suffix="일" />
          </div>
        )}
      </Panel>
    </div>
  );
}

// 매매 대상 탭
export function TradeTargetsTab() {
  const { trade_targets, setTradeTargets } = useBacktestConfigStore();

  return (
    <div className="space-y-6">
      {/* 전체 종목 토글 */}
      <ToggleSwitch
        label="전체 종목 사용"
        checked={trade_targets.use_all_stocks}
        onChange={(checked) => setTradeTargets({ ...trade_targets, use_all_stocks: checked })}
      />

      {!trade_targets.use_all_stocks && (
        <>
          {/* 테마 선택 */}
          <ThemeSelector
            selectedThemes={trade_targets.selected_themes}
            onChange={(themes) => setTradeTargets({ ...trade_targets, selected_themes: themes })}
          />

          {/* 개별 종목 선택 */}
          <StockSelector
            selectedStocks={trade_targets.selected_stocks}
            onChange={(stocks) => setTradeTargets({ ...trade_targets, selected_stocks: stocks })}
          />
        </>
      )}
    </div>
  );
}
```

### 5. 백테스트 결과 컴포넌트

```typescript
/**
 * 백테스트 결과 페이지 (/quant/result/[id])
 *
 * 구조:
 * ┌────────────────────────────────────────────────────────────┐
 * │ 헤더 (전략 이름, 기간, 공유 버튼)                           │
 * ├────────────────────────────────────────────────────────────┤
 * │ 통계 카드 (총 수익률, 연환산, MDD, 샤프, 승률)              │
 * ├────────────────────────────────────────────────────────────┤
 * │ 수익률 차트 (YieldChart)                                   │
 * ├────────────────────────────────────────────────────────────┤
 * │ 탭: [매매내역] [AI 분석] [상세 통계]                        │
 * │   ├─ TradesTable (무한 스크롤)                              │
 * │   ├─ AIAnalysis (마크다운 렌더링)                           │
 * │   └─ DetailedStats                                         │
 * └────────────────────────────────────────────────────────────┘
 */

// 통계 카드
export function StatisticsCards({ statistics }: { statistics: BacktestResult["statistics"] }) {
  return (
    <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
      <StatCard
        label="총 수익률"
        value={statistics.totalReturn}
        format="percent"
        color={statistics.totalReturn >= 0 ? "green" : "red"}
      />
      <StatCard label="연환산 수익률" value={statistics.annualizedReturn} format="percent" />
      <StatCard label="최대 낙폭" value={statistics.maxDrawdown} format="percent" color="red" />
      <StatCard label="샤프 지수" value={statistics.sharpeRatio} format="number" />
      <StatCard label="승률" value={statistics.winRate} format="percent" />
    </div>
  );
}

// 매매 내역 테이블 (무한 스크롤)
export function TradesTable({ backtestId }: { backtestId: string }) {
  const { data, fetchNextPage, hasNextPage, isFetchingNextPage } =
    useBacktestTradesInfiniteQuery(backtestId);

  const trades = data?.pages.flatMap((page) => page.data) ?? [];

  return (
    <div className="overflow-auto">
      <table className="w-full">
        <thead>
          <tr>
            <th>종목</th>
            <th>매수일</th>
            <th>매도일</th>
            <th>수익률</th>
          </tr>
        </thead>
        <tbody>
          {trades.map((trade, idx) => (
            <TradeRow key={idx} trade={trade} />
          ))}
        </tbody>
      </table>

      {hasNextPage && (
        <Button onClick={() => fetchNextPage()} loading={isFetchingNextPage}>
          더 보기
        </Button>
      )}
    </div>
  );
}
```

---

## AI 어시스턴트 컴포넌트

### 1. ChatInterface

```typescript
/**
 * AI 챗봇 메인 인터페이스
 *
 * UI Language 타입에 따른 동적 렌더링:
 * - questionnaire_start/progress: QuestionnaireView
 * - strategy_recommendation: RecommendationView
 * - backtest_configuration: BacktestConfigurationView
 */
export function ChatInterface({
  chatResponse,
  isLoading,
  onAnswerSelect,
  messages,
  questionHistory,
}: ChatInterfaceProps) {
  if (!chatResponse?.ui_language) return null;

  const { ui_language } = chatResponse;

  // 설문조사 화면
  if (ui_language.type === "questionnaire_start" ||
      ui_language.type === "questionnaire_progress") {
    return <QuestionnaireView ... />;
  }

  // 전략 추천 결과
  if (ui_language.type === "strategy_recommendation") {
    return <RecommendationView uiLanguage={ui_language} />;
  }

  return null;
}
```

### 2. QuestionnaireView

```typescript
/**
 * AI 설문조사 화면
 *
 * 투자 성향 파악을 위한 단계별 질문 UI
 *
 * 구조:
 * ┌─────────────────────────────────────────┐
 * │ Q1. 투자 목적이 무엇인가요?              │
 * ├─────────────────────────────────────────┤
 * │ ○ 장기 자산 증식                        │
 * │ ○ 단기 수익 추구                        │
 * │ ○ 안정적인 배당 수익                    │
 * │ ○ 공격적인 성장 투자                    │
 * └─────────────────────────────────────────┘
 */
interface QuestionnaireViewProps {
  uiLanguage: UILanguage;
  isLoading: boolean;
  onAnswerSelect: (questionId: string, optionId: string, answerText: string) => void;
  messages?: Message[];
  questionHistory?: QuestionHistory[];
}

export function QuestionnaireView({
  uiLanguage,
  isLoading,
  onAnswerSelect,
}: QuestionnaireViewProps) {
  const question = uiLanguage.current_question;

  return (
    <div className="max-w-2xl mx-auto p-6">
      {/* 질문 */}
      <div className="bg-white rounded-2xl border p-5 shadow-sm">
        <p className="text-lg font-semibold text-gray-900">
          Q{uiLanguage.current_step}. {question.text}
        </p>
      </div>

      {/* 선택지 */}
      <div className="mt-4 space-y-3">
        {question.options.map((option) => (
          <button
            key={option.id}
            onClick={() => onAnswerSelect(question.id, option.id, option.label)}
            disabled={isLoading}
            className="w-full flex items-start gap-3 rounded-2xl border px-4 py-4
                       hover:border-purple-500 hover:bg-purple-50 transition"
          >
            <div className="text-lg">{option.icon}</div>
            <div className="flex-1 text-left">
              <h3 className="font-bold text-gray-900">{option.label}</h3>
              <p className="text-sm text-gray-600">{option.description}</p>
            </div>
          </button>
        ))}
      </div>
    </div>
  );
}
```

### 3. RecommendationView

```typescript
/**
 * AI 전략 추천 결과 화면
 *
 * 구조:
 * ┌─────────────────────────────────────────┐
 * │ 분석 결과                               │
 * │ "당신의 투자 성향은 가치 투자형입니다"    │
 * ├─────────────────────────────────────────┤
 * │ 추천 전략                               │
 * │ ┌─────────────────────────────────────┐ │
 * │ │ 피터 린치 전략                      │ │
 * │ │ PEG 레이쇼 기반 가치 성장 전략       │ │
 * │ │ 예상 수익률: 연 20-30%              │ │
 * │ │ [백테스트 실행]                     │ │
 * │ └─────────────────────────────────────┘ │
 * └─────────────────────────────────────────┘
 */
export function RecommendationView({ uiLanguage }: { uiLanguage: UILanguage }) {
  return (
    <div className="max-w-3xl mx-auto p-6 space-y-6">
      {/* 분석 결과 */}
      <div className="bg-gradient-to-r from-purple-500 to-indigo-600 rounded-2xl p-6 text-white">
        <h2 className="text-xl font-bold">투자 성향 분석 결과</h2>
        <p className="mt-2">{uiLanguage.analysis_summary}</p>
      </div>

      {/* 추천 전략 카드 */}
      <div className="space-y-4">
        {uiLanguage.strategies.map((strategy) => (
          <StrategyCard key={strategy.id} strategy={strategy} />
        ))}
      </div>
    </div>
  );
}
```

### 4. StreamingChatMessage

```typescript
/**
 * SSE 스트리밍 채팅 메시지
 *
 * 실시간으로 AI 응답을 렌더링
 * 마크다운 지원 (GFM, 코드 하이라이팅)
 */
interface StreamingChatMessageProps {
  content: string;
  isStreaming: boolean;
}

export function StreamingChatMessage({ content, isStreaming }: StreamingChatMessageProps) {
  return (
    <div className="flex gap-3">
      <Avatar type="ai" />
      <div className="flex-1 bg-gray-50 rounded-2xl px-5 py-4">
        <ReactMarkdown
          remarkPlugins={[remarkGfm]}
          rehypePlugins={[rehypeHighlight, rehypeRaw]}
          components={markdownComponents}
        >
          {content}
        </ReactMarkdown>
        {isStreaming && <span className="animate-pulse">▌</span>}
      </div>
    </div>
  );
}
```

### 5. FloatingChatWidget

```typescript
/**
 * 플로팅 챗봇 위젯
 *
 * 모든 페이지에서 우측 하단에 표시
 * 클릭 시 채팅 패널 토글
 */
export function FloatingChatWidget() {
  const [isOpen, setIsOpen] = useState(false);
  const { sendMessage, content, isStreaming } = useChatStream(sessionId);

  return (
    <>
      {/* 플로팅 버튼 */}
      <button
        onClick={() => setIsOpen(true)}
        className="fixed bottom-6 right-6 w-14 h-14 rounded-full bg-purple-600
                   text-white shadow-lg hover:bg-purple-700 transition z-50"
      >
        <ChatIcon />
      </button>

      {/* 채팅 패널 */}
      {isOpen && (
        <div className="fixed bottom-24 right-6 w-96 h-[500px] bg-white rounded-2xl
                        shadow-2xl overflow-hidden z-50">
          <ChatPanel
            onClose={() => setIsOpen(false)}
            sendMessage={sendMessage}
            content={content}
            isStreaming={isStreaming}
          />
        </div>
      )}
    </>
  );
}
```

---

## 차트 컴포넌트

### 1. YieldChart (AMCharts 5)

```typescript
/**
 * 수익률 차트
 *
 * 기능:
 * - 누적 수익률 곡선
 * - 벤치마크 비교선 (KOSPI/KOSDAQ)
 * - 드래그 줌
 * - 호버 툴팁
 */
interface YieldChartProps {
  data: {
    date: string;
    value: number;
    benchmarkCumReturn?: number;
  }[];
}

export function YieldChart({ data }: YieldChartProps) {
  const chartRef = useRef<am5.Root | null>(null);

  useEffect(() => {
    const root = am5.Root.new("chartdiv");

    const chart = root.container.children.push(
      am5xy.XYChart.new(root, {
        panX: true,
        panY: false,
        wheelX: "panX",
        wheelY: "zoomX",
      })
    );

    // X축 (날짜)
    const xAxis = chart.xAxes.push(
      am5xy.DateAxis.new(root, {
        baseInterval: { timeUnit: "day", count: 1 },
        renderer: am5xy.AxisRendererX.new(root, {}),
      })
    );

    // Y축 (수익률)
    const yAxis = chart.yAxes.push(
      am5xy.ValueAxis.new(root, {
        numberFormat: "#.#'%'",
        renderer: am5xy.AxisRendererY.new(root, {}),
      })
    );

    // 포트폴리오 수익률 시리즈
    const portfolioSeries = chart.series.push(
      am5xy.LineSeries.new(root, {
        name: "포트폴리오",
        xAxis,
        yAxis,
        valueYField: "value",
        valueXField: "date",
        stroke: am5.color(0x7c3aed), // purple-600
      })
    );

    // 벤치마크 시리즈
    const benchmarkSeries = chart.series.push(
      am5xy.LineSeries.new(root, {
        name: "KOSPI",
        xAxis,
        yAxis,
        valueYField: "benchmarkCumReturn",
        valueXField: "date",
        stroke: am5.color(0x6b7280), // gray-500
        strokeDasharray: [5, 5],
      })
    );

    portfolioSeries.data.setAll(data);
    benchmarkSeries.data.setAll(data);

    chartRef.current = root;

    return () => root.dispose();
  }, [data]);

  return <div id="chartdiv" className="w-full h-[400px]" />;
}
```

### 2. CandlestickChart (Lightweight Charts)

```typescript
/**
 * 캔들스틱 차트
 *
 * 기능:
 * - OHLC 캔들
 * - 볼륨 차트
 * - 크로스헤어
 * - 실시간 업데이트
 */
interface CandlestickChartProps {
  data: {
    time: string;
    open: number;
    high: number;
    low: number;
    close: number;
    volume?: number;
  }[];
}

export function CandlestickChart({ data }: CandlestickChartProps) {
  const chartContainerRef = useRef<HTMLDivElement>(null);
  const chartRef = useRef<IChartApi | null>(null);

  useEffect(() => {
    if (!chartContainerRef.current) return;

    const chart = createChart(chartContainerRef.current, {
      layout: {
        background: { type: ColorType.Solid, color: 'white' },
        textColor: '#333',
      },
      grid: {
        vertLines: { color: '#e0e0e0' },
        horzLines: { color: '#e0e0e0' },
      },
      crosshair: {
        mode: CrosshairMode.Normal,
      },
    });

    // 캔들스틱 시리즈
    const candlestickSeries = chart.addCandlestickSeries({
      upColor: '#ef4444',     // red (상승)
      downColor: '#3b82f6',   // blue (하락)
      borderVisible: false,
      wickUpColor: '#ef4444',
      wickDownColor: '#3b82f6',
    });

    candlestickSeries.setData(data);

    // 볼륨 시리즈
    const volumeSeries = chart.addHistogramSeries({
      color: '#94a3b8',
      priceFormat: { type: 'volume' },
      priceScaleId: '',
    });

    volumeSeries.setData(
      data.map((d) => ({
        time: d.time,
        value: d.volume || 0,
        color: d.close >= d.open ? '#fecaca' : '#bfdbfe',
      }))
    );

    chart.timeScale().fitContent();
    chartRef.current = chart;

    return () => chart.remove();
  }, [data]);

  return <div ref={chartContainerRef} className="w-full h-[500px]" />;
}
```

---

## 커뮤니티 컴포넌트

### 1. PostList

```typescript
/**
 * 게시글 목록
 *
 * 무한 스크롤 지원
 */
export function PostList({ category }: { category?: string }) {
  const { data, fetchNextPage, hasNextPage } = useCommunityPostsInfiniteQuery({ category });

  const posts = data?.pages.flatMap((page) => page.data) ?? [];

  return (
    <div className="space-y-4">
      {posts.map((post) => (
        <PostCard key={post.id} post={post} />
      ))}

      {hasNextPage && (
        <IntersectionObserver onIntersect={fetchNextPage}>
          <Spinner />
        </IntersectionObserver>
      )}
    </div>
  );
}
```

### 2. PostCard

```typescript
/**
 * 게시글 카드
 */
interface PostCardProps {
  post: {
    id: string;
    title: string;
    category: "STRATEGY" | "FREE" | "QNA";
    author: { nickname: string };
    viewCount: number;
    likeCount: number;
    commentCount: number;
    createdAt: string;
  };
}

export function PostCard({ post }: PostCardProps) {
  return (
    <Link href={`/community/${post.id}`}>
      <div className="p-4 bg-white rounded-lg border hover:shadow-md transition">
        <div className="flex items-center gap-2">
          <CategoryBadge category={post.category} />
          <h3 className="font-medium text-gray-900">{post.title}</h3>
        </div>
        <div className="mt-2 flex items-center gap-4 text-sm text-gray-500">
          <span>{post.author.nickname}</span>
          <span>조회 {post.viewCount}</span>
          <span>좋아요 {post.likeCount}</span>
          <span>댓글 {post.commentCount}</span>
        </div>
      </div>
    </Link>
  );
}
```

---

## 디자인 시스템

### 1. 색상 팔레트

```css
/* Tailwind CSS 커스텀 색상 */
:root {
  /* Primary (Purple) */
  --color-primary-50: #faf5ff;
  --color-primary-500: #8b5cf6;
  --color-primary-600: #7c3aed;
  --color-primary-700: #6d28d9;

  /* 수익/손실 */
  --color-gain: #ef4444;    /* red-500 (상승) */
  --color-loss: #3b82f6;    /* blue-500 (하락) */

  /* 상태 */
  --color-success: #22c55e; /* green-500 */
  --color-warning: #f59e0b; /* amber-500 */
  --color-error: #ef4444;   /* red-500 */

  /* 배경 */
  --color-background: #f9fafb;  /* gray-50 */
  --color-surface: #ffffff;

  /* 텍스트 */
  --color-text-primary: #111827;   /* gray-900 */
  --color-text-secondary: #6b7280; /* gray-500 */
}
```

### 2. 타이포그래피

```css
/* 폰트 스케일 */
.text-xs   { font-size: 0.75rem; }   /* 12px */
.text-sm   { font-size: 0.875rem; }  /* 14px */
.text-base { font-size: 1rem; }      /* 16px */
.text-lg   { font-size: 1.125rem; }  /* 18px */
.text-xl   { font-size: 1.25rem; }   /* 20px */
.text-2xl  { font-size: 1.5rem; }    /* 24px */
.text-3xl  { font-size: 1.875rem; }  /* 30px */

/* 폰트 두께 */
.font-normal   { font-weight: 400; }
.font-medium   { font-weight: 500; }
.font-semibold { font-weight: 600; }
.font-bold     { font-weight: 700; }
```

### 3. 그림자 & 모서리

```css
/* 그림자 */
.shadow-sm { box-shadow: 0 1px 2px rgba(0, 0, 0, 0.05); }
.shadow    { box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1), 0 1px 2px rgba(0, 0, 0, 0.06); }
.shadow-md { box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1); }
.shadow-lg { box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1); }

/* 모서리 반경 */
.rounded     { border-radius: 0.25rem; }  /* 4px */
.rounded-lg  { border-radius: 0.5rem; }   /* 8px */
.rounded-xl  { border-radius: 0.75rem; }  /* 12px */
.rounded-2xl { border-radius: 1rem; }     /* 16px */
.rounded-full { border-radius: 9999px; }
```

### 4. 반응형 브레이크포인트

```css
/* Tailwind 기본 브레이크포인트 */
sm:  640px   /* 태블릿 */
md:  768px   /* 태블릿 확장 */
lg:  1024px  /* 데스크톱 */
xl:  1280px  /* 대형 데스크톱 */
2xl: 1536px  /* 초대형 화면 */

/* 사용 예시 */
<div className="w-full sm:w-1/2 md:w-1/3 lg:w-1/4">
  /* 모바일: 100% → 태블릿: 50% → 태블릿확장: 33% → 데스크톱: 25% */
</div>
```

### 5. 애니메이션

```typescript
// Framer Motion 기본 트랜지션
const fadeIn = {
  initial: { opacity: 0 },
  animate: { opacity: 1 },
  exit: { opacity: 0 },
  transition: { duration: 0.2 },
};

const slideUp = {
  initial: { opacity: 0, y: 20 },
  animate: { opacity: 1, y: 0 },
  exit: { opacity: 0, y: -20 },
  transition: { duration: 0.3 },
};

// 사용 예시
<motion.div {...fadeIn}>
  <Modal />
</motion.div>
```

---

## 부록

### A. 컴포넌트 체크리스트

| 컴포넌트 | 접근성 | 반응형 | 다크모드 | 테스트 |
|---------|--------|--------|---------|--------|
| Button | ✅ | ✅ | ⏳ | ⏳ |
| Input | ✅ | ✅ | ⏳ | ⏳ |
| Modal | ✅ | ✅ | ⏳ | ⏳ |
| Chart | ⏳ | ✅ | ⏳ | ⏳ |
| Table | ✅ | ✅ | ⏳ | ⏳ |

### B. 향후 개선 사항

1. **다크모드**: ThemeContext 기반 다크모드 완전 지원
2. **접근성**: ARIA 속성 강화, 키보드 네비게이션
3. **테스트**: Jest + React Testing Library 도입
4. **스토리북**: 컴포넌트 문서화 및 시각적 테스트
5. **모바일 최적화**: 터치 제스처, 스와이프 네비게이션

---

**최종 수정일**: 2025-11-29
**작성자**: Frontend - 박중섭
