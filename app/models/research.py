from sqlalchemy import Column, String, Text, DateTime, ForeignKey, Enum
from sqlalchemy import UUID as PG_UUID
from datetime import datetime
import uuid
from app.database import Base

class ResearchJob(Base):
    __tablename__ = "research_jobs"

    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(PG_UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    topic = Column(String(500), nullable=False)
    status = Column(
        Enum("pending", "running", "completed", "failed", name="research_status_enum"),
        default="pending"
    )
    search_results = Column(Text, nullable=True)
    scraped_content = Column(Text, nullable=True)
    report = Column(Text, nullable=True)
    feedback = Column(Text, nullable=True)
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)