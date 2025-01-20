from typing import List
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Security, status
from sqlalchemy.orm import Session
from app.api import deps
from app.schemas.user import User, UserCreate, UserUpdate, PasswordReset, PasswordResetConfirm
from app.models.user import User as UserModel
from app.core.security import get_password_hash
from app.db.session import get_db
from app.core.cache import get_cache, set_cache, clear_cache_pattern
from app.utils.email import send_reset_password_email
from fastapi.security import HTTPAuthorizationCredentials
import secrets

router = APIRouter()

# Standard error messages
USER_NOT_FOUND = "User not found"
UNAUTHORIZED = "Not enough permissions"
EMAIL_IN_USE = "Email already registered"

@router.get("/", response_model=List[User])
async def get_users(
    db: Session = Depends(get_db),
    credentials: HTTPAuthorizationCredentials = Security(deps.security),
    skip: int = 0,
    limit: int = 100
):
    """Get all users (admin only)"""
    try:
        current_user = await deps.get_current_user(credentials, db)
        if not current_user.get("is_superuser"):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=UNAUTHORIZED
            )
        
        cache_key = f"user:list:{skip}:{limit}"
        cached_data = get_cache(cache_key)
        if cached_data:
            return cached_data
            
        users = db.query(UserModel).offset(skip).limit(limit).all()
        set_cache(cache_key, users, expire=1800)
        return users
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving users: {str(e)}"
        )

@router.get("/{user_id}", response_model=User)
async def get_user(
    user_id: int,
    db: Session = Depends(get_db),
    credentials: HTTPAuthorizationCredentials = Security(deps.security)
):
    """Get user details"""
    try:
        current_user = await deps.get_current_user(credentials, db)
        
        # Check all possible admin fields
        is_admin = any([
            current_user.get("is_superuser"),
            current_user.get("odoo_login") == "admin",
            current_user.get("name") == "Administrator",
            current_user.get("login") == "admin",
            current_user.get("role") == "admin"
        ])
        
        # Check if the user is an admin or trying to access their own details
        is_self = current_user.get("id") == user_id
        
        if not is_admin and not is_self:
            raise HTTPException(status_code=403, detail="Not enough permissions")
        
        user = db.query(UserModel).filter(UserModel.id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        return user
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error retrieving user: {str(e)}"
        )

@router.post("/", response_model=User)
async def create_user(
    user: UserCreate,
    db: Session = Depends(get_db)
):
    """Create new user"""
    db_user = db.query(UserModel).filter(UserModel.email == user.email).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    hashed_password = get_password_hash(user.password)
    db_user = UserModel(
        **user.dict(exclude={'password'}),
        hashed_password=hashed_password
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

@router.put("/{user_id}", response_model=User)
async def update_user(
    user_id: int,
    user: UserUpdate,
    db: Session = Depends(get_db),
    credentials: HTTPAuthorizationCredentials = Security(deps.security)
):
    """Update user details"""
    current_user = await deps.get_current_user(credentials, db)
    if not current_user.get("is_superuser") and current_user.get("id") != user_id:
        raise HTTPException(status_code=403, detail="Not enough permissions")
    
    db_user = db.query(UserModel).filter(UserModel.id == user_id).first()
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")
    
    for key, value in user.dict(exclude_unset=True).items():
        setattr(db_user, key, value)
    
    db.commit()
    db.refresh(db_user)
    return db_user

@router.delete("/{user_id}")
async def delete_user(
    user_id: int,
    db: Session = Depends(get_db),
    credentials: HTTPAuthorizationCredentials = Security(deps.security)
):
    """Delete user (admin only)"""
    current_user = await deps.get_current_user(credentials, db)
    if not current_user.get("is_superuser"):
        raise HTTPException(status_code=403, detail="Not enough permissions")
    
    user = db.query(UserModel).filter(UserModel.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    db.delete(user)
    db.commit()
    return {"message": "User deleted successfully"}

@router.post("/password-reset", response_model=dict)
async def request_password_reset(
    reset_request: PasswordReset,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """Request password reset"""
    user = db.query(UserModel).filter(UserModel.email == reset_request.email).first()
    if user:
        token = secrets.token_urlsafe(32)
        # Store token in cache with expiry
        set_cache(f"password_reset:{token}", user.id, expire=1800)  # 30 minutes expiry
        background_tasks.add_task(send_reset_password_email, user.email, token)
    
    return {"message": "If the email exists, a password reset link will be sent"}

@router.post("/password-reset/confirm")
async def confirm_password_reset(
    reset_confirm: PasswordResetConfirm,
    db: Session = Depends(get_db)
):
    """Confirm password reset"""
    user_id = get_cache(f"password_reset:{reset_confirm.token}")
    if not user_id:
        raise HTTPException(status_code=400, detail="Invalid or expired token")
    
    user = db.query(UserModel).filter(UserModel.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    user.hashed_password = get_password_hash(reset_confirm.new_password)
    db.commit()
    
    # Clear the reset token
    clear_cache_pattern(f"password_reset:{reset_confirm.token}")
    
    return {"message": "Password updated successfully"} 