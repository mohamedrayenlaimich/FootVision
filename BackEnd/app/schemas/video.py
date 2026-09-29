from pydantic import BaseModel
from typing import Optional

class VideoUploadResponse(BaseModel):
    video_id: str
    filename: str
    status: str
    message: str
    file_size_bytes: int

class VideoStatusResponse(BaseModel):
    video_id: str
    filename: str
    status: str
    progress_percentage: float
    total_frames: int
    processed_frames: int
    error_message: Optional[str] = None
