import asyncio
import sys
sys.path.insert(0, r'D:\AI-Agent-Education-Platform-cursor\backend')

async def check_columns():
    from common.database.postgresql import async_engine
    from sqlalchemy import text
    
    async with async_engine.begin() as conn:
        result = await conn.execute(text("""
            SELECT column_name, data_type 
            FROM information_schema.columns 
            WHERE table_name = 'homework_reviews'
            ORDER BY ordinal_position
        """))
        columns = result.fetchall()
        print("Current homework_reviews columns:")
        for col in columns:
            print(f"  {col[0]}: {col[1]}")

asyncio.run(check_columns())
