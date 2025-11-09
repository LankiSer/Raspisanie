"""Fix password hash for admin@test.ru user."""

import asyncio
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text
from app.core.config import settings
from app.core.auth import get_password_hash

async def fix_password():
    engine = create_async_engine(settings.DATABASE_URL)
    async with engine.begin() as conn:
        # Generate proper password hash
        password_hash = get_password_hash("admin123")
        print(f"New password hash: {password_hash}")
        
        # Update password for admin@test.ru
        await conn.execute(
            text("UPDATE users SET password_hash = :password_hash WHERE email = 'admin@test.ru'"),
            {"password_hash": password_hash}
        )
        
        print("Password updated successfully!")
        
        # Verify the update
        result = await conn.execute(
            text("SELECT user_id, email, password_hash FROM users WHERE email = 'admin@test.ru'")
        )
        user = result.fetchone()
        print(f"Updated user: {user}")
    
    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(fix_password())
