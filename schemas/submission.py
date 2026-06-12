from pydantic import BaseModel
from enum import Enum

class CurrentStatus(Enum):
    approved = "approved"
    rejected = "rejected"
    pending = "pending"

class CreateSubmissionModel(BaseModel):
    level_id: int
    progress: int
    video_url: str