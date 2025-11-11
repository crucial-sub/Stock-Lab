"""
팩터 관련 API 엔드포인트
- 54개 팩터 목록 조회
- 카테고리별 팩터 조회
- 팩터 상세 조회
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Optional
from app.core.database import get_db
from app.models.simulation import Factor, FactorCategory
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/factors", tags=["factors"])


@router.get("/list")
async def get_factors_list(
    category_id: Optional[str] = Query(None, description="카테고리 ID 필터"),
    is_active: bool = Query(True, description="활성화된 팩터만 조회"),
    db: AsyncSession = Depends(get_db)
):
    """
    팩터 목록 조회
    - 모든 활성화된 팩터를 카테고리와 함께 반환합니다
    - 프론트엔드의 팩터 선택 모달에서 사용됩니다
    """
    try:
        logger.info(f"팩터 목록 조회 시작: category_id={category_id}, is_active={is_active}")

        # 쿼리 구성
        query = (
            select(Factor, FactorCategory)
            .join(FactorCategory, Factor.category_id == FactorCategory.category_id)
            .order_by(FactorCategory.display_order, Factor.factor_id)
        )

        if is_active:
            query = query.where(Factor.is_active == True)

        if category_id:
            query = query.where(Factor.category_id == category_id)

        result = await db.execute(query)
        rows = result.all()

        logger.info(f"조회된 팩터 수: {len(rows)}개")

        # 응답 데이터 구성
        factors = []
        for factor, category in rows:
            factors.append({
                "id": factor.factor_id,
                "name": factor.factor_name,
                "display_name": factor.factor_name,
                "category": category.category_name,
                "category_id": category.category_id,
                "description": factor.description,
                "calculation_type": factor.calculation_type,
                "formula": factor.formula,
                "update_frequency": factor.update_frequency,
                "is_active": factor.is_active
            })

        return {
            "success": True,
            "factors": factors,
            "total_count": len(factors)
        }

    except Exception as e:
        logger.error(f"팩터 목록 조회 실패: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"팩터 목록 조회 중 오류 발생: {str(e)}")


@router.get("/categories")
async def get_factor_categories(
    db: AsyncSession = Depends(get_db)
):
    """
    팩터 카테고리 목록 조회
    - 모든 팩터 카테고리를 반환합니다
    """
    try:
        logger.info("팩터 카테고리 조회 시작")

        query = select(FactorCategory).order_by(FactorCategory.display_order)
        result = await db.execute(query)
        categories = result.scalars().all()

        logger.info(f"조회된 카테고리 수: {len(categories)}개")

        return {
            "success": True,
            "categories": [
                {
                    "id": cat.category_id,
                    "name": cat.category_name,
                    "description": cat.description,
                    "display_order": cat.display_order
                }
                for cat in categories
            ],
            "total_count": len(categories)
        }

    except Exception as e:
        logger.error(f"카테고리 조회 실패: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"카테고리 조회 중 오류 발생: {str(e)}")


@router.get("/{factor_id}")
async def get_factor_detail(
    factor_id: str,
    db: AsyncSession = Depends(get_db)
):
    """
    팩터 상세 정보 조회
    - 특정 팩터의 상세 정보를 반환합니다
    """
    try:
        logger.info(f"팩터 상세 조회: factor_id={factor_id}")

        query = (
            select(Factor, FactorCategory)
            .join(FactorCategory, Factor.category_id == FactorCategory.category_id)
            .where(Factor.factor_id == factor_id)
        )

        result = await db.execute(query)
        row = result.first()

        if not row:
            raise HTTPException(status_code=404, detail=f"팩터를 찾을 수 없습니다: {factor_id}")

        factor, category = row

        return {
            "success": True,
            "factor": {
                "id": factor.factor_id,
                "name": factor.factor_name,
                "display_name": factor.factor_name,
                "category": category.category_name,
                "category_id": category.category_id,
                "description": factor.description,
                "calculation_type": factor.calculation_type,
                "formula": factor.formula,
                "update_frequency": factor.update_frequency,
                "is_active": factor.is_active
            }
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"팩터 상세 조회 실패: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"팩터 상세 조회 중 오류 발생: {str(e)}")
