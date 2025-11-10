# 🎯 테마/섹터 기반 종목 선택 시스템 구축 가이드

## 📊 현재 상황
- `companies` 테이블에 `industry` 컬럼 존재 ✅
- 하지만 테마 정보는 없음 ❌

## 🏗️ 해결 방안

### 방법 1: industry 컬럼 활용 (간단, 추천)

#### 장점:
- ✅ 테이블 수정 불필요
- ✅ 빠른 구현 (1-2시간)
- ✅ 표준 업종 분류 활용

#### 단점:
- 테마가 고정적 (유행 테마 반영 어려움)

### 방법 2: 테마 테이블 추가 (유연, 확장성)

#### 장점:
- ✅ 유연한 테마 관리
- ✅ 동적 테마 추가
- ✅ 다중 테마 지원 (한 종목이 여러 테마에 속함)

#### 단점:
- DB 스키마 변경 필요
- 테마 데이터 수동 관리

## ✅ 추천: 두 방법 모두 구현!

### Phase 1: industry 활용 (즉시 사용 가능)
```python
# 표준 업종으로 필터링
sectors = [
    "반도체",
    "IT 서비스",
    "금융",
    "자동차",
    "화학",
    "건설",
    ...
]
```

### Phase 2: 테마 테이블 추가 (고급 기능)
```python
# 동적 테마
themes = [
    "2차전지",
    "K-방산",
    "AI/로봇",
    "메타버스",
    ...
]
```

---

## 📋 Phase 1: industry 활용 (즉시 구현)

### 1. 업종 매핑 정의

```python
# app/core/sector_mapping.py
"""
한국 표준 산업 분류 (KSIC) 기반 섹터 매핑
"""

SECTOR_MAPPING = {
    # 대분류 -> 중분류 매핑
    "IT/기술": [
        "반도체",
        "디스플레이",
        "IT부품",
        "IT H/W",
        "소프트웨어",
        "게임",
        "인터넷",
        "통신서비스",
        "컴퓨터서비스"
    ],
    "금융": [
        "은행",
        "증권",
        "보험",
        "기타금융"
    ],
    "제조": [
        "자동차",
        "조선",
        "철강",
        "화학",
        "기계",
        "전기전자",
        "섬유의류"
    ],
    "소비재": [
        "식품",
        "음료",
        "화장품",
        "제약",
        "의료기기",
        "유통"
    ],
    "에너지/소재": [
        "전기가스",
        "에너지",
        "건설",
        "건자재",
        "비금속"
    ],
    "미디어/엔터": [
        "방송서비스",
        "출판",
        "광고",
        "엔터테인먼트"
    ],
    "운송/서비스": [
        "운송",
        "창고",
        "숙박음식",
        "서비스업"
    ]
}

# 역방향 매핑 (빠른 검색)
INDUSTRY_TO_SECTOR = {}
for sector, industries in SECTOR_MAPPING.items():
    for industry in industries:
        INDUSTRY_TO_SECTOR[industry] = sector


# 업종별 대표 키워드 (검색용)
INDUSTRY_KEYWORDS = {
    "반도체": ["반도체", "반도체장비", "메모리", "시스템반도체", "파운드리"],
    "IT 서비스": ["소프트웨어", "IT서비스", "컴퓨터서비스", "정보통신"],
    "금융": ["은행", "증권", "보험", "금융", "캐피탈"],
    "자동차": ["자동차", "자동차부품", "타이어"],
    "화학": ["화학", "정유화학", "석유화학", "고무"],
    "건설": ["건설", "건자재", "시멘트"],
    "제약": ["제약", "바이오", "의약품"],
    "식품": ["음식료", "식품", "음료"],
    "게임": ["게임", "온라인게임", "모바일게임"],
}
```

### 2. API 엔드포인트 추가

```python
# app/api/v1/sectors.py
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import List, Dict
from app.core.database import get_db
from app.models.company import Company
from app.core.sector_mapping import SECTOR_MAPPING, INDUSTRY_TO_SECTOR

router = APIRouter()


@router.get("/sectors")
async def get_sectors():
    """
    전체 섹터 목록 조회
    """
    sectors = [
        {
            "sector_name": sector,
            "industries": industries,
            "count": len(industries)
        }
        for sector, industries in SECTOR_MAPPING.items()
    ]

    return {
        "sectors": sectors,
        "total_sectors": len(SECTOR_MAPPING)
    }


@router.get("/sectors/{sector_name}/stocks")
async def get_stocks_by_sector(
    sector_name: str,
    db: AsyncSession = Depends(get_db)
):
    """
    특정 섹터의 종목 조회
    """
    # 해당 섹터의 업종 리스트
    industries = SECTOR_MAPPING.get(sector_name)

    if not industries:
        return {"error": "Sector not found"}

    # DB 쿼리
    result = await db.execute(
        select(Company)
        .where(Company.industry.in_(industries))
        .where(Company.is_active == 1)
        .where(Company.stock_code.isnot(None))
    )

    companies = result.scalars().all()

    return {
        "sector": sector_name,
        "industries": industries,
        "stocks": [
            {
                "stock_code": c.stock_code,
                "stock_name": c.stock_name,
                "industry": c.industry,
                "market_type": c.market_type
            }
            for c in companies
        ],
        "total": len(companies)
    }


@router.get("/industries/{industry_name}/stocks")
async def get_stocks_by_industry(
    industry_name: str,
    db: AsyncSession = Depends(get_db)
):
    """
    특정 업종의 종목 조회
    """
    result = await db.execute(
        select(Company)
        .where(Company.industry == industry_name)
        .where(Company.is_active == 1)
        .where(Company.stock_code.isnot(None))
    )

    companies = result.scalars().all()

    return {
        "industry": industry_name,
        "stocks": [
            {
                "stock_code": c.stock_code,
                "stock_name": c.stock_name,
                "market_type": c.market_type
            }
            for c in companies
        ],
        "total": len(companies)
    }


@router.get("/industries")
async def get_all_industries(db: AsyncSession = Depends(get_db)):
    """
    DB에 존재하는 모든 업종 조회 (실제 데이터 기반)
    """
    result = await db.execute(
        select(
            Company.industry,
            func.count(Company.company_id).label('count')
        )
        .where(Company.is_active == 1)
        .where(Company.stock_code.isnot(None))
        .where(Company.industry.isnot(None))
        .group_by(Company.industry)
        .order_by(func.count(Company.company_id).desc())
    )

    industries = result.all()

    return {
        "industries": [
            {
                "name": industry,
                "count": count,
                "sector": INDUSTRY_TO_SECTOR.get(industry, "기타")
            }
            for industry, count in industries
        ],
        "total": len(industries)
    }


@router.get("/search")
async def search_stocks(
    keyword: str,
    db: AsyncSession = Depends(get_db)
):
    """
    종목명 또는 코드로 검색
    """
    result = await db.execute(
        select(Company)
        .where(
            (Company.stock_name.like(f"%{keyword}%")) |
            (Company.stock_code.like(f"%{keyword}%")) |
            (Company.company_name.like(f"%{keyword}%"))
        )
        .where(Company.is_active == 1)
        .where(Company.stock_code.isnot(None))
        .limit(50)
    )

    companies = result.scalars().all()

    return {
        "keyword": keyword,
        "stocks": [
            {
                "stock_code": c.stock_code,
                "stock_name": c.stock_name,
                "industry": c.industry,
                "market_type": c.market_type
            }
            for c in companies
        ],
        "total": len(companies)
    }
```

### 3. 라우터 등록

```python
# app/api/v1/__init__.py
from fastapi import APIRouter
from app.api.v1 import backtest, sectors  # 추가

api_router = APIRouter()

api_router.include_router(backtest.router, prefix="/backtest", tags=["backtest"])
api_router.include_router(sectors.router, prefix="/sectors", tags=["sectors"])  # 추가
```

---

## 📋 Phase 2: 테마 테이블 추가 (고급 기능)

### 1. 테마 모델 생성

```python
# app/models/theme.py
from sqlalchemy import Column, Integer, String, Text, Boolean, TIMESTAMP, ForeignKey, Index, Table
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base


# 다대다 관계 테이블 (종목 ↔ 테마)
stock_theme_association = Table(
    'stock_themes',
    Base.metadata,
    Column('company_id', Integer, ForeignKey('companies.company_id', ondelete='CASCADE'), primary_key=True),
    Column('theme_id', Integer, ForeignKey('themes.theme_id', ondelete='CASCADE'), primary_key=True),
    Column('created_at', TIMESTAMP, server_default=func.now()),
    Index('idx_stock_themes_company', 'company_id'),
    Index('idx_stock_themes_theme', 'theme_id'),
)


class Theme(Base):
    """
    테마/섹터 테이블
    - 업종보다 유연한 그룹핑
    - 시의성 있는 테마 관리
    """
    __tablename__ = "themes"

    # Primary Key
    theme_id = Column(Integer, primary_key=True, autoincrement=True, comment="테마 고유 ID")

    # 테마 정보
    theme_name = Column(String(100), unique=True, nullable=False, index=True, comment="테마명")
    theme_name_eng = Column(String(100), nullable=True, comment="영문 테마명")
    category = Column(String(50), nullable=True, comment="카테고리 (산업/이슈/지역 등)")
    description = Column(Text, nullable=True, comment="테마 설명")

    # 메타 정보
    is_active = Column(Boolean, default=True, comment="활성 상태")
    popularity_score = Column(Integer, default=0, comment="인기도 (검색/사용 횟수)")
    stock_count = Column(Integer, default=0, comment="포함 종목 수")

    # Timestamp
    created_at = Column(TIMESTAMP, server_default=func.now(), nullable=False)
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())

    # Relationships
    companies = relationship(
        "Company",
        secondary=stock_theme_association,
        back_populates="themes"
    )

    __table_args__ = (
        Index('idx_themes_category', 'category'),
        Index('idx_themes_active', 'is_active'),
        {"comment": "테마/섹터 테이블"}
    )
```

### 2. Company 모델 수정

```python
# app/models/company.py에 추가
class Company(Base):
    # ... 기존 코드 ...

    # Relationships 추가
    themes = relationship(
        "Theme",
        secondary="stock_themes",
        back_populates="companies"
    )
```

### 3. 테마 API 추가

```python
# app/api/v1/themes.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import List
from pydantic import BaseModel

from app.core.database import get_db
from app.models.theme import Theme, stock_theme_association
from app.models.company import Company

router = APIRouter()


class ThemeCreate(BaseModel):
    theme_name: str
    theme_name_eng: str = None
    category: str = None
    description: str = None


class ThemeStockAdd(BaseModel):
    stock_codes: List[str]


@router.get("/themes")
async def get_themes(
    category: str = None,
    db: AsyncSession = Depends(get_db)
):
    """전체 테마 목록 조회"""

    query = select(Theme).where(Theme.is_active == True)

    if category:
        query = query.where(Theme.category == category)

    result = await db.execute(query.order_by(Theme.popularity_score.desc()))
    themes = result.scalars().all()

    return {
        "themes": [
            {
                "theme_id": t.theme_id,
                "theme_name": t.theme_name,
                "category": t.category,
                "description": t.description,
                "stock_count": t.stock_count,
                "popularity_score": t.popularity_score
            }
            for t in themes
        ],
        "total": len(themes)
    }


@router.get("/themes/{theme_id}/stocks")
async def get_theme_stocks(
    theme_id: int,
    db: AsyncSession = Depends(get_db)
):
    """특정 테마의 종목 조회"""

    # 테마 조회
    theme_result = await db.execute(
        select(Theme).where(Theme.theme_id == theme_id)
    )
    theme = theme_result.scalar_one_or_none()

    if not theme:
        raise HTTPException(status_code=404, detail="Theme not found")

    # 테마에 속한 종목 조회
    stocks_result = await db.execute(
        select(Company)
        .join(stock_theme_association)
        .where(stock_theme_association.c.theme_id == theme_id)
        .where(Company.is_active == 1)
    )
    stocks = stocks_result.scalars().all()

    return {
        "theme": {
            "theme_id": theme.theme_id,
            "theme_name": theme.theme_name,
            "description": theme.description
        },
        "stocks": [
            {
                "stock_code": s.stock_code,
                "stock_name": s.stock_name,
                "industry": s.industry,
                "market_type": s.market_type
            }
            for s in stocks
        ],
        "total": len(stocks)
    }


@router.post("/themes")
async def create_theme(
    theme_data: ThemeCreate,
    db: AsyncSession = Depends(get_db)
):
    """새 테마 생성 (관리자용)"""

    new_theme = Theme(
        theme_name=theme_data.theme_name,
        theme_name_eng=theme_data.theme_name_eng,
        category=theme_data.category,
        description=theme_data.description
    )

    db.add(new_theme)
    await db.commit()
    await db.refresh(new_theme)

    return {
        "message": "Theme created",
        "theme_id": new_theme.theme_id,
        "theme_name": new_theme.theme_name
    }


@router.post("/themes/{theme_id}/stocks")
async def add_stocks_to_theme(
    theme_id: int,
    stock_data: ThemeStockAdd,
    db: AsyncSession = Depends(get_db)
):
    """테마에 종목 추가 (관리자용)"""

    # 테마 확인
    theme_result = await db.execute(
        select(Theme).where(Theme.theme_id == theme_id)
    )
    theme = theme_result.scalar_one_or_none()

    if not theme:
        raise HTTPException(status_code=404, detail="Theme not found")

    # 종목 조회
    stocks_result = await db.execute(
        select(Company)
        .where(Company.stock_code.in_(stock_data.stock_codes))
        .where(Company.is_active == 1)
    )
    stocks = stocks_result.scalars().all()

    # 테마에 종목 추가
    for stock in stocks:
        await db.execute(
            stock_theme_association.insert().values(
                company_id=stock.company_id,
                theme_id=theme_id
            ).prefix_with('OR IGNORE')  # 중복 방지
        )

    # 종목 수 업데이트
    count_result = await db.execute(
        select(func.count())
        .select_from(stock_theme_association)
        .where(stock_theme_association.c.theme_id == theme_id)
    )
    theme.stock_count = count_result.scalar()

    await db.commit()

    return {
        "message": "Stocks added to theme",
        "theme_id": theme_id,
        "added_count": len(stocks),
        "total_stocks": theme.stock_count
    }
```

### 4. 테이블 생성 스크립트

```python
# scripts/create_theme_tables.py
import asyncio
from app.core.database import engine
from app.models.theme import Theme, stock_theme_association
from app.core.database import Base


async def create_tables():
    """테마 테이블 생성"""

    async with engine.begin() as conn:
        # 테마 관련 테이블 생성
        await conn.run_sync(Base.metadata.create_all)

    print("✅ 테마 테이블 생성 완료")


if __name__ == "__main__":
    asyncio.run(create_tables())
```

---

## 🔄 테마 데이터 삽입 방법

### 방법 1: 수동 삽입 (SQL)

```sql
-- 테마 생성
INSERT INTO themes (theme_name, category, description) VALUES
('2차전지', '산업', '전기차 배터리 관련 종목'),
('K-방산', '산업', '방위산업 관련 종목'),
('AI/로봇', '기술', '인공지능 및 로봇 관련'),
('메타버스', '기술', '가상현실/증강현실'),
('바이오', '산업', '제약/바이오 관련');

-- 종목-테마 연결
INSERT INTO stock_themes (company_id, theme_id)
SELECT c.company_id, 1  -- 2차전지 테마
FROM companies c
WHERE c.stock_code IN ('373220', '066970', '247540');  -- LG에너지솔루션, 엘앤에프, 에코프로비엠
```

### 방법 2: Python 스크립트

```python
# scripts/insert_theme_data.py
import asyncio
from sqlalchemy import select
from app.core.database import get_db_session
from app.models.theme import Theme, stock_theme_association
from app.models.company import Company


# 테마 데이터 정의
THEME_DATA = {
    "2차전지": {
        "category": "산업",
        "description": "전기차 배터리 관련 종목",
        "stocks": ["373220", "066970", "247540", "086520", "357780"]  # LG에솔, 엘앤에프, 에코프로, 에코프로비엠, 포스코퓨처엠
    },
    "K-방산": {
        "category": "산업",
        "description": "방위산업 관련 종목",
        "stocks": ["012450", "079550", "272210", "047810"]  # 한화에어로스페이스, LIG넥스원, 한화시스템, 한화오션
    },
    "반도체": {
        "category": "기술",
        "description": "반도체 제조 및 장비 관련",
        "stocks": ["005930", "000660", "042700", "058470"]  # 삼성전자, SK하이닉스, 유니테스트, 리노공업
    },
    "AI/로봇": {
        "category": "기술",
        "description": "인공지능 및 로봇 관련",
        "stocks": ["035420", "035720", "251270", "366330"]  # NAVER, 카카오, 넷마블, 셀바스AI
    }
}


async def insert_themes():
    """테마 데이터 삽입"""

    async with get_db_session() as db:
        for theme_name, data in THEME_DATA.items():
            # 테마 생성
            theme = Theme(
                theme_name=theme_name,
                category=data["category"],
                description=data["description"]
            )
            db.add(theme)
            await db.flush()  # theme_id 생성

            # 종목 조회
            result = await db.execute(
                select(Company)
                .where(Company.stock_code.in_(data["stocks"]))
            )
            companies = result.scalars().all()

            # 종목-테마 연결
            for company in companies:
                await db.execute(
                    stock_theme_association.insert().values(
                        company_id=company.company_id,
                        theme_id=theme.theme_id
                    )
                )

            # 종목 수 업데이트
            theme.stock_count = len(companies)

            print(f"✅ {theme_name} 테마 생성 ({len(companies)}개 종목)")

        await db.commit()

    print("\n✅ 모든 테마 데이터 삽입 완료")


if __name__ == "__main__":
    asyncio.run(insert_themes())
```

---

## 🎨 프론트엔드 연동

### API 호출 예시

```typescript
// api/sectors.ts
export const sectorAPI = {
    // 섹터 목록
    getSectors: async () => {
        return await fetch('/api/v1/sectors');
    },

    // 섹터별 종목
    getStocksBySector: async (sectorName: string) => {
        return await fetch(`/api/v1/sectors/${sectorName}/stocks`);
    },

    // 업종 목록
    getIndustries: async () => {
        return await fetch('/api/v1/industries');
    },

    // 테마 목록
    getThemes: async () => {
        return await fetch('/api/v1/themes');
    },

    // 테마별 종목
    getStocksByTheme: async (themeId: number) => {
        return await fetch(`/api/v1/themes/${themeId}/stocks`);
    },

    // 종목 검색
    searchStocks: async (keyword: string) => {
        return await fetch(`/api/v1/search?keyword=${keyword}`);
    }
};
```

---

## 🚀 구현 순서

### Step 1: 즉시 사용 가능 (1-2시간)
1. ✅ `sector_mapping.py` 생성
2. ✅ `sectors.py` API 추가
3. ✅ 라우터 등록
4. ✅ 프론트엔드 연동

### Step 2: 테마 시스템 (반나절)
1. ✅ `theme.py` 모델 추가
2. ✅ 테이블 생성
3. ✅ 테마 데이터 삽입
4. ✅ `themes.py` API 추가
5. ✅ 프론트엔드 연동

## 📊 최종 결과

사용자는:
1. **섹터로 선택** (IT/금융/제조 등)
2. **업종으로 선택** (반도체/게임/은행 등)
3. **테마로 선택** (2차전지/K-방산/AI 등)
4. **직접 검색** (종목명/코드)

모든 방법으로 백테스트 대상 종목을 선택할 수 있습니다! 🎯