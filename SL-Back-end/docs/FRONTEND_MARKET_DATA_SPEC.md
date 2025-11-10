## 프런트엔드용 마켓 데이터 명세

이 브랜치에서 변경된 API 계약을 정리해 프런트 시세/종목 화면 개발 시 참고할 수 있도록 했습니다.

---

### 1. 전체 시세 리스트 `GET /api/v1/market/quotes`

| Query | Type | Default | 설명 |
| --- | --- | --- | --- |
| `sort_by` | `volume` \| `change_rate` \| `trading_value` \| `market_cap` \| `name` | `market_cap` | 정렬 기준 |
| `sort_order` | `asc` \| `desc` | `desc` | 정렬 방향 |
| `page` | int ≥ 1 | `1` | 페이지 번호 |
| `page_size` | int 1-100 | `50` | 페이지 크기 |
| `user_id` | UUID (선택) | - | 관심종목 여부 플래그용 |

**응답 예시**

```json
{
  "items": [
    {
      "stockCode": "005930",
      "stockName": "삼성전자",
      "currentPrice": 71200,
      "previousClose": 70100,
      "vsPrevious": 1100,
      "changeRate": 1.57,
      "volume": 12345678,
      "tradingValue": 81234567890,
      "marketCap": 424000000000000,
      "tradeDate": "2024-06-10",
      "isFavorite": true
    }
  ],
  "total": 2500,
  "page": 1,
  "pageSize": 50,
  "hasNext": true
}
```

`previousClose = currentPrice - vsPrevious`. 두 값 중 하나라도 없으면 `previousClose` 는 `null` 입니다.

---

### 2. 종목 상세 `GET /api/v1/company/{stock_code}/info`

`basicInfo` 에 추가된 필드:

| Field | Type | 설명 |
| --- | --- | --- |
| `previousClose` | number \| null | 전일 종가 |
| `changevs1d` | number \| null | 1거래일 전 대비 절대 변화값 (원) |
| `changeRate1d` | number \| null | 1거래일 전 대비 변동률 (%) |
| `changevs1w`, `changevs1m`, `changevs2m` | number \| null | 기존 필드 유지 |
| `changeRate1w`, `changeRate1m`, `changeRate2m` | number \| null | 기존 필드 유지 |

기간별 값은 과거 데이터가 없으면 `null` 로 내려오므로 UI 에서 대시(`-`) 등으로 처리해주세요.

---

### 3. 관심종목 `GET /api/v1/users/{user_id}/favorites`

```json
{
  "items": [
    {
      "stockCode": "000660",
      "stockName": "SK하이닉스",
      "currentPrice": 180000,
      "changeRate": 2.31,
      "previousClose": 176000,
      "volume": 4567890,
      "tradingValue": 8123456780,
      "marketCap": 131000000000000,
      "createdAt": "2024-06-10T02:11:52.123456"
    }
  ],
  "total": 8
}
```

### 4. 최근 본 종목 `GET /api/v1/users/{user_id}/recent-stocks?limit=10`

관심종목과 동일한 필드를 반환하며, 타임스탬프만 `viewedAt` 입니다.

| Field | 비고 |
| --- | --- |
| `previousClose` | 관심종목과 동일 계산 |
| `volume/tradingValue/marketCap` | 최신 거래일 기준 |
| `viewedAt` | 최근 조회 시각, 내림차순 정렬 |

---

### 5. 참고 사항

- 관심 등록/해제 API (`POST /users/{id}/favorites`, `DELETE /users/{id}/favorites/{code}`) 는 계약 변화가 없습니다.
- 모든 응답은 camelCase alias 로 직렬화되므로 TS 타입에서 그대로 사용하면 됩니다.
- 변동 필드가 `null` 인 경우를 대비해 UI 포맷터에 fallback 문자열을 준비해 주세요.
