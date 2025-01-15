from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.api import deps
from app.schemas.notification import Notification, NotificationCreate
from app.models.notification import Notification as NotificationModel
from app.models.user import User
from app.db.session import get_db
from app.core.cache import get_cache, set_cache, clear_cache_pattern

router = APIRouter()

@router.get("/", response_model=List[Notification])
async def get_notifications(
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.get_current_user),
    skip: int = 0,
    limit: int = 100
):
    """
    Get all notifications for the current user
    """
    notifications = db.query(NotificationModel).filter(
        NotificationModel.user_ids.contains([current_user.id])
    ).offset(skip).limit(limit).all()
    return notifications

@router.get("/{notification_id}", response_model=Notification)
async def get_notification(
    notification_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.get_current_user)
):
    """
    Get a specific notification
    """
    notification = db.query(NotificationModel).filter(
        NotificationModel.id == notification_id,
        NotificationModel.user_ids.contains([current_user.id])
    ).first()
    if not notification:
        raise HTTPException(status_code=404, detail="Notification not found")
    return notification

@router.post("/", response_model=Notification)
async def create_notification(
    notification: NotificationCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.get_current_superuser)
):
    """
    Create a new notification (admin only)
    """
    db_notification = NotificationModel(**notification.dict())
    db.add(db_notification)
    db.commit()
    db.refresh(db_notification)
    return db_notification

@router.delete("/{notification_id}")
async def delete_notification(
    notification_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.get_current_superuser)
):
    """
    Delete a notification (admin only)
    """
    notification = db.query(NotificationModel).filter(NotificationModel.id == notification_id).first()
    if not notification:
        raise HTTPException(status_code=404, detail="Notification not found")
    
    db.delete(notification)
    db.commit()
    return {"message": "Notification deleted successfully"} 