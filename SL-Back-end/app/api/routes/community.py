"""
커뮤니티 API 라우터
- 게시글, 댓글, 대댓글 작성
- 게시글에 백테스트 결과 공유
- 백테스트 
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, desc, func

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models.community import CommunityPost, CommunityComment, CommunityLike
from app.models.user import User
from app.models.simulation import PortfolioStrategy, SimulationSession

