from typing import Generator, Callable
from functools import wraps
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError
from sqlalchemy.orm import Session
from app.core.config import settings
from app.db.session import SessionLocal
from app.models.user import User as UserModel
from app.schemas.auth import TokenPayload
from app.core.cache import get_cache, set_cache
import json
from fastapi.encoders import jsonable_encoder

oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.API_V1_STR}/auth/login")

def get_db() -> Generator:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

async def get_current_user(
    db: Session = Depends(get_db),
    token: str = Depends(oauth2_scheme)
) -> UserModel:
    try:
        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
        )
        token_data = TokenPayload(**payload)
        if token_data.sub is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials",
            )
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
        )
    
    user = db.query(UserModel).filter(UserModel.id == int(token_data.sub)).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user

def cache_response(expire: int = 3600, key_prefix: str = "") -> Callable:
    """
    Cache decorator for API responses
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Remove non-serializable objects from cache key generation
            cache_kwargs = {
                k: v for k, v in kwargs.items() 
                if k not in ['db', 'current_user']
            }
            
            # Generate cache key from function name and arguments
            cache_key = f"{key_prefix}:{func.__name__}"
            if cache_kwargs:
                cache_key += f":{json.dumps(cache_kwargs, sort_keys=True)}"
            
            # Try to get from cache
            cached_response = get_cache(cache_key)
            if cached_response is not None:
                return json.loads(cached_response)
            
            # If not in cache, execute function
            response = await func(*args, **kwargs)
            
            # Convert response to JSON-serializable format
            json_response = jsonable_encoder(response)
            
            # Store in cache
            set_cache(
                cache_key,
                json.dumps(json_response),
                expire=expire
            )
            
            return response
        return wrapper
    return decorator

async def get_current_active_user(
    current_user: UserModel = Depends(get_current_user)
) -> UserModel:
    if not current_user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user

async def get_current_superuser(
    current_user: UserModel = Depends(get_current_user)
) -> UserModel:
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=403, 
            detail="The user doesn't have enough privileges"
        )
    return current_user 