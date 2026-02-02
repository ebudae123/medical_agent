"""
Script to initialize test users for development and testing
"""
import asyncio
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from backend.database import async_session_maker
from backend.models.user import User, UserRole


async def init_test_users():
    """Create test user accounts if they don't exist"""
    
    test_users = [
        # Patients
        {"username": "patient1", "password": "test123", "name": "Alice Johnson", "role": UserRole.PATIENT},
        {"username": "patient2", "password": "test123", "name": "Bob Smith", "role": UserRole.PATIENT},
        {"username": "patient3", "password": "test123", "name": "Carol Williams", "role": UserRole.PATIENT},
        {"username": "patient4", "password": "test123", "name": "David Brown", "role": UserRole.PATIENT},
        
        # Clinicians
        {"username": "clinician1", "password": "test123", "name": "Dr. Emily Chen", "role": UserRole.CLINICIAN},
        {"username": "clinician2", "password": "test123", "name": "Dr. Michael Rodriguez", "role": UserRole.CLINICIAN},
    ]
    
    async with async_session_maker() as db:
        for user_data in test_users:
            # Check if user already exists
            result = await db.execute(
                select(User).where(User.username == user_data["username"])
            )
            existing_user = result.scalar_one_or_none()
            
            if not existing_user:
                # Create new user
                user = User(
                    username=user_data["username"],
                    name=user_data["name"],
                    role=user_data["role"],
                    email=f"{user_data['username']}@test.com"
                )
                user.set_password(user_data["password"])
                db.add(user)
                print(f"[OK] Created test user: {user_data['username']} ({user_data['role'].value})")
            else:
                print(f"[SKIP] User already exists: {user_data['username']}")
        
        await db.commit()
    
    print("\n[OK] Test users initialization complete!")


if __name__ == "__main__":
    asyncio.run(init_test_users())
