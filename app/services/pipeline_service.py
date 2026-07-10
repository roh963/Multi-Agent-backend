from sqlalchemy.orm import Session
from datetime import datetime
from app.models.research import ResearchJob
from app.models.user import User
import uuid
import sys
import os

# Tera pipeline.py root mein hai, usse import karo
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from pipeline import run_research_pipeline

class PipelineService:
    def run(self, db: Session, user: User, topic: str) -> ResearchJob:
        # Job create karo DB mein (status = running)
        job = ResearchJob(
            id=uuid.uuid4(),        # ✅ str() mat karo — UUID column hai
            user_id=user.id,        # ✅ same
            topic=topic,
            status="running")
        db.add(job)
        db.commit()

        try:
            # Tera existing pipeline call karo
            state = run_research_pipeline(topic)
            
            # Results save karo
            job.search_results = str(state.get("search_results", ""))
            job.scraped_content = str(state.get("scraped_content", ""))
            job.report = str(state.get("report", ""))
            job.feedback = str(state.get("feedback", ""))
            job.status = "completed"
            job.completed_at = datetime.utcnow()
        except Exception as e:
            job.status = "failed"
            job.error_message = str(e)
        
        db.commit()
        db.refresh(job)
        return job

    def get_job(self, db: Session, job_id: str, user_id: str) -> ResearchJob:
        return db.query(ResearchJob).filter(
            ResearchJob.id == job_id,
            ResearchJob.user_id == user_id
        ).first()

    def get_user_jobs(self, db: Session, user_id: str) -> list:
        return db.query(ResearchJob).filter(
            ResearchJob.user_id == user_id
        ).order_by(ResearchJob.created_at.desc()).all()

pipeline_service = PipelineService()