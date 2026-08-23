from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api import assessment

app = FastAPI(
    title="AI Assessment Generator",
    description="Backend API for AI Assessment Generator",
    version="1.0.0"
)

# Enable CORS for all origins to prevent Network Error / CORS blocking on Vercel deployments
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/api/health")
def health_check():
    return {"status": "ok", "message": "API is healthy"}

app.include_router(assessment.router, prefix="/api/assessment", tags=["Assessment"])
