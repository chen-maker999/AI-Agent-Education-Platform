import asyncio
import sys
sys.path.insert(0, r'D:\AI-Agent-Education-Platform-cursor\backend')

async def check_and_fix():
    from common.database.postgresql import async_engine
    from sqlalchemy import text

    async with async_engine.begin() as conn:
        result = await conn.execute(text("""
            SELECT column_name, data_type, column_default
            FROM information_schema.columns
            WHERE table_name = 'homework_reviews'
            ORDER BY ordinal_position
        """))
        columns = result.fetchall()
        print("Current homework_reviews columns:")
        existing_cols = set()
        for col in columns:
            print(f"  {col[0]}: {col[1]} default={col[2]}")
            existing_cols.add(col[0])

    # Add missing columns
    migrations = {
        'review_id': 'VARCHAR(255)',
        'original_filename': 'VARCHAR(500)',
        'graded_filename': 'VARCHAR(500)',
        'graded_file_url': 'TEXT',
        'file_size': 'INTEGER',
        'total_score': 'FLOAT DEFAULT 100.0',
        'issue_count': 'INTEGER DEFAULT 0',
        'issues_json': 'TEXT',
    }

    async with async_engine.begin() as conn:
        for col_name, col_type in migrations.items():
            if col_name not in existing_cols:
                sql = f"ALTER TABLE homework_reviews ADD COLUMN {col_name} {col_type}"
                try:
                    await conn.execute(text(sql))
                    print(f"Added column: {col_name}")
                except Exception as e:
                    print(f"Error adding {col_name}: {e}")
            else:
                print(f"Column already exists: {col_name}")

asyncio.run(check_and_fix())
