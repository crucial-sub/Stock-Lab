"""
챗봇 전용 테마 추가 (반도체, AI, 2차전지, 바이오/제약, 로봇, 신재생에너지)

Usage:
    python scripts/migrations/add_chatbot_themes.py
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
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Chatbot-specific themes to add
CHATBOT_THEMES = [
    {"code": "T030", "name": "semiconductor", "name_kor": "반도체"},
    {"code": "T031", "name": "ai", "name_kor": "AI"},
    {"code": "T032", "name": "secondary_battery", "name_kor": "2차전지"},
    {"code": "T033", "name": "bio_pharma", "name_kor": "바이오/제약"},
    {"code": "T034", "name": "robot", "name_kor": "로봇"},
    {"code": "T035", "name": "renewable_energy", "name_kor": "신재생에너지"},
]


async def add_chatbot_themes():
    """챗봇 전용 테마 추가"""

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
        print("\n=== Adding chatbot themes ===")
        async with async_session() as session:
            # Check current theme count
            result = await session.execute(text("SELECT COUNT(*) FROM themes"))
            count = result.scalar()
            print(f"Current theme count: {count}")

            # Check which themes already exist
            for theme_data in CHATBOT_THEMES:
                result = await session.execute(
                    text("SELECT theme_code FROM themes WHERE theme_code = :code OR theme_name = :name"),
                    {"code": theme_data["code"], "name": theme_data["name"]}
                )
                existing = result.fetchone()

                if existing:
                    print(f"  ⚠ Theme already exists: {theme_data['code']} ({theme_data['name_kor']})")
                else:
                    # Insert new theme
                    theme = Theme(
                        theme_code=theme_data["code"],
                        theme_name=theme_data["name"],
                        theme_name_kor=theme_data["name_kor"]
                    )
                    session.add(theme)
                    print(f"  ✓ Adding: {theme_data['code']} | {theme_data['name']:25} | {theme_data['name_kor']}")

            await session.commit()
            print("\n✓ Themes added successfully")

            # Show all themes
            result = await session.execute(
                text("SELECT theme_code, theme_name, theme_name_kor FROM themes ORDER BY theme_code")
            )
            themes = result.fetchall()

            print(f"\n=== All themes ({len(themes)} total) ===")
            for theme in themes:
                print(f"  {theme[0]} | {theme[1]:25} | {theme[2]}")

    except Exception as e:
        print(f"✗ Error: {e}")
        raise
    finally:
        await engine.dispose()


if __name__ == "__main__":
    print("Starting chatbot theme addition...")
    asyncio.run(add_chatbot_themes())
    print("\n✓ Migration completed successfully!")
