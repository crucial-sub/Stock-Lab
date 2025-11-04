#!/usr/bin/env python3
"""
Quant API 테스트 스크립트
"""
import requests
import json
from datetime import date

# API 베이스 URL
BASE_URL = "http://localhost:8000"

def test_health():
    """헬스체크 테스트"""
    response = requests.get(f"{BASE_URL}/health")
    print("Health Check:", response.json())
    return response.status_code == 200

def test_per_factor():
    """PER 팩터 계산 테스트"""
    data = {
        "base_date": "2024-01-01",
        "market_type": "KOSPI",
        "stock_codes": None  # 전체 KOSPI 종목
    }

    # factors_extended 엔드포인트 사용
    response = requests.post(
        f"{BASE_URL}/api/v1/factors/per",
        json=data
    )

    if response.status_code == 200:
        result = response.json()
        print(f"\nPER 팩터 계산 결과:")
        print(f"- 계산 날짜: {result.get('base_date')}")
        print(f"- 총 종목 수: {result.get('total_count')}")
        print(f"- 계산 시간: {result.get('calculation_time_ms'):.2f}ms")

        # 상위 5개 종목 출력
        if 'data' in result and result['data']:
            print("\n상위 5개 종목 (낮은 PER):")
            for i, stock in enumerate(result['data'][:5], 1):
                print(f"  {i}. {stock['company_name']} ({stock['stock_code']})")
                print(f"     PER: {stock['value']:.2f}, 순위: {stock['rank']}")
    else:
        print(f"Error: {response.status_code}")
        print(response.text)

    return response.status_code == 200

def test_dividend_yield():
    """배당수익률 팩터 테스트"""
    data = {
        "base_date": "2024-01-01",
        "market_type": "KOSPI"
    }

    response = requests.post(
        f"{BASE_URL}/api/v1/factors/dividend-yield",
        json=data
    )

    if response.status_code == 200:
        result = response.json()
        print(f"\n배당수익률 계산 결과:")
        print(f"- 총 종목 수: {result.get('total_count')}")

        if 'data' in result and result['data']:
            print("\n상위 5개 고배당 종목:")
            for i, stock in enumerate(result['data'][:5], 1):
                print(f"  {i}. {stock['company_name']} ({stock['stock_code']})")
                if stock.get('value'):
                    print(f"     배당수익률: {stock['value']:.2f}%")
    else:
        print(f"Error: {response.status_code}")

    return response.status_code == 200

def main():
    print("=== Quant Investment API 테스트 ===\n")

    # 헬스체크
    if test_health():
        print("✅ 서버 정상 작동 중\n")

    # PER 팩터 테스트
    print("\n" + "="*50)
    if test_per_factor():
        print("✅ PER 팩터 계산 성공")

    # 배당수익률 테스트
    print("\n" + "="*50)
    if test_dividend_yield():
        print("✅ 배당수익률 계산 성공")

    print("\n" + "="*50)
    print("\n📊 API 문서를 보려면 브라우저에서 접속하세요:")
    print("   http://localhost:8000/docs")

if __name__ == "__main__":
    main()