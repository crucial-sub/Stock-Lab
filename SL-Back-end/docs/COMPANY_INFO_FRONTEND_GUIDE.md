# 종목 재무 정보 모달/페이지 - 프론트엔드 개발 가이드

## 개요

종목 선택 시 해당 종목의 상세한 재무 정보를 볼 수 있는 모달 또는 페이지를 구현하기 위한 가이드입니다.

---

## API 엔드포인트

### 1. 종목 상세 정보 조회

**Endpoint:** `GET /api/v1/company/{stock_code}/info`

**설명:** 종목의 모든 재무/시세 정보를 한 번의 API 호출로 가져옵니다. `user_id` 쿼리를 추가하면 관심종목 여부를 판단하고 최근 본 종목에 기록합니다.

**Parameters:**
- `stock_code` (string, required): 종목 코드 (6자리, 예: `005930`)
- `user_id` (UUID, optional): 사용자 ID. 전달 시 `basicInfo.isFavorite` 가 활성화되고 최근 본 종목에 저장됩니다.

**Response:**

```json
{
  "basicInfo": {
    "companyName": "삼성전자",
    "stockCode": "005930",
    "stockName": "삼성전자",
    "marketType": "KOSPI",
    "currentPrice": 71200,
    "previousClose": 70100,
    "vsPrevious": 1100,
    "fluctuationRate": 1.57,
    "tradeDate": "2024-06-10",
    "changevs1d": 1100,
    "changevs1w": 2500,
    "changevs1m": 4200,
    "changevs2m": 6500,
    "changeRate1d": 1.57,
    "changeRate1w": 3.64,
    "changeRate1m": 6.27,
    "changeRate2m": 10.05,
    "marketCap": 500000000000000,
    "listedShares": 5969782550,
    "ceoName": "한종희",
    "listedDate": "1975-06-11",
    "industry": "전자부품 제조업",
    "momentumScore": 78,
    "fundamentalScore": 82,
    "isFavorite": true
  },
  "investmentIndicators": {
    "per": 15.5,
    "psr": 1.2,
    "pbr": 1.8,
    "pcr": null
  },
  "profitabilityIndicators": {
    "eps": 5000,
    "bps": 45000,
    "roe": 12.5,
    "roa": 8.3
  },
  "financialRatios": {
    "debtRatio": 45.2,
    "currentRatio": 250.5
  },
  "quarterlyPerformance": [
    {
      "period": "2024Q3",
      "revenue": 79000000000000,
      "operatingIncome": 10000000000000,
      "netIncome": 8000000000000,
      "netProfitMargin": 10.13,
      "netIncomeGrowth": 5.2,
      "operatingMargin": 12.66,
      "operatingIncomeGrowth": 3.5
    },
    {
      "period": "2024Q2",
      "revenue": 74000000000000,
      "operatingIncome": 9500000000000,
      "netIncome": 7600000000000,
      "netProfitMargin": 10.27,
      "netIncomeGrowth": -2.5,
      "operatingMargin": 12.84,
      "operatingIncomeGrowth": -1.8
    }
    // ... 최근 8분기 데이터
  ],
  "incomeStatements": [
    {
      "period": "2024Q3",
      "revenue": 79000000000000,
      "costOfSales": 50000000000000,
      "grossProfit": 29000000000000,
      "operatingIncome": 10000000000000,
      "netIncome": 8000000000000
    }
    // ... 최근 8분기 데이터
  ],
  "balanceSheets": [
    {
      "period": "2024Q3",
      "totalAssets": 450000000000000,
      "totalLiabilities": 150000000000000,
      "totalEquity": 300000000000000
    }
    // ... 최근 8분기 데이터
  ],
  "priceHistory": [
    {
      "date": "2020-01-02",
      "open": 55000,
      "high": 56000,
      "low": 54500,
      "close": 55500,
      "volume": 15000000
    }
    // ... 최근 5년 일별 데이터
  ]
}
```

---

### 2. 종목 검색

**Endpoint:** `GET /api/v1/company/search`

**설명:** 종목명 또는 종목 코드로 종목을 검색합니다.

**Parameters:**
- `query` (string, required): 검색어 (종목명 또는 종목 코드)
- `limit` (integer, optional): 최대 결과 수 (기본값: 10)

**Response:**

```json
[
  {
    "companyName": "삼성전자",
    "stockCode": "005930",
    "stockName": "삼성전자",
    "marketType": "KOSPI"
  },
  {
    "companyName": "삼성전자우",
    "stockCode": "005935",
    "stockName": "삼성전자우",
    "marketType": "KOSPI"
  }
]
```

---

## 데이터 구조 설명

### 1. 기본 정보 (basicInfo)

| 필드 | 타입 | 설명 |
|------|------|------|
| companyName | string | 정식 회사명 |
| stockCode | string | 종목 코드 (6자리) |
| stockName | string | 종목 약칭 |
| marketType | string | 시장 구분 (KOSPI/KOSDAQ/KONEX) |
| currentPrice | integer \| null | 최신 종가 (원) |
| previousClose | integer \| null | 전일 종가 (원) |
| vsPrevious | integer \| null | 전일 대비 증감액 (원) |
| fluctuationRate | float \| null | 전일 대비 변동률 (%) |
| tradeDate | string \| null | 기준 거래일 (YYYY-MM-DD) |
| changevs1d/1w/1m/2m | integer \| null | 기간별 절대 변화값 (원), 데이터 없으면 `null` |
| changeRate1d/1w/1m/2m | float \| null | 기간별 변동률 (%) |
| marketCap | integer \| null | 시가총액 (원) |
| listedShares | integer \| null | 발행 주식 수 (주) |
| ceoName | string \| null | 대표이사명 |
| listedDate | string \| null | 상장일 (YYYY-MM-DD) |
| industry | string \| null | 업종 |
| momentumScore | float \| null | 모멘텀 점수 (0~100) |
| fundamentalScore | float \| null | 펀더멘털 점수 (0~100) |
| isFavorite | boolean | 사용자 관심종목 여부 (`user_id` 전달 시 계산) |

### 2. 투자지표 (investmentIndicators)

| 필드 | 타입 | 설명 | 계산식 |
|------|------|------|--------|
| per | float | 주가수익비율 | 시가총액 / 순이익 |
| psr | float | 주가매출비율 | 시가총액 / 매출액 |
| pbr | float | 주가순자산비율 | 시가총액 / 자본총계 |
| pcr | float | 주가현금흐름비율 | 시가총액 / 영업현금흐름 (현재 null) |

### 3. 수익지표 (profitabilityIndicators)

| 필드 | 타입 | 설명 | 계산식 |
|------|------|------|--------|
| eps | float | 주당순이익 (원) | 당기순이익 / 발행주식수 |
| bps | float | 주당순자산 (원) | 자본총계 / 발행주식수 |
| roe | float | 자기자본이익률 (%) | (당기순이익 / 자본총계) × 100 |
| roa | float | 총자산이익률 (%) | (당기순이익 / 자산총계) × 100 |

### 4. 재무비율 (financialRatios)

| 필드 | 타입 | 설명 | 계산식 |
|------|------|------|--------|
| debtRatio | float | 부채비율 (%) | (부채총계 / 자본총계) × 100 |
| currentRatio | float | 유동비율 (%) | (유동자산 / 유동부채) × 100 |

### 5. 분기별 실적 (quarterlyPerformance)

| 필드 | 타입 | 설명 |
|------|------|------|
| period | string | 분기 (예: 2024Q3) |
| revenue | integer | 매출액 (원) |
| operatingIncome | integer | 영업이익 (원) |
| netIncome | integer | 당기순이익 (원) |
| netProfitMargin | float | 순이익률 (%) |
| netIncomeGrowth | float | 순이익 성장률 (%) |
| operatingMargin | float | 영업이익률 (%) |
| operatingIncomeGrowth | float | 영업이익 증가율 (%) |

### 6. 손익계산서 (incomeStatements)

| 필드 | 타입 | 설명 |
|------|------|------|
| period | string | 분기 |
| revenue | integer | 매출액 (원) |
| costOfSales | integer | 매출원가 (원) |
| grossProfit | integer | 매출총이익 (원) |
| operatingIncome | integer | 영업이익 (원) |
| netIncome | integer | 당기순이익 (원) |

### 7. 재무상태표 (balanceSheets)

| 필드 | 타입 | 설명 |
|------|------|------|
| period | string | 분기 |
| totalAssets | integer | 자산총계 (원) |
| totalLiabilities | integer | 부채총계 (원) |
| totalEquity | integer | 자본총계 (원) |

### 8. 일별 차트 데이터 (priceHistory)

| 필드 | 타입 | 설명 |
|------|------|------|
| date | string | 거래일자 (YYYY-MM-DD) |
| open | integer | 시가 (원) |
| high | integer | 고가 (원) |
| low | integer | 저가 (원) |
| close | integer | 종가 (원) |
| volume | integer | 거래량 (주) |

- 서비스는 기본적으로 5년 치 일별 데이터를 오름차순으로 제공합니다. 필요한 기간(예: 1Y/3Y)만 필터링해서 사용하세요.
- 거래량/가격이 없는 날은 존재하지 않으므로 별도 결측 처리 없이 바로 차트에 바인딩할 수 있습니다.

---

## UI 구성 제안

### 1. 모달/페이지 레이아웃

```
┌─────────────────────────────────────────────────────────────┐
│  [X]                    삼성전자 (005930)                    │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  [탭 1: 개요] [탭 2: 재무제표] [탭 3: 차트]                 │
│                                                               │
│  ┌─────────────────────────────────────────────────────┐   │
│  │                    탭 1: 개요                        │   │
│  │                                                       │   │
│  │  ■ 기본 정보                                         │   │
│  │    - 종목코드: 005930                                │   │
│  │    - 시장구분: KOSPI                                 │   │
│  │    - 시가총액: 500조원                               │   │
│  │    - 대표이사: 한종희                                │   │
│  │    - 발행주식수: 59억주                              │   │
│  │    - 상장일: 1975-06-11                              │   │
│  │                                                       │   │
│  │  ■ 투자지표 (가치평가)                              │   │
│  │    PER: 15.5  |  PSR: 1.2  |  PBR: 1.8  |  PCR: -  │   │
│  │                                                       │   │
│  │  ■ 수익지표                                          │   │
│  │    EPS: 5,000원 | BPS: 45,000원 | ROE: 12.5% | ROA: 8.3% │
│  │                                                       │   │
│  │  ■ 재무비율                                          │   │
│  │    부채비율: 45.2%  |  유동비율: 250.5%             │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                               │
└─────────────────────────────────────────────────────────────┘
```

### 2. 탭 2: 재무제표

#### 2-1. 분기별 매출 및 순이익 (차트 + 표)

**차트:** 막대 그래프 또는 선 그래프
- X축: 분기 (2024Q3, 2024Q2, ...)
- Y축 (왼쪽): 매출액, 순이익
- Y축 (오른쪽): 순이익률 (%)

**표:**

| 분기 | 매출액 | 순이익 | 순이익률 | 순이익 성장률 |
|------|--------|--------|----------|---------------|
| 2024Q3 | 79조원 | 8조원 | 10.13% | 5.2% |
| 2024Q2 | 74조원 | 7.6조원 | 10.27% | -2.5% |
| ... | ... | ... | ... | ... |

#### 2-2. 분기별 영업이익 (차트 + 표)

**차트:** 막대 그래프
- X축: 분기
- Y축: 영업이익, 영업이익률

**표:**

| 분기 | 영업이익 | 영업이익률 | 영업이익 증가율 |
|------|----------|------------|------------------|
| 2024Q3 | 10조원 | 12.66% | 3.5% |
| 2024Q2 | 9.5조원 | 12.84% | -1.8% |
| ... | ... | ... | ... |

#### 2-3. 손익계산서 (표)

| 분기 | 매출액 | 매출원가 | 매출총이익 | 영업이익 | 당기순이익 |
|------|--------|----------|------------|----------|------------|
| 2024Q3 | 79조원 | 50조원 | 29조원 | 10조원 | 8조원 |
| 2024Q2 | 74조원 | 47조원 | 27조원 | 9.5조원 | 7.6조원 |
| ... | ... | ... | ... | ... | ... |

#### 2-4. 재무상태표 (표)

| 분기 | 자산총계 | 부채총계 | 자본총계 |
|------|----------|----------|----------|
| 2024Q3 | 450조원 | 150조원 | 300조원 |
| 2024Q2 | 440조원 | 145조원 | 295조원 |
| ... | ... | ... | ... |

### 3. 탭 3: 차트

**일별 차트 (최근 5년)**

캔들스틱 차트 또는 선 그래프를 사용하여 시가, 고가, 저가, 종가를 표시합니다.

- X축: 날짜
- Y축: 가격 (원)
- 거래량: 하단에 막대 그래프로 표시

라이브러리 추천:
- Recharts (React)
- Chart.js
- ApexCharts
- TradingView Lightweight Charts (캔들스틱 차트에 최적)

---

## 구현 예시 (React + TypeScript)

### 1. API 호출 예시

```typescript
// types/company.ts
export interface CompanyInfo {
  basicInfo: {
    companyName: string;
    stockCode: string;
    stockName?: string;
    marketType?: string;
    marketCap?: number;
    ceoName?: string;
    listedShares?: number;
    listedDate?: string;
    industry?: string;
  };
  investmentIndicators: {
    per?: number;
    psr?: number;
    pbr?: number;
    pcr?: number;
  };
  profitabilityIndicators: {
    eps?: number;
    bps?: number;
    roe?: number;
    roa?: number;
  };
  financialRatios: {
    debtRatio?: number;
    currentRatio?: number;
  };
  quarterlyPerformance: Array<{
    period: string;
    revenue?: number;
    operatingIncome?: number;
    netIncome?: number;
    netProfitMargin?: number;
    netIncomeGrowth?: number;
    operatingMargin?: number;
    operatingIncomeGrowth?: number;
  }>;
  incomeStatements: Array<{
    period: string;
    revenue?: number;
    costOfSales?: number;
    grossProfit?: number;
    operatingIncome?: number;
    netIncome?: number;
  }>;
  balanceSheets: Array<{
    period: string;
    totalAssets?: number;
    totalLiabilities?: number;
    totalEquity?: number;
  }>;
  priceHistory: Array<{
    date: string;
    open?: number;
    high?: number;
    low?: number;
    close?: number;
    volume?: number;
  }>;
}

// api/companyInfo.ts
import axios from 'axios';
import { CompanyInfo } from '../types/company';

const API_BASE_URL = process.env.REACT_APP_API_BASE_URL || 'http://localhost:8000';

export const getCompanyInfo = async (stockCode: string): Promise<CompanyInfo> => {
  const response = await axios.get<CompanyInfo>(
    `${API_BASE_URL}/api/v1/company/${stockCode}/info`
  );
  return response.data;
};

export const searchCompanies = async (query: string, limit: number = 10) => {
  const response = await axios.get(
    `${API_BASE_URL}/api/v1/company/search`,
    { params: { query, limit } }
  );
  return response.data;
};
```

### 2. 컴포넌트 예시

```typescript
// components/CompanyInfoModal.tsx
import React, { useState, useEffect } from 'react';
import { getCompanyInfo } from '../api/companyInfo';
import { CompanyInfo } from '../types/company';

interface Props {
  stockCode: string;
  onClose: () => void;
}

export const CompanyInfoModal: React.FC<Props> = ({ stockCode, onClose }) => {
  const [data, setData] = useState<CompanyInfo | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<'overview' | 'financials' | 'chart'>('overview');

  useEffect(() => {
    const fetchData = async () => {
      try {
        setLoading(true);
        const result = await getCompanyInfo(stockCode);
        setData(result);
      } catch (err) {
        setError('데이터를 불러오는데 실패했습니다.');
        console.error(err);
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, [stockCode]);

  if (loading) return <div>로딩 중...</div>;
  if (error) return <div>오류: {error}</div>;
  if (!data) return null;

  return (
    <div className="modal-overlay">
      <div className="modal-content">
        <div className="modal-header">
          <h2>{data.basicInfo.companyName} ({data.basicInfo.stockCode})</h2>
          <button onClick={onClose}>X</button>
        </div>

        <div className="tabs">
          <button
            className={activeTab === 'overview' ? 'active' : ''}
            onClick={() => setActiveTab('overview')}
          >
            개요
          </button>
          <button
            className={activeTab === 'financials' ? 'active' : ''}
            onClick={() => setActiveTab('financials')}
          >
            재무제표
          </button>
          <button
            className={activeTab === 'chart' ? 'active' : ''}
            onClick={() => setActiveTab('chart')}
          >
            차트
          </button>
        </div>

        <div className="tab-content">
          {activeTab === 'overview' && <OverviewTab data={data} />}
          {activeTab === 'financials' && <FinancialsTab data={data} />}
          {activeTab === 'chart' && <ChartTab data={data} />}
        </div>
      </div>
    </div>
  );
};

// 개요 탭
const OverviewTab: React.FC<{ data: CompanyInfo }> = ({ data }) => {
  const formatNumber = (num?: number) => {
    if (!num) return '-';
    return num.toLocaleString('ko-KR');
  };

  return (
    <div className="overview-tab">
      <section className="basic-info">
        <h3>기본 정보</h3>
        <div className="info-grid">
          <div>종목코드: {data.basicInfo.stockCode}</div>
          <div>시장구분: {data.basicInfo.marketType || '-'}</div>
          <div>시가총액: {formatNumber(data.basicInfo.marketCap)}원</div>
          <div>대표이사: {data.basicInfo.ceoName || '-'}</div>
          <div>발행주식수: {formatNumber(data.basicInfo.listedShares)}주</div>
          <div>상장일: {data.basicInfo.listedDate || '-'}</div>
        </div>
      </section>

      <section className="investment-indicators">
        <h3>투자지표 (가치평가)</h3>
        <div className="indicators-grid">
          <div>PER: {data.investmentIndicators.per?.toFixed(2) || '-'}</div>
          <div>PSR: {data.investmentIndicators.psr?.toFixed(2) || '-'}</div>
          <div>PBR: {data.investmentIndicators.pbr?.toFixed(2) || '-'}</div>
          <div>PCR: {data.investmentIndicators.pcr?.toFixed(2) || '-'}</div>
        </div>
      </section>

      <section className="profitability-indicators">
        <h3>수익지표</h3>
        <div className="indicators-grid">
          <div>EPS: {formatNumber(data.profitabilityIndicators.eps)}원</div>
          <div>BPS: {formatNumber(data.profitabilityIndicators.bps)}원</div>
          <div>ROE: {data.profitabilityIndicators.roe?.toFixed(2)}%</div>
          <div>ROA: {data.profitabilityIndicators.roa?.toFixed(2)}%</div>
        </div>
      </section>

      <section className="financial-ratios">
        <h3>재무비율</h3>
        <div className="indicators-grid">
          <div>부채비율: {data.financialRatios.debtRatio?.toFixed(2)}%</div>
          <div>유동비율: {data.financialRatios.currentRatio?.toFixed(2)}%</div>
        </div>
      </section>
    </div>
  );
};

// 재무제표 탭
const FinancialsTab: React.FC<{ data: CompanyInfo }> = ({ data }) => {
  // 차트 및 표 구현
  return (
    <div className="financials-tab">
      {/* 분기별 실적 차트/표 */}
      {/* 손익계산서 표 */}
      {/* 재무상태표 표 */}
    </div>
  );
};

// 차트 탭
const ChartTab: React.FC<{ data: CompanyInfo }> = ({ data }) => {
  // 일별 차트 구현 (Recharts, Chart.js 등 사용)
  return (
    <div className="chart-tab">
      {/* 캔들스틱 차트 또는 선 그래프 */}
    </div>
  );
};
```

---

## 데이터 표시 팁

### 1. 숫자 포맷팅

```typescript
// 금액 표시 (원 단위)
const formatCurrency = (value?: number) => {
  if (!value) return '-';

  // 조 단위
  if (value >= 1_000_000_000_000) {
    return `${(value / 1_000_000_000_000).toFixed(2)}조원`;
  }
  // 억 단위
  if (value >= 100_000_000) {
    return `${(value / 100_000_000).toFixed(2)}억원`;
  }
  // 만 단위
  if (value >= 10_000) {
    return `${(value / 10_000).toFixed(2)}만원`;
  }

  return `${value.toLocaleString('ko-KR')}원`;
};

// 퍼센트 표시
const formatPercent = (value?: number) => {
  if (value === null || value === undefined) return '-';

  const sign = value > 0 ? '+' : '';
  return `${sign}${value.toFixed(2)}%`;
};

// 색상 표시 (증가/감소)
const getChangeColor = (value?: number) => {
  if (!value) return 'black';
  return value > 0 ? 'red' : value < 0 ? 'blue' : 'black';
};
```

### 2. 차트 라이브러리 사용 예시 (Recharts)

```typescript
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend } from 'recharts';

const PriceChart: React.FC<{ data: CompanyInfo }> = ({ data }) => {
  // 데이터 변환
  const chartData = data.priceHistory.map(item => ({
    date: item.date,
    close: item.close,
    volume: item.volume
  }));

  return (
    <LineChart width={800} height={400} data={chartData}>
      <CartesianGrid strokeDasharray="3 3" />
      <XAxis dataKey="date" />
      <YAxis />
      <Tooltip />
      <Legend />
      <Line type="monotone" dataKey="close" stroke="#8884d8" name="종가" />
    </LineChart>
  );
};
```

---

## 주의사항

1. **null 값 처리**: 일부 데이터는 null일 수 있으므로 항상 null 체크를 해야 합니다.
2. **대용량 데이터**: 5년치 일별 데이터는 약 1,250개의 데이터 포인트입니다. 차트 렌더링 성능에 주의하세요.
3. **숫자 표시**: 큰 숫자는 조/억 단위로 변환하여 표시하는 것이 좋습니다.
4. **로딩 상태**: API 호출 시 로딩 상태를 표시하여 UX를 개선하세요.
5. **에러 처리**: 네트워크 오류나 종목 없음 등의 에러를 적절히 처리하세요.

---

## 추가 개선 사항

1. **캐싱**: React Query나 SWR을 사용하여 데이터 캐싱 및 재사용
2. **차트 인터랙션**: 줌, 팬, 툴팁 등의 인터랙티브 기능 추가
3. **비교 기능**: 여러 종목의 지표를 비교할 수 있는 기능
4. **다운로드**: 재무제표를 Excel 파일로 다운로드하는 기능
5. **알림**: 특정 지표가 기준치에 도달했을 때 알림 기능

---

## 문제 해결

### Q: PCR(주가현금흐름비율) 데이터가 null인 이유는?

A: 현재 데이터베이스에 현금흐름표(cashflow_statement) 데이터가 있지만, API에서 아직 조회하지 않고 있습니다. 필요하다면 백엔드 개발자에게 요청하세요.

### Q: 일부 재무제표 항목이 없는 경우는?

A: 기업마다 재무제표 항목이 다를 수 있습니다. 항상 null 체크를 하고, 없는 경우 '-' 또는 '데이터 없음'으로 표시하세요.

### Q: 분기별 데이터가 8분기보다 적을 수 있나요?

A: 네, 신규 상장 기업이나 데이터가 부족한 경우 8분기보다 적을 수 있습니다. 배열 길이를 확인하세요.

---

## 연락처

백엔드 관련 문의나 추가 데이터가 필요한 경우 백엔드 팀에 문의하세요.
