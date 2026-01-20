from sqlalchemy import Column, String, Text, Boolean, DateTime, ForeignKey, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

from app.models.base import Base


class JobPosting(Base):
    __tablename__ = "job_postings"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    career_page_id = Column(UUID(as_uuid=True), ForeignKey("career_pages.id"), nullable=False)
    external_id = Column(String, unique=True, nullable=False, index=True)

    # Normalized fields (extracted by LLM from raw_data)
    title = Column(String, nullable=False)
    location = Column(String, nullable=True)
    job_type = Column(String, nullable=True)  # e.g., "Full-time", "Remote", "Contract"
    experience_level = Column(String, nullable=True)  # e.g., "Senior", "Mid-level", "Entry"
    description = Column(Text, nullable=True)
    requirements = Column(Text, nullable=True)
    url = Column(String, nullable=False)

    # Complete raw data from Firecrawl (preserves everything)
    raw_data = Column(JSON, default={}, nullable=False)

    # Metadata
    normalized_at = Column(DateTime, nullable=True)
    first_seen_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    last_seen_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    career_page = relationship("CareerPage", back_populates="job_postings")
    notifications = relationship("Notification", back_populates="job_posting")

    def __repr__(self):
        return f"<JobPosting(title='{self.title}', company='{self.career_page.company_name if self.career_page else 'N/A'}')>"
