import asyncio
import sys
import os

# Add the parent directory to sys.path to allow importing from 'app'
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.db.session import AsyncSessionLocal
from app.db import models  # Ensure all models are registered
from app.modules.users.models.user import User
from app.core.security import hash_password
from sqlalchemy import select

async def create_admin(email, password):
    async with AsyncSessionLocal() as db:
        # Check if user already exists
        result = await db.execute(select(User).where(User.email == email))
        user = result.scalar_one_or_none()
        
        if not user:
            print(f"Creating new admin user: {email}...")
            user = User(
                email=email,
                password_hash=hash_password(password),
                display_name="Admin User",
                native_language="en",
                target_language="en",
                level="advanced",
                is_onboarding_completed=True,
                preferences={"is_admin": True}
            )
            db.add(user)
        else:
            print(f"User {email} already exists. Elevating to admin status...")
            prefs = user.preferences or {}
            prefs["is_admin"] = True
            user.preferences = prefs
        
        await db.commit()
        print(f"Success: {email} is now an admin.")

if __name__ == "__main__":
    # Ensure we are in the 'backend' directory so .env and DB are found correctly
    backend_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    os.chdir(backend_root)
    
    email = "admin123@gmail.com"
    password = "123456"
    
    if len(sys.argv) > 2:
        email = sys.argv[1]
        password = sys.argv[2]
    
    try:
        asyncio.run(create_admin(email, password))
    except Exception as e:
        print(f"\nERROR: Failed to create/update admin user.")
        print(f"Details: {e}")
        if "no such table: users" in str(e).lower():
            print("\nTIP: It looks like the database tables have not been created yet.")
            print("Run 'alembic upgrade head' or 'bash run.sh' to initialize the database.")
        sys.exit(1)
