from sqlalchemy import Column, String, Boolean, DateTime, JSON, ARRAY
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

from app.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String, unique=True, nullable=False, index=True)
    discord_webhook_url = Column(String, nullable=True)

    # User preferences stored as JSON
    # Structure: {
    #   "locations": ["Remote", "New York", "San Francisco"],
    #   "job_types": ["Full-time", "Contract"],
    #   "experience_levels": ["Senior", "Lead"],
    #   "company_ids": ["uuid1", "uuid2"]  # Specific companies to follow
    # }
    preferences = Column(JSON, default={}, nullable=False)

    # Notification channels: email, discord, dashboard
    notification_channels = Column(ARRAY(String), default=["email"], nullable=False)

    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    notifications = relationship("Notification", back_populates="user")

    def __repr__(self):
        return f"<User(email='{self.email}')>"
