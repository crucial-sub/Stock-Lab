"""
종목 정보 API 테스트 스크립트
"""
import requests
import json

# API 베이스 URL
BASE_URL = "http://localhost:8000/api/v1"


def test_company_info(stock_code: str):
    """종목 정보 조회 테스트"""
    print(f"\n{'='*60}")
    print(f"테스트: 종목 정보 조회 - {stock_code}")
    print(f"{'='*60}")

    url = f"{BASE_URL}/company/{stock_code}/info"

    try:
        response = requests.get(url)

        print(f"상태 코드: {response.status_code}")
        print(f"응답 시간: {response.elapsed.total_seconds():.2f}초")

        if response.status_code == 200:
            data = response.json()

            # 기본 정보
            print(f"\n📊 기본 정보:")
            basic = data.get('basicInfo', {})
            print(f"  회사명: {basic.get('companyName')}")
            print(f"  종목코드: {basic.get('stockCode')}")
            print(f"  시장구분: {basic.get('marketType')}")
            print(f"  시가총액: {format_currency(basic.get('marketCap'))}")
            print(f"  대표이사: {basic.get('ceoName')}")

            # 투자지표
            print(f"\n💰 투자지표:")
            inv = data.get('investmentIndicators', {})
            print(f"  PER: {inv.get('per')}")
            print(f"  PSR: {inv.get('psr')}")
            print(f"  PBR: {inv.get('pbr')}")
            print(f"  PCR: {inv.get('pcr')}")

            # 수익지표
            print(f"\n📈 수익지표:")
            prof = data.get('profitabilityIndicators', {})
            print(f"  EPS: {format_currency(prof.get('eps'))}원")
            print(f"  BPS: {format_currency(prof.get('bps'))}원")
            print(f"  ROE: {prof.get('roe')}%")
            print(f"  ROA: {prof.get('roa')}%")

            # 재무비율
            print(f"\n📊 재무비율:")
            fin = data.get('financialRatios', {})
            print(f"  부채비율: {fin.get('debtRatio')}%")
            print(f"  유동비율: {fin.get('currentRatio')}%")

            # 분기별 실적
            print(f"\n📅 최근 분기별 실적:")
            quarterly = data.get('quarterlyPerformance', [])
            if quarterly:
                for q in quarterly[:3]:  # 최근 3분기만 출력
                    print(f"\n  [{q.get('period')}]")
                    print(f"    매출액: {format_currency(q.get('revenue'))}")
                    print(f"    영업이익: {format_currency(q.get('operatingIncome'))}")
                    print(f"    순이익: {format_currency(q.get('netIncome'))}")
                    print(f"    순이익률: {q.get('netProfitMargin')}%")
                    print(f"    순이익 성장률: {q.get('netIncomeGrowth')}%")

            # 차트 데이터
            print(f"\n📉 차트 데이터:")
            price_history = data.get('priceHistory', [])
            print(f"  총 {len(price_history)}개 데이터 포인트")
            if price_history:
                latest = price_history[-1]
                print(f"  최신 데이터: {latest.get('date')}")
                print(f"  종가: {format_currency(latest.get('close'))}원")

            # 전체 JSON 저장
            with open(f"company_{stock_code}_info.json", "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            print(f"\n✅ 전체 응답을 company_{stock_code}_info.json 파일로 저장했습니다.")

        elif response.status_code == 404:
            print(f"❌ 종목을 찾을 수 없습니다: {response.json()}")
        else:
            print(f"❌ 오류 발생: {response.json()}")

    except requests.exceptions.ConnectionError:
        print("❌ 서버에 연결할 수 없습니다. 서버가 실행 중인지 확인하세요.")
    except Exception as e:
        print(f"❌ 예외 발생: {e}")


def test_search_companies(query: str, limit: int = 10):
    """종목 검색 테스트"""
    print(f"\n{'='*60}")
    print(f"테스트: 종목 검색 - '{query}'")
    print(f"{'='*60}")

    url = f"{BASE_URL}/company/search"
    params = {"query": query, "limit": limit}

    try:
        response = requests.get(url, params=params)

        print(f"상태 코드: {response.status_code}")

        if response.status_code == 200:
            data = response.json()
            print(f"\n검색 결과: {len(data)}개")

            for idx, company in enumerate(data, 1):
                print(f"\n{idx}. {company.get('companyName')}")
                print(f"   종목코드: {company.get('stockCode')}")
                print(f"   종목명: {company.get('stockName')}")
                print(f"   시장: {company.get('marketType')}")
        else:
            print(f"❌ 오류 발생: {response.json()}")

    except requests.exceptions.ConnectionError:
        print("❌ 서버에 연결할 수 없습니다. 서버가 실행 중인지 확인하세요.")
    except Exception as e:
        print(f"❌ 예외 발생: {e}")


def format_currency(value):
    """금액 포맷팅"""
    if value is None:
        return "-"

    if value >= 1_000_000_000_000:
        return f"{value / 1_000_000_000_000:.2f}조"
    elif value >= 100_000_000:
        return f"{value / 100_000_000:.2f}억"
    elif value >= 10_000:
        return f"{value / 10_000:.2f}만"
    else:
        return f"{value:,.0f}"


if __name__ == "__main__":
    print("=" * 60)
    print("종목 정보 API 테스트")
    print("=" * 60)

    # 1. 종목 정보 조회 테스트
    test_company_info("005930")  # 삼성전자

    # 2. 종목 검색 테스트
    test_search_companies("삼성", limit=5)
    test_search_companies("005930", limit=1)

    # 3. 다른 종목 테스트
    # test_company_info("000660")  # SK하이닉스
    # test_company_info("035720")  # 카카오
    # test_company_info("051910")  # LG화학

    print(f"\n{'='*60}")
    print("테스트 완료!")
    print("=" * 60)
