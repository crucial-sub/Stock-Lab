# Momentum·Fundamental Score 연동 시 프론트 작업 목록

## 1. 개요
- 백엔드 `companies` 테이블(`SL-Back-end/app/models/company.py:37-47`)과 관련 API에서 `momentum_score`, `fundamental_score` 필드를 지원하도록 확장되었습니다.
- `/backtest/run` 요청(`SL-Back-end/app/api/routes/backtest.py:90-107, 348-364`)과 `/company-info/{stockCode}` 응답(`SL-Back-end/app/api/routes/company_info.py:33-47, 433-446`)에 신규 필드가 노출되므로, 프론트 전략 빌더·회사 정보 화면에서 필수 입력/표시 요소를 추가해야 합니다.
- 아래 체크리스트를 완료하면 프론트가 모멘텀/펀더멘털 점수를 필터·표시·전달할 수 있습니다.

## 2. 백엔드 노출 지점 요약
| 구분 | 필드 | 위치 | 설명 |
| --- | --- | --- | --- |
| Company Info API | `momentumScore`, `fundamentalScore` | `CompanyInfoResponse.basic_info` (`SL-Back-end/app/api/routes/company_info.py:433-446`) | 종목 상세 패널의 기본정보에 점수 포함 |
| Backtest Request | `minMomentumScore`, `minFundamentalScore` | `BacktestRequest` (`SL-Back-end/app/api/routes/backtest.py:90-107`) | 전략 실행 시 유니버스 필터 파라미터 |
| Factors List | `MOMENTUM_SCORE`, `FUNDAMENTAL_SCORE` | `/api/backtest/factors/list` (`SL-Back-end/app/api/routes/backtest.py:717-745`) | 팩터 선택 UI에서 노출 필요 |

## 3. 프론트 수정 체크리스트

### 3.1 타입 · 전역 상태
1. `BacktestRunRequest`에 선택적 범위 필드를 추가  
   - 파일: `SL-Front-End/src/types/api.ts:28-69`  
   - 필드명 제안: `min_momentum_score?: number | null;`, `min_fundamental_score?: number | null;`  
   - 주석/alias는 백엔드 `minMomentumScore`와 camelCase 그대로 맞추고, 직렬화 시 snake_case → camelCase 매핑 여부 확인.

2. Zustand 스토어 확장  
   - 파일: `SL-Front-End/src/stores/backtestConfigStore.ts:9-150`  
   - 해야 할 일:
     - `BacktestConfigStore` 인터페이스에 새 필드와 setter (`setMinMomentumScore`, `setMinFundamentalScore`) 추가.
     - `defaultConfig`에 초기값(예: `null` 또는 제품 기획 값) 정의.
     - `getBacktestRequest()` 반환 객체에 필드 포함.
     - `reset()` 호출 시 값이 초기화되도록 `defaultConfig`만으로 처리되는지 확인.

3. 백테스트 실행 훅/버튼 연결  
   - `useRunBacktestMutation`(`SL-Front-End/src/hooks/useBacktestQuery.ts:22-62`)와 `runBacktest` API(`SL-Front-End/src/lib/api/backtest.ts:1-40`)는 `BacktestRunRequest` 타입을 그대로 사용하므로 타입 업데이트만으로 직렬화가 되지만, `BacktestRunButton` 등 요청을 조립하는 컴포넌트가 별도 수동 객체를 만들고 있지 않은지 확인 (현재는 `useBacktestConfigStore().getBacktestRequest()` 사용). 만약 수동 객체가 있다면 동일 필드를 추가.

### 3.2 전략 빌더 UI
1. 입력 컨트롤 배치  
   - 추천 위치: `TargetSelectionTab` 또는 별도 "필터" 섹션 (파일: `SL-Front-End/src/components/quant/TargetSelectionTab.tsx`)  
   - 컴포넌트 요구사항:
     - 범위를 0~100으로 제한한 Slider/Number Input 2개 (`minMomentumScore`, `minFundamentalScore`).  
     - `useBacktestConfigStore` setter에 연결하고, 상태 값이 `null`일 땐 "필터 미사용"으로 표시.  
     - 백테스트 요청에 들어가는 단위(점수)가 사용자에게 명확히 보이도록 라벨/툴팁 제공.

2. Preview / 전략 요약 반영  
   - 전략 확인 패널(`ShowBacktestStrategyButton`이 호출하는 요약)에 두 점수 필터 값이 포함되도록 텍스트 업데이트.  
   - 향후 결과 화면에 "최소 점수 조건"을 표기할 위치가 있다면 동일 값 노출.

3. UX Validation  
   - 입력 범위가 0~100을 벗어나면 즉시 교정하거나 validation 메시지를 보여줍니다.  
   - 두 값 모두 `null`일 때는 요청 payload에서 키를 완전히 생략하거나 `null` 전송 중 한 가지로 정책을 결정하고, 백엔드 기대값과 맞춥니다(현재 FastAPI 모델은 `None` 허용).

### 3.3 회사 정보 화면(추후/진행 중)
1. 종목 상세 컴포넌트가 구현되어 있다면, `company.basic_info.momentumScore`와 `fundamentalScore`를 시각화 요소로 추가합니다.  
2. 아직 상세 화면이 없다면, API 스텁/타입 정의 (`src/types/stock.ts` 등)에 필드를 넣어두고 UI 설계 시 바로 사용할 수 있게 합니다.  
3. 디자인 가이드: 0~100 범위를 사용하는 Meter/Chip을 사용하고, "데이터 미존재 시 - 또는 'N/A' 출력" 규칙 정의.

### 3.4 팩터/조건 선택 리소스
1. 정적 팩터 상수(`SL-Front-End/src/constants/factors.ts`) 및 팩터 선택 UI에서 `MOMENTUM_SCORE`/`FUNDAMENTAL_SCORE`가 노출되도록 항목을 추가.  
2. 만약 서버에서 내려준 팩터 리스트만을 사용하는 UI라면, 새 ID가 지원되는지(아이콘/설명 존재 여부, 카테고리 매핑) 확인.  
3. 조건식 빌더가 `{MOMENTUM_SCORE}` 같은 토큰을 허용하도록 파서/자동완성 사전을 최신화.

## 4. QA & 테스트 플랜
- [ ] `useBacktestConfigStore.getBacktestRequest()` 결과가 백엔드 FastAPI 모델과 동일한 키 집합을 갖는지 확인 (`console.log`/unit test).  
- [ ] 전략 빌더에서 값 입력 → `/backtest/run` 호출 시 네트워크 패킷에 `minMomentumScore`, `minFundamentalScore`가 포함되는지 확인.  
- [ ] 값이 `null`일 때 필드가 빠지거나 `null`로 직렬화되는 동작을 백엔드 기대와 맞춰 통일.  
- [ ] 회사 정보 API 호출 후 화면에 두 점수가 렌더링되는지 스냅샷 테스트 또는 Storybook으로 검증.  
- [ ] 팩터 선택 모달/자동완성에서 새 팩터가 정상적으로 필터링·검색되는지 수동 테스트.  
- [ ] 회귀: 기존 전략 실행/회사 정보 조회 플로우에서 콘솔 에러나 타입 오류가 없는지 확인.

위 목록을 베이스라인으로 사용하면 프론트가 모멘텀·펀더멘털 점수 기능을 일관되게 소비할 수 있습니다.
