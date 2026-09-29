from fastapi import APIRouter
from app.api.v1.endpoints import health, video, analytics, prediction

api_router = APIRouter()

api_router.include_router(health.router, tags=["Health"])
api_router.include_router(video.router, prefix="/video", tags=["Video Processing"])
api_router.include_router(analytics.router, prefix="/analytics", tags=["Analytics"])
api_router.include_router(prediction.router, prefix="/prediction", tags=["Match Prediction"])
