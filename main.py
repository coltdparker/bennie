#!/usr/bin/env python3
"""
Main application entry point for Bennie.
This file serves the frontend and provides API endpoints.
"""

import os
import sys
from fastapi import FastAPI, HTTPException, Depends
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from dotenv import load_dotenv
import uvicorn

# Add the project root to the Python path
sys.path.append(os.path.dirname(__file__))

from database.connection import get_db, init_db, test_connection
from database.crud import UserCRUD, EmailScheduler
from database.models import LanguageEnum, AuthProviderEnum

load_dotenv()

# Create FastAPI app
app = FastAPI(
    title="Bennie - AI Language Learning",
    description="AI-powered language learning through personalized emails",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure this properly for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files
app.mount("/static", StaticFiles(directory="."), name="static")

@app.on_event("startup")
async def startup_event():
    """Initialize the application on startup."""
    print("🚀 Starting Bennie application...")
    
    # Test database connection
    if not test_connection():
        print("❌ Database connection failed!")
        return
    
    # Initialize database tables
    try:
        init_db()
        print("✅ Database initialized successfully!")
    except Exception as e:
        print(f"❌ Database initialization failed: {e}")

@app.get("/")
async def read_root():
    """Serve the main landing page."""
    return FileResponse("index.html")

@app.get("/onboard")
async def read_onboard():
    """Serve the onboarding page."""
    return FileResponse("onboard.html")

@app.get("/health")
async def health_check():
    """Health check endpoint for Railway."""
    return {"status": "healthy", "service": "bennie"}

# API Endpoints
from pydantic import BaseModel

class UserCreate(BaseModel):
    email: str
    name: str
    language: str
    nickname: str = None

@app.post("/api/users")
async def create_user(
    user_data: UserCreate,
    db: Session = Depends(get_db)
):
    """Create a new user."""
    try:
        # Validate language
        try:
            target_language = LanguageEnum(user_data.language.lower())
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid language")
        
        # Check if user already exists
        existing_user = UserCRUD.get_user_by_email(db, user_data.email)
        if existing_user:
            raise HTTPException(status_code=400, detail="User already exists")
        
        # Create user
        user = UserCRUD.create_user(
            db=db,
            email=user_data.email,
            name=user_data.name,
            target_language=target_language,
            nickname=user_data.nickname
        )
        
        # Set up default email schedule
        scheduler = EmailScheduler()
        scheduler.setup_default_schedules(user.id)
        
        return {
            "success": True,
            "user_id": user.id,
            "message": "User created successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/onboard")
async def complete_onboarding(
    token: str,
    skill_level: int,
    learning_goal: str,
    topics_of_interest: str,
    db: Session = Depends(get_db)
):
    """Complete user onboarding."""
    try:
        # In a real app, you'd validate the token
        # For now, we'll assume it's valid
        
        # Update user profile with onboarding data
        # This is a simplified version - you'd need to implement token validation
        
        return {
            "success": True,
            "message": "Onboarding completed successfully"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/users/{user_id}")
async def get_user(user_id: int, db: Session = Depends(get_db)):
    """Get user information."""
    user = UserCRUD.get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    return {
        "id": user.id,
        "email": user.email,
        "name": user.name,
        "nickname": user.nickname,
        "target_language": user.target_language.value,
        "proficiency_level": user.proficiency_level,
        "is_active": user.is_active,
        "created_at": user.created_at.isoformat() if user.created_at else None
    }

@app.post("/api/emails/send-scheduled")
async def send_scheduled_emails():
    """Manually trigger scheduled email sending (for testing)."""
    try:
        from database.email_scheduler import run_scheduled_emails
        results = run_scheduled_emails()
        return {
            "success": True,
            "results": results
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    # Get port from environment (Railway sets PORT)
    port = int(os.getenv("PORT", 8000))
    
    # Run the application
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=port,
        reload=os.getenv("DEBUG", "False").lower() == "true"
    ) 