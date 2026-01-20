from sqlalchemy import Column, String, Text, DateTime, ForeignKey, Enum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid
import enum

from app.database import Base


class NotificationChannel(str, enum.Enum):
    EMAIL = "email"
    DISCORD = "discord"
    DASHBOARD = "dashboard"


class NotificationStatus(str, enum.Enum):
    PENDING = "pending"
    SENT = "sent"
    FAILED = "failed"


class Notification(Base):
    __tablename__ = "notifications"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    job_posting_id = Column(UUID(as_uuid=True), ForeignKey("job_postings.id"), nullable=False)

    channel = Column(Enum(NotificationChannel), nullable=False)
    status = Column(Enum(NotificationStatus), default=NotificationStatus.PENDING, nullable=False)

    sent_at = Column(DateTime, nullable=True)
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    user = relationship("User", back_populates="notifications")
    job_posting = relationship("JobPosting", back_populates="notifications")

    def __repr__(self):
        return f"<Notification(user_id='{self.user_id}', channel='{self.channel}', status='{self.status}')>"


class NotificationQueue(Base):
    __tablename__ = "notification_queue"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    job_posting_id = Column(UUID(as_uuid=True), ForeignKey("job_postings.id"), nullable=False)

    # Which channels to notify (can be multiple)
    channels = Column(String, nullable=False)  # Comma-separated: "email,discord,dashboard"
    priority = Column(String, default=0, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    def __repr__(self):
        return f"<NotificationQueue(user_id='{self.user_id}', channels='{self.channels}')>"
