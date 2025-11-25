"""
커뮤니티 API 라우터
- 게시글 CRUD
- 댓글/대댓글 CRUD
- 좋아요 토글
- 수익률 랭킹
- 전략 복제
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, desc, func, update, delete as sql_delete
from typing import Optional, List, Literal
from datetime import datetime
import logging
import json

from app.core.database import get_db
from app.core.dependencies import get_current_user, get_current_user_optional
from app.models.community import (
    CommunityPost, CommunityComment, CommunityLike, CommunityCommentLike
)
from app.models.user import User
from app.models.simulation import (
    PortfolioStrategy, SimulationSession, SimulationStatistics, TradingRule
)
from app.schemas.community import (
    PostCreate, PostUpdate, PostSummary, PostDetail, PostListResponse,
    CommentCreate, CommentUpdate, CommentItem, CommentListResponse,
    LikeResponse, RankingItem, TopRankingsResponse, RankingListResponse,
    CloneStrategyData
)

logger = logging.getLogger(__name__)

router = APIRouter()


# ============================================================
# 게시글 API
# ============================================================

@router.get("/posts", response_model=PostListResponse)
async def get_posts(
    post_type: Optional[str] = Query(None, description="게시글 유형 필터 (STRATEGY_SHARE/DISCUSSION/QUESTION)"),
    tags: Optional[str] = Query(None, description="태그 필터 (쉼표로 구분)"),
    search: Optional[str] = Query(None, description="제목+내용 검색"),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db)
):
    """게시글 목록 조회"""
    try:
        # 기본 쿼리
        query = select(CommunityPost, User).join(
            User, User.user_id == CommunityPost.user_id
        ).where(
            CommunityPost.is_public == True
        )

        # 필터 적용
        if post_type:
            query = query.where(CommunityPost.post_type == post_type)

        if tags:
            tag_list = [t.strip() for t in tags.split(',')]
            # JSON 배열에 포함 여부 확인 (PostgreSQL)
            for tag in tag_list:
                query = query.where(func.jsonb_contains(CommunityPost.tags, json.dumps([tag])))

        if search:
            search_pattern = f"%{search}%"
            query = query.where(
                or_(
                    CommunityPost.title.ilike(search_pattern),
                    CommunityPost.content.ilike(search_pattern)
                )
            )

        # 정렬 및 페이지네이션
        query = query.order_by(CommunityPost.created_at.desc())
        offset = (page - 1) * limit

        # 전체 개수 조회
        count_query = select(func.count()).select_from(CommunityPost).where(
            CommunityPost.is_public == True
        )
        if post_type:
            count_query = count_query.where(CommunityPost.post_type == post_type)

        total_result = await db.execute(count_query)
        total = total_result.scalar()

        # 데이터 조회
        query = query.offset(offset).limit(limit)
        result = await db.execute(query)
        rows = result.all()

        # 응답 생성
        posts = []
        for post, user in rows:
            # 내용 미리보기 (한 줄)
            content_preview = post.content.split('\n')[0][:100]
            if len(post.content) > 100:
                content_preview += "..."

            posts.append(PostSummary(
                post_id=post.post_id,
                title=post.title,
                content_preview=content_preview,
                author_nickname=user.nickname if not post.is_anonymous else None,
                author_id=str(post.user_id),
                is_anonymous=post.is_anonymous,
                tags=post.tags,
                post_type=post.post_type,
                view_count=post.view_count,
                like_count=post.like_count,
                comment_count=post.comment_count,
                created_at=post.created_at,
                updated_at=post.updated_at
            ))

        return PostListResponse(
            posts=posts,
            total=total,
            page=page,
            limit=limit,
            has_next=(offset + limit) < total
        )

    except Exception as e:
        logger.error(f"게시글 목록 조회 실패: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/posts/{post_id}", response_model=PostDetail)
async def get_post(
    post_id: str,
    current_user: Optional[User] = Depends(get_current_user_optional),
    db: AsyncSession = Depends(get_db)
):
    """게시글 상세 조회 (조회수 증가)"""
    try:
        # 게시글 조회
        query = select(CommunityPost, User).join(
            User, User.user_id == CommunityPost.user_id
        ).where(
            CommunityPost.post_id == post_id
        )

        result = await db.execute(query)
        row = result.one_or_none()

        if not row:
            raise HTTPException(status_code=404, detail="게시글을 찾을 수 없습니다")

        post, user = row

        # 조회수 증가
        await db.execute(
            update(CommunityPost)
            .where(CommunityPost.post_id == post_id)
            .values(view_count=CommunityPost.view_count + 1)
        )
        await db.commit()

        # 좋아요 여부 확인
        is_liked = False
        if current_user:
            like_query = select(CommunityLike).where(
                and_(
                    CommunityLike.post_id == post_id,
                    CommunityLike.user_id == current_user.user_id
                )
            )
            like_result = await db.execute(like_query)
            is_liked = like_result.scalar_one_or_none() is not None

        return PostDetail(
            post_id=post.post_id,
            title=post.title,
            content=post.content,
            author_nickname=user.nickname if not post.is_anonymous else None,
            author_id=str(post.user_id) if current_user and post.user_id == current_user.user_id else None,
            is_anonymous=post.is_anonymous,
            tags=post.tags,
            post_type=post.post_type,
            view_count=post.view_count + 1,  # 증가된 값
            like_count=post.like_count,
            comment_count=post.comment_count,
            is_liked=is_liked,
            created_at=post.created_at,
            updated_at=post.updated_at
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"게시글 상세 조회 실패: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/posts", response_model=PostDetail)
async def create_post(
    post_data: PostCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """게시글 작성"""
    try:
        # 게시글 생성
        new_post = CommunityPost(
            user_id=current_user.user_id,
            title=post_data.title,
            content=post_data.content,
            tags=post_data.tags,
            post_type=post_data.post_type,
            is_anonymous=post_data.is_anonymous
        )

        db.add(new_post)
        await db.commit()
        await db.refresh(new_post)

        # 사용자 정보 조회
        user_query = select(User).where(User.user_id == current_user.user_id)
        user_result = await db.execute(user_query)
        user = user_result.scalar_one()

        return PostDetail(
            post_id=new_post.post_id,
            title=new_post.title,
            content=new_post.content,
            author_nickname=user.nickname if not new_post.is_anonymous else None,
            author_id=str(new_post.user_id),
            is_anonymous=new_post.is_anonymous,
            tags=new_post.tags,
            post_type=new_post.post_type,
            view_count=0,
            like_count=0,
            comment_count=0,
            is_liked=False,
            created_at=new_post.created_at,
            updated_at=new_post.updated_at
        )

    except Exception as e:
        logger.error(f"게시글 작성 실패: {e}", exc_info=True)
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/posts/{post_id}", response_model=PostDetail)
async def update_post(
    post_id: str,
    post_data: PostUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """게시글 수정"""
    try:
        # 게시글 조회 및 권한 확인
        query = select(CommunityPost).where(CommunityPost.post_id == post_id)
        result = await db.execute(query)
        post = result.scalar_one_or_none()

        if not post:
            raise HTTPException(status_code=404, detail="게시글을 찾을 수 없습니다")

        if post.user_id != current_user.user_id:
            raise HTTPException(status_code=403, detail="수정 권한이 없습니다")

        # 수정
        update_data = post_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(post, field, value)

        post.updated_at = datetime.now()

        await db.commit()
        await db.refresh(post)

        # 사용자 정보 조회
        user_query = select(User).where(User.user_id == current_user.user_id)
        user_result = await db.execute(user_query)
        user = user_result.scalar_one()

        return PostDetail(
            post_id=post.post_id,
            title=post.title,
            content=post.content,
            author_nickname=user.nickname if not post.is_anonymous else None,
            author_id=str(post.user_id),
            is_anonymous=post.is_anonymous,
            tags=post.tags,
            post_type=post.post_type,
            view_count=post.view_count,
            like_count=post.like_count,
            comment_count=post.comment_count,
            is_liked=False,
            created_at=post.created_at,
            updated_at=post.updated_at
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"게시글 수정 실패: {e}", exc_info=True)
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/posts/{post_id}")
async def delete_post(
    post_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """게시글 삭제"""
    try:
        # 게시글 조회 및 권한 확인
        query = select(CommunityPost).where(CommunityPost.post_id == post_id)
        result = await db.execute(query)
        post = result.scalar_one_or_none()

        if not post:
            raise HTTPException(status_code=404, detail="게시글을 찾을 수 없습니다")

        if post.user_id != current_user.user_id:
            raise HTTPException(status_code=403, detail="삭제 권한이 없습니다")

        # 삭제
        await db.delete(post)
        await db.commit()

        return {"message": "게시글이 삭제되었습니다"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"게시글 삭제 실패: {e}", exc_info=True)
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================
# 댓글 API
# ============================================================

@router.get("/posts/{post_id}/comments", response_model=CommentListResponse)
async def get_comments(
    post_id: str,
    current_user: Optional[User] = Depends(get_current_user_optional),
    db: AsyncSession = Depends(get_db)
):
    """댓글 목록 조회 (대댓글 포함)"""
    try:
        # 댓글 조회 (최상위 댓글만)
        query = select(CommunityComment, User).join(
            User, User.user_id == CommunityComment.user_id
        ).where(
            and_(
                CommunityComment.post_id == post_id,
                CommunityComment.parent_comment_id.is_(None)
            )
        ).order_by(CommunityComment.created_at)

        result = await db.execute(query)
        rows = result.all()

        # 댓글 변환 (재귀적으로 대댓글 로드)
        comments = []
        for comment, user in rows:
            comment_item = await _build_comment_tree(comment, user, current_user, db)
            comments.append(comment_item)

        return CommentListResponse(
            comments=comments,
            total=len(comments)
        )

    except Exception as e:
        logger.error(f"댓글 목록 조회 실패: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


async def _build_comment_tree(
    comment: CommunityComment,
    user: User,
    current_user: Optional[User],
    db: AsyncSession
) -> CommentItem:
    """댓글 트리 구조 생성 (재귀)"""
    # 좋아요 여부 확인
    is_liked = False
    if current_user:
        like_query = select(CommunityCommentLike).where(
            and_(
                CommunityCommentLike.comment_id == comment.comment_id,
                CommunityCommentLike.user_id == current_user.user_id
            )
        )
        like_result = await db.execute(like_query)
        is_liked = like_result.scalar_one_or_none() is not None

    # 대댓글 조회
    reply_query = select(CommunityComment, User).join(
        User, User.user_id == CommunityComment.user_id
    ).where(
        CommunityComment.parent_comment_id == comment.comment_id
    ).order_by(CommunityComment.created_at)

    reply_result = await db.execute(reply_query)
    reply_rows = reply_result.all()

    # 대댓글 재귀 처리
    replies = []
    for reply_comment, reply_user in reply_rows:
        reply_item = await _build_comment_tree(reply_comment, reply_user, current_user, db)
        replies.append(reply_item)

    return CommentItem(
        comment_id=comment.comment_id,
        post_id=comment.post_id,
        content=comment.content,
        author_nickname=user.nickname if not comment.is_anonymous else None,
        author_id=str(comment.user_id) if current_user and comment.user_id == current_user.user_id else None,
        is_anonymous=comment.is_anonymous,
        parent_comment_id=comment.parent_comment_id,
        like_count=comment.like_count,
        is_liked=is_liked,
        created_at=comment.created_at,
        updated_at=comment.updated_at,
        replies=replies
    )


@router.post("/posts/{post_id}/comments", response_model=CommentItem)
async def create_comment(
    post_id: str,
    comment_data: CommentCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """댓글 작성"""
    try:
        # 게시글 존재 확인
        post_query = select(CommunityPost).where(CommunityPost.post_id == post_id)
        post_result = await db.execute(post_query)
        post = post_result.scalar_one_or_none()

        if not post:
            raise HTTPException(status_code=404, detail="게시글을 찾을 수 없습니다")

        # 댓글 생성
        new_comment = CommunityComment(
            post_id=post_id,
            user_id=current_user.user_id,
            content=comment_data.content,
            parent_comment_id=comment_data.parent_comment_id,
            is_anonymous=comment_data.is_anonymous
        )

        db.add(new_comment)

        # 게시글 댓글 수 증가
        await db.execute(
            update(CommunityPost)
            .where(CommunityPost.post_id == post_id)
            .values(comment_count=CommunityPost.comment_count + 1)
        )

        await db.commit()
        await db.refresh(new_comment)

        # 사용자 정보 조회
        user_query = select(User).where(User.user_id == current_user.user_id)
        user_result = await db.execute(user_query)
        user = user_result.scalar_one()

        return CommentItem(
            comment_id=new_comment.comment_id,
            post_id=new_comment.post_id,
            content=new_comment.content,
            author_nickname=user.nickname if not new_comment.is_anonymous else None,
            author_id=str(new_comment.user_id),
            is_anonymous=new_comment.is_anonymous,
            parent_comment_id=new_comment.parent_comment_id,
            like_count=0,
            is_liked=False,
            created_at=new_comment.created_at,
            updated_at=new_comment.updated_at,
            replies=[]
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"댓글 작성 실패: {e}", exc_info=True)
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/comments/{comment_id}", response_model=CommentItem)
async def update_comment(
    comment_id: str,
    comment_data: CommentUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """댓글 수정"""
    try:
        # 댓글 조회 및 권한 확인
        query = select(CommunityComment).where(CommunityComment.comment_id == comment_id)
        result = await db.execute(query)
        comment = result.scalar_one_or_none()

        if not comment:
            raise HTTPException(status_code=404, detail="댓글을 찾을 수 없습니다")

        if comment.user_id != current_user.user_id:
            raise HTTPException(status_code=403, detail="수정 권한이 없습니다")

        # 수정
        comment.content = comment_data.content
        comment.updated_at = datetime.now()

        await db.commit()
        await db.refresh(comment)

        # 사용자 정보 조회
        user_query = select(User).where(User.user_id == current_user.user_id)
        user_result = await db.execute(user_query)
        user = user_result.scalar_one()

        return CommentItem(
            comment_id=comment.comment_id,
            post_id=comment.post_id,
            content=comment.content,
            author_nickname=user.nickname if not comment.is_anonymous else None,
            author_id=str(comment.user_id),
            is_anonymous=comment.is_anonymous,
            parent_comment_id=comment.parent_comment_id,
            like_count=comment.like_count,
            is_liked=False,
            created_at=comment.created_at,
            updated_at=comment.updated_at,
            replies=[]
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"댓글 수정 실패: {e}", exc_info=True)
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/comments/{comment_id}")
async def delete_comment(
    comment_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """댓글 삭제"""
    try:
        # 댓글 조회 및 권한 확인
        query = select(CommunityComment).where(CommunityComment.comment_id == comment_id)
        result = await db.execute(query)
        comment = result.scalar_one_or_none()

        if not comment:
            raise HTTPException(status_code=404, detail="댓글을 찾을 수 없습니다")

        if comment.user_id != current_user.user_id:
            raise HTTPException(status_code=403, detail="삭제 권한이 없습니다")

        post_id = comment.post_id

        # 삭제 (대댓글은 CASCADE로 자동 삭제됨)
        await db.delete(comment)

        # 게시글 댓글 수 감소
        await db.execute(
            update(CommunityPost)
            .where(CommunityPost.post_id == post_id)
            .values(comment_count=CommunityPost.comment_count - 1)
        )

        await db.commit()

        return {"message": "댓글이 삭제되었습니다"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"댓글 삭제 실패: {e}", exc_info=True)
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================
# 좋아요 API
# ============================================================

@router.post("/posts/{post_id}/like", response_model=LikeResponse)
async def toggle_post_like(
    post_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """게시글 좋아요 토글"""
    try:
        # 기존 좋아요 확인
        like_query = select(CommunityLike).where(
            and_(
                CommunityLike.post_id == post_id,
                CommunityLike.user_id == current_user.user_id
            )
        )
        like_result = await db.execute(like_query)
        existing_like = like_result.scalar_one_or_none()

        if existing_like:
            # 좋아요 취소
            await db.delete(existing_like)
            await db.execute(
                update(CommunityPost)
                .where(CommunityPost.post_id == post_id)
                .values(like_count=CommunityPost.like_count - 1)
            )
            is_liked = False
        else:
            # 좋아요 추가
            new_like = CommunityLike(
                post_id=post_id,
                user_id=current_user.user_id
            )
            db.add(new_like)
            await db.execute(
                update(CommunityPost)
                .where(CommunityPost.post_id == post_id)
                .values(like_count=CommunityPost.like_count + 1)
            )
            is_liked = True

        await db.commit()

        # 최신 like_count 조회
        post_query = select(CommunityPost.like_count).where(CommunityPost.post_id == post_id)
        post_result = await db.execute(post_query)
        like_count = post_result.scalar()

        return LikeResponse(
            is_liked=is_liked,
            like_count=like_count
        )

    except Exception as e:
        logger.error(f"게시글 좋아요 토글 실패: {e}", exc_info=True)
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/comments/{comment_id}/like", response_model=LikeResponse)
async def toggle_comment_like(
    comment_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """댓글 좋아요 토글"""
    try:
        # 기존 좋아요 확인
        like_query = select(CommunityCommentLike).where(
            and_(
                CommunityCommentLike.comment_id == comment_id,
                CommunityCommentLike.user_id == current_user.user_id
            )
        )
        like_result = await db.execute(like_query)
        existing_like = like_result.scalar_one_or_none()

        if existing_like:
            # 좋아요 취소
            await db.delete(existing_like)
            await db.execute(
                update(CommunityComment)
                .where(CommunityComment.comment_id == comment_id)
                .values(like_count=CommunityComment.like_count - 1)
            )
            is_liked = False
        else:
            # 좋아요 추가
            new_like = CommunityCommentLike(
                comment_id=comment_id,
                user_id=current_user.user_id
            )
            db.add(new_like)
            await db.execute(
                update(CommunityComment)
                .where(CommunityComment.comment_id == comment_id)
                .values(like_count=CommunityComment.like_count + 1)
            )
            is_liked = True

        await db.commit()

        # 최신 like_count 조회
        comment_query = select(CommunityComment.like_count).where(CommunityComment.comment_id == comment_id)
        comment_result = await db.execute(comment_query)
        like_count = comment_result.scalar()

        return LikeResponse(
            is_liked=is_liked,
            like_count=like_count
        )

    except Exception as e:
        logger.error(f"댓글 좋아요 토글 실패: {e}", exc_info=True)
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================
# 수익률 랭킹 API
# ============================================================

@router.get("/rankings/top", response_model=TopRankingsResponse)
async def get_top_rankings(
    db: AsyncSession = Depends(get_db)
):
    """상위 3개 수익률 랭킹 조회 (Redis Sorted Set 사용, Redis 없으면 DB 폴백)"""
    try:
        from app.services.ranking_service import get_ranking_service

        # 🚀 Redis Sorted Set에서 TOP 3 조회 (O(1))
        ranking_service = await get_ranking_service()

        if ranking_service.enabled:
            # Redis에서 세션 ID 가져오기
            top_session_ids = await ranking_service.get_top_rankings(limit=3)

            if top_session_ids:
                # DB에서 상세 정보만 조회 (필요한 것만 SELECT)
                rankings = await _get_rankings_by_session_ids(db, top_session_ids)

                response = TopRankingsResponse(
                    rankings=rankings,
                    updated_at=datetime.now()
                )

                logger.info(f"✅ Redis Sorted Set에서 TOP 3 조회 완료")
                return response
            else:
                logger.warning("Redis Sorted Set이 비어있음, DB로 폴백")
        else:
            logger.info("Redis 비활성화 상태, DB에서 직접 조회")

        # ⚠️ Fallback: Redis 비활성화 또는 데이터 없을 때 DB 직접 조회
        rankings = await _get_rankings_from_db(db, limit=3)

        response = TopRankingsResponse(
            rankings=rankings,
            updated_at=datetime.now()
        )

        return response

    except Exception as e:
        logger.error(f"랭킹 조회 실패: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/rankings", response_model=RankingListResponse)
async def get_rankings(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db)
):
    """전체 랭킹 목록 조회"""
    try:
        # 전체 개수 조회
        count_query = (
            select(func.count())
            .select_from(PortfolioStrategy)
            .join(SimulationSession, SimulationSession.strategy_id == PortfolioStrategy.strategy_id)
            .join(SimulationStatistics, SimulationStatistics.session_id == SimulationSession.session_id)
            .where(
                and_(
                    PortfolioStrategy.is_public == True,
                    SimulationSession.status == "COMPLETED"
                )
            )
        )
        count_result = await db.execute(count_query)
        total = count_result.scalar()

        # 데이터 조회
        offset = (page - 1) * limit
        rankings = await _get_rankings_from_db(db, offset=offset, limit=limit)

        return RankingListResponse(
            rankings=rankings,
            total=total,
            page=page,
            limit=limit
        )

    except Exception as e:
        logger.error(f"랭킹 목록 조회 실패: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


async def _get_rankings_by_session_ids(
    db: AsyncSession,
    session_ids: List[str]
) -> List[RankingItem]:
    """
    세션 ID 리스트로 랭킹 데이터 조회 (Redis Sorted Set용)

    Args:
        db: DB 세션
        session_ids: 세션 ID 리스트 (이미 정렬됨)

    Returns:
        RankingItem 리스트
    """
    from sqlalchemy import cast
    from sqlalchemy.dialects.postgresql import UUID as PostgreSQL_UUID

    if not session_ids:
        return []

    # session_id IN (...) 쿼리 (순서 유지를 위해 CASE 사용)
    query = (
        select(
            PortfolioStrategy,
            SimulationSession,
            SimulationStatistics,
            User
        )
        .join(SimulationSession, SimulationSession.strategy_id == PortfolioStrategy.strategy_id)
        .join(SimulationStatistics, SimulationStatistics.session_id == SimulationSession.session_id)
        .outerjoin(User, User.user_id == cast(PortfolioStrategy.user_id, PostgreSQL_UUID))
        .where(SimulationSession.session_id.in_(session_ids))
    )

    result = await db.execute(query)
    rows = result.all()

    # session_id -> 데이터 매핑
    session_map = {}
    for strategy, session, stats, user in rows:
        session_map[session.session_id] = (strategy, session, stats, user)

    # Redis에서 받은 순서대로 정렬
    rankings = []
    for rank, session_id in enumerate(session_ids, start=1):
        if session_id in session_map:
            strategy, session, stats, user = session_map[session_id]
            rankings.append(RankingItem(
                rank=rank,
                strategy_id=strategy.strategy_id,
                session_id=session.session_id,
                strategy_name=strategy.strategy_name,
                author_nickname=user.nickname if user and not strategy.is_anonymous else None,
                total_return=stats.total_return,
                annualized_return=stats.annualized_return,
                max_drawdown=stats.max_drawdown,
                sharpe_ratio=stats.sharpe_ratio
            ))

    return rankings


async def _get_rankings_from_db(
    db: AsyncSession,
    offset: int = 0,
    limit: int = 3
) -> List[RankingItem]:
    """DB에서 랭킹 데이터 조회 (Fallback용)"""
    from sqlalchemy import cast
    from sqlalchemy.dialects.postgresql import UUID as PostgreSQL_UUID

    query = (
        select(
            PortfolioStrategy,
            SimulationSession,
            SimulationStatistics,
            User
        )
        .join(SimulationSession, SimulationSession.strategy_id == PortfolioStrategy.strategy_id)
        .join(SimulationStatistics, SimulationStatistics.session_id == SimulationSession.session_id)
        .outerjoin(User, User.user_id == cast(PortfolioStrategy.user_id, PostgreSQL_UUID))
        .where(
            and_(
                PortfolioStrategy.is_public == True,
                SimulationSession.status == "COMPLETED"
            )
        )
        .order_by(SimulationStatistics.total_return.desc())
        .offset(offset)
        .limit(limit)
    )

    result = await db.execute(query)
    rows = result.all()

    rankings = []
    for rank, (strategy, session, stats, user) in enumerate(rows, start=offset + 1):
        rankings.append(RankingItem(
            rank=rank,
            strategy_id=strategy.strategy_id,
            session_id=session.session_id,
            strategy_name=strategy.strategy_name,
            author_nickname=user.nickname if user and not strategy.is_anonymous else None,
            total_return=stats.total_return,
            annualized_return=stats.annualized_return,
            max_drawdown=stats.max_drawdown,
            sharpe_ratio=stats.sharpe_ratio
        ))

    return rankings


# ============================================================
# 랭킹 관리 API (관리자용)
# ============================================================

@router.post("/rankings/rebuild")
async def rebuild_rankings(
    limit: int = Query(100, ge=1, le=500, description="재구축할 개수"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Redis 랭킹 재구축 (관리자 전용)
    - 기존 백테스트 데이터를 Redis에 로드
    - DB에서 TOP N개를 조회하여 Redis Sorted Set에 추가
    """
    try:
        from app.services.ranking_service import get_ranking_service

        # 관리자 권한 체크 (선택사항)
        if not current_user.is_superuser:
            raise HTTPException(status_code=403, detail="관리자 권한이 필요합니다")

        logger.info(f"🔄 랭킹 재구축 시작 (요청: {current_user.email}, limit={limit})")

        ranking_service = await get_ranking_service()

        if not ranking_service.enabled:
            raise HTTPException(
                status_code=503,
                detail="Redis가 비활성화되어 있습니다"
            )

        # 기존 랭킹 삭제
        from app.core.cache import get_redis
        redis_client = get_redis()
        old_count = await redis_client.zcard("rankings:all")
        await redis_client.delete("rankings:all")
        logger.info(f"🗑️ 기존 랭킹 삭제: {old_count}개")

        # DB에서 재구축
        rebuilt_count = await ranking_service.rebuild_from_db(db, limit=limit)

        logger.info(f"✅ 랭킹 재구축 완료: {rebuilt_count}개 항목")

        return {
            "message": "랭킹 재구축 완료",
            "old_count": old_count,
            "new_count": rebuilt_count,
            "limit": limit
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"랭킹 재구축 실패: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================
# 전략 복제 API
# ============================================================

@router.get("/strategies/{strategy_id}/clone-data", response_model=CloneStrategyData)
async def get_clone_data(
    strategy_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """전략 복제 데이터 조회 (백테스트 창으로 전달)"""
    try:
        # 전략 조회
        query = (
            select(PortfolioStrategy, TradingRule, SimulationSession)
            .join(TradingRule, TradingRule.strategy_id == PortfolioStrategy.strategy_id)
            .join(SimulationSession, SimulationSession.strategy_id == PortfolioStrategy.strategy_id)
            .where(
                and_(
                    PortfolioStrategy.strategy_id == strategy_id,
                    PortfolioStrategy.is_public == True
                )
            )
            .order_by(SimulationSession.created_at.desc())
            .limit(1)
        )

        result = await db.execute(query)
        row = result.one_or_none()

        if not row:
            raise HTTPException(status_code=404, detail="전략을 찾을 수 없습니다")

        strategy, trading_rule, session = row

        # buy_condition과 sell_condition 파싱
        buy_condition = trading_rule.buy_condition or {}
        sell_condition = trading_rule.sell_condition or {}

        return CloneStrategyData(
            strategy_name=f"{strategy.strategy_name} (복제)",
            is_day_or_month="daily",  # 기본값
            initial_investment=int(session.initial_capital / 10000),  # 원 -> 만원
            start_date=session.start_date.strftime("%Y%m%d"),
            end_date=session.end_date.strftime("%Y%m%d"),
            commission_rate=float(trading_rule.commission_rate * 100) if trading_rule.commission_rate else 0.015,
            slippage=0.1,  # 기본값
            buy_conditions=buy_condition.get('conditions', []),
            buy_logic=buy_condition.get('logic', 'AND'),
            priority_factor=buy_condition.get('priority_factor'),
            priority_order=buy_condition.get('priority_order', 'desc'),
            per_stock_ratio=buy_condition.get('per_stock_ratio', 5.0),
            max_holdings=trading_rule.max_positions or 20,
            max_buy_value=buy_condition.get('max_buy_value'),
            max_daily_stock=buy_condition.get('max_daily_stock'),
            buy_price_basis=buy_condition.get('buy_price_basis', 'CLOSE'),
            buy_price_offset=buy_condition.get('buy_price_offset', 0.0),
            target_and_loss=sell_condition.get('target_and_loss'),
            hold_days=sell_condition.get('hold_days'),
            condition_sell=sell_condition.get('condition_sell'),
            trade_targets=buy_condition.get('trade_targets', {
                "use_all_stocks": True,
                "selected_themes": [],
                "selected_stocks": []
            })
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"전략 복제 데이터 조회 실패: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/clone-strategy/{session_id}")
async def clone_strategy_by_session(
    session_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    세션 ID로 공개 전략 복제 (내 포트폴리오에 추가)
    - 공개된 전략의 세션 ID를 받아 복제
    - 전략 설정, 매수/매도 조건, 백테스트 기간 등 모든 설정 복사
    """
    try:
        # 세션, 전략, 트레이딩 룰 조회
        query = (
            select(SimulationSession, PortfolioStrategy, TradingRule)
            .join(
                PortfolioStrategy,
                PortfolioStrategy.strategy_id == SimulationSession.strategy_id
            )
            .join(
                TradingRule,
                TradingRule.strategy_id == PortfolioStrategy.strategy_id
            )
            .where(
                and_(
                    SimulationSession.session_id == session_id,
                    or_(
                        PortfolioStrategy.is_public == True,
                        PortfolioStrategy.user_id == current_user.user_id
                    )  # 공개된 전략또는 내 전략일때
                )
            )
        )

        result = await db.execute(query)
        row = result.one_or_none()

        if not row:
            raise HTTPException(
                status_code=404,
                detail="공개된 전략 세션을 찾을 수 없습니다"
            )

        session, strategy, trading_rule = row

        # 새로운 전략 생성
        new_strategy = PortfolioStrategy(
            strategy_name=f"{strategy.strategy_name} (복제)",
            strategy_type=strategy.strategy_type,
            description=f"복제된 전략 (원본: {strategy.strategy_name})",
            user_id=current_user.user_id,
            is_public=False,
            is_anonymous=False,
            hide_strategy_details=False
        )
        db.add(new_strategy)
        await db.flush()

        # TradingRule 복사
        new_trading_rule = TradingRule(
            strategy_id=new_strategy.strategy_id,
            rule_type=trading_rule.rule_type,
            rebalance_frequency=trading_rule.rebalance_frequency,
            max_positions=trading_rule.max_positions,
            position_sizing=trading_rule.position_sizing,
            commission_rate=trading_rule.commission_rate,
            buy_condition=trading_rule.buy_condition,
            sell_condition=trading_rule.sell_condition
        )
        db.add(new_trading_rule)

        # SimulationSession 복사 (내 전략 목록에 표시되려면 필요)
        new_session = SimulationSession(
            user_id=current_user.user_id,
            strategy_id=new_strategy.strategy_id,
            source_session_id=session_id,  # 원본 세션 ID 추적
            initial_capital=session.initial_capital,
            start_date=session.start_date,
            end_date=session.end_date,
            status="PENDING",  # 복제된 전략은 아직 실행 안함
            is_active=False,
            is_portfolio=True  # 포트폴리오 목록에 표시되도록 설정
        )
        db.add(new_session)
        await db.flush()  # session_id 생성을 위해 flush

        # 원본 세션의 통계 데이터 복사 (수익률 표시용)
        stats_query = select(SimulationStatistics).where(
            SimulationStatistics.session_id == session_id
        )
        stats_result = await db.execute(stats_query)
        original_stats = stats_result.scalar_one_or_none()

        if original_stats:
            new_stats = SimulationStatistics(
                session_id=new_session.session_id,
                total_return=original_stats.total_return,
                annualized_return=original_stats.annualized_return,
                max_drawdown=original_stats.max_drawdown,
                sharpe_ratio=original_stats.sharpe_ratio,
                win_rate=original_stats.win_rate,
                total_trades=original_stats.total_trades,
                winning_trades=original_stats.winning_trades,
                losing_trades=original_stats.losing_trades,
                avg_loss=original_stats.avg_loss,
                profit_factor=original_stats.profit_factor,
                final_capital=original_stats.final_capital
            )
            db.add(new_stats)
            logger.info(f"📊 통계 데이터 복사 완료: total_return={original_stats.total_return}%")

        await db.commit()
        await db.refresh(new_strategy)
        await db.refresh(new_session)

        logger.info(
            f"✅ 전략 복제 완료: {session_id} -> {new_strategy.strategy_id} "
            f"(사용자: {current_user.email})"
        )

        return {
            "message": "전략이 성공적으로 복제되었습니다",
            "strategy_id": new_strategy.strategy_id,
            "strategy_name": new_strategy.strategy_name
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"전략 복제 실패: {e}", exc_info=True)
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e))




