from datetime import timedelta
from typing import Any
from fastapi import APIRouter, Depends, HTTPException, status, Security
from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer
from sqlalchemy.orm import Session
from jose import JWTError, jwt
import time

from app.api import deps
from app.core.config import settings
from app.core.security import (
    create_access_token,
    create_refresh_token,
    verify_password,
    get_token_payload,
    get_password_hash
)
from app.schemas.auth import Token, UserLogin, RefreshToken
from app.models.user import User as UserModel
from app.db.session import get_db
from app.core.cache import redis_client
from app.schemas.user import UserCreate, User as UserSchema

router = APIRouter()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.API_V1_STR}/auth/login")

@router.post("/login", response_model=Token)
def login(
    db: Session = Depends(get_db),
    form_data: OAuth2PasswordRequestForm = Depends()
) -> Any:
    """
    OAuth2 compatible token login, get an access token for future requests
    """
    user = db.query(UserModel).filter(UserModel.email == form_data.username).first()
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token = create_access_token(data={"sub": str(user.id)})
    refresh_token = create_refresh_token(data={"sub": str(user.id)})
    
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer"
    }

@router.post("/refresh", response_model=Token)
async def refresh_token(
    refresh_token_data: RefreshToken,
    db: Session = Depends(get_db)
) -> Any:
    """
    Refresh access token using refresh token
    """
    try:
        payload = get_token_payload(refresh_token_data.refresh_token)
        if not payload or not payload.get("sub"):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token",
            )
        
        # Check if token is blacklisted
        if redis_client.get(f"blacklist:{refresh_token_data.refresh_token}"):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token has been invalidated",
            )
        
        user = db.query(UserModel).filter(UserModel.id == int(payload["sub"])).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found",
            )
        
        access_token = create_access_token(data={"sub": str(user.id)})
        refresh_token = create_refresh_token(data={"sub": str(user.id)})
        
        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer"
        }
        
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate refresh token",
        )

@router.post("/logout")
async def logout(
    token: str = Security(oauth2_scheme)
) -> dict:
    """
    Invalidate the current JWT token by adding it to a blacklist
    """
    try:
        # Add token to blacklist with expiration
        payload = get_token_payload(token)
        exp = payload.get("exp", 0)
        current_time = int(time.time())
        ttl = max(exp - current_time, 0)
        
        # Store in Redis blacklist
        redis_client.setex(
            f"blacklist:{token}",
            ttl,
            "true"
        )
        
        return {"message": "Successfully logged out"}
        
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate token",
        )

@router.get("/me", response_model=Any)
def read_users_me(current_user: UserSchema = Depends(deps.get_current_user)) -> Any:
    """
    Get current user information
    """
    return current_user 

@router.post("/register", response_model=UserSchema)
def register_user(
    user_in: UserCreate,
    db: Session = Depends(deps.get_db)
):
    """
    Register a new user.
    """
    # Check if user already exists
    user = db.query(UserModel).filter(UserModel.email == user_in.email).first()
    if user:
        raise HTTPException(
            status_code=400,
            detail="The user with this email already exists in the system",
        )
    
    # Create new user
    user = UserModel(
        email=user_in.email,
        name=user_in.name,
        hashed_password=get_password_hash(user_in.password),
        phone=user_in.phone,
        is_active=True,
        is_company=user_in.is_company
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user 