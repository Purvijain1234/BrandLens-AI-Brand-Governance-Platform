from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, Dict, Any

from backend.app.core.config import settings
from backend.app.core.security import get_current_user, create_access_token, UserPayload, DEMO_USERS
from backend.app.db.database import db

app = FastAPI(
    title="BrandLens API",
    description="AI Brand-Governance Platform by Team Double Trouble (Inkloom AI Hackathon)",
    version="1.0.0",
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all during hackathon development / previews
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class LoginRequest(BaseModel):
    role: str = "creator"  # 'creator' | 'reviewer' | 'manager' | 'admin'
    email: Optional[str] = None
    password: Optional[str] = None

@app.get("/")
def root():
    return {
        "app": "BrandLens",
        "team": "Double Trouble",
        "status": "online",
        "environment": settings.ENVIRONMENT,
        "llm_provider": settings.LLM_PROVIDER,
        "database": "sqlite_ready" if not settings.SUPABASE_URL else "supabase_configured",
    }

@app.get("/health")
def health():
    return {"status": "ok"}

@app.post("/auth/login")
def login(req: LoginRequest):
    role_key = req.role.lower()
    if role_key not in DEMO_USERS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid role '{req.role}'. Choose from {list(DEMO_USERS.keys())}",
        )
    user_data = DEMO_USERS[role_key]
    token = create_access_token(user_data)
    return {
        "access_token": token,
        "token_type": "bearer",
        "user": user_data,
    }

@app.get("/auth/me")
def get_me(current_user: UserPayload = Depends(get_current_user)):
    return {
        "user": current_user.model_dump(),
        "available_roles": list(DEMO_USERS.keys()),
    }

from backend.app.api.knowledge_base import router as kb_router

app.include_router(kb_router)
