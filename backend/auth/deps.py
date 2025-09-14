"""
Authentication dependencies for FastAPI.
"""

from typing import AsyncGenerator, Optional
from fastapi import Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from ..core.db import get_async_session
from ..models.user import User
from .security import oauth2_scheme, verify_refresh_token, get_current_user

async def get_current_active_user(
    current_user: str = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session)
) -> User:
    """Get current active user.
    
    Args:
        current_user: Current user ID from token
        db: Database session
        
    Returns:
        User object
        
    Raises:
        HTTPException: If user is inactive or not found
    """
    result = await db.execute(
        select(User).where(User.id == current_user)
    )
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user"
        )
    return user

async def get_current_superuser(
    current_user: User = Depends(get_current_active_user),
) -> User:
    """Get current superuser.
    
    Args:
        current_user: Current active user
        
    Returns:
        User object
        
    Raises:
        HTTPException: If user is not a superuser
    """
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="The user doesn't have enough privileges"
        )
    return current_user

async def get_token_from_refresh_token(
    refresh_token: str,
    db: AsyncSession = Depends(get_async_session)
) -> Optional[str]:
    """Get user ID from refresh token.
    
    Args:
        refresh_token: Refresh token
        db: Database session
        
    Returns:
        User ID if token is valid
        
    Raises:
        HTTPException: If token is invalid
    """
    user_id = verify_refresh_token(refresh_token)
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token"
        )
    
    # Verify user exists and is active
    result = await db.execute(
        select(User).where(User.id == user_id)
    )
    user = result.scalar_one_or_none()
    
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token"
        )
    
    return user_id
