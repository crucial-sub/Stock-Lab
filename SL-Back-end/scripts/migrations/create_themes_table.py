"""
테마 마스터 테이블 생성 및 초기 데이터 시딩

Usage:
    python scripts/migrations/create_themes_table.py
"""
import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import text
from app.models.theme import Theme
from app.core.database import Base
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Theme data combining all sources
THEME_DATA = [
    # Standard industry themes (based on THEME_DEFINITIONS from backtest.py)
    {"code": "T001", "name": "construction", "name_kor": "건설", "order": 1},
    {"code": "T002", "name": "metal", "name_kor": "금속", "order": 2},
    {"code": "T003", "name": "finance", "name_kor": "금융", "order": 3},
    {"code": "T004", "name": "machinery", "name_kor": "기계/장비", "order": 4},
    {"code": "T005", "name": "other_finance", "name_kor": "기타 금융", "order": 5},
    {"code": "T006", "name": "other_manufacturing", "name_kor": "기타 제조", "order": 6},
    {"code": "T007", "name": "other", "name_kor": "기타", "order": 7},
    {"code": "T008", "name": "agriculture", "name_kor": "농업/임업/어업", "order": 8},
    {"code": "T009", "name": "insurance", "name_kor": "보험", "order": 9},
    {"code": "T010", "name": "real_estate", "name_kor": "부동산", "order": 10},
    {"code": "T011", "name": "non_metal", "name_kor": "비금속", "order": 11},
    {"code": "T012", "name": "textile", "name_kor": "섬유/의류", "order": 12},
    {"code": "T013", "name": "entertainment", "name_kor": "오락/문화", "order": 13},
    {"code": "T014", "name": "transport", "name_kor": "운송/창고", "order": 14},
    {"code": "T015", "name": "transport_equipment", "name_kor": "운송장비/부품", "order": 15},
    {"code": "T016", "name": "distribution", "name_kor": "유통", "order": 16},
    {"code": "T017", "name": "bank", "name_kor": "은행", "order": 17},
    {"code": "T018", "name": "food", "name_kor": "음식료/담배", "order": 18},
    {"code": "T019", "name": "medical", "name_kor": "의료/정밀기기", "order": 19},
    {"code": "T020", "name": "service", "name_kor": "일반 서비스", "order": 20},
    {"code": "T021", "name": "utility", "name_kor": "전기/가스/수도", "order": 21},
    {"code": "T022", "name": "electronics", "name_kor": "전기/전자", "order": 22},
    {"code": "T023", "name": "pharma", "name_kor": "제약", "order": 23},
    {"code": "T024", "name": "paper", "name_kor": "종이/목재", "order": 24},
    {"code": "T025", "name": "securities", "name_kor": "증권", "order": 25},
    {"code": "T026", "name": "publishing", "name_kor": "출판/매체복제", "order": 26},
    {"code": "T027", "name": "telecom", "name_kor": "통신", "order": 27},
    {"code": "T028", "name": "chemical", "name_kor": "화학", "order": 28},
    {"code": "T029", "name": "it_service", "name_kor": "IT서비스", "order": 29},

    # Chatbot-specific themes (from shared_data.py)
    {"code": "T030", "name": "semiconductor", "name_kor": "반도체", "order": 30},
    {"code": "T031", "name": "ai", "name_kor": "AI", "order": 31},
    {"code": "T032", "name": "secondary_battery", "name_kor": "2차전지", "order": 32},
    {"code": "T033", "name": "bio_pharma", "name_kor": "바이오/제약", "order": 33},
    {"code": "T034", "name": "robot", "name_kor": "로봇", "order": 34},
    {"code": "T035", "name": "renewable_energy", "name_kor": "신재생에너지", "order": 35},
]


async def create_themes_table():
    """테마 마스터 테이블 생성 및 데이터 시딩"""

    # Get database URL from environment
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        raise ValueError("DATABASE_URL environment variable not set")

    # Create async engine
    engine = create_async_engine(
        database_url,
        echo=True,
        pool_pre_ping=True
    )

    # Create session factory
    async_session = sessionmaker(
        engine,
        class_=AsyncSession,
        expire_on_commit=False
    )

    try:
        # Create table
        print("\n=== Creating themes table ===")
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all, tables=[Theme.__table__])
        print("✓ Table created successfully")

        # Insert theme data
        print("\n=== Inserting theme data ===")
        async with async_session() as session:
            # Check if data already exists
            result = await session.execute(text("SELECT COUNT(*) FROM themes"))
            count = result.scalar()

            if count > 0:
                print(f"⚠ Table already contains {count} records")
                response = input("Do you want to clear and re-insert? (y/n): ")
                if response.lower() == 'y':
                    await session.execute(text("DELETE FROM themes"))
                    await session.commit()
                    print("✓ Existing data cleared")
                else:
                    print("Skipping insertion")
                    return

            # Insert themes
            for theme_data in THEME_DATA:
                theme = Theme(
                    theme_code=theme_data["code"],
                    theme_name=theme_data["name"],
                    theme_name_kor=theme_data["name_kor"],
                    is_active=True,
                    display_order=theme_data["order"]
                )
                session.add(theme)

            await session.commit()
            print(f"✓ Successfully inserted {len(THEME_DATA)} themes")

            # Verify insertion
            result = await session.execute(text("SELECT theme_code, theme_name, theme_name_kor FROM themes ORDER BY display_order"))
            themes = result.fetchall()

            print("\n=== Inserted themes ===")
            for theme in themes:
                print(f"  {theme[0]} | {theme[1]:25} | {theme[2]}")

    except Exception as e:
        print(f"✗ Error: {e}")
        raise
    finally:
        await engine.dispose()


if __name__ == "__main__":
    print("Starting theme table migration...")
    asyncio.run(create_themes_table())
    print("\n✓ Migration completed successfully!")
