"""Test database connection and RAG documents"""
import asyncio
from common.database.postgresql import AsyncSessionLocal
from sqlalchemy import text, select

async def test_db():
    print("Testing database connection...")
    try:
        async with AsyncSessionLocal() as session:
            # Test connection
            result = await session.execute(text("SELECT 1"))
            print(f"DB connection OK: {result.scalar()}")
            
            # Check if rag_documents table exists and has data
            result = await session.execute(text("SELECT COUNT(*) FROM rag_documents"))
            count = result.scalar()
            print(f"rag_documents count: {count}")
            
            # Check table structure
            result = await session.execute(text("""
                SELECT column_name, data_type 
                FROM information_schema.columns 
                WHERE table_name = 'rag_documents'
            """))
            columns = result.fetchall()
            print(f"rag_documents columns: {columns}")
            
    except Exception as e:
        print(f"Database error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_db())
