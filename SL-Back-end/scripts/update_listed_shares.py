"""
상장주식수(listed_shares) 업데이트 스크립트
- 한국투자증권 API를 통해 최신 상장주식수 조회
- stock_prices 테이블의 최신 거래일 데이터 업데이트
"""
import asyncio
import os
from datetime import datetime
from sqlalchemy import select, update, desc
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.models.company import Company
from app.models.stock_price import StockPrice
from app.core.config import settings
import httpx


class ListedSharesUpdater:
    """상장주식수 업데이트"""

    def __init__(self):
        self.engine = create_async_engine(settings.DATABASE_URL, echo=False)
        self.async_session = sessionmaker(
            self.engine, class_=AsyncSession, expire_on_commit=False
        )
        # 한국투자증권 API 설정
        self.app_key = os.getenv("KIS_APP_KEY")
        self.app_secret = os.getenv("KIS_APP_SECRET")
        self.base_url = "https://openapi.koreainvestment.com:9443"
        self.access_token = None

    async def get_access_token(self):
        """접근 토큰 발급"""
        if self.access_token:
            return self.access_token

        url = f"{self.base_url}/oauth2/tokenP"
        headers = {"content-type": "application/json"}
        body = {
            "grant_type": "client_credentials",
            "appkey": self.app_key,
            "appsecret": self.app_secret,
        }

        async with httpx.AsyncClient() as client:
            response = await client.post(url, json=body, headers=headers)
            if response.status_code == 200:
                self.access_token = response.json()["access_token"]
                return self.access_token
            else:
                raise Exception(f"토큰 발급 실패: {response.text}")

    async def get_stock_info(self, stock_code: str) -> dict:
        """종목 정보 조회 (상장주식수 포함)"""
        token = await self.get_access_token()

        url = f"{self.base_url}/uapi/domestic-stock/v1/quotations/inquire-price"
        headers = {
            "content-type": "application/json",
            "authorization": f"Bearer {token}",
            "appkey": self.app_key,
            "appsecret": self.app_secret,
            "tr_id": "FHKST01010100",  # 주식현재가 시세
        }
        params = {
            "FID_COND_MRKT_DIV_CODE": "J",  # 주식
            "FID_INPUT_ISCD": stock_code,
        }

        async with httpx.AsyncClient() as client:
            response = await client.get(url, headers=headers, params=params)
            if response.status_code == 200:
                data = response.json()
                if data.get("rt_cd") == "0":
                    output = data.get("output", {})
                    return {
                        "listed_shares": int(output.get("lstn_stqt", 0)),  # 상장주식수
                        "market_cap": int(output.get("hts_avls", 0)),  # 시가총액
                    }
            return None

    async def update_all_listed_shares(self):
        """전체 종목의 상장주식수 업데이트"""
        async with self.async_session() as session:
            # 1. 모든 활성 종목 조회
            result = await session.execute(
                select(Company).where(Company.stock_code.isnot(None))
            )
            companies = result.scalars().all()

            total = len(companies)
            success = 0
            failed = 0

            print(f"총 {total}개 종목의 상장주식수 업데이트 시작...")

            for idx, company in enumerate(companies, 1):
                try:
                    # API 호출
                    stock_info = await self.get_stock_info(company.stock_code)

                    if stock_info:
                        # 최신 거래일의 stock_prices 업데이트
                        latest_price_query = (
                            select(StockPrice)
                            .where(StockPrice.company_id == company.company_id)
                            .order_by(desc(StockPrice.trade_date))
                            .limit(1)
                        )
                        latest_price_result = await session.execute(latest_price_query)
                        latest_price = latest_price_result.scalar_one_or_none()

                        if latest_price:
                            latest_price.listed_shares = stock_info["listed_shares"]
                            latest_price.market_cap = stock_info["market_cap"]
                            success += 1

                            if idx % 10 == 0:
                                print(
                                    f"진행: {idx}/{total} ({idx/total*100:.1f}%) - "
                                    f"{company.stock_name} 완료"
                                )
                        else:
                            print(f"경고: {company.stock_name} - 가격 데이터 없음")
                            failed += 1
                    else:
                        print(f"실패: {company.stock_name} - API 응답 없음")
                        failed += 1

                    # Rate Limit 방지 (초당 20회 제한)
                    await asyncio.sleep(0.05)  # 50ms 대기

                    # 100건마다 커밋
                    if idx % 100 == 0:
                        await session.commit()
                        print(f"✓ {idx}건 저장 완료")

                except Exception as e:
                    print(f"에러: {company.stock_name} - {str(e)}")
                    failed += 1
                    continue

            # 최종 커밋
            await session.commit()

            print("\n" + "=" * 50)
            print(f"업데이트 완료!")
            print(f"성공: {success}건")
            print(f"실패: {failed}건")
            print(f"전체: {total}건")
            print("=" * 50)

    async def close(self):
        """리소스 정리"""
        await self.engine.dispose()


async def main():
    """메인 실행 함수"""
    updater = ListedSharesUpdater()

    try:
        await updater.update_all_listed_shares()
    finally:
        await updater.close()


if __name__ == "__main__":
    print(f"시작 시간: {datetime.now()}")
    asyncio.run(main())
    print(f"종료 시간: {datetime.now()}")
