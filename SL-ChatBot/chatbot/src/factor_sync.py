"""Backend Factor Sync - 백엔드 팩터 데이터 동기화"""
import os
import aiohttp
from typing import List, Dict, Optional
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
env_path = Path(__file__).parent.parent.parent.parent / ".env"
load_dotenv(env_path)


class FactorSync:
    """백엔드에서 팩터 데이터를 실시간으로 가져오는 클래스"""

    def __init__(self):
        self.backend_url = os.getenv("STOCK_LAB_API_URL", "http://backend:8000")
        self._factor_cache = None

    async def get_all_factors(self) -> List[Dict]:
        """백엔드에서 모든 팩터 정보 조회

        Returns:
            팩터 목록 [
                {
                    "id": "PER",
                    "name": "주가수익비율",
                    "category": "value",
                    "description": "..."
                },
                ...
            ]
        """
        if self._factor_cache:
            return self._factor_cache

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self.backend_url}/api/v1/factors/list",
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        self._factor_cache = data.get("factors", [])
                        return self._factor_cache
                    else:
                        print(f"Factor API error: {resp.status}")
                        return []
        except Exception as e:
            print(f"Failed to fetch factors from backend: {e}")
            return []

    async def get_factors_by_category(self, category: str) -> List[Dict]:
        """카테고리별 팩터 조회

        Args:
            category: value/growth/profitability/momentum/quality/risk/size/liquidity

        Returns:
            해당 카테고리의 팩터 목록
        """
        all_factors = await self.get_all_factors()
        return [f for f in all_factors if f.get("category") == category]

    async def get_factor_by_id(self, factor_id: str) -> Optional[Dict]:
        """팩터 ID로 팩터 조회

        Args:
            factor_id: PER, PBR, ROE 등

        Returns:
            팩터 정보 또는 None
        """
        all_factors = await self.get_all_factors()
        for factor in all_factors:
            if factor.get("id") == factor_id:
                return factor
        return None

    async def build_strategy_recommendation(self, strategy_type: str) -> Dict:
        """전략 타입에 맞는 팩터 추천

        Args:
            strategy_type: value/growth/quality/momentum/dividend/multi_factor

        Returns:
            {
                "strategy": "value",
                "description": "가치주 투자 전략",
                "primary_factors": ["PER", "PBR", "PSR"],
                "secondary_factors": ["ROE", "DIV_YIELD"],
                "sample_conditions": [...]
            }
        """
        # 전략별 카테고리 매핑
        strategy_category_map = {
            "value": ["value"],
            "growth": ["growth"],
            "quality": ["quality", "profitability"],
            "momentum": ["momentum"],
            "dividend": ["value"],  # 배당은 value 카테고리
            "multi_factor": ["value", "growth", "quality", "momentum"]
        }

        # 전략 설명
        strategy_descriptions = {
            "value": "저평가 주식 발굴 - 낮은 밸류에이션 지표 활용",
            "growth": "고성장 기업 선별 - 높은 성장률 지표 활용",
            "quality": "우량 기업 선별 - 높은 수익성과 안정성",
            "momentum": "모멘텀 추세 활용 - 가격 상승세가 강한 종목",
            "dividend": "안정적 배당 수익 - 높은 배당수익률",
            "multi_factor": "다중 팩터 조합 - 여러 전략의 장점 결합"
        }

        categories = strategy_category_map.get(strategy_type, ["value"])
        all_factors = await self.get_all_factors()

        # 카테고리별 팩터 필터링
        relevant_factors = [
            f for f in all_factors
            if f.get("category") in categories
        ]

        # Primary와 Secondary 구분
        primary_count = min(3, len(relevant_factors))
        primary_factors = [f["id"] for f in relevant_factors[:primary_count]]
        secondary_factors = [f["id"] for f in relevant_factors[primary_count:primary_count+3]]

        # 샘플 조건 생성
        sample_conditions = await self._generate_sample_conditions(
            strategy_type,
            primary_factors
        )

        return {
            "strategy": strategy_type,
            "description": strategy_descriptions.get(strategy_type, ""),
            "primary_factors": primary_factors,
            "secondary_factors": secondary_factors,
            "sample_conditions": sample_conditions,
            "all_available_factors": [f["id"] for f in relevant_factors]
        }

    async def _generate_sample_conditions(
        self,
        strategy_type: str,
        factors: List[str]
    ) -> List[Dict]:
        """전략별 샘플 조건 생성"""

        # 전략별 기본 샘플 조건
        samples = {
            "value": [
                {"factor": "PER", "operator": "<", "value": 15},
                {"factor": "PBR", "operator": "<", "value": 1.5},
                {"factor": "ROE", "operator": ">", "value": 10}
            ],
            "growth": [
                {"factor": "REVENUE_GROWTH", "operator": ">", "value": 20},
                {"factor": "EARNINGS_GROWTH", "operator": ">", "value": 15},
                {"factor": "ROE", "operator": ">", "value": 15}
            ],
            "quality": [
                {"factor": "ROE", "operator": ">", "value": 15},
                {"factor": "ROA", "operator": ">", "value": 10},
                {"factor": "DEBT_RATIO", "operator": "<", "value": 100}
            ],
            "momentum": [
                {"factor": "MOMENTUM_3M", "operator": ">", "value": 10},
                {"factor": "MOMENTUM_6M", "operator": ">", "value": 20}
            ],
            "dividend": [
                {"factor": "DIV_YIELD", "operator": ">", "value": 3},
                {"factor": "ROE", "operator": ">", "value": 10},
                {"factor": "DEBT_RATIO", "operator": "<", "value": 100}
            ],
            "multi_factor": [
                {"factor": "PER", "operator": "<", "value": 20},
                {"factor": "ROE", "operator": ">", "value": 12},
                {"factor": "REVENUE_GROWTH", "operator": ">", "value": 10}
            ]
        }

        return samples.get(strategy_type, [])

    def clear_cache(self):
        """캐시 초기화"""
        self._factor_cache = None
