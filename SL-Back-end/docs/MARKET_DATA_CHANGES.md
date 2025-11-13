## 마켓 데이터 변경 요약 (Feat/PROJ-46/company_info)

### 개요
- 종목 정보·시세·관심종목·최근 본 종목 API가 모두 동일한 시세 필드를 노출하도록 정리했습니다. 전일 종가, 기간별 변동량/변동률, 거래량/거래대금/시가총액 등 프런트 요구값을 즉시 사용할 수 있습니다.
- 과거 데이터가 없을 때 잘못된 수치가 내려가는 문제를 방지하는 헬퍼를 추가했고, 재무제표 정렬을 최신 분기 우선으로 고정했습니다.
- 스테이징 반영 전 백엔드에서 바뀐 내용을 빠르게 확인할 수 있도록 정리한 문서입니다.

### 종목 정보 (`GET /api/v1/company/{stock_code}/info`)
- `basicInfo` 변경사항
  - `previousClose`, `changevs1d`, `changeRate1d` 필드를 추가했고 기존 1주/1개월/2개월 필드는 그대로 유지됩니다.
  - 기간별 변동량/변동률은 기준 데이터가 없으면 `null` 로 내려가므로, 프런트에서 결측 처리를 쉽게 할 수 있습니다.
- `_calculate_period_change_rates` 는 더 이상 과거 값이 없을 때 0을 넣지 않고 `null` 을 반환합니다.
- 재무제표 조회는 `bsns_year DESC + quarter_priority` 로 정렬되어 항상 최신 분기부터 계산됩니다.

### 시세 목록 (`GET /api/v1/market/quotes`)
- 모든 아이템에 `previousClose` 를 추가했습니다.
- `_calculate_previous_close` 헬퍼가 `currentPrice` 혹은 `vsPrevious` 가 없을 경우 `null` 을 반환해 잘못된 값 노출을 방지합니다.

### 관심/최근 본 종목
- 관심종목(`GET /api/v1/users/{user_id}/favorites`)과 최근 본 종목(`GET /api/v1/users/{user_id}/recent-stocks`) 항목이 다음 필드를 추가로 제공합니다.
  - `previousClose`, `volume`, `tradingValue`, `marketCap`
  - 기존 `currentPrice`, `changeRate`, 타임스탬프는 그대로 유지됩니다.
- 두 API 모두 동일한 전일 종가 계산 로직을 사용하여 응답 일관성을 확보했습니다.
- 최신 거래일이 존재하지 않는 경우에도 리스트 자체는 그대로 내려가도록 쿼리를 분기하고, 가격 관련 필드는 `null` 로 채워집니다. 초기 데이터 적재 이전에도 프런트 UI 를 구성할 수 있습니다.

### 위험 요소 및 후속 과제
- `StockPrice` 데이터가 비어 있으면 리스트 자체가 비게 되므로, 프런트는 `items.length === 0` 케이스를 대비해 빈 상태 UI 를 유지해야 합니다.
- `UserStockService` 가 최신 거래일을 찾지 못하면 조인 조건상 가격 필드가 모두 `null` 이 되므로, 데이터 초기화 시 최신 거래일이 보장되도록 하거나, `latest_trade_date` 가 없을 때 가격 필드를 명시적으로 `null` 처리하는 추가 로직을 고려해 주세요.
