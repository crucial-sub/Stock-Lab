"""
테마 테이블 스키마 확인

Usage:
    python scripts/migrations/inspect_themes_schema.py
"""
import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

import asyncio
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text, inspect
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


async def inspect_themes_schema():
    """테마 테이블 스키마 확인"""

    # Get database URL from environment
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        raise ValueError("DATABASE_URL environment variable not set")

    # Create async engine
    engine = create_async_engine(database_url, echo=False)

    try:
        async with engine.connect() as conn:
            # Get column info
            result = await conn.execute(text("""
                SELECT column_name, data_type, is_nullable, column_default
                FROM information_schema.columns
                WHERE table_name = 'themes'
                ORDER BY ordinal_position
            """))
            columns = result.fetchall()

            print("\n=== Themes table schema ===")
            for col in columns:
                print(f"  {col[0]:20} {col[1]:15} {'NULL' if col[2] == 'YES' else 'NOT NULL':10} {col[3] or ''}")

            # Get sample data
            result = await conn.execute(text("SELECT * FROM themes LIMIT 5"))
            rows = result.fetchall()

            print(f"\n=== Sample data ({len(rows)} rows) ===")
            if columns:
                headers = [col[0] for col in columns]
                print("  " + " | ".join(headers))
                print("  " + "-" * 80)
                for row in rows:
                    print("  " + " | ".join(str(v) for v in row))

    except Exception as e:
        print(f"✗ Error: {e}")
        raise
    finally:
        await engine.dispose()


if __name__ == "__main__":
    asyncio.run(inspect_themes_schema())
