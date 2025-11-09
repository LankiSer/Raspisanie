"""Authentication router."""

from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from ..core.database import get_db
from ..core.auth import (
    verify_password, get_password_hash, create_access_token,
    get_current_active_user
)
from ..core.config import settings
from ..repositories.user import UserRepository
from ..repositories.organization import OrganizationRepository
from ..models.user import UserRole
from ..schemas.auth import LoginRequest, LoginResponse, RegisterRequest, UserInfo

router = APIRouter()
security = HTTPBearer()


@router.post("/register", response_model=LoginResponse)
async def register(
    request: RegisterRequest,
    db: AsyncSession = Depends(get_db)
):
    """Register new organization and admin user."""
    
    # Check if user already exists
    user_repo = UserRepository(db)
    existing_user = await user_repo.get_by_email(request.email)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    try:
        # Create organization
        org_repo = OrganizationRepository(db)
        org_data = {
            "name": request.organization_name,
            "locale": request.locale,
            "tz": request.tz
        }
        organization = await org_repo.create(org_data)
        
        # Create admin user
        user_data = {
            "email": request.email,
            "password_hash": get_password_hash(request.password),
            "role": UserRole.ADMIN,
            "org_id": organization.org_id,
            "is_active": True
        }
        user = await user_repo.create(user_data)
        
        # Create access token
        access_token = create_access_token(
            data={"sub": str(user.user_id)},
            expires_delta=timedelta(seconds=settings.JWT_EXPIRES)
        )
        
        return LoginResponse(
            access_token=access_token,
            user=UserInfo(
                user_id=user.user_id,
                email=user.email,
                role=user.role,
                org_id=user.org_id,
                is_active=user.is_active
            )
        )
        
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create organization and user"
        )


@router.post("/login", response_model=LoginResponse)
async def login(
    request: LoginRequest,
    db: AsyncSession = Depends(get_db)
):
    """Authenticate user and return JWT token."""
    
    # Get user by email
    user_repo = UserRepository(db)
    user = await user_repo.get_by_email(request.email)
    
    if not user or not verify_password(request.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password"
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user"
        )
    
    # Create access token
    access_token = create_access_token(
        data={"sub": str(user.user_id)},
        expires_delta=timedelta(seconds=settings.JWT_EXPIRES)
    )
    
    return LoginResponse(
        access_token=access_token,
        user=UserInfo(
            user_id=user.user_id,
            email=user.email,
            role=user.role,
            org_id=user.org_id,
            is_active=user.is_active
        )
    )


@router.get("/me", response_model=UserInfo)
async def get_current_user_info(
    current_user = Depends(get_current_active_user)
):
    """Get current user information."""
    return UserInfo(
        user_id=current_user.user_id,
        email=current_user.email,
        role=current_user.role,
        org_id=current_user.org_id,
        is_active=current_user.is_active
    )


@router.post("/demo-login", response_model=LoginResponse)
async def demo_login(db: AsyncSession = Depends(get_db)):
    """Demo login for development/testing."""
    # Get first available user
    user_repo = UserRepository(db)
    user = await user_repo.get_by_id(1)  # Get first user
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No demo user found"
        )
    
    # Create demo access token
    access_token = create_access_token(
        data={"sub": str(user.user_id), "org_id": user.org_id}
    )
    
    return LoginResponse(
        access_token=access_token,
        user=UserInfo(
            user_id=user.user_id,
            email=user.email,
            role=user.role,
            org_id=user.org_id,
            is_active=user.is_active
        )
    )
