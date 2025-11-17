"""
실시간 틱 데이터 API (Tick Service 프록시)
"""
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from typing import Optional
import httpx
import websockets
import asyncio
import json
from loguru import logger


router = APIRouter()

# Tick Service URL
TICK_SERVICE_URL = "http://localhost:8002"
TICK_SERVICE_WS_URL = "ws://localhost:8002"


@router.get("/realtime/health")
async def health_check():
    """Tick Service 헬스체크"""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{TICK_SERVICE_URL}/health", timeout=5.0)
            return response.json()
    except Exception as e:
        return {"status": "error", "message": str(e)}


@router.get("/realtime/stocks")
async def get_stocks():
    """
    전체 종목 리스트 조회 (Tick Service 프록시)
    """
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{TICK_SERVICE_URL}/api/stocks", timeout=10.0)
            return response.json()
    except Exception as e:
        logger.error(f"종목 리스트 조회 실패: {e}")
        return []


@router.get("/realtime/mode")
async def get_mode():
    """
    현재 모드 조회 (LIVE/REPLAY)
    """
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{TICK_SERVICE_URL}/api/replay/mode", timeout=5.0)
            return response.json()
    except Exception as e:
        logger.error(f"모드 조회 실패: {e}")
        return {"mode": "UNKNOWN"}


@router.get("/realtime/stocks/{stock_code}/latest")
async def get_latest_tick(stock_code: str):
    """
    종목 최신 틱 데이터
    """
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{TICK_SERVICE_URL}/api/stocks/{stock_code}/latest",
                timeout=5.0
            )
            return response.json()
    except Exception as e:
        logger.error(f"최신 틱 조회 실패: {e}")
        return {"error": str(e)}


@router.get("/realtime/stocks/{stock_code}/history")
async def get_stock_history(stock_code: str, limit: int = 100):
    """
    종목 히스토리
    """
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{TICK_SERVICE_URL}/api/stocks/{stock_code}/history?limit={limit}",
                timeout=10.0
            )
            return response.json()
    except Exception as e:
        logger.error(f"히스토리 조회 실패: {e}")
        return []


@router.get("/realtime/highlights")
async def get_highlights():
    """
    하이라이트 구간 조회
    """
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{TICK_SERVICE_URL}/api/replay/highlights", timeout=5.0)
            return response.json()
    except Exception as e:
        logger.error(f"하이라이트 조회 실패: {e}")
        return {"highlights": []}


@router.websocket("/ws/realtime")
async def websocket_proxy(websocket: WebSocket):
    """
    Tick Service WebSocket 프록시
    """
    await websocket.accept()

    try:
        # Tick Service WebSocket에 연결
        async with websockets.connect(f"{TICK_SERVICE_WS_URL}/ws/realtime") as tick_ws:
            logger.info("Tick Service WebSocket 연결됨")

            # 양방향 프록시
            async def forward_to_client():
                """Tick Service → 클라이언트"""
                try:
                    async for message in tick_ws:
                        await websocket.send_text(message)
                except Exception as e:
                    logger.error(f"클라이언트 전송 오류: {e}")

            async def forward_to_tick_service():
                """클라이언트 → Tick Service"""
                try:
                    while True:
                        data = await websocket.receive_text()
                        await tick_ws.send(data)
                except WebSocketDisconnect:
                    logger.info("클라이언트 연결 해제")
                except Exception as e:
                    logger.error(f"Tick Service 전송 오류: {e}")

            # 양방향 동시 실행
            await asyncio.gather(
                forward_to_client(),
                forward_to_tick_service()
            )

    except Exception as e:
        logger.error(f"WebSocket 프록시 오류: {e}")
    finally:
        await websocket.close()
