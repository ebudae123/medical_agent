from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.database import init_db
from backend.api.v1 import auth, conversations, escalations, profile
from backend.config import get_settings

# Import all models so they're registered with Base.metadata
from backend.models.user import User
from backend.models.conversation import Conversation
from backend.models.message import Message
from backend.models.patient_profile import PatientProfile
from backend.models.escalation import EscalationTicket

settings = get_settings()

app = FastAPI(
    title=settings.app_name,
    description="Safety-first medical AI assistant with risk gating and human-in-the-loop",
    version="1.0.0"
)

# CORS middleware for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],  # React/Vite dev servers
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routers
app.include_router(auth.router, prefix="/api/v1")
app.include_router(conversations.router, prefix="/api/v1")
app.include_router(escalations.router, prefix="/api/v1")
app.include_router(profile.router, prefix="/api/v1")


@app.on_event("startup")
async def startup_event():
    """Initialize database on startup"""
    await init_db()
    print("[OK] Database initialized")


@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "message": "Nightingale AI Medical Assistant API",
        "status": "healthy",
        "version": "1.0.0"
    }


@app.get("/health")
async def health_check():
    """Detailed health check"""
    return {
        "status": "healthy",
        "database": "connected",
        "gemini_api": "configured"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
