import os
import uuid
from fastapi import APIRouter, UploadFile, File, HTTPException, BackgroundTasks
from app.core.config import settings
from app.schemas.video import VideoUploadResponse, VideoStatusResponse

router = APIRouter()

# In-memory status store for demo/initial implementation
processing_jobs = {}

@router.post("/upload", response_model=VideoUploadResponse, summary="Upload match video")
async def upload_video(file: UploadFile = File(...)):
    if not file.filename.endswith(('.mp4', '.avi', '.mov', '.mkv')):
        raise HTTPException(status_code=400, detail="Invalid video format. Supported: mp4, avi, mov, mkv")
    
    video_id = str(uuid.uuid4())
    filename = f"{video_id}_{file.filename}"
    file_path = os.path.join(settings.UPLOAD_DIR, filename)
    
    try:
        contents = await file.read()
        file_size = len(contents)
        with open(file_path, "wb") as f:
            f.write(contents)
            
        processing_jobs[video_id] = {
            "filename": file.filename,
            "status": "uploaded",
            "progress_percentage": 0.0,
            "total_frames": 0,
            "processed_frames": 0,
            "file_path": file_path
        }
        
        return VideoUploadResponse(
            video_id=video_id,
            filename=file.filename,
            status="uploaded",
            message="File uploaded successfully",
            file_size_bytes=file_size
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save video: {str(e)}")

@router.get("/status/{video_id}", response_model=VideoStatusResponse, summary="Get processing status")
def get_video_status(video_id: str):
    if video_id not in processing_jobs:
        raise HTTPException(status_code=404, detail="Video job not found")
    
    job = processing_jobs[video_id]
    return VideoStatusResponse(
        video_id=video_id,
        filename=job["filename"],
        status=job["status"],
        progress_percentage=job["progress_percentage"],
        total_frames=job["total_frames"],
        processed_frames=job["processed_frames"],
        error_message=job.get("error_message")
    )
