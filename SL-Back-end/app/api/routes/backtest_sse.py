"""
백테스트 SSE (Server-Sent Events) API
실시간 진행률 스트리밍 지원
"""
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from typing import AsyncGenerator
import asyncio
import json
import logging
from uuid import UUID

from app.core.dependencies import get_current_user
from app.models.user import User
from app.core.cache import get_redis_client

logger = logging.getLogger(__name__)

router = APIRouter()


async def progress_stream(backtest_id: str) -> AsyncGenerator[str, None]:
    """
    백테스트 진행률을 실시간으로 스트리밍

    Args:
        backtest_id: 백테스트 세션 ID

    Yields:
        SSE 형식의 진행률 데이터
    """
    redis_client = await get_redis_client()
    last_progress = -1
    max_retries = 600  # 10분 (600초) 타임아웃
    retry_count = 0

    try:
        while retry_count < max_retries:
            try:
                # Redis에서 진행률 조회
                progress_key = f"backtest:progress:{backtest_id}"
                progress_data = await redis_client.get(progress_key)

                if progress_data:
                    data = json.loads(progress_data)
                    current_progress = data.get('progress', 0)
                    status = data.get('status', 'running')

                    # 진행률이 업데이트된 경우에만 전송
                    if current_progress != last_progress or status != 'running':
                        last_progress = current_progress

                        # SSE 형식으로 전송
                        yield f"data: {json.dumps(data)}\n\n"

                        # 완료 또는 실패 시 스트림 종료
                        if status in ['completed', 'failed']:
                            logger.info(f"백테스트 {backtest_id} 진행률 스트림 종료: {status}")
                            break

                # 1초 대기
                await asyncio.sleep(1)
                retry_count += 1

            except Exception as e:
                logger.error(f"진행률 스트림 에러: {e}")
                yield f"data: {json.dumps({'error': str(e), 'progress': last_progress})}\n\n"
                await asyncio.sleep(1)
                retry_count += 1

        # 타임아웃 메시지
        if retry_count >= max_retries:
            yield f"data: {json.dumps({'status': 'timeout', 'message': '진행률 업데이트 타임아웃'})}\n\n"

    except asyncio.CancelledError:
        logger.info(f"진행률 스트림 취소됨: {backtest_id}")
    except Exception as e:
        logger.error(f"진행률 스트림 예외: {e}")
        yield f"data: {json.dumps({'status': 'error', 'message': str(e)})}\n\n"


@router.get("/backtest/{backtest_id}/progress/stream")
async def stream_backtest_progress(
    backtest_id: str,
    current_user: User = Depends(get_current_user)
):
    """
    백테스트 진행률 실시간 스트리밍 (SSE)

    Args:
        backtest_id: 백테스트 세션 ID
        current_user: 현재 로그인한 사용자

    Returns:
        SSE 스트림
    """
    logger.info(f"백테스트 진행률 스트림 시작: {backtest_id}")

    return StreamingResponse(
        progress_stream(backtest_id),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",  # Nginx 버퍼링 비활성화
        }
    )


@router.get("/backtest/{backtest_id}/progress")
async def get_backtest_progress(
    backtest_id: str,
    current_user: User = Depends(get_current_user)
):
    """
    백테스트 현재 진행률 조회 (일회성)

    Args:
        backtest_id: 백테스트 세션 ID
        current_user: 현재 로그인한 사용자

    Returns:
        진행률 정보
    """
    redis_client = await get_redis_client()

    try:
        progress_key = f"backtest:progress:{backtest_id}"
        progress_data = await redis_client.get(progress_key)

        if not progress_data:
            raise HTTPException(
                status_code=404,
                detail=f"백테스트 진행률 정보를 찾을 수 없습니다: {backtest_id}"
            )

        data = json.loads(progress_data)
        return data

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"진행률 조회 에러: {e}")
        raise HTTPException(status_code=500, detail=str(e))
