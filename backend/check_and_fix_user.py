#!/usr/bin/env python3
"""Check and fix user password if needed."""

import asyncio
import sys
import os

# Add parent directory to path to import app modules
sys.path.insert(0, os.path.dirname(__file__))

from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlalchemy import select
from app.core.config import settings
from app.core.auth import get_password_hash, verify_password
from app.models.user import User

async def check_and_fix_user():
    """Check if user exists and fix password if needed."""
    
    print("🔍 Checking user in database...")
    
    engine = create_async_engine(settings.DATABASE_URL, echo=False)
    async_session = async_sessionmaker(engine, expire_on_commit=False)
    
    async with async_session() as session:
        # Check if user exists
        result = await session.execute(
            select(User).where(User.email == "admin@university.edu")
        )
        user = result.scalar_one_or_none()
        
        if not user:
            print("❌ User 'admin@university.edu' not found in database!")
            print("🔧 Creating user...")
            
            # Get or create organization
            from app.models.organization import Organization
            from app.models.user import UserRole
            
            org_result = await session.execute(
                select(Organization).limit(1)
            )
            org = org_result.scalar_one_or_none()
            
            if not org:
                print("📚 Creating organization...")
                org = Organization(
                    name="Московский технический университет",
                    locale="ru",
                    tz="Europe/Moscow"
                )
                session.add(org)
                await session.flush()
            
            # Create user
            user = User(
                org_id=org.org_id,
                email="admin@university.edu",
                password_hash=get_password_hash("admin123"),
                role=UserRole.ADMIN,
                is_active=True
            )
            session.add(user)
            await session.commit()
            
            print("✅ User created successfully!")
            is_valid = True
            return
        
        print(f"✅ User found: {user.email}")
        print(f"   User ID: {user.user_id}")
        print(f"   Role: {user.role}")
        print(f"   Is Active: {user.is_active}")
        print(f"   Password Hash: {user.password_hash[:50]}...")
        
        # Test password
        test_password = "admin123"
        print(f"\n🔐 Testing password '{test_password}'...")
        
        is_valid = verify_password(test_password, user.password_hash)
        
        if is_valid:
            print("✅ Password is correct!")
        else:
            print("❌ Password verification failed!")
            print("🔧 Fixing password...")
            
            # Re-hash password
            user.password_hash = get_password_hash(test_password)
            await session.commit()
            
            # Verify again
            is_valid_after = verify_password(test_password, user.password_hash)
            if is_valid_after:
                print("✅ Password fixed and verified!")
            else:
                print("❌ Password fix failed!")
                return
        
        print("\n📊 Summary:")
        print(f"   Email: {user.email}")
        print(f"   Password: {test_password}")
        print(f"   Status: {'✅ Valid' if is_valid else '❌ Invalid'}")
    
    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(check_and_fix_user())

