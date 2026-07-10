from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.dependencies.auth import get_current_user
from app.models.user import User
from app.schemas.research import RunPipelineRequest, PipelineResponse
from app.services.pipeline_service import pipeline_service

router = APIRouter(prefix="/pipeline", tags=["Pipeline"])

@router.post("/run", response_model=PipelineResponse)
def run_pipeline(
    request: RunPipelineRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)  # JWT guard!
):
    """Multi-agent research pipeline run karo — authenticated users only"""
    job = pipeline_service.run(db, current_user, request.topic)
    return job

@router.get("/jobs", response_model=list[PipelineResponse])
def get_my_jobs(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Mere saare past research jobs dekho"""
    return pipeline_service.get_user_jobs(db, current_user.id)

@router.get("/jobs/{job_id}", response_model=PipelineResponse)
def get_job(
    job_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    job = pipeline_service.get_job(db, job_id, current_user.id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job