"""
Simple script to drop all tables using raw SQL with CASCADE
"""
import asyncio
from backend.database import engine
from sqlalchemy import text


async def drop_all_tables():
    """Drop all tables using CASCADE"""
    print("Dropping all tables with CASCADE...")
    
    tables = ["audit_logs", "escalation_tickets", "messages", "patient_profiles", "conversations", "users"]
    
    async with engine.begin() as conn:
        for table in tables:
            try:
                await conn.execute(text(f"DROP TABLE IF EXISTS {table} CASCADE"))
                print(f"  Dropped {table}")
            except Exception as e:
                print(f"  Could not drop {table}: {e}")
    
    print("\nAll tables dropped successfully!")
    print("\nNow restart the server with: python start.py")
    print("The server will recreate all tables with the new schema.")


if __name__ == "__main__":
    asyncio.run(drop_all_tables())
