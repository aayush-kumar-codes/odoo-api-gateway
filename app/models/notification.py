from sqlalchemy import Column, Integer, String, DateTime, Enum, Table, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
import enum
from app.db.session import Base

class NotificationStatus(str, enum.Enum):
    PENDING = "pending"
    SENT = "sent"
    FAILED = "failed"

# Many-to-many relationship table for notifications and users
notification_users = Table(
    'notification_users',
    Base.metadata,
    Column('notification_id', Integer, ForeignKey('notifications.id')),
    Column('user_id', Integer, ForeignKey('users.id'))
)

class Notification(Base):
    __tablename__ = "notifications"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    body = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    status = Column(Enum(NotificationStatus), default=NotificationStatus.PENDING)
    
    # Many-to-many relationship with users
    users = relationship("User", secondary=notification_users, backref="notifications") 