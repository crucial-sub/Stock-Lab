import requests
import json
import sys
sys.path.append('/Users/a2/Desktop/Stock-Lab-Demo/SL-Back-end')

from app.core.database import AsyncSessionLocal
from app.models.user import User
from sqlalchemy import select
import asyncio

async def test_buy_order():
    async with AsyncSessionLocal() as db:
        result = await db.execute(select(User).filter(User.email == 'ainrluca@gmail.com'))
        user = result.scalar_one_or_none()

        if not user or not user.kiwoom_access_token:
            print('No user or token found')
            return

        # 키움 API 매수 주문 테스트
        url = "https://mockapi.kiwoom.com/api/dostk/ordr"
        headers = {
            "Content-Type": "application/json;charset=UTF-8",
            "authorization": f"Bearer {user.kiwoom_access_token}",
            "cont-yn": "N",
            "next-key": "",
            "api-id": "kt10000",
        }
        data = {
            "dmst_stex_tp": "KRX",
            "stk_cd": "005930",  # 삼성전자
            "ord_qty": "1",
            "ord_uv": "",
            "trde_tp": "3",
            "cond_uv": "",
        }

        print("=" * 80)
        print("🔍 키움 API 매수 주문 테스트")
        print("=" * 80)
        print(f"URL: {url}")
        print(f"Headers: {json.dumps(headers, indent=2, ensure_ascii=False)}")
        print(f"Data: {json.dumps(data, indent=2, ensure_ascii=False)}")
        print()

        response = requests.post(url, headers=headers, json=data, timeout=10)

        print("=" * 80)
        print("📥 API 응답")
        print("=" * 80)
        print(f"Status Code: {response.status_code}")
        print(f"Response Headers: {dict(response.headers)}")
        print()
        print("Response Body:")
        print(json.dumps(response.json(), indent=2, ensure_ascii=False))

asyncio.run(test_buy_order())
