#!/bin/bash

echo "================================================================================"
echo "종합 백테스트 실행"
echo "================================================================================"
echo ""
echo "매수 조건: (PBR<2.5 AND PER<20) OR ROE>8%"
echo "매도 조건: 목표수익 20%, 손절 10%, 최소 3일, 최대 90일"
echo "매매 대상: IT서비스+반도체 테마 + 삼성전자,SK하이닉스,NAVER,LG화학"
echo "리밸런싱: 주간"
echo ""

# Docker 컨테이너에서 Python 스크립트 실행
docker exec sl_backend_dev python3 -c "
import asyncio
import sys
sys.path.insert(0, '/app')

from uuid import uuid4
from datetime import date
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import text

DATABASE_URL = 'postgresql+asyncpg://stocklabadmin:nmmteam05@host.docker.internal:5433/stock_lab_investment_db'

async def main():
    engine = create_async_engine(DATABASE_URL, echo=False)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as session:
        # 사용자 조회
        result = await session.execute(text('SELECT user_id FROM users LIMIT 1'))
        user_id = result.scalar()

        # 기존 전략 조회
        result = await session.execute(text('SELECT strategy_id FROM trading_rules LIMIT 1'))
        strategy_id = result.scalar()

        if not strategy_id:
            print('❌ 전략을 찾을 수 없습니다')
            return

        # 매매 규칙 업데이트
        await session.execute(text('''
            UPDATE trading_rules
            SET buy_condition = :buy_cond,
                sell_condition = :sell_cond,
                rebalance_frequency = 'WEEKLY'
            WHERE strategy_id = :sid
        '''), {
            'sid': strategy_id,
            'buy_cond': {
                'conditions': [
                    {'name': 'A', 'exp_left_side': '기본값({pbr})', 'inequality': '<', 'exp_right_side': 2.5},
                    {'name': 'B', 'exp_left_side': '기본값({per})', 'inequality': '<', 'exp_right_side': 20},
                    {'name': 'C', 'exp_left_side': '기본값({roe})', 'inequality': '>', 'exp_right_side': 8}
                ],
                'logic': '(A and B) or C',
                'priority_factor': '기본값({roe})',
                'priority_order': 'desc',
                'per_stock_ratio': 5.0,
                'max_daily_stock': 3,
                'trade_targets': {
                    'use_all_stocks': False,
                    'selected_themes': ['IT 서비스', '반도체'],
                    'selected_stocks': ['005930', '000660', '035420', '051910']
                }
            },
            'sell_cond': {
                'target_and_loss': {'target_gain': 20.0, 'stop_loss': 10.0},
                'hold_days': {'min_hold_days': 3, 'max_hold_days': 90}
            }
        })

        # 백테스트 세션 생성
        session_id = str(uuid4())
        await session.execute(text('''
            INSERT INTO simulation_sessions
            (session_id, strategy_id, user_id, session_name, start_date, end_date, initial_capital, status, progress)
            VALUES (:sid, :strat, :uid, :name, :start, :end, :capital, 'PENDING', 0)
        '''), {
            'sid': session_id,
            'strat': strategy_id,
            'uid': user_id,
            'name': '종합 테스트',
            'start': date(2024, 6, 1),
            'end': date(2025, 1, 31),
            'capital': 100000000
        })

        await session.commit()
        print(f'✅ 백테스트 세션 생성: {session_id}')

        # 백테스트 실행
        from app.services.advanced_backtest import _run_backtest_async
        print('\\n백테스트 실행 중...')
        await _run_backtest_async(db=session, session_id=session_id)
        print(f'\\n✅ 완료! Session ID: {session_id}')

    await engine.dispose()

asyncio.run(main())
"

echo ""
echo "프론트엔드에서 결과 확인하세요!"
