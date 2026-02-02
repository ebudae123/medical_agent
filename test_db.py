"""
Diagnostic script to test database connectivity and initialization
"""
import asyncio
import sys
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text

async def test_database():
    """Test database connection and check tables"""
    database_url = "postgresql+asyncpg://postgres:23640928@localhost:5432/nightingale"
    
    print("[*] Testing database connection...")
    print(f"Database URL: {database_url.replace(':23640928@', ':****@')}\n")
    
    try:
        # Create engine
        engine = create_async_engine(database_url, echo=False)
        
        # Test connection
        async with engine.begin() as conn:
            result = await conn.execute(text("SELECT version()"))
            version = result.scalar()
            print(f"[+] Database connected successfully!")
            print(f"PostgreSQL version: {version}\n")
            
            # Check if tables exist
            result = await conn.execute(text("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public'
                ORDER BY table_name
            """))
            tables = result.fetchall()
            
            if tables:
                print(f"[+] Found {len(tables)} tables:")
                for table in tables:
                    print(f"   - {table[0]}")
            else:
                print("[!] No tables found in database!")
                print("   This is likely the issue - database needs to be initialized.")
                
        await engine.dispose()
        return True
        
    except Exception as e:
        print(f"[-] Database connection failed!")
        print(f"Error: {str(e)}\n")
        print("Possible issues:")
        print("1. PostgreSQL is not running")
        print("2. Database 'nightingale' doesn't exist")
        print("3. Wrong password in .env file")
        print("4. PostgreSQL is not listening on localhost:5432")
        return False

if __name__ == "__main__":
    success = asyncio.run(test_database())
    sys.exit(0 if success else 1)
