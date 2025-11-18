"""
키움증권 API 서비스
"""
import requests
import logging
import time
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.user import User

logger = logging.getLogger(__name__)

# 키움증권 모의투자 API 호스트
KIWOOM_MOCK_HOST = "https://mockapi.kiwoom.com"


class KiwoomService:
    """키움증권 API 서비스"""

    @staticmethod
    def get_access_token(app_key: str, app_secret: str) -> Dict[str, Any]:
        """
        접근 토큰 발급

        Args:
            app_key: 앱 키
            app_secret: 앱 시크릿

        Returns:
            응답 데이터 (access_token, expires_in 등)

        Raises:
            requests.RequestException: API 요청 실패시
        """
        url = f"{KIWOOM_MOCK_HOST}/oauth2/token"
        headers = {
            "Content-Type": "application/json;charset=UTF-8",
        }
        data = {
            "grant_type": "client_credentials",
            "appkey": app_key,
            "secretkey": app_secret,
        }

        try:
            response = requests.post(url, headers=headers, json=data, timeout=10)
            response.raise_for_status()
            response_data = response.json()
            logger.info(f"키움증권 API 응답: {response_data}")
            return response_data
        except requests.RequestException as e:
            logger.error(f"키움증권 토큰 발급 실패: {e}")
            if hasattr(e, 'response') and e.response is not None:
                logger.error(f"응답 내용: {e.response.text}")
            raise

    @staticmethod
    async def update_user_kiwoom_credentials(
        db: Session,
        user_id: str,
        app_key: str,
        app_secret: str,
        access_token: str,
        expires_in: int
    ) -> User:
        """
        사용자의 키움증권 인증 정보 업데이트

        Args:
            db: 데이터베이스 세션
            user_id: 사용자 ID
            app_key: 앱 키
            app_secret: 앱 시크릿
            access_token: 접근 토큰
            expires_in: 토큰 만료 시간(초)

        Returns:
            업데이트된 사용자 객체
        """
        from sqlalchemy import select

        # 비동기 세션을 위한 select 사용
        result = await db.execute(select(User).filter(User.user_id == user_id))
        user = result.scalar_one_or_none()

        if not user:
            raise ValueError(f"사용자를 찾을 수 없습니다: {user_id}")

        # 토큰 만료 시간 계산 (현재 시간 + expires_in 초)
        from datetime import timezone
        expires_at = datetime.now(timezone.utc) + timedelta(seconds=expires_in)

        user.kiwoom_app_key = app_key
        user.kiwoom_app_secret = app_secret
        user.kiwoom_access_token = access_token
        user.kiwoom_token_expires_at = expires_at

        await db.commit()
        await db.refresh(user)

        logger.info(f"사용자 {user_id}의 키움증권 인증 정보가 업데이트되었습니다.")
        return user

    @staticmethod
    def refresh_token_if_needed(db: Session, user: User) -> Optional[str]:
        """
        필요시 토큰 갱신

        Args:
            db: 데이터베이스 세션
            user: 사용자 객체

        Returns:
            갱신된 access_token (갱신이 필요없으면 기존 토큰)
        """
        # 토큰이 없거나 만료된 경우 갱신
        if not user.kiwoom_access_token or not user.kiwoom_token_expires_at:
            return None

        # 만료 10분 전에 갱신
        from datetime import timezone
        if datetime.now(timezone.utc) >= user.kiwoom_token_expires_at - timedelta(minutes=10):
            try:
                response_data = KiwoomService.get_access_token(
                    user.kiwoom_app_key,
                    user.kiwoom_app_secret
                )

                # 토큰 업데이트
                # 키움 API는 'token' 필드로 응답 (access_token이 아님)
                access_token = response_data.get("token")

                # expires_dt를 파싱하여 만료 시간 계산
                from datetime import timezone
                expires_dt = response_data.get("expires_dt")
                if expires_dt:
                    try:
                        expire_time = datetime.strptime(expires_dt, "%Y%m%d%H%M%S").replace(tzinfo=timezone.utc)
                        expires_in = int((expire_time - datetime.now(timezone.utc)).total_seconds())
                    except:
                        expires_in = 86400  # 파싱 실패시 기본 24시간
                else:
                    expires_in = 86400  # 기본 24시간

                user.kiwoom_access_token = access_token
                user.kiwoom_token_expires_at = datetime.now(timezone.utc) + timedelta(seconds=expires_in)

                db.commit()
                db.refresh(user)

                logger.info(f"사용자 {user.user_id}의 토큰이 갱신되었습니다.")
                return access_token

            except Exception as e:
                logger.error(f"토큰 갱신 실패: {e}")
                return None

        return user.kiwoom_access_token

    @staticmethod
    def get_deposit_info(access_token: str, qry_tp: str = "3") -> Dict[str, Any]:
        """
        예수금 상세 현황 조회 (REST API)

        Args:
            access_token: 접근 토큰
            qry_tp: 조회구분 (3: 추정조회, 2: 일반조회, 기본값: 3)

        Returns:
            예수금 상세 정보

        Raises:
            requests.RequestException: API 요청 실패시
        """
        url = f"{KIWOOM_MOCK_HOST}/api/dostk/acnt"
        headers = {
            "Content-Type": "application/json;charset=UTF-8",
            "authorization": f"Bearer {access_token}",
            "cont-yn": "N",
            "next-key": "",
            "api-id": "kt00001",  # 예수금상세현황요청
        }
        data = {
            "qry_tp": qry_tp,
        }

        try:
            response = requests.post(url, headers=headers, json=data, timeout=10)
            response.raise_for_status()
            response_data = response.json()
            logger.info(f"예수금 조회 API 응답: {response_data}")
            return response_data
        except requests.RequestException as e:
            logger.error(f"예수금 조회 실패: {e}")
            if hasattr(e, 'response') and e.response is not None:
                logger.error(f"응답 내용: {e.response.text}")
            raise

    @staticmethod
    def get_account_evaluation(access_token: str, qry_tp: str = "3", dmst_stex_tp: str = "1", stex_tp: str = "0") -> Dict[str, Any]:
        """
        계좌 평가/잔고 조회 (REST API)

        Args:
            access_token: 접근 토큰
            qry_tp: 조회구분 (3: 추정조회, 2: 일반조회, 기본값: 3)
            dmst_stex_tp: 국내외거래소구분 (1: 국내, 2: 해외, 기본값: 1)
            stex_tp: 거래소구분 (0: 통합, 1: KRX, 2: NXT, 기본값: 0)

        Returns:
            계좌 평가 잔고 정보

        Raises:
            requests.RequestException: API 요청 실패시
        """
        url = f"{KIWOOM_MOCK_HOST}/api/dostk/acnt"
        headers = {
            "Content-Type": "application/json;charset=UTF-8",
            "authorization": f"Bearer {access_token}",
            "cont-yn": "N",
            "next-key": "",
            "api-id": "kt00018",  # 계좌평가잔고조회
        }
        data = {
            "qry_tp": qry_tp,
            "dmst_stex_tp": dmst_stex_tp,
            "stex_tp": stex_tp,
        }

        try:
            response = requests.post(url, headers=headers, json=data, timeout=10)
            response.raise_for_status()
            response_data = response.json()
            logger.info(f"계좌 평가 조회 API 응답: {response_data}")
            return response_data
        except requests.RequestException as e:
            logger.error(f"계좌 평가 조회 실패: {e}")
            if hasattr(e, 'response') and e.response is not None:
                logger.error(f"응답 내용: {e.response.text}")
            raise

    @staticmethod
    def get_account_balance(access_token: str, stex_tp: str = "0") -> Dict[str, Any]:
        """
        계좌 수익률 조회 (REST API)

        Args:
            access_token: 접근 토큰
            stex_tp: 거래소구분 (0: 통합, 1: KRX, 2: NXT, 기본값: 0)

        Returns:
            계좌 수익률 정보

        Raises:
            requests.RequestException: API 요청 실패시
        """
        url = f"{KIWOOM_MOCK_HOST}/api/dostk/acnt"
        headers = {
            "Content-Type": "application/json;charset=UTF-8",
            "authorization": f"Bearer {access_token}",
            "cont-yn": "N",
            "next-key": "",
            "api-id": "ka10085",  # 계좌수익률요청
        }
        data = {
            "stex_tp": stex_tp,
        }

        try:
            response = requests.post(url, headers=headers, json=data, timeout=10)
            response.raise_for_status()
            response_data = response.json()
            logger.info(f"계좌 수익률 조회 API 응답: {response_data}")
            return response_data
        except requests.RequestException as e:
            logger.error(f"계좌 수익률 조회 실패: {e}")
            if hasattr(e, 'response') and e.response is not None:
                logger.error(f"응답 내용: {e.response.text}")
            raise

    @staticmethod
    def get_unexecuted_orders(access_token: str, all_stk_tp: str = "0", trde_tp: str = "0", stex_tp: str = "0") -> Dict[str, Any]:
        """
        미체결 조회 (REST API)

        Args:
            access_token: 접근 토큰
            all_stk_tp: 전체종목구분 (0: 전체, 1: 일반, 기본값: 0)
            trde_tp: 매매구분 (0: 전체, 1: 매수, 2: 매도, 기본값: 0)
            stex_tp: 거래소구분 (0: 통합, 1: KRX, 2: NXT, 기본값: 0)

        Returns:
            미체결 정보

        Raises:
            requests.RequestException: API 요청 실패시
        """
        url = f"{KIWOOM_MOCK_HOST}/api/dostk/acnt"
        headers = {
            "Content-Type": "application/json;charset=UTF-8",
            "authorization": f"Bearer {access_token}",
            "cont-yn": "N",
            "next-key": "",
            "api-id": "ka10075",  # 미체결조회
        }
        data = {
            "all_stk_tp": all_stk_tp,
            "trde_tp": trde_tp,
            "stex_tp": stex_tp,
        }

        try:
            response = requests.post(url, headers=headers, json=data, timeout=10)
            response.raise_for_status()
            response_data = response.json()
            logger.info(f"미체결 조회 API 응답: {response_data}")
            return response_data
        except requests.RequestException as e:
            logger.error(f"미체결 조회 실패: {e}")
            if hasattr(e, 'response') and e.response is not None:
                logger.error(f"응답 내용: {e.response.text}")
            raise

    @staticmethod
    def get_executed_orders(access_token: str, qry_tp: str = "2", sell_tp: str = "0", stex_tp: str = "0") -> Dict[str, Any]:
        """
        체결 조회 (REST API)

        Args:
            access_token: 접근 토큰
            qry_tp: 조회구분 (2: 일반조회, 기본값: 2)
            sell_tp: 매도구분 (0: 전체, 1: 매도, 기본값: 0)
            stex_tp: 거래소구분 (0: 통합, 1: KRX, 2: NXT, 기본값: 0)

        Returns:
            체결 정보

        Raises:
            requests.RequestException: API 요청 실패시
        """
        url = f"{KIWOOM_MOCK_HOST}/api/dostk/acnt"
        headers = {
            "Content-Type": "application/json;charset=UTF-8",
            "authorization": f"Bearer {access_token}",
            "cont-yn": "N",
            "next-key": "",
            "api-id": "ka10076",  # 체결조회
        }
        data = {
            "qry_tp": qry_tp,
            "sell_tp": sell_tp,
            "stex_tp": stex_tp,
        }

        try:
            response = requests.post(url, headers=headers, json=data, timeout=10)
            response.raise_for_status()
            response_data = response.json()
            logger.info(f"체결 조회 API 응답: {response_data}")
            return response_data
        except requests.RequestException as e:
            logger.error(f"체결 조회 실패: {e}")
            if hasattr(e, 'response') and e.response is not None:
                logger.error(f"응답 내용: {e.response.text}")
            raise

    @staticmethod
    def get_unified_balance(access_token: str) -> Dict[str, Any]:
        """
        통합 잔고 조회 - 여러 API를 조합하여 통합된 잔고 정보 반환

        Args:
            access_token: 접근 토큰

        Returns:
            통합 잔고 정보 (cash, stock, pnl, orders)
        """
        try:
            # 1. 예수금 조회
            deposit = KiwoomService.get_deposit_info(access_token)
            time.sleep(0.3)  # Rate Limit 방지

            # 2. 계좌 평가/잔고 조회
            evaluation = KiwoomService.get_account_evaluation(access_token)
            time.sleep(0.3)  # Rate Limit 방지

            # 3. 수익률 조회
            profit = KiwoomService.get_account_balance(access_token)
            time.sleep(0.3)  # Rate Limit 방지

            # 4. 미체결 조회
            unexecuted = KiwoomService.get_unexecuted_orders(access_token)
            time.sleep(0.3)  # Rate Limit 방지

            # 5. 체결 조회
            executed = KiwoomService.get_executed_orders(access_token)

            # 통합 데이터 구성
            unified_data = {
                "cash": {
                    "balance": deposit.get("entr", "0"),  # 예수금
                    "withdrawable": deposit.get("pymn_alow_amt", "0"),  # 출금가능금액
                    "orderable": deposit.get("ord_alow_amt", "0"),  # 주문가능금액
                    "d1_estimated": deposit.get("d1_entra", "0"),  # D+1 추정예수금
                    "d2_estimated": deposit.get("d2_entra", "0"),  # D+2 추정예수금
                },
                "holdings": evaluation,  # 계좌 평가/잔고
                "profit": profit,  # 수익률
                "unexecuted": unexecuted,  # 미체결
                "executed": executed,  # 체결
            }

            return unified_data

        except Exception as e:
            logger.error(f"통합 잔고 조회 실패: {e}")
            raise

    @staticmethod
    def buy_stock(
        access_token: str,
        stock_code: str,
        quantity: str,
        price: str = "",
        trade_type: str = "3",
        dmst_stex_tp: str = "KRX"
    ) -> Dict[str, Any]:
        """
        주식 매수 주문

        Args:
            access_token: 접근 토큰
            stock_code: 종목 코드
            quantity: 주문 수량
            price: 주문 단가 (시장가일 경우 빈 문자열)
            trade_type: 매매 구분 (3: 시장가)
            dmst_stex_tp: 국내거래소구분

        Returns:
            주문 결과

        Raises:
            requests.RequestException: API 요청 실패시
        """
        url = f"{KIWOOM_MOCK_HOST}/api/dostk/ordr"
        headers = {
            "Content-Type": "application/json;charset=UTF-8",
            "authorization": f"Bearer {access_token}",
            "cont-yn": "N",
            "next-key": "",
            "api-id": "kt10000",
        }
        data = {
            "dmst_stex_tp": dmst_stex_tp,
            "stk_cd": stock_code,
            "ord_qty": quantity,
            "ord_uv": price,
            "trde_tp": trade_type,
            "cond_uv": "",
        }

        try:
            response = requests.post(url, headers=headers, json=data, timeout=10)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            logger.error(f"주식 매수 주문 실패: {e}")
            raise

    @staticmethod
    def sell_stock(
        access_token: str,
        stock_code: str,
        quantity: str,
        price: str = "",
        trade_type: str = "3",
        dmst_stex_tp: str = "KRX"
    ) -> Dict[str, Any]:
        """
        주식 매도 주문

        Args:
            access_token: 접근 토큰
            stock_code: 종목 코드
            quantity: 주문 수량
            price: 주문 단가 (시장가일 경우 빈 문자열)
            trade_type: 매매 구분 (3: 시장가)
            dmst_stex_tp: 국내거래소구분

        Returns:
            주문 결과

        Raises:
            requests.RequestException: API 요청 실패시
        """
        url = f"{KIWOOM_MOCK_HOST}/api/dostk/ordr"
        headers = {
            "Content-Type": "application/json;charset=UTF-8",
            "authorization": f"Bearer {access_token}",
            "cont-yn": "N",
            "next-key": "",
            "api-id": "kt10001",
        }
        data = {
            "dmst_stex_tp": dmst_stex_tp,
            "stk_cd": stock_code,
            "ord_qty": quantity,
            "ord_uv": price,
            "trde_tp": trade_type,
            "cond_uv": "",
        }

        try:
            response = requests.post(url, headers=headers, json=data, timeout=10)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            logger.error(f"주식 매도 주문 실패: {e}")
            raise

    @staticmethod
    async def ensure_valid_token(db: AsyncSession, user: User) -> str:
        """
        키움 토큰 유효성 보장 - 만료 시 자동 갱신

        Args:
            db: 데이터베이스 세션
            user: 유저 객체

        Returns:
            유효한 access_token

        Raises:
            ValueError: 토큰 갱신 실패
        """
        if not user.kiwoom_access_token:
            raise ValueError("키움 토큰이 없습니다. 계정 연동을 먼저 진행해주세요.")

        try:
            # 간단한 API 호출로 토큰 유효성 테스트
            test_result = KiwoomService.get_deposit_info(
                access_token=user.kiwoom_access_token,
                qry_tp="3"
            )

            # 토큰이 유효하면 그대로 반환
            if test_result.get("return_code") == 0:
                logger.debug(f"✅ 키움 토큰 유효 (user: {user.email})")
                return user.kiwoom_access_token

            # 토큰이 만료되었으면 갱신 시도
            error_msg = test_result.get("return_msg", "")
            logger.warning(f"⚠️ 키움 토큰 만료 감지: {error_msg}")

            if not user.kiwoom_app_key or not user.kiwoom_app_secret:
                raise ValueError("app_key/app_secret이 없어 토큰 갱신이 불가능합니다.")

            # 토큰 갱신
            logger.info(f"🔄 키움 토큰 자동 갱신 시작 (user: {user.email})")

            new_token_response = KiwoomService.get_access_token(
                app_key=user.kiwoom_app_key,
                app_secret=user.kiwoom_app_secret
            )

            new_access_token = new_token_response.get("token")
            expires_dt = new_token_response.get("expires_dt")

            if not new_access_token:
                raise ValueError("토큰 갱신 응답에 token 필드가 없습니다.")

            # 만료 시간 계산
            from datetime import timezone
            if expires_dt:
                try:
                    expire_time = datetime.strptime(expires_dt, "%Y%m%d%H%M%S").replace(tzinfo=timezone.utc)
                    user.kiwoom_token_expires_at = expire_time
                except:
                    user.kiwoom_token_expires_at = datetime.now(timezone.utc) + timedelta(days=1)
            else:
                user.kiwoom_token_expires_at = datetime.now(timezone.utc) + timedelta(days=1)

            # DB 업데이트
            user.kiwoom_access_token = new_access_token
            await db.commit()
            await db.refresh(user)

            logger.info(f"✅ 키움 토큰 자동 갱신 성공 (user: {user.email})")
            return new_access_token

        except Exception as e:
            logger.error(f"❌ 키움 토큰 검증/갱신 실패: {e}", exc_info=True)
            raise ValueError(f"키움 토큰 갱신 실패: {e}")
