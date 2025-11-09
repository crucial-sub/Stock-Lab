# 프로젝트용 팩터 후보 (2020~현재)

## 데이터 가정
- **재무/공시**: DART 연·분기 재무제표(재무상태표, 손익계산서, 현금흐름표, 주석) 및 주요 공시 이벤트.
- **시세**: 공공데이터포털에서 수집한 일별 시가/고가/저가/종가/거래량/거래대금.
- **기간**: 2020년 1월 이후 데이터로 산출 가능한 팩터만 포함.

## 팩터 정의 표(Notion 호환)

| 카테고리 | 팩터 | 정의/수식 | 필요 데이터 | 구현 메모 |
| --- | --- | --- | --- | --- |
| 밸류 | PER | `Adjusted Close / (순이익 TTM / 유통주식수)` | 조정종가, 순이익TTM, 유통주식수 | 적자 기업은 제거 또는 Winsorize |
| 밸류 | Forward PER | `현재가 / (다음 분기/연 EPS 추정)` | 조정종가, 컨센서스 EPS 또는 자체 추정 | 추정치 없으면 PER 대체 |
| 밸류 | PBR | `시가총액 / 자본총계` | 조정종가, 유통주식수, 자본총계 | 연결/별도 기준 통일 |
| 밸류 | PSR | `시가총액 / 매출액 TTM` | 조정종가, 유통주식수, 매출액TTM | 금융/비금융 분리 필요 |
| 밸류 | EV/EBITDA | `(시총 + 순부채 - 현금성)/EBITDA` | 시가총액, 총차입금, 현금성자산, EBITDA | EBITDA<0인 종목 제외 |
| 밸류 | Dividend Yield | `최근 연간 배당금 / 현재가` | 배당 공시, 조정종가 | 분기배당은 연환산 |
| 수익성 | ROE | `순이익 TTM / 평균자본` | 순이익TTM, 기초/기말 자본 | 발표지연 반영(T+45/60) |
| 수익성 | ROA | `순이익 TTM / 평균총자산` | 순이익TTM, 총자산 | 산업별 비교시 Z-Score |
| 수익성 | Gross Margin | `매출총이익 / 매출액` | 매출총이익, 매출액 | 분기→TTM 변환 |
| 수익성 | Operating Margin | `영업이익 / 매출액` | 영업이익, 매출액 | IFRS 조정(기타포괄 제외) |
| 수익성 | Cash Conversion Ratio | `영업CF / 순이익` | 영업활동현금흐름, 순이익 | 0 나눔 방지(Clip) |
| 수익성 | Asset Turnover | `매출액 TTM / 평균총자산` | 매출액TTM, 총자산 | 제조/서비스 구분 |
| 성장 | Revenue Growth YoY | `(금분기 매출 - 전년동분기)/전년동분기` | 분기 매출 | 비정상 분기 제거 |
| 성장 | Operating Income Growth | `(영업이익 YoY%)` | 분기 영업이익 | 마이너스→0 처리 가능 |
| 성장 | Net Income Growth | `(순이익 YoY%)` | 분기 순이익 | 일회성 제거(주석 필요) |
| 성장 | EPS Growth | `(EPS TTM YoY%)` | 순이익, 주식수 | 희석주식수 사용 |
| 성장 | FCF Growth | `(FCF TTM YoY%)` | 영업CF, CapEx | CapEx=투자CF 중 유형자산 |
| 레버리지 | Debt/Equity | `총차입금 / 자본총계` | 단기+장기차입, 자본총계 | IFRS 유동/비유동 합산 |
| 레버리지 | Net Debt/EBITDA | `(총차입-현금)/EBITDA` | 총차입, 현금성자산, EBITDA | EBITDA=0일 때 capped |
| 레버리지 | Interest Coverage | `EBIT / 이자비용` | EBIT, 이자비용 | 음수 제거 |
| 레버리지 | Current Ratio | `유동자산 / 유동부채` | 유동자산, 유동부채 | Quick Ratio 병행 권장 |
| 레버리지 | Altman Z (제조) | `1.2·X1 + 1.4·X2 + 3.3·X3 + 0.6·X4 + 1.0·X5` | 운전자본, 이익잉여금, EBIT, 시총, 매출 | 산업별 버전 선택 |
| 현금흐름 | Free Cash Flow Yield | `FCF TTM / 시가총액` | 영업CF, CapEx, 시가총액 | FCF=영업CF-CapEx |
| 현금흐름 | Operating CF Yield | `영업CF TTM / 시가총액` | 영업CF, 시가총액 | |
| 현금흐름 | CapEx Ratio | `CapEx / 매출액` | 투자CF(유형), 매출액 | 성장주 vs 가치 비교 |
| 현금흐름 | Dividend Payout | `총배당 / 순이익` | 배당금, 순이익 | >100% 경고 |
| 현금흐름 | Shareholder Yield | `(배당 + 자사주순매입)/시가총액` | 배당, 자사주변동, 시총 | 공시 데이터 병합 |
| 퀄리티 | Piotroski F-Score | 9개 득점 합 | 재무지표 9개 | 회계품질 필터 |
| 퀄리티 | Beneish M-Score | `-4.84 + Σ(계수·지표)` | 매출/매출총익/DSRI 등 8항목 | 분식 탐지 |
| 퀄리티 | Accruals Ratio | `(순이익-영업CF)/총자산` | 순이익, 영업CF, 총자산 | 절대값 사용 |
| 퀄리티 | Gross Profit/Assets | `매출총이익 / 총자산` | 매출총이익, 총자산 | Novy-Marx Quality |
| 퀄리티 | R&D Intensity | `R&D비용 / 매출` | 연구개발비, 매출 | 주석에서 추출 |
| 모멘텀 | 12M-1M Momentum | `(Price_{t-21}-Price_{t-252})/Price_{t-252}` | 조정종가 | 최근 1개월 제외 |
| 모멘텀 | 3M Momentum | `(Price_{t}-Price_{t-63})/Price_{t-63}` | 조정종가 | 63거래일≈3M |
| 모멘텀 | Short-term Reversal | `-(Price_{t}-Price_{t-5})/Price_{t-5}` | 조정종가 | 음수=반등 기대 |
| 모멘텀 | Bollinger %B | `(Close - LowerBand)/(UpperBand-LowerBand)` | 종가, SMA(N), 표준편차 | N=20,K=2 기본 |
| 모멘텀 | Bollinger BandWidth | `(Upper-Lower)/SMA` | 종가, SMA(N), 표준편차 | 변동성 팩터 |
| 모멘텀 | 20D Historical Vol | `StdDev(일간수익률,20)*√252` | 일간 수익률 | 로그수익률 권장 |
| 모멘텀 | Beta (252일) | `Cov(r_i,r_m)/Var(r_m)` | 일간 수익률, 시장수익률 | KOSPI/KOSDAQ 구분 |
| 모멘텀 | Average True Range | `EMA( TrueRange, n )` | 고가, 저가, 종가 | n=14 기본 |
| 모멘텀 | 52W High Proximity | `Close / 52주최고가` | 종가, 252일 최고 | 0~1 스케일 |
| 유동성 | Avg Daily Turnover | `mean(거래대금_{20D})` | 거래량, 종가 | 거래량*종가 |
| 유동성 | Turnover Ratio | `거래량 / 유통주식수` | 거래량, 유통주식 | Free-float 필요 |
| 유동성 | Amihud Illiquidity | `mean(|r| / 거래대금)` | 일간 수익률, 거래대금 | log-scale 변환 |
| 유동성 | Volume Momentum | `Volume_{20D SMA} / Volume_{60D SMA}` | 거래량 | >1=수요 증가 |
| 유동성 | Order Imbalance Proxy | `(매수체결-매도체결)/총체결` | 체결 데이터(가능 시) | 데이터 없으면 생략 |
| 이벤트 | Dividend Drift | `배당 공시일~+5d 초과수익` | 공시일, 주가, 시장수익 | 공시 파싱 필요 |
| 이벤트 | Buyback AR | `자사주 매입 공시 ±초과수익` | 공시, 주가 | 금액/비율 함께 |
| 이벤트 | Equity Issuance Flag | `유상증자 공시 더미` | 공시 | 디루션 리스크 |
| 이벤트 | Audit Opinion Flag | `감사의견(적정/한정/거절)` | 감사보고서 | 부정적 의견 필터 |
| 이벤트 | IR Frequency | `IR/설명회 공시 횟수(연)` | 공시 | 커뮤니케이션 지표 |
| 혼합 | Quality × Value Rank | `Quality Z + Value Z` | 위 품질/밸류 지표 | 득점 합산 후 순위 |
| 혼합 | Momentum + Value Score | `0.5·MomentumZ + 0.5·ValueZ` | 모멘텀, 밸류 Z | 가중치 조정 가능 |
| 혼합 | Low Vol + Yield | `LowVol Rank + Dividend Yield Rank` | Vol, 배당 | 안정성 전략 |

## 데이터 파이프라인 & 코드 템플릿

| 단계 | 설명 | 구현 포인트 |
| --- | --- | --- |
| 1. 원천 수집 | 공공데이터포털 시세 API + DART 재무/공시 OpenAPI | 동일 종목코드 맵핑, 휴장일 보정 |
| 2. 정제/동기화 | 시세는 조정주가·거래정지 구간 처리, 재무는 공시일 기준 지연 반영 | `effective_date = 공시일 + N일` 룰 |
| 3. 파생 지표 계산 | 재무는 분기→TTM/YoY 변환, 시세는 rolling window | 결측치 forward fill, outlier clip |
| 4. 팩터 스코어링 | 팩터별 Winsorize/Standardize 후 섹터/시총 neutral | `z = (x - median_sector)/mad_sector` |
| 5. 저장/캐싱 | 팩터 테이블(SQL/Parquet) + 메타데이터(버전, 산출일) | 백테스트와 실거래 동일 스냅샷 유지 |
| 6. 검증/모니터링 | 분기별 리포트, 팩터 분포·상관·IC 추적 | Notion에 자동 업로드 |

### Python 계산 템플릿(예시)

```python
import pandas as pd

prices = pd.read_parquet("prices_adj.parquet")  # columns: date, ticker, close, high, low, volume
financials = pd.read_parquet("financials_ttm.parquet")  # columns: ticker, date, revenue_ttm, net_income_ttm, equity, shares_out

# 1) 밸류 팩터
valuation = financials.assign(
    market_cap=lambda df: df["close"] * df["shares_out"],
    per=lambda df: df["close"] / (df["net_income_ttm"] / df["shares_out"]),
    pbr=lambda df: (df["close"] * df["shares_out"]) / df["equity"],
)

# 2) 모멘텀 & 볼린저
prices = prices.set_index(["ticker", "date"]).sort_index()
window = 20
mult = 2
rolling = prices.groupby(level=0)["close"].rolling(window)
sma = rolling.mean().droplevel(0)
std = rolling.std(ddof=0).droplevel(0)
bb = pd.DataFrame(
    {
        "sma": sma,
        "upper": sma + mult * std,
        "lower": sma - mult * std,
    }
)
bb["percent_b"] = (prices["close"] - bb["lower"]) / (bb["upper"] - bb["lower"])
bb["bandwidth"] = (bb["upper"] - bb["lower"]) / bb["sma"]

# 3) 팩터 병합
factors = (
    valuation[["per", "pbr"]]
    .join(bb[["percent_b", "bandwidth"]], how="inner")
    .reset_index()
)
```

## 구현 체크리스트
- 재무·시세 **동일 기준일** 정렬(결산 발표 지연 반영, 재무 수치는 발표 이후 구간에만 사용).
- **분기/연간** 스케일 표준화(rolling fill 또는 TTM) 후 팩터 비교.
- 거래정지·합병 등 **이벤트 전처리** 필요.
- 시세 기반 팩터는 **조정주가** 사용해 액면분할·배당락 효과 제거.
