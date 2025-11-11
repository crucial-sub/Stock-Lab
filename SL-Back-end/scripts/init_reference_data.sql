-- =============================================
-- 백테스트 참조 데이터 초기화 스크립트
-- 54개 팩터 + 카테고리 + 테스트 사용자
-- =============================================

-- 1. 테스트 사용자 생성 (admin/admin)
INSERT INTO users (user_id, name, email, phone_number, hashed_password, is_active, is_superuser, created_at, updated_at)
VALUES (
    'admin'::uuid,  -- UUID로 'admin' 문자열 변환
    'Admin User',
    'admin@stacklab.com',
    '010-0000-0000',
    '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TcxMQJqhN8/LewY5aeO1V8ypX9DG',  -- bcrypt hash of 'admin'
    true,
    true,
    NOW(),
    NOW()
)
ON CONFLICT (email) DO NOTHING;

-- 2. 팩터 카테고리 생성 (6개)
INSERT INTO factor_categories (category_id, category_name, description, display_order, created_at, updated_at)
VALUES
    ('VALUE', '가치', '저평가된 주식을 찾기 위한 가치 지표', 1, NOW(), NOW()),
    ('QUALITY', '수익성', '기업의 재무 건전성과 수익성을 평가하는 지표', 2, NOW(), NOW()),
    ('GROWTH', '성장', '기업의 성장 가능성을 평가하는 지표', 3, NOW(), NOW()),
    ('MOMENTUM', '모멘텀', '주가의 추세와 강도를 측정하는 지표', 4, NOW(), NOW()),
    ('STABILITY', '안정성', '기업의 재무 안정성과 리스크를 평가하는 지표', 5, NOW(), NOW()),
    ('TECHNICAL', '기술적분석', '차트 기반 기술적 분석 지표', 6, NOW(), NOW())
ON CONFLICT (category_id) DO NOTHING;

-- 3. 54개 팩터 데이터 삽입

-- 가치 지표 (Value) - 14개
INSERT INTO factors (factor_id, category_id, factor_name, factor_name_en, description, calculation_type, calculation_formula, data_source, update_frequency, display_order, is_active, created_at, updated_at)
VALUES
    ('PER', 'VALUE', 'PER', 'Price to Earnings Ratio', '주가를 주당순이익으로 나눈 비율. 낮을수록 저평가', 'ratio', '주가 / 주당순이익(EPS)', 'financial_statement', 'quarterly', 1, true, NOW(), NOW()),
    ('PBR', 'VALUE', 'PBR', 'Price to Book Ratio', '주가를 주당순자산으로 나눈 비율. 낮을수록 저평가', 'ratio', '주가 / 주당순자산(BPS)', 'financial_statement', 'quarterly', 2, true, NOW(), NOW()),
    ('PSR', 'VALUE', 'PSR', 'Price to Sales Ratio', '시가총액을 매출액으로 나눈 비율. 낮을수록 저평가', 'ratio', '시가총액 / 매출액', 'financial_statement', 'quarterly', 3, true, NOW(), NOW()),
    ('PCR', 'VALUE', 'PCR', 'Price to Cash Flow Ratio', '시가총액을 영업현금흐름으로 나눈 비율', 'ratio', '시가총액 / 영업현금흐름', 'financial_statement', 'quarterly', 4, true, NOW(), NOW()),
    ('PEG', 'VALUE', 'PEG', 'Price/Earnings to Growth', 'PER을 순이익증가율로 나눈 비율', 'ratio', 'PER / 순이익증가율', 'financial_statement', 'quarterly', 5, true, NOW(), NOW()),
    ('EV_EBITDA', 'VALUE', 'EV/EBITDA', 'Enterprise Value to EBITDA', '기업가치를 EBITDA로 나눈 비율', 'ratio', '(시가총액 + 순부채) / EBITDA', 'financial_statement', 'quarterly', 6, true, NOW(), NOW()),
    ('EV_SALES', 'VALUE', 'EV/Sales', 'Enterprise Value to Sales', '기업가치를 매출액으로 나눈 비율', 'ratio', '(시가총액 + 순부채) / 매출액', 'financial_statement', 'quarterly', 7, true, NOW(), NOW()),
    ('EV_FCF', 'VALUE', 'EV/FCF', 'Enterprise Value to Free Cash Flow', '기업가치를 잉여현금흐름으로 나눈 비율', 'ratio', '(시가총액 + 순부채) / 잉여현금흐름', 'financial_statement', 'quarterly', 8, true, NOW(), NOW()),
    ('DIVIDEND_YIELD', 'VALUE', '배당수익률', 'Dividend Yield', '주당배당금을 주가로 나눈 비율', 'percentage', '주당배당금 / 주가 × 100', 'financial_statement', 'annually', 9, true, NOW(), NOW()),
    ('EARNINGS_YIELD', 'VALUE', '이익수익률', 'Earnings Yield', 'PER의 역수. 높을수록 저평가', 'percentage', '순이익 / 시가총액 × 100', 'financial_statement', 'quarterly', 10, true, NOW(), NOW()),
    ('FCF_YIELD', 'VALUE', 'FCF 수익률', 'Free Cash Flow Yield', '잉여현금흐름을 시가총액으로 나눈 비율', 'percentage', '잉여현금흐름 / 시가총액 × 100', 'financial_statement', 'quarterly', 11, true, NOW(), NOW()),
    ('BOOK_TO_MARKET', 'VALUE', '장부가 대비 시가', 'Book to Market Ratio', '장부가를 시가총액으로 나눈 비율', 'ratio', '순자산 / 시가총액', 'financial_statement', 'quarterly', 12, true, NOW(), NOW()),
    ('CAPE_RATIO', 'VALUE', 'CAPE Ratio', 'Cyclically Adjusted PE', '10년 평균 실질이익 기반 PER', 'ratio', '시가총액 / 10년 평균 순이익', 'financial_statement', 'quarterly', 13, true, NOW(), NOW()),
    ('PTBV', 'VALUE', 'PTBV', 'Price to Tangible Book Value', '주가를 유형자산 기준 순자산으로 나눈 비율', 'ratio', '시가총액 / (순자산 - 무형자산)', 'financial_statement', 'quarterly', 14, true, NOW(), NOW()),

-- 수익성 지표 (Quality) - 10개
    ('ROE', 'QUALITY', 'ROE', 'Return on Equity', '당기순이익을 자기자본으로 나눈 비율', 'percentage', '당기순이익 / 자기자본 × 100', 'financial_statement', 'quarterly', 1, true, NOW(), NOW()),
    ('ROA', 'QUALITY', 'ROA', 'Return on Assets', '당기순이익을 총자산으로 나눈 비율', 'percentage', '당기순이익 / 총자산 × 100', 'financial_statement', 'quarterly', 2, true, NOW(), NOW()),
    ('ROIC', 'QUALITY', 'ROIC', 'Return on Invested Capital', '세후영업이익을 투하자본으로 나눈 비율', 'percentage', 'NOPAT / (자기자본 + 부채 - 현금) × 100', 'financial_statement', 'quarterly', 3, true, NOW(), NOW()),
    ('GPM', 'QUALITY', '매출총이익률', 'Gross Profit Margin', '매출총이익을 매출액으로 나눈 비율', 'percentage', '매출총이익 / 매출액 × 100', 'financial_statement', 'quarterly', 4, true, NOW(), NOW()),
    ('OPM', 'QUALITY', '영업이익률', 'Operating Profit Margin', '영업이익을 매출액으로 나눈 비율', 'percentage', '영업이익 / 매출액 × 100', 'financial_statement', 'quarterly', 5, true, NOW(), NOW()),
    ('NPM', 'QUALITY', '순이익률', 'Net Profit Margin', '당기순이익을 매출액으로 나눈 비율', 'percentage', '당기순이익 / 매출액 × 100', 'financial_statement', 'quarterly', 6, true, NOW(), NOW()),
    ('ASSET_TURNOVER', 'QUALITY', '자산회전율', 'Asset Turnover', '매출액을 총자산으로 나눈 비율', 'ratio', '매출액 / 총자산', 'financial_statement', 'quarterly', 7, true, NOW(), NOW()),
    ('INVENTORY_TURNOVER', 'QUALITY', '재고자산회전율', 'Inventory Turnover', '매출원가를 재고자산으로 나눈 비율', 'ratio', '매출원가 / 재고자산', 'financial_statement', 'quarterly', 8, true, NOW(), NOW()),
    ('QUALITY_SCORE', 'QUALITY', '품질점수', 'Quality Score', 'Piotroski F-Score 기반 품질 평가', 'score', '9개 재무지표 기반 점수 (0-9)', 'financial_statement', 'quarterly', 9, true, NOW(), NOW()),
    ('ACCRUALS_RATIO', 'QUALITY', '발생액 비율', 'Accruals Ratio', '순이익 대비 현금흐름 차이', 'ratio', '(순이익 - 영업현금흐름) / 총자산', 'financial_statement', 'quarterly', 10, true, NOW(), NOW()),

-- 성장 지표 (Growth) - 8개
    ('REVENUE_GROWTH_1Y', 'GROWTH', '매출액증가율(1Y)', 'Revenue Growth 1Y', '전년 대비 매출액 증가율', 'percentage', '(당기매출액 - 전기매출액) / 전기매출액 × 100', 'financial_statement', 'quarterly', 1, true, NOW(), NOW()),
    ('REVENUE_GROWTH_3Y', 'GROWTH', '매출액증가율(3Y CAGR)', 'Revenue Growth 3Y', '3년 연평균 매출액 증가율', 'percentage', '((당기매출액 / 3년전매출액)^(1/3) - 1) × 100', 'financial_statement', 'quarterly', 2, true, NOW(), NOW()),
    ('EARNINGS_GROWTH_1Y', 'GROWTH', '순이익증가율(1Y)', 'Earnings Growth 1Y', '전년 대비 순이익 증가율', 'percentage', '(당기순이익 - 전기순이익) / 전기순이익 × 100', 'financial_statement', 'quarterly', 3, true, NOW(), NOW()),
    ('EARNINGS_GROWTH_3Y', 'GROWTH', '순이익증가율(3Y CAGR)', 'Earnings Growth 3Y', '3년 연평균 순이익 증가율', 'percentage', '((당기순이익 / 3년전순이익)^(1/3) - 1) × 100', 'financial_statement', 'quarterly', 4, true, NOW(), NOW()),
    ('OCF_GROWTH_1Y', 'GROWTH', '영업현금흐름증가율', 'OCF Growth 1Y', '전년 대비 영업현금흐름 증가율', 'percentage', '(당기OCF - 전기OCF) / 전기OCF × 100', 'financial_statement', 'quarterly', 5, true, NOW(), NOW()),
    ('ASSET_GROWTH_1Y', 'GROWTH', '자산증가율', 'Asset Growth 1Y', '전년 대비 총자산 증가율', 'percentage', '(당기자산 - 전기자산) / 전기자산 × 100', 'financial_statement', 'quarterly', 6, true, NOW(), NOW()),
    ('BOOK_VALUE_GROWTH_1Y', 'GROWTH', '순자산증가율', 'Book Value Growth 1Y', '전년 대비 순자산 증가율', 'percentage', '(당기순자산 - 전기순자산) / 전기순자산 × 100', 'financial_statement', 'quarterly', 7, true, NOW(), NOW()),
    ('SUSTAINABLE_GROWTH_RATE', 'GROWTH', '지속가능성장률', 'Sustainable Growth Rate', 'ROE × 유보율로 계산한 지속가능 성장률', 'percentage', 'ROE × (1 - 배당성향)', 'financial_statement', 'quarterly', 8, true, NOW(), NOW()),

-- 모멘텀 지표 (Momentum) - 8개
    ('MOMENTUM_1M', 'MOMENTUM', '1개월 모멘텀', '1-Month Momentum', '최근 1개월(20영업일) 수익률', 'percentage', '(현재가 - 1개월전가) / 1개월전가 × 100', 'market_data', 'daily', 1, true, NOW(), NOW()),
    ('MOMENTUM_3M', 'MOMENTUM', '3개월 모멘텀', '3-Month Momentum', '최근 3개월(60영업일) 수익률', 'percentage', '(현재가 - 3개월전가) / 3개월전가 × 100', 'market_data', 'daily', 2, true, NOW(), NOW()),
    ('MOMENTUM_6M', 'MOMENTUM', '6개월 모멘텀', '6-Month Momentum', '최근 6개월(120영업일) 수익률', 'percentage', '(현재가 - 6개월전가) / 6개월전가 × 100', 'market_data', 'daily', 3, true, NOW(), NOW()),
    ('MOMENTUM_12M', 'MOMENTUM', '12개월 모멘텀', '12-Month Momentum', '최근 12개월(240영업일) 수익률', 'percentage', '(현재가 - 12개월전가) / 12개월전가 × 100', 'market_data', 'daily', 4, true, NOW(), NOW()),
    ('DISTANCE_FROM_52W_HIGH', 'MOMENTUM', '52주 최고가 대비', 'Distance from 52W High', '현재가와 52주 최고가의 거리', 'percentage', '(현재가 - 52주최고가) / 52주최고가 × 100', 'market_data', 'daily', 5, true, NOW(), NOW()),
    ('DISTANCE_FROM_52W_LOW', 'MOMENTUM', '52주 최저가 대비', 'Distance from 52W Low', '현재가와 52주 최저가의 거리', 'percentage', '(현재가 - 52주최저가) / 52주최저가 × 100', 'market_data', 'daily', 6, true, NOW(), NOW()),
    ('RELATIVE_STRENGTH', 'MOMENTUM', '상대강도', 'Relative Strength', '시장 대비 초과 수익률', 'percentage', '개별종목 수익률 - 시장 수익률', 'market_data', 'daily', 7, true, NOW(), NOW()),
    ('VOLUME_MOMENTUM', 'MOMENTUM', '거래량 모멘텀', 'Volume Momentum', '거래량 증가율', 'percentage', '(현재거래량 - 과거평균거래량) / 과거평균거래량 × 100', 'market_data', 'daily', 8, true, NOW(), NOW()),

-- 안정성 지표 (Stability) - 8개
    ('DEBT_TO_EQUITY', 'STABILITY', '부채비율', 'Debt to Equity', '부채총계를 자기자본으로 나눈 비율', 'ratio', '부채총계 / 자기자본', 'financial_statement', 'quarterly', 1, true, NOW(), NOW()),
    ('DEBT_RATIO', 'STABILITY', '부채비율(%)', 'Debt Ratio', '부채총계를 총자산으로 나눈 비율', 'percentage', '부채총계 / 총자산 × 100', 'financial_statement', 'quarterly', 2, true, NOW(), NOW()),
    ('CURRENT_RATIO', 'STABILITY', '유동비율', 'Current Ratio', '유동자산을 유동부채로 나눈 비율', 'ratio', '유동자산 / 유동부채', 'financial_statement', 'quarterly', 3, true, NOW(), NOW()),
    ('QUICK_RATIO', 'STABILITY', '당좌비율', 'Quick Ratio', '당좌자산을 유동부채로 나눈 비율', 'ratio', '(유동자산 - 재고자산) / 유동부채', 'financial_statement', 'quarterly', 4, true, NOW(), NOW()),
    ('INTEREST_COVERAGE', 'STABILITY', '이자보상배율', 'Interest Coverage', '영업이익을 이자비용으로 나눈 비율', 'ratio', 'EBIT / 이자비용', 'financial_statement', 'quarterly', 5, true, NOW(), NOW()),
    ('ALTMAN_Z_SCORE', 'STABILITY', 'Altman Z-Score', 'Altman Z-Score', '파산 위험도 측정 지표', 'score', '1.2×운전자본비율 + 1.4×유보이익비율 + 3.3×EBIT비율 + 0.6×시가총액/부채 + 1.0×매출액회전율', 'financial_statement', 'quarterly', 6, true, NOW(), NOW()),
    ('BETA', 'STABILITY', '베타', 'Beta', '시장 대비 변동성', 'ratio', '주가변동성 / 시장변동성', 'market_data', 'daily', 7, true, NOW(), NOW()),
    ('EARNINGS_QUALITY', 'STABILITY', '이익품질', 'Earnings Quality', '현금흐름 대비 순이익 비율', 'ratio', '영업현금흐름 / 당기순이익', 'financial_statement', 'quarterly', 8, true, NOW(), NOW()),

-- 기술적 지표 (Technical) - 6개
    ('RSI_14', 'TECHNICAL', 'RSI(14)', 'Relative Strength Index', '14일 기준 상대강도지수 (0-100)', 'index', '100 - (100 / (1 + RS))', 'market_data', 'daily', 1, true, NOW(), NOW()),
    ('BOLLINGER_POSITION', 'TECHNICAL', '볼린저밴드 위치', 'Bollinger Band Position', '볼린저밴드 내 현재가 위치', 'ratio', '(현재가 - MA20) / (2 × 표준편차)', 'market_data', 'daily', 2, true, NOW(), NOW()),
    ('MACD_SIGNAL', 'TECHNICAL', 'MACD 시그널', 'MACD Signal', 'MACD와 시그널선 차이', 'value', '(EMA12 - EMA26) - Signal', 'market_data', 'daily', 3, true, NOW(), NOW()),
    ('STOCHASTIC_14', 'TECHNICAL', '스토캐스틱(14)', 'Stochastic Oscillator', '14일 기준 스토캐스틱 (0-100)', 'percentage', '(현재가 - 14일최저가) / (14일최고가 - 14일최저가) × 100', 'market_data', 'daily', 4, true, NOW(), NOW()),
    ('VOLUME_ROC', 'TECHNICAL', '거래량 변화율', 'Volume Rate of Change', '거래량 변화율', 'percentage', '(현재거래량 - 과거거래량) / 과거거래량 × 100', 'market_data', 'daily', 5, true, NOW(), NOW()),
    ('PRICE_POSITION', 'TECHNICAL', '가격 위치', 'Price Position', '52주 범위 내 현재가 위치 (0-100)', 'percentage', '(현재가 - 52주최저가) / (52주최고가 - 52주최저가) × 100', 'market_data', 'daily', 6, true, NOW(), NOW())

ON CONFLICT (factor_id) DO NOTHING;

-- 완료 메시지
SELECT '✅ 참조 데이터 초기화 완료' AS status,
       (SELECT COUNT(*) FROM users WHERE email = 'admin@stacklab.com') AS users_count,
       (SELECT COUNT(*) FROM factor_categories) AS categories_count,
       (SELECT COUNT(*) FROM factors) AS factors_count;
