# app/schemas/research.py

from pydantic import BaseModel, Field , field_validator
from typing import Optional
from datetime import datetime

class RunPipelineRequest(BaseModel):
    topic: str

class PipelineResponse(BaseModel):
    job_id: str = Field(alias='id')
    topic: str
    status: str
    search_results: Optional[str] = None
    scraped_content: Optional[str] = None
    report: Optional[str] = None
    feedback: Optional[str] = None
    created_at: datetime

    model_config = {
        "from_attributes": True,
        "populate_by_name": True,
    }

    @field_validator("job_id", mode="before")
    @classmethod
    def uuid_to_str(cls, v) -> str:
        return str(v)   # ✅ UUID → str