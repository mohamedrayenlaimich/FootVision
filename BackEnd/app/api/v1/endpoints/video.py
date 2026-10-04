import json
import logging
import os
import shutil
import uuid
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, UploadFile, File, HTTPException, BackgroundTasks, Query
from fastapi.responses import FileResponse

from app.core.config import settings
from app.schemas.video import VideoUploadResponse, VideoStatusResponse, VideoTelemetryResponse
from app.services.video_analysis_service import VideoAnalysisPipeline

logger = logging.getLogger("footvision.video_api")

router = APIRouter()

# In-memory status store for video analysis jobs
processing_jobs = {}

# Lazy pipeline singleton instance
_pipeline: Optional[VideoAnalysisPipeline] = None


def get_pipeline() -> VideoAnalysisPipeline:
    global _pipeline
    if _pipeline is None:
        _pipeline = VideoAnalysisPipeline(process_every_n=1)
    return _pipeline


def run_video_pipeline_job(video_id: str, file_path: str, max_frames: Optional[int] = None, process_every_n: int = 1):
    """
    Background worker that runs the computer vision tracking & analysis pipeline.
    """
    try:
        processing_jobs[video_id]["status"] = "processing"
        processing_jobs[video_id]["current_stage"] = "Multi-Object Tracking & Color Classification"

        output_video_path = os.path.join(settings.PROCESSED_DIR, f"annotated_{video_id}.mp4")
        output_telemetry_path = os.path.join(settings.PROCESSED_DIR, f"tracking_{video_id}.json")

        pipeline = get_pipeline()
        pipeline.process_every_n = max(1, process_every_n)

        def on_progress(data: dict):
            # Update in-memory job status with live pipeline metrics
            job = processing_jobs.get(video_id)
            if job:
                job.update(data)
                job["processed_video_url"] = f"/api/v1/video/stream/{video_id}"
                job["original_video_url"] = f"/api/v1/video/original/{video_id}"
                job["download_url"] = f"/api/v1/video/download/{video_id}"
                job["telemetry_url"] = f"/api/v1/video/tracking/{video_id}"

        summary = pipeline.process_video(
            video_id=video_id,
            input_path=file_path,
            output_video_path=output_video_path,
            output_telemetry_path=output_telemetry_path,
            progress_callback=on_progress,
            max_frames=max_frames,
        )

        processing_jobs[video_id]["status"] = "completed"
        processing_jobs[video_id]["progress_percentage"] = 100.0
        processing_jobs[video_id]["current_stage"] = "Analysis Complete"
        processing_jobs[video_id]["output_video_path"] = summary.get("output_video_path", output_video_path)
        processing_jobs[video_id]["output_telemetry_path"] = output_telemetry_path
        processing_jobs[video_id]["total_detected_players"] = summary.get("total_unique_players", 0)
        processing_jobs[video_id]["team_a_players_count"] = summary.get("team_a_players_count", 0)
        processing_jobs[video_id]["team_b_players_count"] = summary.get("team_b_players_count", 0)
        processing_jobs[video_id]["referee_detected"] = summary.get("referee_detected", False)
        processing_jobs[video_id]["ball_visibility_percentage"] = summary.get("ball_visibility_percentage", 0.0)
        processing_jobs[video_id]["duration_seconds"] = summary.get("duration_seconds", 0.0)
        processing_jobs[video_id]["processed_video_url"] = f"/api/v1/video/stream/{video_id}"
        processing_jobs[video_id]["original_video_url"] = f"/api/v1/video/original/{video_id}"
        processing_jobs[video_id]["download_url"] = f"/api/v1/video/download/{video_id}"
        processing_jobs[video_id]["telemetry_url"] = f"/api/v1/video/tracking/{video_id}"

        logger.info(f"Video job {video_id} completed successfully.")

    except Exception as err:
        logger.exception(f"Error in video pipeline job {video_id}: {err}")
        processing_jobs[video_id]["status"] = "failed"
        processing_jobs[video_id]["error_message"] = str(err)
        processing_jobs[video_id]["current_stage"] = "Failed"


@router.post("/upload", response_model=VideoUploadResponse, summary="Upload match video for AI visual tracking")
async def upload_video(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    max_frames: Optional[int] = Query(None, description="Optional limit of frames to process for quick preview"),
    process_every_n: int = Query(1, ge=1, le=5, description="Inference frame stride (1=every frame, 2=CPU speedup)"),
):
    if not file.filename.lower().endswith(('.mp4', '.avi', '.mov', '.mkv')):
        raise HTTPException(status_code=400, detail="Invalid video format. Supported: MP4, AVI, MOV, MKV")

    video_id = str(uuid.uuid4())
    safe_filename = f"{video_id}_{file.filename}"
    file_path = os.path.join(settings.UPLOAD_DIR, safe_filename)

    try:
        contents = await file.read()
        file_size = len(contents)
        with open(file_path, "wb") as f:
            f.write(contents)

        processing_jobs[video_id] = {
            "video_id": video_id,
            "filename": file.filename,
            "status": "uploaded",
            "current_stage": "Video Ingestion & Validation",
            "progress_percentage": 0.0,
            "total_frames": 0,
            "processed_frames": 0,
            "file_path": file_path,
            "original_video_url": f"/api/v1/video/original/{video_id}",
        }

        # Launch real AI computer vision pipeline asynchronously in background
        background_tasks.add_task(
            run_video_pipeline_job,
            video_id,
            file_path,
            max_frames,
            process_every_n,
        )

        return VideoUploadResponse(
            video_id=video_id,
            filename=file.filename,
            status="uploaded",
            message="Video uploaded successfully. AI Computer Vision tracking initiated in background.",
            file_size_bytes=file_size,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to process video upload: {str(e)}")


@router.post("/process-sample", response_model=VideoUploadResponse, summary="Process existing test sample video")
def process_sample_video(
    background_tasks: BackgroundTasks,
    max_frames: Optional[int] = Query(150, description="Number of frames to process (default 150 for quick demo)"),
    process_every_n: int = Query(1, ge=1, le=5),
):
    """
    Convenience endpoint: process Data/raw/test.mp4 directly without uploading.
    """
    raw_sample = os.path.join(settings.BASE_DIR, "Data", "raw", "test.mp4")
    if not os.path.exists(raw_sample):
        raise HTTPException(status_code=404, detail="Data/raw/test.mp4 sample video not found on server.")

    video_id = str(uuid.uuid4())
    target_path = os.path.join(settings.UPLOAD_DIR, f"{video_id}_sample_test.mp4")
    shutil.copy2(raw_sample, target_path)
    file_size = os.path.getsize(target_path)

    processing_jobs[video_id] = {
        "video_id": video_id,
        "filename": "sample_match.mp4",
        "status": "uploaded",
        "current_stage": "Sample Ingested",
        "progress_percentage": 0.0,
        "total_frames": 0,
        "processed_frames": 0,
        "file_path": target_path,
        "original_video_url": f"/api/v1/video/original/{video_id}",
    }

    background_tasks.add_task(
        run_video_pipeline_job,
        video_id,
        target_path,
        max_frames,
        process_every_n,
    )

    return VideoUploadResponse(
        video_id=video_id,
        filename="sample_match.mp4",
        status="uploaded",
        message="Sample match video loaded. AI tracking started in background.",
        file_size_bytes=file_size,
    )


@router.get("/status/{video_id}", response_model=VideoStatusResponse, summary="Get tracking job status and metrics")
def get_video_status(video_id: str):
    if video_id not in processing_jobs:
        raise HTTPException(status_code=404, detail="Video job not found")

    job = processing_jobs[video_id]
    return VideoStatusResponse(
        video_id=video_id,
        filename=job["filename"],
        status=job["status"],
        progress_percentage=job.get("progress_percentage", 0.0),
        total_frames=job.get("total_frames", 0),
        processed_frames=job.get("processed_frames", 0),
        error_message=job.get("error_message"),
        current_stage=job.get("current_stage"),
        current_fps=job.get("current_fps"),
        total_detected_players=job.get("total_detected_players"),
        team_a_players_count=job.get("team_a_players_count"),
        team_b_players_count=job.get("team_b_players_count"),
        referee_detected=job.get("referee_detected"),
        ball_detected=job.get("ball_detected"),
        ball_visibility_percentage=job.get("ball_visibility_percentage"),
        duration_seconds=job.get("duration_seconds"),
        processed_video_url=job.get("processed_video_url"),
        original_video_url=job.get("original_video_url"),
        download_url=job.get("download_url"),
        telemetry_url=job.get("telemetry_url"),
    )


def find_processed_video(video_id: str, job: Optional[dict] = None) -> Optional[str]:
    if job and "output_video_path" in job and os.path.exists(job["output_video_path"]):
        return job["output_video_path"]

    candidates = [
        os.path.join(settings.PROCESSED_DIR, f"annotated_{video_id}.mp4"),
        os.path.join(settings.BASE_DIR, "Data", "processed", f"annotated_{video_id}.mp4"),
        os.path.join(settings.BASE_DIR, "..", "Data", "processed", f"annotated_{video_id}.mp4"),
        os.path.join(settings.PROCESSED_DIR, f"annotated_{video_id}.avi"),
    ]
    for c in candidates:
        if os.path.exists(c):
            return os.path.abspath(c)
    return None


def find_original_video(video_id: str, job: Optional[dict] = None) -> Optional[str]:
    if job and "file_path" in job and os.path.exists(job["file_path"]):
        return job["file_path"]

    search_dirs = [
        settings.UPLOAD_DIR,
        os.path.join(settings.BASE_DIR, "Data", "uploads"),
        os.path.join(settings.BASE_DIR, "..", "Data", "uploads"),
    ]
    for d in search_dirs:
        if os.path.exists(d):
            for f in os.listdir(d):
                if f.startswith(video_id):
                    return os.path.join(d, f)
    return None


@router.get("/stream/{video_id}", summary="Stream annotated video")
def stream_processed_video(video_id: str):
    job = processing_jobs.get(video_id)
    out_path = find_processed_video(video_id, job)

    if not out_path or not os.path.exists(out_path):
        raise HTTPException(status_code=404, detail="Processed video not available yet")

    return FileResponse(out_path, media_type="video/mp4", headers={"Accept-Ranges": "bytes"})


@router.get("/original/{video_id}", summary="Stream original uploaded video")
def stream_original_video(video_id: str):
    job = processing_jobs.get(video_id)
    orig_path = find_original_video(video_id, job)
    if not orig_path or not os.path.exists(orig_path):
        raise HTTPException(status_code=404, detail="Original video file not found")

    return FileResponse(orig_path, media_type="video/mp4", headers={"Accept-Ranges": "bytes"})


@router.get("/download/{video_id}", summary="Download processed annotated video")
def download_processed_video(video_id: str):
    job = processing_jobs.get(video_id)
    out_path = find_processed_video(video_id, job)

    if not out_path or not os.path.exists(out_path):
        raise HTTPException(status_code=404, detail="Processed video file not available for download")

    filename = job.get("filename", "match.mp4") if job else "match.mp4"
    return FileResponse(
        out_path,
        media_type="video/mp4",
        filename=f"annotated_{filename}",
    )


@router.get("/tracking/{video_id}", summary="Get structured tracking telemetry JSON")
def get_video_tracking_data(video_id: str):
    telemetry_file = os.path.join(settings.PROCESSED_DIR, f"tracking_{video_id}.json")
    if not os.path.exists(telemetry_file):
        raise HTTPException(status_code=404, detail="Tracking telemetry data not found for this video")

    with open(telemetry_file, "r", encoding="utf-8") as f:
        data = json.load(f)

    return data
