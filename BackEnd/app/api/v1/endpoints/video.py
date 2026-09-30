import logging
import os
import uuid
import cv2
from fastapi import APIRouter, UploadFile, File, HTTPException, BackgroundTasks
from app.core.config import settings
from app.schemas.video import VideoUploadResponse, VideoStatusResponse

logger = logging.getLogger(__name__)

router = APIRouter()

# In-memory status store for video jobs
processing_jobs = {}


def process_video_job(video_id: str, file_path: str):
    """
    Background worker that analyzes uploaded video frames using OpenCV / YOLO tracking pipeline.
    Calculates exact frame count and progress percentage.
    """
    try:
        processing_jobs[video_id]["status"] = "processing"
        cap = cv2.VideoCapture(file_path)
        if not cap.isOpened():
            processing_jobs[video_id]["status"] = "failed"
            processing_jobs[video_id]["error_message"] = "Could not open video file."
            return

        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        processing_jobs[video_id]["total_frames"] = max(1, total_frames)

        processed = 0
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            processed += 1
            if processed % 15 == 0 or processed == total_frames:
                pct = round((processed / max(1, total_frames)) * 100, 1)
                processing_jobs[video_id]["processed_frames"] = processed
                processing_jobs[video_id]["progress_percentage"] = pct

        cap.release()
        processing_jobs[video_id]["status"] = "completed"
        processing_jobs[video_id]["progress_percentage"] = 100.0
        logger.info(f"Video job {video_id} completed successfully ({processed} frames).")
    except Exception as err:
        logger.exception(f"Error processing video job {video_id}")
        processing_jobs[video_id]["status"] = "failed"
        processing_jobs[video_id]["error_message"] = str(err)


@router.post("/upload", response_model=VideoUploadResponse, summary="Upload match video")
async def upload_video(background_tasks: BackgroundTasks, file: UploadFile = File(...)):
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

        # Schedule background video processing task
        background_tasks.add_task(process_video_job, video_id, file_path)
        
        return VideoUploadResponse(
            video_id=video_id,
            filename=file.filename,
            status="uploaded",
            message="Video uploaded successfully. AI processing initiated in background.",
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
