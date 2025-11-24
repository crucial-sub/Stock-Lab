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
from concurrent.futures import ThreadPoolExecutor, as_completed
from functools import lru_cache
import hashlib

logger = logging.getLogger(__name__)

# 키움증권 모의투자 API 호스트
KIWOOM_MOCK_HOST = "https://mockapi.kiwoom.com"

# 캐시 저장소 (토큰별로 캐시)
_balance_cache: Dict[str, Dict[str, Any]] = {}
_cache_timestamps: Dict[str, datetime] = {}
CACHE_DURATION_SECONDS = 10  # 10초 캐싱

# 예수금 캐시 (60초)
_deposit_cache: Dict[str, Dict[str, Any]] = {}
_deposit_timestamps: Dict[str, datetime] = {}


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
        
        * 60초 캐싱 적용
        """
        # 캐시 키 생성
        cache_key = f"{KiwoomService._get_cache_key(access_token)}_{qry_tp}"
        
        # 캐시 유효성 확인 (60초)
        if cache_key in _deposit_timestamps:
            elapsed = (datetime.now() - _deposit_timestamps[cache_key]).total_seconds()
            if elapsed < 60:
                logger.debug("💾 캐시된 예수금 데이터 반환")
                return _deposit_cache[cache_key]

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
            
            # 캐시 저장
            _deposit_cache[cache_key] = response_data
            _deposit_timestamps[cache_key] = datetime.now()
            
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
    def _call_api_with_retry(
        api_func,
        api_name: str,
        access_token: str,
        max_retries: int = 3,
        initial_delay: float = 1.0
    ) -> Dict[str, Any]:
        """
        Rate Limit을 고려한 API 호출 재시도 로직

        Args:
            api_func: 호출할 API 함수
            api_name: API 이름 (로깅용)
            access_token: 접근 토큰
            max_retries: 최대 재시도 횟수
            initial_delay: 초기 대기 시간 (초)

        Returns:
            API 응답 데이터

        Raises:
            Exception: 모든 재시도 실패시
        """
        delay = initial_delay

        for attempt in range(max_retries):
            try:
                result = api_func(access_token)
                if attempt > 0:
                    logger.info(f"✅ {api_name} API 재시도 성공 (시도 {attempt + 1}/{max_retries})")
                return result

            except requests.RequestException as e:
                # 429 Rate Limit 에러 확인
                is_rate_limit = False
                if hasattr(e, 'response') and e.response is not None:
                    if e.response.status_code == 429:
                        is_rate_limit = True
                        logger.warning(f"⚠️ {api_name} API Rate Limit 발생 (시도 {attempt + 1}/{max_retries})")

                # 마지막 시도였다면 예외 발생
                if attempt == max_retries - 1:
                    logger.error(f"❌ {api_name} API 호출 최종 실패 ({max_retries}회 시도)")
                    raise

                # Rate Limit 에러면 더 긴 대기, 아니면 지수 백오프
                if is_rate_limit:
                    wait_time = delay * 2  # Rate Limit시 2배 대기
                else:
                    wait_time = delay * (2 ** attempt)  # 지수 백오프

                logger.info(f"🔄 {wait_time:.1f}초 후 재시도...")
                time.sleep(wait_time)

            except Exception as e:
                logger.error(f"❌ {api_name} API 호출 중 예상치 못한 에러: {e}")
                if attempt == max_retries - 1:
                    raise
                time.sleep(delay)

        raise Exception(f"{api_name} API 호출 실패")

    @staticmethod
    def _get_cache_key(access_token: str) -> str:
        """토큰으로 캐시 키 생성"""
        return hashlib.md5(access_token.encode()).hexdigest()

    @staticmethod
    def _is_cache_valid(cache_key: str) -> bool:
        """캐시가 유효한지 확인"""
        if cache_key not in _cache_timestamps:
            return False

        elapsed = (datetime.now() - _cache_timestamps[cache_key]).total_seconds()
        return elapsed < CACHE_DURATION_SECONDS

    @staticmethod
    def get_unified_balance(access_token: str) -> Dict[str, Any]:
        """
        통합 잔고 조회 - 여러 API를 조합하여 통합된 잔고 정보 반환

        성능 최적화:
        1. 5개 API를 병렬로 호출 (ThreadPoolExecutor 사용)
        2. 10초간 결과 캐싱 (동일 토큰 재요청시 즉시 응답)
        3. Rate Limit 발생시 자동 재시도

        Args:
            access_token: 접근 토큰

        Returns:
            통합 잔고 정보 (cash, stock, pnl, orders)
        """
        # 캐시 확인
        cache_key = KiwoomService._get_cache_key(access_token)
        if KiwoomService._is_cache_valid(cache_key):
            logger.info("💾 캐시된 잔고 데이터 반환 (10초 이내)")
            return _balance_cache[cache_key]

        try:
            start_time = time.time()
            logger.info("📊 통합 잔고 조회 시작 (5개 API 병렬 호출)")

            # 병렬로 호출할 API 함수들 정의
            api_calls = [
                ("예수금 조회", KiwoomService.get_deposit_info),
                ("계좌 평가/잔고", KiwoomService.get_account_evaluation),
                ("수익률 조회", KiwoomService.get_account_balance),
                ("미체결 조회", KiwoomService.get_unexecuted_orders),
                ("체결 조회", KiwoomService.get_executed_orders),
            ]

            results = {}

            # ThreadPoolExecutor로 병렬 호출
            with ThreadPoolExecutor(max_workers=5) as executor:
                # 각 API 호출을 스레드로 실행
                future_to_name = {
                    executor.submit(
                        KiwoomService._call_api_with_retry,
                        api_func,
                        api_name,
                        access_token,
                        3,  # max_retries
                        0.5  # initial_delay (병렬이므로 짧게)
                    ): api_name
                    for api_name, api_func in api_calls
                }

                # 완료된 순서대로 결과 수집
                for future in as_completed(future_to_name):
                    api_name = future_to_name[future]
                    try:
                        result = future.result()
                        results[api_name] = result
                        logger.info(f"✅ {api_name} 완료")
                    except Exception as e:
                        logger.error(f"❌ {api_name} 실패: {e}")
                        # 실패한 API는 빈 딕셔너리로 처리
                        results[api_name] = {}

            # 통합 데이터 구성
            deposit = results.get("예수금 조회", {})
            evaluation = results.get("계좌 평가/잔고", {})
            profit = results.get("수익률 조회", {})
            unexecuted = results.get("미체결 조회", {})
            executed = results.get("체결 조회", {})

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

            # 캐시 저장
            _balance_cache[cache_key] = unified_data
            _cache_timestamps[cache_key] = datetime.now()

            elapsed = time.time() - start_time
            logger.info(f"✅ 통합 잔고 조회 완료 (소요시간: {elapsed:.2f}초)")

            return unified_data

        except Exception as e:
            logger.error(f"❌ 통합 잔고 조회 실패: {e}")
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
            result = response.json()

            # 응답 로깅
            logger.info(f"💰 매수 주문 API 응답 (종목: {stock_code}, 수량: {quantity})")
            logger.info(f"  - return_code: {result.get('return_code', 'N/A')}")
            logger.info(f"  - return_msg: {result.get('return_msg', 'N/A')}")
            logger.info(f"  - 전체 응답: {result}")

            return result
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
            result = response.json()

            # 응답 로깅
            logger.info(f"💰 매도 주문 API 응답 (종목: {stock_code}, 수량: {quantity})")
            logger.info(f"  - return_code: {result.get('return_code', 'N/A')}")
            logger.info(f"  - return_msg: {result.get('return_msg', 'N/A')}")
            logger.info(f"  - 전체 응답: {result}")

            return result
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
            # DB에 저장된 만료 시간 확인
            from datetime import timezone
            now = datetime.now(timezone.utc)
            
            # 만료 시간이 없거나, 이미 만료되었거나, 만료 10분 전이면 갱신
            if (not user.kiwoom_token_expires_at or 
                now >= user.kiwoom_token_expires_at - timedelta(minutes=10)):
                
                logger.info(f"🔄 키움 토큰 만료 임박/경과 (user: {user.email})")
            else:
                # 유효하면 그대로 반환
                return user.kiwoom_access_token

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
