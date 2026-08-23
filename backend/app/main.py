from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api import assessment
from app.config import settings

app = FastAPI(
    title="AI Assessment Generator",
    description="Backend API for AI Assessment Generator",
    version="1.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.FRONTEND_URL, "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/api/health")
def health_check():
    return {"status": "ok", "message": "API is healthy"}

app.include_router(assessment.router, prefix="/api/assessment", tags=["Assessment"])
