"""
Script to reset the database - drops all tables and recreates them
WARNING: This will delete all existing data!
"""
import asyncio
from backend.database import engine, Base, init_db

# Import all models so they're registered with Base.metadata
from backend.models.user import User
from backend.models.conversation import Conversation
from backend.models.message import Message
from backend.models.patient_profile import PatientProfile
from backend.models.escalation import EscalationTicket


async def reset_database():
    """Drop all tables and recreate them"""
    print("WARNING: This will delete all existing data!")
    print("Dropping all tables...")
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    
    print("All tables dropped")
    print("Creating new tables with updated schema...")
    
    await init_db()
    
    print("Database reset complete!")


if __name__ == "__main__":
    asyncio.run(reset_database())
