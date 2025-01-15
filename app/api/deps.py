from typing import Generator, Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError
from sqlalchemy.orm import Session
from app.core.config import settings
from app.core import security
from app.core.security import verify_password
from app.db.session import get_db
from app.models.user import User
from app.schemas.auth import TokenPayload
from functools import wraps
from app.core.cache import get_cache, set_cache
from app.core.security import get_token_payload

oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.API_V1_STR}/auth/login")

async def get_current_user(
    db: Session = Depends(get_db),
    token: str = Depends(oauth2_scheme)
) -> User:
    """
    Get current user from token
    """
    try:
        payload = get_token_payload(token)
        user = db.query(User).filter(User.id == int(payload["sub"])).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        return user
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

def cache_response(expire: int = 3600, key_prefix: str = ""):
    """
    Cache decorator for API responses
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Generate cache key from function arguments
            cache_key = f"{key_prefix}:{func.__name__}"
            if kwargs:
                cache_key += f":{hash(frozenset(kwargs.items()))}"
            
            # Try to get from cache
            cached_data = get_cache(cache_key)
            if cached_data is not None:
                return cached_data
            
            # Execute function and cache result
            result = await func(*args, **kwargs)
            set_cache(cache_key, result, expire)
            return result
        return wrapper
    return decorator 

def get_db() -> Generator:
    try:
        db = SessionLocal()
        yield db
    finally:
        db.close()

async def get_current_active_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """
    Get current active user
    """
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user"
        )
    return current_user

async def get_current_superuser(
    current_user: User = Depends(get_current_active_user)
) -> User:
    """
    Get current superuser
    """
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    return current_user 