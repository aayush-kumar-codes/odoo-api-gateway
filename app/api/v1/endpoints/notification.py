from typing import List
from fastapi import APIRouter, Depends, HTTPException, Security, status
from sqlalchemy.orm import Session
from app.api import deps
from app.schemas.notification import Notification, NotificationCreate
from app.models.notification import Notification as NotificationModel
from app.db.session import get_db
from app.core.cache import get_cache, set_cache, delete_cache, clear_cache_pattern
from fastapi.security import HTTPAuthorizationCredentials

router = APIRouter()

# Standard error messages
NOTIFICATION_NOT_FOUND = "Notification not found"
UNAUTHORIZED = "Not enough permissions"

@router.get("/", response_model=List[Notification])
async def get_notifications(
    db: Session = Depends(get_db),
    credentials: HTTPAuthorizationCredentials = Security(deps.security),
    skip: int = 0,
    limit: int = 100
):
    """Get user notifications"""
    try:
        current_user = await deps.get_current_user(credentials, db)
        user_id = current_user.get('id')
        
        cache_key = f"notification:list:{user_id}:{skip}:{limit}"
        cached_data = get_cache(cache_key)
        if cached_data:
            return cached_data
            
        notifications = db.query(NotificationModel)\
            .filter(NotificationModel.user_id == user_id)\
            .order_by(NotificationModel.created_at.desc())\
            .offset(skip)\
            .limit(limit)\
            .all()
            
        set_cache(cache_key, notifications, expire=300)  # Cache for 5 minutes
        return notifications
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving notifications: {str(e)}"
        )

@router.get("/{notification_id}", response_model=Notification)
async def get_notification(
    notification_id: int,
    db: Session = Depends(get_db),
    credentials: HTTPAuthorizationCredentials = Security(deps.security)
):
    """
    Get a specific notification
    """
    current_user = await deps.get_current_user(credentials, db)
    
    cache_key = f"notification:{notification_id}:user:{current_user.get('id')}"
    cached_data = get_cache(cache_key)
    if cached_data:
        return cached_data
    
    notification = db.query(NotificationModel).filter(
        NotificationModel.id == notification_id,
        NotificationModel.user_ids.contains([current_user.get('id')])
    ).first()
    
    if not notification:
        raise HTTPException(status_code=404, detail="Notification not found")
    
    set_cache(cache_key, notification, expire=300)  # Cache for 5 minutes
    return notification

@router.post("/", response_model=Notification)
async def create_notification(
    notification: NotificationCreate,
    db: Session = Depends(get_db),
    credentials: HTTPAuthorizationCredentials = Security(deps.security)
):
    """
    Create a new notification (admin only)
    """
    # Verify authentication and superuser status
    current_user = await deps.get_current_user(credentials, db)
    if not current_user.get("is_superuser"):
        raise HTTPException(
            status_code=403,
            detail="Not enough permissions. Superuser required."
        )
    
    db_notification = NotificationModel(**notification.dict())
    db.add(db_notification)
    db.commit()
    db.refresh(db_notification)
    
    # Clear notification caches for affected users
    for user_id in notification.user_ids:
        delete_cache(f"notifications:user:{user_id}:*")
    
    return db_notification

@router.delete("/{notification_id}")
async def delete_notification(
    notification_id: int,
    db: Session = Depends(get_db),
    credentials: HTTPAuthorizationCredentials = Security(deps.security)
):
    """
    Delete a notification (admin only)
    """
    # Verify authentication and superuser status
    current_user = await deps.get_current_user(credentials, db)
    if not current_user.get("is_superuser"):
        raise HTTPException(
            status_code=403,
            detail="Not enough permissions. Superuser required."
        )
    
    notification = db.query(NotificationModel).filter(NotificationModel.id == notification_id).first()
    if not notification:
        raise HTTPException(status_code=404, detail="Notification not found")
    
    # Store user_ids before deletion for cache clearing
    affected_user_ids = notification.user_ids
    
    db.delete(notification)
    db.commit()
    
    # Clear notification caches for affected users
    for user_id in affected_user_ids:
        delete_cache(f"notifications:user:{user_id}:*")
        delete_cache(f"notification:{notification_id}:user:{user_id}")
    
    return {"message": "Notification deleted successfully"}

@router.put("/{notification_id}/mark-read")
async def mark_notification_read(
    notification_id: int,
    db: Session = Depends(get_db),
    credentials: HTTPAuthorizationCredentials = Security(deps.security)
):
    """
    Mark a notification as read for the current user
    """
    current_user = await deps.get_current_user(credentials, db)
    
    notification = db.query(NotificationModel).filter(
        NotificationModel.id == notification_id,
        NotificationModel.user_ids.contains([current_user.get('id')])
    ).first()
    
    if not notification:
        raise HTTPException(status_code=404, detail="Notification not found")
    
    if current_user.get('id') not in notification.read_by:
        notification.read_by.append(current_user.get('id'))
        db.commit()
        db.refresh(notification)
        
        # Clear user's notification caches
        delete_cache(f"notifications:user:{current_user.get('id')}:*")
        delete_cache(f"notification:{notification_id}:user:{current_user.get('id')}")
    
    return notification 