"""Authentication and authorization utilities."""

from datetime import datetime, timedelta
from typing import Optional
import hashlib

import bcrypt
from jose import JWTError, jwt
from fastapi import HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from .config import settings
from .database import get_db
from ..models.user import User
from ..repositories.user import UserRepository

# JWT
security = HTTPBearer()


def _hash_secret(password: str) -> bytes:
    """Return a fixed-length digest suitable for bcrypt."""
    return hashlib.sha256(password.encode("utf-8")).digest()


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plain password against hashed password with legacy support."""
    if not hashed_password:
        return False

    stored = hashed_password.encode("utf-8")

    # First try the new SHA256+bcrypt flow (handles >72 bytes safely)
    try:
        if bcrypt.checkpw(_hash_secret(plain_password), stored):
            return True
    except ValueError:
        # Raised if hash format is invalid; fall back to legacy path
        pass

    # Legacy fallback: direct bcrypt check (will work for old hashes)
    try:
        return bcrypt.checkpw(plain_password.encode("utf-8"), stored)
    except ValueError:
        # bcrypt refuses passwords longer than 72 bytes; treat as failure
        return False


def get_password_hash(password: str) -> str:
    """Generate hash for a password."""
    return bcrypt.hashpw(_hash_secret(password), bcrypt.gensalt()).decode("utf-8")


def create_access_token(
    data: dict, 
    expires_delta: Optional[timedelta] = None
) -> str:
    """Create JWT access token."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(seconds=settings.JWT_EXPIRES)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(
        to_encode, 
        settings.JWT_SECRET, 
        algorithm=settings.JWT_ALGORITHM
    )
    return encoded_jwt


def decode_token(token: str) -> dict:
    """Decode JWT token."""
    try:
        payload = jwt.decode(
            token, 
            settings.JWT_SECRET, 
            algorithms=[settings.JWT_ALGORITHM]
        )
        return payload
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db)
) -> User:
    """Get current authenticated user."""
    try:
        payload = decode_token(credentials.credentials)
        user_id: str = payload.get("sub")
        if user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials"
            )
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials"
        )
    
    user_repo = UserRepository(db)
    user = await user_repo.get_by_id(int(user_id))
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found"
        )
    return user


async def get_current_active_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """Get current active user."""
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user"
        )
    return current_user


async def get_current_user_or_demo(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db)
) -> User:
    """Get current user or return demo user for demo tokens."""
    try:
        payload = decode_token(credentials.credentials)
        user_id: str = payload.get("sub")
        org_id: int = payload.get("org_id", 1)
        
        if user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials"
            )
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials"
        )
    
    # For demo user (user_id = "1"), return a mock user object
    if user_id == "1":
        from ..models.user import User
        demo_user = User()
        demo_user.user_id = 1
        demo_user.org_id = 1  # Always use org_id = 1 for demo
        demo_user.email = "demo@university.edu"
        demo_user.role = "admin"
        demo_user.is_active = True
        return demo_user
    
    # For real users, look up in database
    user_repo = UserRepository(db)
    user = await user_repo.get_by_id(int(user_id))
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found"
        )
    
    # Ensure all users use org_id = 1 for consistency
    user.org_id = 1
    return user


async def get_current_active_user_or_demo(
    current_user: User = Depends(get_current_user_or_demo)
) -> User:
    """Get current active user or demo user."""
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user"
        )
    return current_user


def require_role(allowed_roles: list):
    """Decorator to require specific user roles."""
    def role_checker(current_user: User = Depends(get_current_active_user)):
        if current_user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not enough permissions"
            )
        return current_user
    return role_checker
