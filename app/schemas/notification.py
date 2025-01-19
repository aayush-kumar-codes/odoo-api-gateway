from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime
from enum import Enum

class NotificationStatus(str, Enum):
    PENDING = "pending"
    SENT = "sent"
    FAILED = "failed"

class NotificationBase(BaseModel):
    title: str
    body: str
    user_ids: List[int]

class NotificationCreate(NotificationBase):
    pass

class NotificationUpdate(BaseModel):
    title: Optional[str] = None
    body: Optional[str] = None
    status: Optional[NotificationStatus] = None

class Notification(NotificationBase):
    id: int
    created_at: datetime
    updated_at: datetime
    status: NotificationStatus

    model_config = {
        "from_attributes": True
    } 