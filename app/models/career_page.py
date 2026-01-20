from sqlalchemy import Column, String, Boolean, DateTime, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

from app.database import Base


class CareerPage(Base):
    __tablename__ = "career_pages"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_name = Column(String, nullable=False)
    url = Column(String, unique=True, nullable=False, index=True)
    scrape_config = Column(JSON, default={})
    is_active = Column(Boolean, default=True, nullable=False)
    last_scraped_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    job_postings = relationship("JobPosting", back_populates="career_page")

    def __repr__(self):
        return f"<CareerPage(company_name='{self.company_name}', url='{self.url}')>"
