import asyncio
from app.db.session import AsyncSessionLocal
from app.modules.users.repository import UserRepository

__test__ = False

async def test_insert():
    async with AsyncSessionLocal() as db:
        try:
            # Create a test email
            test_email = "test_insert_bug@example.com"
            user = await UserRepository.get_active_by_email(db, test_email)
            if user:
                await db.delete(user)
                await db.commit()
            
            # Now try to create
            user = await UserRepository.create(
                db, 
                email=test_email,
                auth_provider="google",
                google_id="test_google_id",
            )
            print(f"Success! Inserted user {user.email} with id {user.id}")
            
            # Clean up
            await db.delete(user)
            await db.commit()
        except Exception as e:
            print(f"Error during insert: {e}")

if __name__ == "__main__":
    asyncio.run(test_insert())
