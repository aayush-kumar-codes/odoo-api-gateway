from typing import List
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from app.api import deps
from app.schemas.user import User, UserCreate, UserUpdate, PasswordReset, PasswordResetConfirm
from app.models.user import User as UserModel
from app.core.security import get_password_hash
from app.db.session import get_db
from app.core.cache import get_cache, set_cache, clear_cache_pattern
from app.utils.email import send_reset_password_email
import secrets

router = APIRouter()

@router.get("/", response_model=List[User])
async def get_users(
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(deps.get_current_superuser),
    skip: int = 0,
    limit: int = 100
):
    """Get all users (admin only)"""
    users = db.query(UserModel).offset(skip).limit(limit).all()
    return users

@router.get("/{user_id}", response_model=User)
async def get_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(deps.get_current_user)
):
    """Get user details"""
    if not current_user.is_superuser and current_user.id != user_id:
        raise HTTPException(status_code=403, detail="Not enough permissions")
    
    user = db.query(UserModel).filter(UserModel.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user

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
    current_user: UserModel = Depends(deps.get_current_user)
):
    """Update user details"""
    if not current_user.is_superuser and current_user.id != user_id:
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
    current_user: UserModel = Depends(deps.get_current_superuser)
):
    """Delete user (admin only)"""
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