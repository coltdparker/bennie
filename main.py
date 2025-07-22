#!/usr/bin/env python3
"""
Main application entry point for Bennie.
This file serves the frontend and provides API endpoints.
"""

import os
import logging
import secrets
from fastapi import FastAPI, HTTPException, BackgroundTasks, Request, Header, Query, status
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
import uvicorn
from pydantic import BaseModel, EmailStr, Field
from supabase import create_client, Client
from typing import Optional
import sys
sys.path.append('./Backend')
from new_user_email import send_welcome_email
from Backend.bennie_email_sender import send_language_learning_email
from Backend.openai_connectivity_test import test_openai

import base64
import httpx
from fastapi.exceptions import RequestValidationError

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()

SUPABASE_URL: str = os.getenv("SUPABASE_URL")
SUPABASE_KEY: str = os.getenv("SUPABASE_KEY")

# Debug: Print environment variables (mask key)
logger.info(f"SUPABASE_URL: {SUPABASE_URL}")
logger.info(f"SUPABASE_KEY: {SUPABASE_KEY[:6] + '...' if SUPABASE_KEY else None}")

if not SUPABASE_URL or not SUPABASE_KEY:
    logger.error("Missing required environment variables: SUPABASE_URL or SUPABASE_KEY")
    raise ValueError("Missing required environment variables")

try:
    supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
    logger.info("Supabase client initialized successfully")
except Exception as e:
    logger.error(f"Failed to initialize Supabase client: {e}")
    raise

app = FastAPI()

# CORS middleware configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Update static files configuration
app.mount("/static", StaticFiles(directory="frontend/public/static"), name="static")

# Pydantic models
class UserCreate(BaseModel):
    email: EmailStr
    name: str
    language: str

class OnboardingData(BaseModel):
    token: str
    skill_level: int = Field(ge=1, le=100)
    learning_goal: str
    target_proficiency: int = Field(ge=1, le=100)
    motivation_goal: str
    topics_of_interest: str

@app.get("/")
async def read_root():
    """Serve the landing page."""
    return FileResponse("frontend/src/index.html")

@app.get("/onboard")
async def read_onboard():
    """Serve the onboarding page."""
    return FileResponse("frontend/src/onboard.html")

@app.get("/api/verify-token/{token}")
async def verify_token(token: str):
    """
    Verify a user's onboarding token and return their basic information.
    
    Args:
        token: The verification token from the email link
        
    Returns:
        dict: User information if token is valid
        
    Raises:
        HTTPException: If token is invalid or expired
    """
    try:
        logger.info(f"Verifying token: {token[:10]}...")
        
        # Find user by verification token in auth metadata
        response = supabase.auth.verify_otp(token)
        
        if not response or not response.user:
            logger.warning(f"Invalid token: {token[:10]}...")
            raise HTTPException(status_code=404, detail="Invalid or expired token")
        
        # Get user profile from public.users
        user_response = supabase.table("users").select("auth_user_id, name, target_language").eq("auth_user_id", response.user.id).execute()
        
        if not user_response.data:
            logger.error(f"User profile not found for auth_user_id: {response.user.id}")
            raise HTTPException(status_code=404, detail="User profile not found")
        
        user = user_response.data[0]
        
        return {
            "success": True,
            "user": {
                "id": user["auth_user_id"],
                "email": response.user.email,
                "name": user["name"],
                "target_language": user["target_language"]
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error in verify_token: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@app.post("/api/complete-onboarding")
async def complete_onboarding(onboarding_data: OnboardingData):
    """
    Complete the user's onboarding process.
    
    Args:
        onboarding_data: Onboarding information including token and user preferences
        
    Returns:
        dict: Success response
        
    Raises:
        HTTPException: If token is invalid or update fails
    """
    try:
        # Log all incoming data (except token)
        log_data = onboarding_data.dict()
        log_data["token"] = log_data["token"][:10] + "..."  # Truncate token for logging
        logger.info(f"Received onboarding data: {log_data}")
        
        # First verify the token and get user
        auth_response = supabase.auth.verify_otp(onboarding_data.token)
        
        if not auth_response or not auth_response.user:
            logger.warning(f"Invalid token attempted: {onboarding_data.token[:10]}...")
            raise HTTPException(status_code=404, detail="Invalid or expired token")
        
        auth_user_id = auth_response.user.id
        logger.info(f"Token verified for auth_user_id: {auth_user_id}")
        
        # Update user with onboarding information
        update_data = {
            "proficiency_level": onboarding_data.skill_level,
            "learning_goal": onboarding_data.learning_goal,
            "target_proficiency": onboarding_data.target_proficiency,
            "motivation_goal": onboarding_data.motivation_goal,
            "topics_of_interest": onboarding_data.topics_of_interest,
            "updated_at": "now()"
        }
        
        logger.info(f"Updating user {auth_user_id} with data: {update_data}")
        update_response = supabase.table("users").update(update_data).eq("auth_user_id", auth_user_id).execute()
        
        if not update_response.data:
            logger.error(f"Failed to update user: {update_response.error}")
            raise HTTPException(status_code=500, detail="Failed to update user profile")
        
        return {
            "success": True,
            "message": "Onboarding completed successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error in complete_onboarding: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@app.get("/health")
async def health_check():
    """Health check endpoint for Railway."""
    try:
        # Test Supabase connection
        response = supabase.table("users").select("count", count="exact").limit(1).execute()
        logger.info("Health check: Supabase connection successful")
        return {
            "status": "healthy", 
            "service": "bennie",
            "database": "connected",
            "timestamp": "2025-01-27T00:00:00Z"
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {
            "status": "unhealthy",
            "service": "bennie", 
            "database": "disconnected",
            "error": str(e)
        }

@app.post("/api/users")
async def create_user(user_data: UserCreate, background_tasks: BackgroundTasks):
    """
    Create a new user in the database.
    
    Args:
        user_data: User information including email, name, and target language
        
    Returns:
        dict: Success response with user ID and message
        
    Raises:
        HTTPException: If user already exists or database operation fails
    """
    try:
        logger.info(f"Creating user: {user_data.email}")
        
        # Check if user already exists in auth.users
        try:
            existing_user = supabase.auth.admin.get_user_by_email(user_data.email)
            if existing_user:
                logger.warning(f"User already exists: {user_data.email}")
                raise HTTPException(status_code=400, detail="User already exists")
        except Exception as e:
            if "User not found" not in str(e):
                raise
        
        # Create user in auth.users with metadata
        auth_response = supabase.auth.admin.create_user({
            "email": user_data.email.lower().strip(),
            "email_confirm": True,  # Auto-confirm for now
            "user_metadata": {
                "name": user_data.name.strip(),
                "target_language": user_data.language.lower().strip(),
                "proficiency_level": 1,  # Default starting level
                "topics_of_interest": "",  # Will be set during onboarding
                "learning_goal": None,  # Will be set during onboarding
                "motivation_goal": None,  # Will be set during onboarding
                "target_proficiency": 50,  # Default target
                "email_schedule": {"frequency": "weekly"}
            }
        })
        
        if not auth_response or not auth_response.user:
            logger.error("Failed to create auth user")
            raise HTTPException(status_code=500, detail="Failed to create user")
        
        # The trigger will automatically create the user profile in public.users
        
        # Generate and send magic link for onboarding
        magic_link = supabase.auth.admin.generate_magic_link(user_data.email)
        
        # Send welcome email with magic link
        background_tasks.add_task(
            send_welcome_email,
            user_name=user_data.name,
            user_email=user_data.email,
            user_language=user_data.language,
            user_token=magic_link
        )
        
        return {
            "success": True,
            "user_id": auth_response.user.id,
            "message": "User created successfully. Check your email to complete onboarding.",
            "user": {
                "email": user_data.email,
                "name": user_data.name,
                "target_language": user_data.language
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error in create_user: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@app.get("/api/users/{email}")
async def get_user(email: str):
    """
    Get user information by email.
    
    Args:
        email: User's email address
        
    Returns:
        dict: User information
        
    Raises:
        HTTPException: If user not found or database operation fails
    """
    try:
        logger.info(f"Getting user: {email}")
        
        # Get auth user first
        auth_user = supabase.auth.admin.get_user_by_email(email)
        
        if not auth_user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Get user profile from public.users
        response = supabase.table("users").select("*").eq("auth_user_id", auth_user.id).execute()
        
        if not response.data:
            raise HTTPException(status_code=404, detail="User profile not found")
        
        user = response.data[0]
        # Remove sensitive fields
        user.pop("auth_user_id", None)
        
        return {"success": True, "user": user}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error in get_user: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@app.post("/api/sendgrid-inbound")
async def sendgrid_inbound(request: Request, secret: Optional[str] = Query(None)):
    """Handle inbound emails from SendGrid."""
    try:
        # Log all form data for debugging
        form = await request.form()
        logger.info(f"Form data received: {dict(form)}")
        
        sender_email = form.get('from')
        text_content = form.get('text')
        subject = form.get('subject', 'No subject')
        
        logger.info(f"Sender: {sender_email}")
        logger.info(f"Subject: {subject}")
        logger.info(f"Content length: {len(text_content) if text_content else 0}")

        if not sender_email or not text_content:
            logger.error("Missing sender or content in webhook")
            return {"success": False, "error": "Missing sender or content"}

        # Extract just the email address (in case it's 'Name <email@example.com>')
        import re
        match = re.search(r'<(.+?)>', sender_email)
        if match:
            sender_email = match.group(1)
        else:
            sender_email = sender_email.strip()
            
        logger.info(f"Cleaned sender email: {sender_email}")

        # Get auth user first
        auth_user = supabase.auth.admin.get_user_by_email(sender_email.lower())
        
        if not auth_user:
            logger.error(f"User not found for email: {sender_email}")
            return {"success": False, "error": "User not found"}
        
        # Find user profile
        user_resp = supabase.table("users").select(
            "auth_user_id, name, target_language, proficiency_level, instant_reply"
        ).eq("auth_user_id", auth_user.id).execute()
        
        if not user_resp.data:
            logger.error(f"User profile not found for auth_user_id: {auth_user.id}")
            return {"success": False, "error": "User profile not found"}
        
        user = user_resp.data[0]
        instant_reply = user.get("instant_reply", False)
        
        # Save the email in history
        email_data = {
            "auth_user_id": user["auth_user_id"],
            "content": text_content,
            "is_from_bennie": False,
            "difficulty_level": user.get("proficiency_level", 1)
        }
        
        email_resp = supabase.table("email_history").insert(email_data).execute()
        
        if not email_resp.data:
            logger.error("Failed to save email to history")
            return {"success": False, "error": "Failed to save email"}
        
        # If instant reply is enabled, send a response
        if instant_reply:
            background_tasks.add_task(send_language_learning_email, sender_email)
        
        return {"success": True}
        
    except Exception as e:
        logger.error(f"Error processing inbound email: {e}")
        return {"success": False, "error": str(e)}

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True) 