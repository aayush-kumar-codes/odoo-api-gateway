from typing import Generator, Dict, Any, Callable
from functools import wraps
from fastapi import Depends, HTTPException, status, Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import jwt, JWTError
from sqlalchemy.orm import Session
from app.core.config import settings
from app.core.odoo_client import OdooClient
from app.db.session import SessionLocal
from app.models.user import User as UserModel
from app.schemas.auth import TokenPayload
from app.core.cache import get_cache, set_cache, redis_client
import json
from fastapi.encoders import jsonable_encoder

security = HTTPBearer()

def get_db() -> Generator:
    try:
        db = SessionLocal()
        yield db
    finally:
        db.close()

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Security(security),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """Base authentication - returns current user info"""
    try:
        token = credentials.credentials
        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
        )
        uid = int(payload.get("sub"))
        if not uid:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials"
            )
        
        # Check token blacklist
        if redis_client and redis_client.get(f"blacklist:{token}"):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token has been invalidated"
            )
            
        # Verify user in Odoo
        try:
            odoo = OdooClient()
            user_info = odoo.get_user_info(uid)
            if not user_info:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="User no longer exists"
                )
            return user_info
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Error connecting to authentication service"
            )
            
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials"
        )
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Authentication error occurred"
        )

def cache_response(expire: int = 3600, key_prefix: str = "") -> Callable:
    """
    Cache decorator for API responses
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            try:
                # Cache key generation
                cache_kwargs = {
                    k: v for k, v in kwargs.items() 
                    if k not in ['db', 'current_user', 'credentials']
                }
                
                cache_key = f"{key_prefix}:{func.__name__}"
                if cache_kwargs:
                    cache_key += f":{json.dumps(cache_kwargs, sort_keys=True)}"
                
                # Try cache
                if redis_client:
                    cached_response = get_cache(cache_key)
                    if cached_response is not None:
                        return json.loads(cached_response)
                
                # Execute function
                response = await func(*args, **kwargs)
                json_response = jsonable_encoder(response)
                
                # Cache response
                if redis_client:
                    set_cache(
                        cache_key,
                        json.dumps(json_response),
                        expire=expire
                    )
                
                return response
            except Exception as e:
                # Log cache error but continue with original function
                response = await func(*args, **kwargs)
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
    current_user: Dict[str, Any] = Security(get_current_user)
) -> Dict[str, Any]:
    """Superuser authentication - returns current superuser info"""
    if not current_user.get("is_superuser"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Superuser privileges required"
        )
    return current_user

# Callable dependencies for router use
require_auth = Security(get_current_user)
require_superuser = Security(get_current_superuser) 